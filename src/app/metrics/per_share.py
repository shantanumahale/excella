"""Per-share metrics: normalized financial data on a per-share basis."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(income: dict, balance: dict, cashflow: dict) -> dict:
    """Compute per-share metrics using shares_diluted.

    Returns a dict of metric_name -> value (float | None).
    """
    shares = income.get("shares_diluted")

    revenue = income.get("revenue")
    gross_profit = income.get("gross_profit")
    operating_income = income.get("operating_income")
    ebitda = income.get("ebitda")
    net_income = income.get("net_income")

    total_equity = balance.get("total_stockholders_equity") or balance.get("total_equity")
    goodwill = balance.get("goodwill")
    intangible_assets = balance.get("intangible_assets")
    long_term_debt = balance.get("long_term_debt")
    short_term_debt = balance.get("short_term_debt")
    cash_and_equivalents = balance.get("cash_and_equivalents")

    operating_cash_flow = cashflow.get("operating_cash_flow")
    capital_expenditure = cashflow.get("capital_expenditure")
    dividends_paid = cashflow.get("dividends_paid")

    # --- Income per share ---
    revenue_per_share = _safe_div(revenue, shares)
    gross_profit_per_share = _safe_div(gross_profit, shares)
    operating_income_per_share = _safe_div(operating_income, shares)
    ebitda_per_share = _safe_div(ebitda, shares)
    net_income_per_share = _safe_div(net_income, shares)

    # --- Book value per share ---
    book_value_per_share = _safe_div(total_equity, shares)

    tangible_equity = None
    if total_equity is not None:
        tangible_equity = total_equity - (goodwill or 0) - (intangible_assets or 0)
    tangible_book_value_per_share = _safe_div(tangible_equity, shares)

    # --- Cash flow per share ---
    operating_cash_flow_per_share = _safe_div(operating_cash_flow, shares)

    abs_capex = abs(capital_expenditure) if capital_expenditure is not None else None
    fcf = None
    if operating_cash_flow is not None and abs_capex is not None:
        fcf = operating_cash_flow - abs_capex
    free_cash_flow_per_share = _safe_div(fcf, shares)

    # --- Dividends per share ---
    abs_dividends = abs(dividends_paid) if dividends_paid is not None else None
    dividends_per_share = _safe_div(abs_dividends, shares)

    # --- Debt per share ---
    _ltd = long_term_debt or 0
    _std = short_term_debt or 0
    has_debt = long_term_debt is not None or short_term_debt is not None
    total_debt = (_ltd + _std) if has_debt else None
    total_debt_per_share = _safe_div(total_debt, shares)

    net_debt = None
    if total_debt is not None:
        net_debt = total_debt - (cash_and_equivalents or 0)
    net_debt_per_share = _safe_div(net_debt, shares)

    cash_per_share = _safe_div(cash_and_equivalents, shares)

    return {
        "revenue_per_share": revenue_per_share,
        "gross_profit_per_share": gross_profit_per_share,
        "operating_income_per_share": operating_income_per_share,
        "ebitda_per_share": ebitda_per_share,
        "net_income_per_share": net_income_per_share,
        "book_value_per_share": book_value_per_share,
        "tangible_book_value_per_share": tangible_book_value_per_share,
        "operating_cash_flow_per_share": operating_cash_flow_per_share,
        "free_cash_flow_per_share": free_cash_flow_per_share,
        "dividends_per_share": dividends_per_share,
        "total_debt_per_share": total_debt_per_share,
        "net_debt_per_share": net_debt_per_share,
        "cash_per_share": cash_per_share,
    }
