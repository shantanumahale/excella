"""Orchestrator: loads financial data, runs all metric modules, and upserts DerivedMetrics."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import Company, DerivedMetrics, FinancialStatement
from app.metrics import (
    cashflow as cashflow_mod,
    dupont as dupont_mod,
    efficiency as efficiency_mod,
    forensic as forensic_mod,
    growth as growth_mod,
    leverage as leverage_mod,
    liquidity as liquidity_mod,
    per_share as per_share_mod,
    profitability as profitability_mod,
    quality as quality_mod,
    shareholder as shareholder_mod,
    valuation as valuation_mod,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Statement enrichment — compute missing fields from available components
# ---------------------------------------------------------------------------

def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def _enrich_statements(
    income: dict, balance: dict, cashflow: dict,
) -> tuple[dict, dict, dict]:
    """Fill in missing derived fields from available components.

    This ensures metric modules get the most complete data possible,
    even if the EDGAR source didn't report certain fields directly.
    """
    # Work on copies to avoid mutating originals
    inc = dict(income)
    bal = dict(balance)
    cf = dict(cashflow)

    # --- Income statement fallbacks ---

    # Pull D&A from cashflow if missing from income
    if inc.get("depreciation_amortization") is None:
        da = cf.get("depreciation_amortization_cf") or cf.get("depreciation_amortization")
        if da is not None:
            inc["depreciation_amortization"] = da

    # gross_profit = revenue - cost_of_revenue
    if inc.get("gross_profit") is None:
        rev = inc.get("revenue")
        cogs = inc.get("cost_of_revenue")
        if rev is not None and cogs is not None:
            inc["gross_profit"] = rev - cogs

    # operating_income fallbacks
    if inc.get("operating_income") is None:
        rev = inc.get("revenue")
        opex = inc.get("operating_expenses")
        if rev is not None and opex is not None:
            inc["operating_income"] = rev - opex
        elif inc.get("gross_profit") is not None:
            rd = inc.get("research_and_development", 0)
            sga = inc.get("selling_general_admin", 0)
            if rd or sga:
                inc["operating_income"] = inc["gross_profit"] - rd - sga

    # ebitda = operating_income + D&A
    if inc.get("ebitda") is None:
        oi = inc.get("operating_income")
        da = inc.get("depreciation_amortization")
        if oi is not None and da is not None:
            inc["ebitda"] = oi + da

    # pretax_income fallback
    if inc.get("pretax_income") is None and inc.get("operating_income") is not None:
        oi = inc["operating_income"]
        other = inc.get("other_income_expense", 0)
        int_exp = inc.get("interest_expense", 0)
        int_inc = inc.get("interest_income", 0)
        inc["pretax_income"] = oi + (other or 0) - (int_exp or 0) + (int_inc or 0)

    # --- Balance sheet fallbacks ---

    # total_equity fallback from stockholders_equity
    if bal.get("total_equity") is None and bal.get("total_stockholders_equity") is not None:
        bal["total_equity"] = bal["total_stockholders_equity"]
    elif bal.get("total_stockholders_equity") is None and bal.get("total_equity") is not None:
        bal["total_stockholders_equity"] = bal["total_equity"]

    # total_liabilities fallback from total_assets - total_equity
    if bal.get("total_liabilities") is None:
        ta = bal.get("total_assets")
        te = bal.get("total_equity") or bal.get("total_stockholders_equity")
        if ta is not None and te is not None:
            bal["total_liabilities"] = ta - te

    return inc, bal, cf


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _stmt_to_dict(stmt: FinancialStatement | None) -> dict:
    """Convert a FinancialStatement ORM object to a plain dict.

    Returns an empty dict if stmt is None.
    """
    if stmt is None:
        return {}
    # Assume the model exposes a .data JSON column or individual columns.
    # Try .data first (JSONB column pattern), then fall back to __dict__.
    if hasattr(stmt, "data") and isinstance(stmt.data, dict):
        return dict(stmt.data)
    result = {}
    for col in stmt.__table__.columns:
        result[col.name] = getattr(stmt, col.name, None)
    return result


def _load_statements(
    db: Session,
    company_id: int,
    period_end: date,
    fiscal_period: str,
) -> tuple[dict, dict, dict]:
    """Load income, balance, and cashflow statement dicts for a given period."""
    stmts = (
        db.query(FinancialStatement)
        .filter(
            FinancialStatement.company_id == company_id,
            FinancialStatement.period_end == period_end,
            FinancialStatement.fiscal_period == fiscal_period,
        )
        .all()
    )

    income: dict = {}
    balance: dict = {}
    cashflow_data: dict = {}

    for stmt in stmts:
        stype = getattr(stmt, "statement_type", None) or getattr(stmt, "type", None)
        d = _stmt_to_dict(stmt)
        if stype == "income":
            income = d
        elif stype == "balance":
            balance = d
        elif stype in ("cashflow", "cash_flow"):
            cashflow_data = d

    return income, balance, cashflow_data


def _load_prior_statements(
    db: Session,
    company_id: int,
    period_end: date,
    fiscal_period: str,
) -> tuple[dict, dict, dict]:
    """Load the most recent prior period statements (same fiscal_period, earlier date)."""
    stmts = (
        db.query(FinancialStatement)
        .filter(
            FinancialStatement.company_id == company_id,
            FinancialStatement.period_end < period_end,
            FinancialStatement.fiscal_period == fiscal_period,
        )
        .order_by(FinancialStatement.period_end.desc())
        .all()
    )

    if not stmts:
        return {}, {}, {}

    # Take the latest prior period_end
    latest_end = stmts[0].period_end
    prior_stmts = [s for s in stmts if s.period_end == latest_end]

    income: dict = {}
    balance: dict = {}
    cashflow_data: dict = {}

    for stmt in prior_stmts:
        stype = getattr(stmt, "statement_type", None) or getattr(stmt, "type", None)
        d = _stmt_to_dict(stmt)
        if stype == "income":
            income = d
        elif stype == "balance":
            balance = d
        elif stype in ("cashflow", "cash_flow"):
            cashflow_data = d

    return income, balance, cashflow_data


def _load_latest_price(db: Session, company_id: int) -> float | None:
    """Load the most recent closing price from the daily_prices hypertable.

    Joins via the companies table to resolve company_id → ticker.
    """
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company or not company.ticker:
            return None
        result = db.execute(
            text(
                "SELECT adj_close FROM daily_prices "
                "WHERE ticker = :ticker "
                "ORDER BY time DESC LIMIT 1"
            ),
            {"ticker": company.ticker},
        ).fetchone()
        if result and result[0]:
            return float(result[0])
    except Exception:
        logger.debug("Could not load price for company_id=%s", company_id, exc_info=True)
    return None


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def compute_metrics(
    db: Session,
    company_id: int,
    period_end: date,
    fiscal_period: str,
) -> dict[str, Any] | None:
    """Compute all derived metrics for a single company-period.

    Returns the assembled metrics dict, or None if base data is missing.
    """
    income_raw, balance_raw, cashflow_raw = _load_statements(db, company_id, period_end, fiscal_period)

    if not income_raw and not balance_raw and not cashflow_raw:
        logger.info(
            "No financial statements for company_id=%s period_end=%s fiscal_period=%s",
            company_id, period_end, fiscal_period,
        )
        return None

    # Enrich: compute missing derived fields from available components
    income, balance, cashflow_data = _enrich_statements(income_raw, balance_raw, cashflow_raw)

    prior_income_raw, prior_balance_raw, prior_cashflow_raw = _load_prior_statements(
        db, company_id, period_end, fiscal_period,
    )
    # Enrich prior period too so growth comparisons work
    if prior_income_raw or prior_balance_raw or prior_cashflow_raw:
        prior_income, prior_balance, prior_cashflow = _enrich_statements(
            prior_income_raw or {}, prior_balance_raw or {}, prior_cashflow_raw or {},
        )
    else:
        prior_income, prior_balance, prior_cashflow = {}, {}, {}

    price = _load_latest_price(db, company_id)

    # --- Run all metric modules ---
    metrics: dict[str, Any] = {}

    try:
        metrics["profitability"] = profitability_mod.compute(income, balance)
    except Exception:
        logger.exception("profitability failed for company_id=%s", company_id)
        metrics["profitability"] = {}

    try:
        metrics["liquidity"] = liquidity_mod.compute(income, balance)
    except Exception:
        logger.exception("liquidity failed for company_id=%s", company_id)
        metrics["liquidity"] = {}

    try:
        metrics["leverage"] = leverage_mod.compute(income, balance)
    except Exception:
        logger.exception("leverage failed for company_id=%s", company_id)
        metrics["leverage"] = {}

    try:
        metrics["efficiency"] = efficiency_mod.compute(income, balance, cashflow_data)
    except Exception:
        logger.exception("efficiency failed for company_id=%s", company_id)
        metrics["efficiency"] = {}

    try:
        metrics["cashflow"] = cashflow_mod.compute(income, balance, cashflow_data)
    except Exception:
        logger.exception("cashflow failed for company_id=%s", company_id)
        metrics["cashflow"] = {}

    try:
        metrics["growth"] = growth_mod.compute(
            income, balance, cashflow_data,
            prior_income or None, prior_balance or None, prior_cashflow or None,
        )
    except Exception:
        logger.exception("growth failed for company_id=%s", company_id)
        metrics["growth"] = {}

    try:
        metrics["dupont"] = dupont_mod.compute(income, balance)
    except Exception:
        logger.exception("dupont failed for company_id=%s", company_id)
        metrics["dupont"] = {}

    # Valuation needs eps_growth_pct
    eps_growth_pct = metrics.get("growth", {}).get("eps_growth")
    if eps_growth_pct is not None:
        eps_growth_pct = eps_growth_pct * 100  # convert ratio to percentage

    try:
        metrics["valuation"] = valuation_mod.compute(
            income, balance, cashflow_data, price, eps_growth_pct=eps_growth_pct,
        )
    except Exception:
        logger.exception("valuation failed for company_id=%s", company_id)
        metrics["valuation"] = {}

    try:
        metrics["quality"] = quality_mod.compute(
            income, balance, cashflow_data,
            prior_income or None, prior_balance or None, prior_cashflow or None,
        )
    except Exception:
        logger.exception("quality failed for company_id=%s", company_id)
        metrics["quality"] = {}

    # Forensic needs market_cap
    market_cap = metrics.get("valuation", {}).get("market_cap")
    try:
        metrics["forensic"] = forensic_mod.compute(
            income, balance, cashflow_data,
            prior_income or None, prior_balance or None, prior_cashflow or None,
            market_cap=market_cap,
        )
    except Exception:
        logger.exception("forensic failed for company_id=%s", company_id)
        metrics["forensic"] = {}

    try:
        metrics["shareholder"] = shareholder_mod.compute(
            income, balance, cashflow_data, market_cap=market_cap,
        )
    except Exception:
        logger.exception("shareholder failed for company_id=%s", company_id)
        metrics["shareholder"] = {}

    try:
        metrics["per_share"] = per_share_mod.compute(income, balance, cashflow_data)
    except Exception:
        logger.exception("per_share failed for company_id=%s", company_id)
        metrics["per_share"] = {}

    return metrics


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _upsert_derived_metrics(
    db: Session,
    company_id: int,
    period_end: date,
    fiscal_period: str,
    metrics: dict[str, Any],
) -> None:
    """Insert or update DerivedMetrics record.

    The metrics dict has category keys (profitability, liquidity, etc.)
    matching the JSONB columns on DerivedMetrics.
    """
    existing = (
        db.query(DerivedMetrics)
        .filter(
            DerivedMetrics.company_id == company_id,
            DerivedMetrics.period_end == period_end,
            DerivedMetrics.fiscal_period == fiscal_period,
        )
        .first()
    )

    if existing is not None:
        for category, values in metrics.items():
            if hasattr(existing, category):
                setattr(existing, category, values)
        db.commit()
        logger.info(
            "Updated DerivedMetrics for company_id=%s period_end=%s",
            company_id, period_end,
        )
    else:
        record = DerivedMetrics(
            company_id=company_id,
            period_end=period_end,
            fiscal_period=fiscal_period,
        )
        for category, values in metrics.items():
            if hasattr(record, category):
                setattr(record, category, values)
        db.add(record)
        db.commit()
        logger.info(
            "Inserted DerivedMetrics for company_id=%s period_end=%s",
            company_id, period_end,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_for_period(
    db: Session,
    company_id: int,
    period_end: date,
    fiscal_period: str,
) -> dict[str, Any] | None:
    """Compute and persist metrics for a single company-period."""
    metrics = compute_metrics(db, company_id, period_end, fiscal_period)
    if metrics is None:
        return None
    try:
        _upsert_derived_metrics(db, company_id, period_end, fiscal_period, metrics)
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to upsert DerivedMetrics for company_id=%s period_end=%s",
            company_id, period_end,
        )
    return metrics


def compute_for_company(db: Session, company_id: int) -> int:
    """Compute metrics for ALL periods of a company.

    Returns the number of periods processed.
    """
    # Find all distinct (period_end, fiscal_period) combos for this company
    periods = (
        db.query(
            FinancialStatement.period_end,
            FinancialStatement.fiscal_period,
        )
        .filter(FinancialStatement.company_id == company_id)
        .distinct()
        .order_by(FinancialStatement.period_end)
        .all()
    )

    count = 0
    for period_end, fiscal_period in periods:
        try:
            result = compute_for_period(db, company_id, period_end, fiscal_period)
            if result is not None:
                count += 1
        except Exception:
            logger.exception(
                "Failed computing metrics for company_id=%s period_end=%s",
                company_id, period_end,
            )
    logger.info("Computed metrics for %d periods of company_id=%s", count, company_id)
    return count


def compute_all(db: Session) -> int:
    """Compute metrics for ALL companies and ALL periods.

    Returns the total number of periods processed.
    """
    companies = db.query(Company.id).all()
    total = 0
    for (company_id,) in companies:
        try:
            total += compute_for_company(db, company_id)
        except Exception:
            logger.exception("Failed computing metrics for company_id=%s", company_id)
    logger.info("Computed metrics for %d total periods across %d companies", total, len(companies))
    return total
