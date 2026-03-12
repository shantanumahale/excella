"""DuPont decomposition: 3-factor and 5-factor ROE analysis."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(income: dict, balance: dict) -> dict:
    """Compute DuPont ROE decomposition.

    Returns a dict of metric_name -> value (float | None).
    """
    revenue = income.get("revenue")
    net_income = income.get("net_income")
    operating_income = income.get("operating_income")
    pretax_income = income.get("pretax_income")

    total_assets = balance.get("total_assets")
    total_equity = balance.get("total_stockholders_equity") or balance.get("total_equity")

    # --- Components ---
    net_margin = _safe_div(net_income, revenue)
    asset_turnover = _safe_div(revenue, total_assets)
    equity_multiplier = _safe_div(total_assets, total_equity)

    # --- 3-factor DuPont ---
    roe_3factor = None
    if net_margin is not None and asset_turnover is not None and equity_multiplier is not None:
        roe_3factor = net_margin * asset_turnover * equity_multiplier

    # --- 5-factor DuPont ---
    tax_burden = _safe_div(net_income, pretax_income)            # tax efficiency
    interest_burden = _safe_div(pretax_income, operating_income)  # interest efficiency
    operating_profit_margin = _safe_div(operating_income, revenue)

    roe_5factor = None
    if all(v is not None for v in [tax_burden, interest_burden, operating_profit_margin, asset_turnover, equity_multiplier]):
        roe_5factor = tax_burden * interest_burden * operating_profit_margin * asset_turnover * equity_multiplier

    return {
        # 3-factor components (suffixed to avoid collision with profitability/efficiency keys)
        "net_margin_dupont": net_margin,
        "asset_turnover_dupont": asset_turnover,
        "equity_multiplier_dupont": equity_multiplier,
        "roe_3factor": roe_3factor,
        # 5-factor components
        "tax_burden": tax_burden,
        "interest_burden": interest_burden,
        "operating_profit_margin": operating_profit_margin,
        "roe_5factor": roe_5factor,
        # Aliases for clarity
        "tax_efficiency": tax_burden,
        "interest_efficiency": interest_burden,
    }
