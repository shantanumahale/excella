"""
Validator: Data quality checks for normalized financial statements.

Catches accounting-identity violations, missing required fields,
suspicious outliers, and time-series anomalies before data reaches
downstream metrics and analytics.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Required fields per statement type (at least these must be present)
# ---------------------------------------------------------------------------

REQUIRED_FIELDS: dict[str, list[str]] = {
    "income": ["revenue", "net_income"],
    "balance": ["total_assets"],
    "cashflow": ["operating_cash_flow"],
}

# Maximum plausible value for any single financial field (in USD)
_MAX_PLAUSIBLE_VALUE = 1e15

# Tolerance for accounting identity checks
_IDENTITY_TOLERANCE = 0.01  # 1%
_EPS_TOLERANCE = 0.05       # 5%

# Time-series swing threshold
_MAX_PERIOD_CHANGE = 5.0  # 500%


def _approx_equal(a: float, b: float, tolerance: float = _IDENTITY_TOLERANCE) -> bool:
    """Return True if a and b are within *tolerance* of each other (relative)."""
    if a == 0 and b == 0:
        return True
    denom = max(abs(a), abs(b))
    if denom == 0:
        return True
    return abs(a - b) / denom <= tolerance


def _check_required_fields(
    statement_type: str,
    data: dict[str, Any],
    errors: list[str],
) -> None:
    required = REQUIRED_FIELDS.get(statement_type, [])
    for field in required:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")


def _check_outliers(
    data: dict[str, Any],
    warnings: list[str],
) -> None:
    for field, value in data.items():
        if value is None:
            continue
        try:
            num = float(value)
        except (TypeError, ValueError):
            continue
        if abs(num) > _MAX_PLAUSIBLE_VALUE:
            warnings.append(
                f"Suspicious value for {field}: {num:.2e} exceeds {_MAX_PLAUSIBLE_VALUE:.0e}"
            )


def _check_signs(
    statement_type: str,
    data: dict[str, Any],
    warnings: list[str],
) -> None:
    """Verify that fields which should be non-negative are non-negative."""
    if statement_type == "income":
        revenue = data.get("revenue")
        if revenue is not None and revenue < 0:
            warnings.append(f"Revenue is negative: {revenue}")
        shares = data.get("shares_basic")
        if shares is not None and shares <= 0:
            warnings.append(f"Basic shares outstanding is non-positive: {shares}")
        shares_d = data.get("shares_diluted")
        if shares_d is not None and shares_d <= 0:
            warnings.append(f"Diluted shares outstanding is non-positive: {shares_d}")

    elif statement_type == "balance":
        total_assets = data.get("total_assets")
        if total_assets is not None and total_assets < 0:
            warnings.append(f"Total assets is negative: {total_assets}")


def _check_balance_sheet_identity(
    data: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Assets should approximately equal Liabilities + Equity."""
    assets = data.get("total_assets")
    liabilities = data.get("total_liabilities")
    equity = data.get("total_equity") or data.get("total_stockholders_equity")

    if assets is None or liabilities is None or equity is None:
        return  # cannot check

    liab_plus_equity = liabilities + equity
    if not _approx_equal(assets, liab_plus_equity):
        errors.append(
            f"Balance sheet identity violated: assets ({assets:,.0f}) != "
            f"liabilities ({liabilities:,.0f}) + equity ({equity:,.0f}) = {liab_plus_equity:,.0f}"
        )


def _check_gross_profit_identity(
    data: dict[str, Any],
    warnings: list[str],
) -> None:
    """gross_profit should approximately equal revenue - cost_of_revenue."""
    gp = data.get("gross_profit")
    revenue = data.get("revenue")
    cor = data.get("cost_of_revenue")

    if gp is None or revenue is None or cor is None:
        return

    expected = revenue - cor
    if not _approx_equal(gp, expected):
        warnings.append(
            f"Gross profit ({gp:,.0f}) != revenue ({revenue:,.0f}) "
            f"- cost_of_revenue ({cor:,.0f}) = {expected:,.0f}"
        )


