"""Liquidity metrics: ratios, working capital, and cash conversion cycle."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(income: dict, balance: dict) -> dict:
    """Compute liquidity metrics from income statement and balance sheet data.

    Returns a dict of metric_name -> value (float | None).
    """
    revenue = income.get("revenue")
    cost_of_revenue = income.get("cost_of_revenue")
    operating_expenses = income.get("operating_expenses")

    cash_and_equivalents = balance.get("cash_and_equivalents")
    short_term_investments = balance.get("short_term_investments")
    accounts_receivable = balance.get("accounts_receivable")
    inventory = balance.get("inventory")
    total_current_assets = balance.get("total_current_assets")
    total_current_liabilities = balance.get("total_current_liabilities")
    accounts_payable = balance.get("accounts_payable")

    # --- Ratios ---
    current_ratio = _safe_div(total_current_assets, total_current_liabilities)

    # Quick ratio = (current_assets - inventory) / current_liabilities
    quick_assets = None
    if total_current_assets is not None:
        quick_assets = total_current_assets - (inventory or 0)
    quick_ratio = _safe_div(quick_assets, total_current_liabilities)

    # Cash ratio = cash / current_liabilities
    _total_cash = (cash_and_equivalents or 0) + (short_term_investments or 0)
    cash_ratio = _safe_div(_total_cash if (cash_and_equivalents is not None or short_term_investments is not None) else None,
                           total_current_liabilities)

    # --- Net working capital ---
    nwc = None
    if total_current_assets is not None and total_current_liabilities is not None:
        nwc = total_current_assets - total_current_liabilities
    nwc_pct_revenue = _safe_div(nwc, revenue)

    # --- Days metrics ---
    daily_cogs = _safe_div(cost_of_revenue, 365)
    daily_revenue = _safe_div(revenue, 365)

    dio = _safe_div(inventory, daily_cogs)
    dso = _safe_div(accounts_receivable, daily_revenue)
    dpo = _safe_div(accounts_payable, daily_cogs)

    # Cash conversion cycle
    ccc = None
    if dio is not None and dso is not None and dpo is not None:
        ccc = dio + dso - dpo

    # Defensive interval = liquid assets / daily operating expenses
    liquid_assets = None
    if cash_and_equivalents is not None or short_term_investments is not None or accounts_receivable is not None:
        liquid_assets = (cash_and_equivalents or 0) + (short_term_investments or 0) + (accounts_receivable or 0)

    daily_opex = _safe_div(operating_expenses, 365) if operating_expenses is not None else None
    # Fallback: use cost_of_revenue + SGA if operating_expenses is missing
    if daily_opex is None and cost_of_revenue is not None:
        sga = income.get("selling_general_admin") or 0
        daily_opex = (cost_of_revenue + sga) / 365

    defensive_interval = _safe_div(liquid_assets, daily_opex)

    return {
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "cash_ratio": cash_ratio,
        "net_working_capital": nwc,
        "nwc_pct_revenue": nwc_pct_revenue,
        "days_inventory_outstanding": dio,
        "days_sales_outstanding": dso,
        "days_payable_outstanding": dpo,
        "cash_conversion_cycle": ccc,
        "defensive_interval": defensive_interval,
    }
