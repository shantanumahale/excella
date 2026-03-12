"""Growth metrics: period-over-period growth rates and sustainable growth."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def _growth(current, prior):
    """Compute growth rate: (current - prior) / abs(prior)."""
    if current is None or prior is None or prior == 0:
        return None
    return (current - prior) / abs(prior)


def compute(
    income: dict,
    balance: dict,
    cashflow: dict,
    prior_income: dict | None,
    prior_balance: dict | None,
    prior_cashflow: dict | None,
) -> dict:
    """Compute growth metrics comparing current and prior periods.

    Returns a dict of metric_name -> value (float | None).
    """
    prior_income = prior_income or {}
    prior_balance = prior_balance or {}
    prior_cashflow = prior_cashflow or {}

    # --- Inline fallbacks for current period ---
    def _gross_profit(inc: dict):
        gp = inc.get("gross_profit")
        if gp is None:
            rev = inc.get("revenue")
            cogs = inc.get("cost_of_revenue")
            if rev is not None and cogs is not None:
                gp = rev - cogs
        return gp

    def _operating_income(inc: dict):
        oi = inc.get("operating_income")
        if oi is None:
            rev = inc.get("revenue")
            opex = inc.get("operating_expenses")
            if rev is not None and opex is not None:
                oi = rev - opex
        return oi

    def _ebitda(inc: dict):
        eb = inc.get("ebitda")
        if eb is None:
            oi = _operating_income(inc)
            da = inc.get("depreciation_amortization")
            if oi is not None and da is not None:
                eb = oi + da
        return eb

    # --- Core growth rates ---
    revenue_growth = _growth(income.get("revenue"), prior_income.get("revenue"))
    gross_profit_growth = _growth(_gross_profit(income), _gross_profit(prior_income))
    operating_income_growth = _growth(_operating_income(income), _operating_income(prior_income))
    ebitda_growth = _growth(_ebitda(income), _ebitda(prior_income))
    net_income_growth = _growth(income.get("net_income"), prior_income.get("net_income"))
    eps_growth = _growth(income.get("eps_diluted"), prior_income.get("eps_diluted"))

    # --- Cash flow growth ---
    ocf_growth = _growth(cashflow.get("operating_cash_flow"), prior_cashflow.get("operating_cash_flow"))

    # FCF = OCF - |capex|
    def _fcf(cf: dict) -> float | None:
        ocf = cf.get("operating_cash_flow")
        capex = cf.get("capital_expenditure")
        if ocf is None or capex is None:
            return None
        return ocf - abs(capex)

    fcf_growth = _growth(_fcf(cashflow), _fcf(prior_cashflow))

    # --- Balance sheet growth ---
    total_assets_growth = _growth(balance.get("total_assets"), prior_balance.get("total_assets"))

    equity = balance.get("total_stockholders_equity") or balance.get("total_equity")
    prior_equity = prior_balance.get("total_stockholders_equity") or prior_balance.get("total_equity")
    equity_growth = _growth(equity, prior_equity)

    # --- Dividend growth ---
    div_current = cashflow.get("dividends_paid")
    div_prior = prior_cashflow.get("dividends_paid")
    # dividends_paid is negative; compare absolute values
    dividend_growth = None
    if div_current is not None and div_prior is not None and div_prior != 0:
        dividend_growth = (abs(div_current) - abs(div_prior)) / abs(div_prior)

    # --- Sustainable growth rate ---
    # SGR = ROE * retention_ratio, retention = 1 - payout_ratio
    roe = _safe_div(income.get("net_income"), equity)
    payout_ratio = None
    if div_current is not None and income.get("net_income") is not None and income["net_income"] != 0:
        payout_ratio = abs(div_current) / abs(income["net_income"])
    retention_ratio = (1 - payout_ratio) if payout_ratio is not None else None
    sgr = None
    if roe is not None and retention_ratio is not None:
        sgr = roe * retention_ratio

    # --- Acquisition-adjusted revenue growth ---
    acquisitions = cashflow.get("acquisitions")
    is_acquisition_period = acquisitions is not None and acquisitions != 0
    acquisition_to_revenue = _safe_div(abs(acquisitions) if acquisitions else None, income.get("revenue"))

    # --- Reinvestment rate growth ---
    def _reinvestment_rate(cf: dict, inc: dict, bal: dict) -> float | None:
        capex = cf.get("capital_expenditure")
        oi = inc.get("operating_income")
        pi = inc.get("pretax_income")
        tax = inc.get("income_tax")
        if capex is None or oi is None:
            return None
        etr = _safe_div(tax, pi)
        tr = etr if etr is not None else 0
        nopat = oi * (1 - tr)
        if nopat == 0:
            return None
        return abs(capex) / nopat

    rr_current = _reinvestment_rate(cashflow, income, balance)
    rr_prior = _reinvestment_rate(prior_cashflow, prior_income, prior_balance)
    reinvestment_rate_growth = _growth(rr_current, rr_prior)

    return {
        "revenue_growth": revenue_growth,
        "gross_profit_growth": gross_profit_growth,
        "operating_income_growth": operating_income_growth,
        "ebitda_growth": ebitda_growth,
        "net_income_growth": net_income_growth,
        "eps_growth": eps_growth,
        "operating_cash_flow_growth": ocf_growth,
        "free_cash_flow_growth": fcf_growth,
        "total_assets_growth": total_assets_growth,
        "equity_growth": equity_growth,
        "dividend_growth": dividend_growth,
        "sustainable_growth_rate": sgr,
        "is_acquisition_period": is_acquisition_period,
        "acquisition_to_revenue": acquisition_to_revenue,
        "reinvestment_rate_growth": reinvestment_rate_growth,
    }
