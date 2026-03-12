"""Leverage metrics: debt ratios, coverage, and financial structure."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(income: dict, balance: dict) -> dict:
    """Compute leverage metrics from income statement and balance sheet data.

    Returns a dict of metric_name -> value (float | None).
    """
    operating_income = income.get("operating_income")
    interest_expense = income.get("interest_expense")
    ebitda = income.get("ebitda")
    depreciation_amortization = income.get("depreciation_amortization")

    # Inline fallbacks
    if operating_income is None:
        rev = income.get("revenue")
        opex = income.get("operating_expenses")
        if rev is not None and opex is not None:
            operating_income = rev - opex
    if ebitda is None and operating_income is not None and depreciation_amortization is not None:
        ebitda = operating_income + depreciation_amortization

    total_assets = balance.get("total_assets")
    total_equity = balance.get("total_stockholders_equity") or balance.get("total_equity")
    long_term_debt = balance.get("long_term_debt")
    short_term_debt = balance.get("short_term_debt")
    cash_and_equivalents = balance.get("cash_and_equivalents")

    # Total debt
    _ltd = long_term_debt or 0
    _std = short_term_debt or 0
    has_any_debt = long_term_debt is not None or short_term_debt is not None
    total_debt = (_ltd + _std) if has_any_debt else None

    # Net debt
    net_debt = None
    if total_debt is not None:
        net_debt = total_debt - (cash_and_equivalents or 0)

    # Ratios
    debt_to_equity = _safe_div(total_debt, total_equity)
    debt_to_assets = _safe_div(total_debt, total_assets)
    debt_to_ebitda = _safe_div(net_debt, ebitda)
    interest_coverage = _safe_div(operating_income, interest_expense)

    equity_multiplier = _safe_div(total_assets, total_equity)

    # Debt to capital = total_debt / (total_debt + total_equity)
    debt_to_capital = None
    if total_debt is not None and total_equity is not None:
        denom = total_debt + total_equity
        debt_to_capital = _safe_div(total_debt, denom)

    long_term_debt_to_equity = _safe_div(long_term_debt, total_equity)

    # Financial leverage ratio (avg assets / avg equity — single period approximation)
    financial_leverage_ratio = _safe_div(total_assets, total_equity)

    return {
        "total_debt": total_debt,
        "net_debt": net_debt,
        "debt_to_equity": debt_to_equity,
        "debt_to_assets": debt_to_assets,
        "debt_to_ebitda": debt_to_ebitda,
        "interest_coverage": interest_coverage,
        "equity_multiplier": equity_multiplier,
        "debt_to_capital": debt_to_capital,
        "long_term_debt_to_equity": long_term_debt_to_equity,
        "financial_leverage_ratio": financial_leverage_ratio,
    }
