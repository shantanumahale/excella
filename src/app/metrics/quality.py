"""Quality metrics: earnings quality, accruals, and growth sustainability."""

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
    prior_income: dict | None = None,
    prior_balance: dict | None = None,
    prior_cashflow: dict | None = None,
) -> dict:
    """Compute quality metrics.

    Returns a dict of metric_name -> value (float | None).
    """
    prior_income = prior_income or {}
    prior_balance = prior_balance or {}
    prior_cashflow = prior_cashflow or {}

    net_income = income.get("net_income")
    revenue = income.get("revenue")
    selling_general_admin = income.get("selling_general_admin")
    depreciation_amortization = income.get("depreciation_amortization")

    total_assets = balance.get("total_assets")
    accounts_receivable = balance.get("accounts_receivable")

    operating_cash_flow = cashflow.get("operating_cash_flow")
    capital_expenditure = cashflow.get("capital_expenditure")
    acquisitions = cashflow.get("acquisitions")

    # --- Accruals ratio ---
    accruals = None
    if net_income is not None and operating_cash_flow is not None:
        accruals = net_income - operating_cash_flow
    accruals_ratio = _safe_div(accruals, total_assets)

    # Sloan ratio (same formula, single-period assets as denominator)
    sloan_ratio = accruals_ratio

    # --- Cash flow to earnings ---
    cash_flow_to_earnings = _safe_div(operating_cash_flow, net_income)

    # --- Earnings quality score (simple flag) ---
    earnings_quality_score = None
    if operating_cash_flow is not None and net_income is not None:
        earnings_quality_score = 1 if operating_cash_flow > net_income else 0

    # --- Divergence metrics (require prior period) ---
    revenue_growth = _growth(revenue, prior_income.get("revenue"))
    receivables_growth = _growth(accounts_receivable, prior_balance.get("accounts_receivable"))

    revenue_vs_receivables_divergence = None
    if revenue_growth is not None and receivables_growth is not None:
        revenue_vs_receivables_divergence = revenue_growth - receivables_growth

    net_income_growth = _growth(net_income, prior_income.get("net_income"))
    ocf_growth = _growth(operating_cash_flow, prior_cashflow.get("operating_cash_flow"))

    net_income_vs_ocf_divergence = None
    if net_income_growth is not None and ocf_growth is not None:
        net_income_vs_ocf_divergence = net_income_growth - ocf_growth

    # --- Capex consistency ---
    abs_capex = abs(capital_expenditure) if capital_expenditure is not None else None
    capex_consistency = _safe_div(abs_capex, revenue)

    # --- Organic revenue flag ---
    organic_revenue_flag = acquisitions is None or acquisitions == 0

    # --- SGA efficiency: SGA growth vs revenue growth ---
    sga_growth = _growth(selling_general_admin, prior_income.get("selling_general_admin"))
    sga_efficiency = None
    if sga_growth is not None and revenue_growth is not None:
        sga_efficiency = revenue_growth - sga_growth  # positive = SGA growing slower than revenue

    # --- Depreciation to capex ---
    depreciation_to_capex = _safe_div(depreciation_amortization, abs_capex)

    return {
        "accruals_ratio": accruals_ratio,
        "sloan_ratio": sloan_ratio,
        "cash_flow_to_earnings": cash_flow_to_earnings,
        "earnings_quality_score": earnings_quality_score,
        "revenue_vs_receivables_divergence": revenue_vs_receivables_divergence,
        "net_income_vs_ocf_divergence": net_income_vs_ocf_divergence,
        "capex_consistency": capex_consistency,
        "organic_revenue_flag": organic_revenue_flag,
        "sga_efficiency": sga_efficiency,
        "depreciation_to_capex": depreciation_to_capex,
    }
