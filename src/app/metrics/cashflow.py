"""Cash flow metrics: free cash flows, quality, and reinvestment."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(income: dict, balance: dict, cashflow: dict) -> dict:
    """Compute cash flow metrics.

    Returns a dict of metric_name -> value (float | None).
    """
    revenue = income.get("revenue")
    operating_income = income.get("operating_income")
    net_income = income.get("net_income")
    pretax_income = income.get("pretax_income")
    income_tax = income.get("income_tax")
    interest_expense = income.get("interest_expense")
    depreciation_amortization = income.get("depreciation_amortization")

    # Inline fallback: pull D&A from cashflow if missing from income
    if depreciation_amortization is None:
        depreciation_amortization = cashflow.get("depreciation_amortization_cf") or cashflow.get("depreciation_amortization")

    # operating_income fallback
    if operating_income is None and revenue is not None:
        opex = income.get("operating_expenses")
        gp = income.get("gross_profit")
        cogs = income.get("cost_of_revenue")
        if opex is not None:
            operating_income = revenue - opex
        elif gp is not None or (cogs is not None):
            if gp is None:
                gp = revenue - cogs
            rd = income.get("research_and_development", 0)
            sga = income.get("selling_general_admin", 0)
            if rd or sga:
                operating_income = gp - rd - sga

    total_equity = balance.get("total_stockholders_equity") or balance.get("total_equity")
    long_term_debt = balance.get("long_term_debt")
    short_term_debt = balance.get("short_term_debt")
    cash_and_equivalents = balance.get("cash_and_equivalents")

    operating_cash_flow = cashflow.get("operating_cash_flow")
    capital_expenditure = cashflow.get("capital_expenditure")
    debt_issuance = cashflow.get("debt_issuance")
    debt_repayment = cashflow.get("debt_repayment")

    # Effective tax rate
    effective_tax_rate = _safe_div(income_tax, pretax_income)
    tax_rate = effective_tax_rate if effective_tax_rate is not None else 0

    # abs capex (typically negative in cashflow)
    abs_capex = abs(capital_expenditure) if capital_expenditure is not None else None

    # --- FCFF ---
    # Primary: OCF - capex + interest_expense*(1-tax_rate)
    fcff = None
    if operating_cash_flow is not None and abs_capex is not None:
        interest_tax_shield = 0
        if interest_expense is not None:
            interest_tax_shield = interest_expense * (1 - tax_rate)
        fcff = operating_cash_flow - abs_capex + interest_tax_shield

    # Simplified FCFF (fallback): OCF - capex
    fcff_simplified = None
    if operating_cash_flow is not None and abs_capex is not None:
        fcff_simplified = operating_cash_flow - abs_capex

    # --- FCFE ---
    # FCFE = OCF - capex + net_borrowing
    net_borrowing = None
    _di = debt_issuance or 0
    _dr = debt_repayment or 0
    if debt_issuance is not None or debt_repayment is not None:
        net_borrowing = _di - abs(_dr)  # debt_repayment is often negative

    fcfe = None
    if operating_cash_flow is not None and abs_capex is not None:
        _nb = net_borrowing or 0
        fcfe = operating_cash_flow - abs_capex + _nb

    # --- Margins & quality ---
    ocf_margin = _safe_div(operating_cash_flow, revenue)
    cf_to_net_income = _safe_div(operating_cash_flow, net_income)
    capex_to_ocf = _safe_div(abs_capex, operating_cash_flow)

    # --- NOPAT for reinvestment ---
    nopat = None
    if operating_income is not None and effective_tax_rate is not None:
        nopat = operating_income * (1 - effective_tax_rate)

    # Invested capital
    _ltd = long_term_debt or 0
    _std = short_term_debt or 0
    _cash = cash_and_equivalents or 0
    invested_capital = None
    if total_equity is not None:
        invested_capital = total_equity + _ltd + _std - _cash
        if invested_capital == 0:
            invested_capital = None

    # Cash return on invested capital
    cash_roic = _safe_div(fcff, invested_capital)

    # Reinvestment rate (approximate as capex / NOPAT)
    reinvestment_rate = _safe_div(abs_capex, nopat)

    # Capex to depreciation
    capex_to_depreciation = _safe_div(abs_capex, depreciation_amortization)

    return {
        "free_cash_flow_to_firm": fcff,
        "free_cash_flow_to_firm_simplified": fcff_simplified,
        "free_cash_flow_to_equity": fcfe,
        "net_borrowing": net_borrowing,
        "operating_cash_flow_margin": ocf_margin,
        "cash_flow_to_net_income": cf_to_net_income,
        "capex_to_operating_cash_flow": capex_to_ocf,
        "cash_return_on_invested_capital": cash_roic,
        "reinvestment_rate": reinvestment_rate,
        "capex_to_depreciation": capex_to_depreciation,
        "nopat": nopat,
    }
