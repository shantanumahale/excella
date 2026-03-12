"""Valuation metrics: multiples, yields, and per-share intrinsic measures."""

from __future__ import annotations

import math


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(
    income: dict,
    balance: dict,
    cashflow: dict,
    price: float | None,
    eps_growth_pct: float | None = None,
) -> dict:
    """Compute valuation metrics.

    Args:
        price: Current share price (may be None if unavailable).
        eps_growth_pct: EPS growth rate as a percentage (e.g. 15 for 15%).

    Returns a dict of metric_name -> value (float | None).
    """
    revenue = income.get("revenue")
    operating_income = income.get("operating_income")
    ebitda = income.get("ebitda")
    net_income = income.get("net_income")
    eps_diluted = income.get("eps_diluted")
    shares_diluted = income.get("shares_diluted")
    depreciation_amortization = income.get("depreciation_amortization")
    cost_of_revenue = income.get("cost_of_revenue")
    gross_profit = income.get("gross_profit")

    # Inline fallbacks
    if gross_profit is None and revenue is not None and cost_of_revenue is not None:
        gross_profit = revenue - cost_of_revenue
    if operating_income is None and revenue is not None:
        opex = income.get("operating_expenses")
        if opex is not None:
            operating_income = revenue - opex
        elif gross_profit is not None:
            rd = income.get("research_and_development", 0)
            sga = income.get("selling_general_admin", 0)
            if rd or sga:
                operating_income = gross_profit - rd - sga
    if ebitda is None and operating_income is not None and depreciation_amortization is not None:
        ebitda = operating_income + depreciation_amortization

    total_equity = balance.get("total_stockholders_equity") or balance.get("total_equity")
    long_term_debt = balance.get("long_term_debt")
    short_term_debt = balance.get("short_term_debt")
    cash_and_equivalents = balance.get("cash_and_equivalents")
    minority_interest = balance.get("minority_interest")
    goodwill = balance.get("goodwill")
    intangible_assets = balance.get("intangible_assets")

    operating_cash_flow = cashflow.get("operating_cash_flow")
    capital_expenditure = cashflow.get("capital_expenditure")
    dividends_paid = cashflow.get("dividends_paid")

    # --- Market cap & EV ---
    market_cap = None
    if price is not None and shares_diluted is not None:
        market_cap = price * shares_diluted

    total_debt = (long_term_debt or 0) + (short_term_debt or 0)
    has_debt_info = long_term_debt is not None or short_term_debt is not None

    enterprise_value = None
    if market_cap is not None:
        ev = market_cap + (total_debt if has_debt_info else 0) - (cash_and_equivalents or 0)
        if minority_interest is not None:
            ev += minority_interest
        enterprise_value = ev

    # --- Price multiples ---
    pe_ratio = _safe_div(price, eps_diluted)
    price_to_book = _safe_div(market_cap, total_equity)
    price_to_sales = _safe_div(market_cap, revenue)
    price_to_cash_flow = _safe_div(market_cap, operating_cash_flow)

    # --- EV multiples ---
    ev_to_ebitda = _safe_div(enterprise_value, ebitda)
    ev_to_ebit = _safe_div(enterprise_value, operating_income)
    ev_to_revenue = _safe_div(enterprise_value, revenue)

    # FCF = OCF - |capex|
    abs_capex = abs(capital_expenditure) if capital_expenditure is not None else None
    fcf = None
    if operating_cash_flow is not None and abs_capex is not None:
        fcf = operating_cash_flow - abs_capex
    ev_to_fcf = _safe_div(enterprise_value, fcf)

    # --- Yields ---
    earnings_yield = _safe_div(eps_diluted, price)

    fcf_per_share = _safe_div(fcf, shares_diluted)
    fcf_yield = _safe_div(fcf_per_share, price)

    div_per_share = _safe_div(abs(dividends_paid) if dividends_paid is not None else None, shares_diluted)
    dividend_yield = _safe_div(div_per_share, price)

    # --- PEG ---
    peg_ratio = _safe_div(pe_ratio, eps_growth_pct)

    # --- Per-share measures ---
    book_value_per_share = _safe_div(total_equity, shares_diluted)

    tangible_equity = None
    if total_equity is not None:
        tangible_equity = total_equity - (goodwill or 0) - (intangible_assets or 0)
    tangible_book_value_per_share = _safe_div(tangible_equity, shares_diluted)

    revenue_per_share = _safe_div(revenue, shares_diluted)

    # --- Graham number ---
    graham_number = None
    if eps_diluted is not None and book_value_per_share is not None:
        product = 22.5 * eps_diluted * book_value_per_share
        if product >= 0:
            graham_number = math.sqrt(product)

    return {
        "market_cap": market_cap,
        "enterprise_value": enterprise_value,
        "pe_ratio": pe_ratio,
        "price_to_book": price_to_book,
        "price_to_sales": price_to_sales,
        "price_to_cash_flow": price_to_cash_flow,
        "ev_to_ebitda": ev_to_ebitda,
        "ev_to_ebit": ev_to_ebit,
        "ev_to_revenue": ev_to_revenue,
        "ev_to_fcf": ev_to_fcf,
        "earnings_yield": earnings_yield,
        "fcf_yield": fcf_yield,
        "dividend_yield": dividend_yield,
        "peg_ratio": peg_ratio,
        "book_value_per_share": book_value_per_share,
        "tangible_book_value_per_share": tangible_book_value_per_share,
        "revenue_per_share": revenue_per_share,
        "graham_number": graham_number,
    }
