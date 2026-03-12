"""
Enricher: Orchestrates the full raw -> refined pipeline for a company.

Loads raw XBRL data, normalizes it into canonical statements, validates
data quality, persists refined records, and triggers downstream metrics.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Company, Filing, FinancialStatement, IngestionLog
from app.db.session import SessionLocal
from app.pipeline.normalizer import normalize_company_facts
from app.pipeline.validator import validate_statement, validate_time_series

logger = logging.getLogger(__name__)

# Filing statuses that indicate data is ready for enrichment
_ENRICHABLE_STATUSES = {"parsed", "raw"}


def _load_raw_facts(db_session: Session, company: Company) -> dict | None:
    """Load raw company facts JSON for a company.

    Tries to find the raw JSON stored on the most recent filing record
    or associated ingestion log.
    """
    # Look for the most recent filing with raw data
    filing = (
        db_session.query(Filing)
        .filter(
            Filing.company_id == company.id,
            Filing.status.in_(_ENRICHABLE_STATUSES),
        )
        .order_by(Filing.filing_date.desc())
        .first()
    )

    if filing is None:
        logger.info("No enrichable filing found for company %s (id=%s)", company.ticker, company.id)
        return None

    # Try to get raw JSON from the filing's raw_data field
    raw_data = getattr(filing, "raw_data", None)
    if raw_data:
        if isinstance(raw_data, str):
            return json.loads(raw_data)
        return raw_data

    # Fallback: check the ingestion log for raw payload
    log_entry = (
        db_session.query(IngestionLog)
        .filter(
            IngestionLog.source == "edgar",
            IngestionLog.status == "success",
        )
        .order_by(IngestionLog.started_at.desc())
        .first()
    )

    if log_entry is not None:
        payload = getattr(log_entry, "raw_payload", None) or getattr(log_entry, "payload", None)
        if payload:
            if isinstance(payload, str):
                return json.loads(payload)
            return payload

    logger.warning(
        "Could not locate raw facts JSON for company %s (id=%s)",
        company.ticker, company.id,
    )
    return None


def _upsert_financial_statement(
    db_session: Session,
    company_id: int,
    statement: dict,
    validation: dict,
) -> FinancialStatement:
    """Create or update a FinancialStatement record."""
    existing = (
        db_session.query(FinancialStatement)
        .filter(
            FinancialStatement.company_id == company_id,
            FinancialStatement.period_end == statement["period_end"],
            FinancialStatement.statement_type == statement["statement_type"],
            FinancialStatement.fiscal_period == statement["fiscal_period"],
        )
        .first()
    )

    data_payload = statement["data"]

    if existing:
        existing.data = data_payload
        existing.fiscal_year = statement["fiscal_year"]
        existing.period_type = statement.get("period_type", "annual")
        existing.is_valid = validation["is_valid"]
        existing.validation_warnings = validation.get("warnings", [])
        existing.validation_errors = validation.get("errors", [])
        existing.updated_at = datetime.now(timezone.utc)
        return existing

    record = FinancialStatement(
        company_id=company_id,
        period_end=statement["period_end"],
        fiscal_year=statement["fiscal_year"],
        fiscal_period=statement["fiscal_period"],
        period_type=statement.get("period_type", "annual"),
        statement_type=statement["statement_type"],
        data=data_payload,
        is_valid=validation["is_valid"],
        validation_warnings=validation.get("warnings", []),
        validation_errors=validation.get("errors", []),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(record)
    return record


def _update_filing_status(
    db_session: Session,
    company_id: int,
    new_status: str,
) -> None:
    """Mark all enrichable filings for this company as refined (or errored)."""
    filings = (
        db_session.query(Filing)
        .filter(
            Filing.company_id == company_id,
            Filing.status.in_(_ENRICHABLE_STATUSES),
        )
        .all()
    )
    for filing in filings:
        filing.status = new_status
        filing.updated_at = datetime.now(timezone.utc)


def _log_enrichment(
    db_session: Session,
    company_id: int,
    status: str,
    detail: str | None = None,
) -> None:
    """Write an ingestion log entry for the enrichment step."""
    try:
        log = IngestionLog(
            source="enrichment",
            job_type=f"company_id={company_id}",
            status=status,
            error_message=detail if status == "error" else None,
            started_at=datetime.now(timezone.utc),
        )
        db_session.add(log)
    except Exception:
        # Logging should never break the pipeline
        logger.exception("Failed to write ingestion log for company_id=%s", company_id)


def enrich_company(db_session: Session, company_id: int) -> dict[str, Any]:
    """Run the full raw -> refined pipeline for a single company.

    Steps:
        1. Load raw company facts JSON
        2. Normalize into canonical statement dicts
        3. Validate each statement
        4. Persist/update FinancialStatement records
        5. Trigger downstream metrics computation
        6. Update filing status to "refined"
        7. Log outcome

    Args:
        db_session: Active SQLAlchemy session.
        company_id: Primary key of the Company record.

    Returns:
        Summary dict with counts of statements processed and any issues.
    """
    result: dict[str, Any] = {
        "company_id": company_id,
        "status": "pending",
        "statements_created": 0,
        "statements_updated": 0,
        "validation_errors": 0,
        "validation_warnings": 0,
        "errors": [],
    }

    company = db_session.query(Company).get(company_id)
    if company is None:
        msg = f"Company not found: id={company_id}"
        logger.error(msg)
        result["status"] = "error"
        result["errors"].append(msg)
        return result

    ticker = getattr(company, "ticker", str(company_id))
    logger.info("Starting enrichment for %s (id=%s)", ticker, company_id)

    # Step 1: Load raw data
    raw_json = _load_raw_facts(db_session, company)

    if raw_json is not None:
        # Step 2: Normalize
        try:
            statements = normalize_company_facts(raw_json)
        except Exception as exc:
            msg = f"Normalization failed for {ticker}: {exc}"
            logger.exception(msg)
            result["status"] = "error"
            result["errors"].append(msg)
            _update_filing_status(db_session, company_id, "error")
            _log_enrichment(db_session, company_id, "error", msg)
            db_session.commit()
            return result

        if statements:
            # Step 3 & 4: Validate and persist each statement
            time_series_by_type: dict[str, list[dict]] = {}

            for stmt in statements:
                stmt_type = stmt["statement_type"]
                validation = validate_statement(stmt_type, stmt["data"])

                result["validation_errors"] += len(validation.get("errors", []))
                result["validation_warnings"] += len(validation.get("warnings", []))

                # Skip persisting statements that fail validation (e.g. ghost
                # entries missing required fields like revenue/net_income).
                # This prevents junk rows from reaching the metrics layer.
                if not validation["is_valid"]:
                    logger.info(
                        "Skipping invalid %s statement for %s period_end=%s: %s",
                        stmt_type, ticker, stmt["period_end"],
                        "; ".join(validation.get("errors", [])),
                    )
                    continue

                record = _upsert_financial_statement(db_session, company_id, stmt, validation)

                # Track whether this was an insert or update for the summary
                if record in db_session.new:
                    result["statements_created"] += 1
                else:
                    result["statements_updated"] += 1

                # Collect for time-series validation
                time_series_by_type.setdefault(stmt_type, []).append(stmt)

            # Time-series validation (cross-period checks)
            for stmt_type, series in time_series_by_type.items():
                ts_warnings = validate_time_series(series)
                if ts_warnings:
                    result["validation_warnings"] += len(ts_warnings)
                    for w in ts_warnings:
                        logger.warning("Time-series [%s] %s: %s", ticker, stmt_type, w)

    # Check if FinancialStatement rows exist (either just created or from EDGAR ingestor)
    existing_stmts = (
        db_session.query(FinancialStatement)
        .filter(FinancialStatement.company_id == company_id)
        .count()
    )
    if existing_stmts == 0 and raw_json is None:
        msg = f"No raw facts or financial statements available for {ticker}"
        logger.warning(msg)
        result["status"] = "skipped"
        result["errors"].append(msg)
        return result

    logger.info("Found %d financial statement rows for %s — computing metrics", existing_stmts, ticker)

    # Step 5: Trigger metrics computation
    try:
        from app.metrics.compute import compute_for_company
        compute_for_company(db_session, company_id)
    except ImportError:
        logger.debug("Metrics module not available; skipping compute_for_company")
    except Exception as exc:
        msg = f"Metrics computation failed for {ticker}: {exc}"
        logger.warning(msg)
        result["errors"].append(msg)
        # Non-fatal: enrichment itself succeeded

    # Step 6: Update filing status
    _update_filing_status(db_session, company_id, "refined")

    # Step 7: Commit and log
    try:
        db_session.commit()
        result["status"] = "success"
        _log_enrichment(db_session, company_id, "success",
                        f"Created {result['statements_created']}, "
                        f"updated {result['statements_updated']} statements")
        db_session.commit()
    except Exception as exc:
        db_session.rollback()
        msg = f"Database commit failed for {ticker}: {exc}"
        logger.exception(msg)
        result["status"] = "error"
        result["errors"].append(msg)

    logger.info(
        "Enrichment complete for %s: status=%s, created=%d, updated=%d, "
        "errors=%d, warnings=%d",
        ticker,
        result["status"],
        result["statements_created"],
        result["statements_updated"],
        result["validation_errors"],
        result["validation_warnings"],
    )
    return result


def enrich_all(db_session: Session | None = None) -> dict[str, Any]:
    """Run enrichment for all companies with unprocessed data.

    Finds every company that has filings in "parsed" or "raw" status and
    runs the full pipeline for each.

    Args:
        db_session: Optional SQLAlchemy session. If None, creates one via SessionLocal.

    Returns:
        Summary dict with overall counts and per-company results.
    """
    own_session = False
    if db_session is None:
        db_session = SessionLocal()
        own_session = True

    summary: dict[str, Any] = {
        "total_companies": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped": 0,
        "results": [],
    }

    try:
        # Find companies with enrichable filings OR existing financial statements
        filing_ids = set(
            cid for (cid,) in
            db_session.query(Filing.company_id)
            .filter(Filing.status.in_(_ENRICHABLE_STATUSES))
            .distinct()
            .all()
        )
        stmt_ids = set(
            cid for (cid,) in
            db_session.query(FinancialStatement.company_id)
            .distinct()
            .all()
        )
        company_ids = sorted(filing_ids | stmt_ids)
        summary["total_companies"] = len(company_ids)

        logger.info("Found %d companies with unprocessed filings", len(company_ids))

        for company_id in company_ids:
            try:
                result = enrich_company(db_session, company_id)
                summary["results"].append(result)

                if result["status"] == "success":
                    summary["succeeded"] += 1
                elif result["status"] == "skipped":
                    summary["skipped"] += 1
                else:
                    summary["failed"] += 1

            except Exception as exc:
                logger.exception(
                    "Unexpected error enriching company_id=%s: %s",
                    company_id, exc,
                )
                summary["failed"] += 1
                summary["results"].append({
                    "company_id": company_id,
                    "status": "error",
                    "errors": [str(exc)],
                })

        logger.info(
            "Enrichment batch complete: %d total, %d succeeded, %d failed, %d skipped",
            summary["total_companies"],
            summary["succeeded"],
            summary["failed"],
            summary["skipped"],
        )

    finally:
        if own_session:
            db_session.close()

    return summary
