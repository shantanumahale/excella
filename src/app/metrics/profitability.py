"""Profitability metrics: margins, returns on capital, and cost ratios."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(income: dict, balance: dict) -> dict:
    """Compute profitability metrics from income statement and balance sheet data.

    Returns a dict of metric_name -> value (float | None).
    """
    revenue = income.get("revenue")
    cost_of_revenue = income.get("cost_of_revenue")
    gross_profit = income.get("gross_profit")
    operating_income = income.get("operating_income")
    net_income = income.get("net_income")
    ebitda = income.get("ebitda")
    pretax_income = income.get("pretax_income")
    income_tax = income.get("income_tax")
    research_and_development = income.get("research_and_development")
    selling_general_admin = income.get("selling_general_admin")
    stock_based_compensation = income.get("stock_based_compensation")
    depreciation_amortization = income.get("depreciation_amortization")

    # Inline fallbacks for missing derived fields
    if gross_profit is None and revenue is not None and cost_of_revenue is not None:
        gross_profit = revenue - cost_of_revenue
    if operating_income is None and revenue is not None:
        opex = income.get("operating_expenses")
        if opex is not None:
            operating_income = revenue - opex
        elif gross_profit is not None:
            rd = research_and_development or 0
            sga = selling_general_admin or 0
            if rd or sga:
                operating_income = gross_profit - rd - sga
    if ebitda is None and operating_income is not None and depreciation_amortization is not None:
        ebitda = operating_income + depreciation_amortization

    total_assets = balance.get("total_assets")
    total_equity = balance.get("total_stockholders_equity") or balance.get("total_equity")
    long_term_debt = balance.get("long_term_debt")
    short_term_debt = balance.get("short_term_debt")
    cash_and_equivalents = balance.get("cash_and_equivalents")
    total_current_liabilities = balance.get("total_current_liabilities")

    # --- Margins ---
    gross_margin = _safe_div(gross_profit, revenue)
    operating_margin = _safe_div(operating_income, revenue)
    net_margin = _safe_div(net_income, revenue)
    ebitda_margin = _safe_div(ebitda, revenue)

    # EBIT approximation: operating_income or ebitda - D&A
    ebit = operating_income
    ebit_margin = _safe_div(ebit, revenue)

    # --- Returns on capital ---
    roa = _safe_div(net_income, total_assets)
    roe = _safe_div(net_income, total_equity)

    # Capital employed = total_assets - total_current_liabilities
    capital_employed = None
    if total_assets is not None and total_current_liabilities is not None:
        capital_employed = total_assets - total_current_liabilities
    roce = _safe_div(ebit, capital_employed)

    # Effective tax rate
    effective_tax_rate = _safe_div(income_tax, pretax_income)

    # NOPAT = operating_income * (1 - effective_tax_rate)
    nopat = None
    if operating_income is not None and effective_tax_rate is not None:
        nopat = operating_income * (1 - effective_tax_rate)

    # Invested capital = total_equity + long_term_debt + short_term_debt - cash
    invested_capital = None
    _ltd = long_term_debt or 0
    _std = short_term_debt or 0
    _cash = cash_and_equivalents or 0
    if total_equity is not None:
        invested_capital = total_equity + _ltd + _std - _cash
        if invested_capital == 0:
            invested_capital = None

    roic = _safe_div(nopat, invested_capital)

    # --- Cost ratios ---
    rd_intensity = _safe_div(research_and_development, revenue)
    sga_ratio = _safe_div(selling_general_admin, revenue)
    sbc_pct_revenue = _safe_div(stock_based_compensation, revenue)

    return {
        "gross_margin": gross_margin,
        "operating_margin": operating_margin,
        "net_margin": net_margin,
        "ebitda_margin": ebitda_margin,
        "ebit_margin": ebit_margin,
        "return_on_assets": roa,
        "return_on_equity": roe,
        "return_on_capital_employed": roce,
        "return_on_invested_capital": roic,
        "effective_tax_rate": effective_tax_rate,
        "nopat": nopat,
        "invested_capital": invested_capital,
        "capital_employed": capital_employed,
        "rd_intensity": rd_intensity,
        "sga_ratio": sga_ratio,
        "sbc_pct_revenue": sbc_pct_revenue,
    }
