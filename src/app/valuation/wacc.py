"""Weighted Average Cost of Capital (WACC) computation."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DEFAULT_EQUITY_RISK_PREMIUM = 0.055  # Damodaran long-term average
DEFAULT_RISK_FREE_RATE = 0.04  # fallback if FRED data unavailable


def load_risk_free_rate(db: Session) -> float:
    """Load the latest 10-Year Treasury yield from FRED observations.

    Returns the yield as a decimal (e.g. 0.042 for 4.2%).
    Falls back to DEFAULT_RISK_FREE_RATE if unavailable.
    """
    try:
        result = db.execute(
            text(
                "SELECT value FROM fred_observations "
                "WHERE series_id = 'DGS10' "
                "ORDER BY time DESC LIMIT 1"
            ),
        ).fetchone()
        if result and result[0] is not None:
            return float(result[0]) / 100.0  # FRED reports as percentage
    except Exception:
        logger.debug("Could not load DGS10 risk-free rate", exc_info=True)
    return DEFAULT_RISK_FREE_RATE


def compute_wacc(
    beta: float,
    risk_free_rate: float,
    erp: float = DEFAULT_EQUITY_RISK_PREMIUM,
    cost_of_debt: float | None = None,
    tax_rate: float | None = None,
    debt_weight: float | None = None,
    equity_weight: float | None = None,
) -> dict:
    """Compute WACC using CAPM for cost of equity.

    Args:
        beta: Equity beta
        risk_free_rate: Risk-free rate (decimal)
        erp: Equity risk premium (decimal)
        cost_of_debt: Pre-tax cost of debt (decimal). If None, uses risk_free_rate + 0.02.
        tax_rate: Effective tax rate (decimal). If None, defaults to 0.21.
        debt_weight: Debt / (Debt + Equity). If None, defaults to 0.
        equity_weight: Equity / (Debt + Equity). If None, defaults to 1.

    Returns:
        dict with wacc, cost_of_equity, cost_of_debt_after_tax, equity_weight, debt_weight
    """
    # CAPM: cost of equity = risk_free + beta * ERP
    cost_of_equity = risk_free_rate + beta * erp

    # Defaults
    if cost_of_debt is None:
        cost_of_debt = risk_free_rate + 0.02
    if tax_rate is None:
        tax_rate = 0.21
    if debt_weight is None:
        debt_weight = 0.0
    if equity_weight is None:
        equity_weight = 1.0 - debt_weight

    cost_of_debt_after_tax = cost_of_debt * (1 - tax_rate)

    wacc = equity_weight * cost_of_equity + debt_weight * cost_of_debt_after_tax

    return {
        "wacc": round(wacc, 6),
        "cost_of_equity": round(cost_of_equity, 6),
        "cost_of_debt_after_tax": round(cost_of_debt_after_tax, 6),
        "equity_weight": round(equity_weight, 4),
        "debt_weight": round(debt_weight, 4),
    }


def compute_capital_weights(
    market_cap: float | None,
    total_debt: float | None,
) -> tuple[float, float]:
    """Compute debt and equity weights from market cap and total debt.

    Returns (debt_weight, equity_weight). Falls back to (0, 1) if data missing.
    """
    if market_cap is None or market_cap <= 0:
        return 0.0, 1.0
    debt = total_debt or 0.0
    total_capital = market_cap + debt
    if total_capital <= 0:
        return 0.0, 1.0
    return debt / total_capital, market_cap / total_capital
