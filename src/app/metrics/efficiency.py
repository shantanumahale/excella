"""Efficiency metrics: turnover ratios, operating and cash cycles."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(income: dict, balance: dict, cashflow: dict) -> dict:
    """Compute efficiency metrics.

    Returns a dict of metric_name -> value (float | None).
    """
    revenue = income.get("revenue")
    cost_of_revenue = income.get("cost_of_revenue")
    depreciation_amortization = income.get("depreciation_amortization")

    total_assets = balance.get("total_assets")
    property_plant_equipment = balance.get("property_plant_equipment")
    inventory = balance.get("inventory")
    accounts_receivable = balance.get("accounts_receivable")
    accounts_payable = balance.get("accounts_payable")
    total_equity = balance.get("total_stockholders_equity") or balance.get("total_equity")

    capital_expenditure = cashflow.get("capital_expenditure")

    # --- Turnover ratios ---
    asset_turnover = _safe_div(revenue, total_assets)
    fixed_asset_turnover = _safe_div(revenue, property_plant_equipment)
    inventory_turnover = _safe_div(cost_of_revenue, inventory)
    receivables_turnover = _safe_div(revenue, accounts_receivable)
    payables_turnover = _safe_div(cost_of_revenue, accounts_payable)
    equity_turnover = _safe_div(revenue, total_equity)

    # --- Capex ratios ---
    # capital_expenditure is typically negative in cashflow; use abs for ratios
    abs_capex = abs(capital_expenditure) if capital_expenditure is not None else None
    capex_to_revenue = _safe_div(abs_capex, revenue)
    capex_to_depreciation = _safe_div(abs_capex, depreciation_amortization)

    # --- Cycles (in days) ---
    daily_cogs = _safe_div(cost_of_revenue, 365)
    daily_revenue = _safe_div(revenue, 365)

    dio = _safe_div(inventory, daily_cogs)
    dso = _safe_div(accounts_receivable, daily_revenue)
    dpo = _safe_div(accounts_payable, daily_cogs)

    operating_cycle = None
    if dio is not None and dso is not None:
        operating_cycle = dio + dso

    cash_cycle = None
    if operating_cycle is not None and dpo is not None:
        cash_cycle = operating_cycle - dpo

    return {
        "asset_turnover": asset_turnover,
        "fixed_asset_turnover": fixed_asset_turnover,
        "inventory_turnover": inventory_turnover,
        "receivables_turnover": receivables_turnover,
        "payables_turnover": payables_turnover,
        "equity_turnover": equity_turnover,
        "capital_expenditure_to_revenue": capex_to_revenue,
        "capex_to_depreciation": capex_to_depreciation,
        "operating_cycle": operating_cycle,
        "cash_cycle": cash_cycle,
    }
