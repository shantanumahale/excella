"""Shareholder return metrics: payouts, buybacks, and capital allocation."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute(
    income: dict,
    balance: dict,
    cashflow: dict,
    market_cap: float | None = None,
) -> dict:
    """Compute shareholder return and capital allocation metrics.

    Returns a dict of metric_name -> value (float | None).
    """
    net_income = income.get("net_income")
    shares_diluted = income.get("shares_diluted")

    operating_cash_flow = cashflow.get("operating_cash_flow")
    dividends_paid = cashflow.get("dividends_paid")
    share_repurchase = cashflow.get("share_repurchase")
    debt_issuance = cashflow.get("debt_issuance")
    debt_repayment = cashflow.get("debt_repayment")

    # Absolute values for negative cashflow items
    abs_dividends = abs(dividends_paid) if dividends_paid is not None else None
    abs_buybacks = abs(share_repurchase) if share_repurchase is not None else None

    # --- Payout ratios ---
    payout_ratio = _safe_div(abs_dividends, abs(net_income) if net_income is not None else None)
    # Correct sign: if net_income is negative, payout ratio is not meaningful
    if net_income is not None and net_income < 0:
        payout_ratio = None

    dividend_payout_ratio = payout_ratio

    retention_ratio = None
    if payout_ratio is not None:
        retention_ratio = 1 - payout_ratio

    # --- Buyback ratio ---
    buyback_ratio = _safe_div(abs_buybacks, abs(net_income) if net_income is not None else None)
    if net_income is not None and net_income < 0:
        buyback_ratio = None

    # --- Shareholder yield ---
    total_returned = None
    if abs_dividends is not None or abs_buybacks is not None:
        total_returned = (abs_dividends or 0) + (abs_buybacks or 0)
    shareholder_yield = _safe_div(total_returned, market_cap)

    # --- Total capital returned ---
    total_capital_returned = total_returned

    # --- Net debt paydown ---
    abs_repayment = abs(debt_repayment) if debt_repayment is not None else None
    abs_issuance = abs(debt_issuance) if debt_issuance is not None else None
    net_debt_paydown = None
    if abs_repayment is not None or abs_issuance is not None:
        net_debt_paydown = (abs_repayment or 0) - (abs_issuance or 0)

    # --- Total shareholder return allocation as % of OCF ---
    total_allocation = None
    if total_returned is not None or net_debt_paydown is not None:
        total_allocation = (total_returned or 0) + max(net_debt_paydown or 0, 0)
    total_shareholder_return_allocation = _safe_div(total_allocation, operating_cash_flow)

    # --- Per-share ---
    dividends_per_share = _safe_div(abs_dividends, shares_diluted)
    buyback_per_share = _safe_div(abs_buybacks, shares_diluted)

    return {
        "payout_ratio": payout_ratio,
        "dividend_payout_ratio": dividend_payout_ratio,
        "retention_ratio": retention_ratio,
        "buyback_ratio": buyback_ratio,
        "shareholder_yield": shareholder_yield,
        "total_capital_returned": total_capital_returned,
        "net_debt_paydown": net_debt_paydown,
        "total_shareholder_return_allocation": total_shareholder_return_allocation,
        "dividends_per_share": dividends_per_share,
        "buyback_per_share": buyback_per_share,
    }
