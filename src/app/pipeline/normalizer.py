"""
Normalizer: Transforms raw SEC EDGAR companyfacts JSON into structured,
canonical financial statement records ready for storage and analysis.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from app.pipeline.xbrl_mapper import (
    STATEMENT_FIELDS,
    get_canonical_field,
    resolve_xbrl_facts,
)

logger = logging.getLogger(__name__)

# Forms we consider authoritative, in preference order
_PREFERRED_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A"}


def _parse_date(date_str: str) -> date:
    """Parse an ISO-format date string."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _period_key(entry: dict) -> tuple[str, int, str]:
    """Build a grouping key from a single XBRL fact entry.

    Returns (end_date_str, fiscal_year, fiscal_period).
    """
    return (entry["end"], entry.get("fy", 0), entry.get("fp", ""))


def _is_preferred_form(form: str) -> bool:
    return form in _PREFERRED_FORMS


def _extract_unit_facts(
    tag: str,
    unit_entries: list[dict],
) -> list[dict]:
    """Filter and annotate entries for a single XBRL tag + unit combination.

    Returns a list of dicts each containing:
        xbrl_tag, end, fy, fp, form, filed, val
    """
    results = []
    for entry in unit_entries:
        # Skip entries that have a "start" and "end" that differ by more than
        # ~400 days when the tag is a balance-sheet (instant) concept being
        # reported with a duration context -- these are almost always garbage.
        form = entry.get("form", "")
        if not _is_preferred_form(form):
            continue

        results.append({
            "xbrl_tag": tag,
            "end": entry.get("end", ""),
            "fy": entry.get("fy", 0),
            "fp": entry.get("fp", ""),
            "form": form,
            "filed": entry.get("filed", ""),
            "val": entry.get("val"),
        })
    return results


def _collect_all_facts(raw_json: dict) -> list[dict]:
    """Walk the companyfacts JSON and emit a flat list of fact dicts."""
    us_gaap = raw_json.get("facts", {}).get("us-gaap", {})
    all_facts: list[dict] = []

    for tag, tag_data in us_gaap.items():
        # Only consider tags that map to a canonical field
        canonical = get_canonical_field(tag)
        if canonical is None:
            continue

        units = tag_data.get("units", {})
        for unit_key, entries in units.items():
            all_facts.extend(_extract_unit_facts(tag, entries))

    return all_facts


def _group_by_period(
    facts: list[dict],
) -> dict[tuple[str, int, str], list[dict]]:
    """Group fact entries by (end_date, fiscal_year, fiscal_period)."""
    groups: dict[tuple[str, int, str], list[dict]] = defaultdict(list)
    for fact in facts:
        key = _period_key(fact)
        groups[key].append(fact)
    return groups


def _deduplicate_facts(facts_for_period: list[dict]) -> dict[str, Any]:
    """For a single period, pick the best value for each XBRL tag.

    When multiple filings report the same tag for the same period, prefer
    the most recently filed value.

    Returns {xbrl_tag: value}.
    """
    best: dict[str, dict] = {}
    for fact in facts_for_period:
        tag = fact["xbrl_tag"]
        if tag not in best:
            best[tag] = fact
        else:
            # Prefer the most recently filed entry
            if fact.get("filed", "") > best[tag].get("filed", ""):
                best[tag] = fact

    return {tag: entry["val"] for tag, entry in best.items()}


def _determine_fiscal_period_type(fp: str) -> str:
    """Map fiscal period codes to human-readable labels."""
    mapping = {
        "FY": "annual",
        "Q1": "quarterly",
        "Q2": "quarterly",
        "Q3": "quarterly",
        "Q4": "quarterly",
    }
    return mapping.get(fp, "other")


def normalize_company_facts(raw_json: dict) -> list[dict]:
    """Parse SEC EDGAR companyfacts JSON into canonical statement dicts.

    Args:
        raw_json: The full companyfacts JSON as returned by the SEC EDGAR API.

    Returns:
        A list of statement dicts, each with:
            - period_end: date
            - fiscal_year: int
            - fiscal_period: str  (e.g. "FY", "Q1")
            - period_type: str  ("annual" or "quarterly")
            - statement_type: str  ("income", "balance", "cashflow")
            - data: dict[str, numeric]  (canonical field -> value)
    """
    entity_name = raw_json.get("entityName", "Unknown")
    cik = raw_json.get("cik", 0)
    logger.info("Normalizing company facts for %s (CIK %s)", entity_name, cik)

    all_facts = _collect_all_facts(raw_json)
    if not all_facts:
        logger.warning("No mappable US-GAAP facts found for CIK %s", cik)
        return []

    period_groups = _group_by_period(all_facts)
    logger.info("Found %d distinct periods for CIK %s", len(period_groups), cik)

    statements: list[dict] = []

    for (end_str, fy, fp), period_facts in period_groups.items():
        if not end_str:
            continue

        try:
            period_end = _parse_date(end_str)
        except (ValueError, TypeError):
            logger.debug("Skipping period with unparseable date: %s", end_str)
            continue

        # Skip non-standard fiscal periods
        period_type = _determine_fiscal_period_type(fp)
        if period_type == "other":
            continue

        # Deduplicate: one value per XBRL tag for this period
        deduped_facts = _deduplicate_facts(period_facts)

        # Resolve into each statement type
        for stmt_type in ("income", "balance", "cashflow"):
            resolved = resolve_xbrl_facts(deduped_facts, stmt_type)
            if not resolved:
                continue

            statements.append({
                "period_end": period_end,
                "fiscal_year": fy,
                "fiscal_period": fp,
                "period_type": period_type,
                "statement_type": stmt_type,
                "data": resolved,
            })

    # Sort by period_end ascending, then statement_type
    statements.sort(key=lambda s: (s["period_end"], s["statement_type"]))

    logger.info(
        "Produced %d statement records for %s (CIK %s)",
        len(statements), entity_name, cik,
    )
    return statements