def _check_eps_consistency(
    data: dict[str, Any],
    warnings: list[str],
) -> None:
    """EPS should approximately equal net_income / shares."""
    net_income = data.get("net_income")
    eps = data.get("eps_basic")
    shares = data.get("shares_basic")

    if net_income is None or eps is None or shares is None:
        return
    if shares == 0:
        warnings.append("Basic shares outstanding is zero; cannot verify EPS")
        return

    computed_eps = net_income / shares
    if not _approx_equal(eps, computed_eps, tolerance=_EPS_TOLERANCE):
        warnings.append(
            f"EPS inconsistency: reported eps_basic ({eps}) vs "
            f"net_income/shares ({computed_eps:.4f})"
        )


def validate_statement(statement_type: str, data: dict[str, Any]) -> dict:
    """Validate a single normalized financial statement.

    Args:
        statement_type: One of "income", "balance", "cashflow".
        data: Dict of canonical field names to numeric values.

    Returns:
        {
            "is_valid": bool,
            "warnings": list[str],
            "errors": list[str],
        }
    """
    errors: list[str] = []
    warnings: list[str] = []

    _check_required_fields(statement_type, data, errors)
    _check_outliers(data, warnings)
    _check_signs(statement_type, data, warnings)

    if statement_type == "income":
        _check_gross_profit_identity(data, warnings)
        _check_eps_consistency(data, warnings)

    if statement_type == "balance":
        _check_balance_sheet_identity(data, errors, warnings)

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(
            "Statement validation failed (%s): %s", statement_type, "; ".join(errors)
        )

    return {
        "is_valid": is_valid,
        "warnings": warnings,
        "errors": errors,
    }


def validate_time_series(statements: list[dict]) -> list[str]:
    """Check a chronological series of statements for anomalies.

    Expects each element to have "period_end", "statement_type", and "data" keys.
    All statements should be of the same type.

    Returns a list of warning strings.
    """
    if len(statements) < 2:
        return []

    warnings: list[str] = []

    # Sort chronologically
    sorted_stmts = sorted(statements, key=lambda s: s["period_end"])

    # Check for period gaps (annual statements should be ~365 days apart)
    for i in range(1, len(sorted_stmts)):
        prev_end = sorted_stmts[i - 1]["period_end"]
        curr_end = sorted_stmts[i]["period_end"]
        gap_days = (curr_end - prev_end).days

        # Annual filings: expect ~365 days; quarterly: ~90 days
        # Flag if gap is unexpectedly large
        if gap_days > 400:
            warnings.append(
                f"Large gap between periods: {prev_end} -> {curr_end} ({gap_days} days)"
            )
        elif gap_days < 30:
            warnings.append(
                f"Suspiciously short period gap: {prev_end} -> {curr_end} ({gap_days} days)"
            )

    # Check for extreme swings in key metrics
    swing_fields = ["revenue", "net_income", "total_assets", "operating_cash_flow"]

    for i in range(1, len(sorted_stmts)):
        prev_data = sorted_stmts[i - 1].get("data", {})
        curr_data = sorted_stmts[i].get("data", {})

        for field in swing_fields:
            prev_val = prev_data.get(field)
            curr_val = curr_data.get(field)

            if prev_val is None or curr_val is None:
                continue
            if prev_val == 0:
                continue

            change_ratio = abs((curr_val - prev_val) / prev_val)
            if change_ratio > _MAX_PERIOD_CHANGE:
                warnings.append(
                    f"Extreme swing in {field}: "
                    f"{prev_val:,.0f} -> {curr_val:,.0f} "
                    f"({change_ratio:.0%} change) between "
                    f"{sorted_stmts[i-1]['period_end']} and {sorted_stmts[i]['period_end']}"
                )

    return warnings
