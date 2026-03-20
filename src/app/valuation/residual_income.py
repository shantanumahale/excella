"""Residual Income valuation model."""

from __future__ import annotations


def compute_residual_income(
    bvps: float | None,
    roe: float | None,
    cost_of_equity: float,
    growth_rate: float = 0.03,
    years: int = 5,
    retention_ratio: float | None = None,
) -> dict | None:
    """Compute intrinsic value using the Residual Income Model.

    Intrinsic Value = Current BV + PV(Excess Returns) + Terminal Value of Excess Returns

    Args:
        bvps: Current book value per share.
        roe: Return on equity (decimal, e.g. 0.15 for 15%).
        cost_of_equity: Required return on equity (decimal).
        growth_rate: Terminal growth rate for residual income.
        years: Projection horizon.
        retention_ratio: Fraction of earnings retained (1 - payout ratio).
                         If None, defaults to 0.5.

    Returns:
        dict with intrinsic_value_per_share, excess_returns, etc. or None if invalid.
    """
    if bvps is None or bvps <= 0:
        return None
    if roe is None:
        return None
    if cost_of_equity <= growth_rate:
        return None

    # Use actual retention ratio from shareholder metrics, default 50%
    retention = retention_ratio if retention_ratio is not None else 0.5
    # Clamp to [0, 1] for safety
    retention = max(0.0, min(1.0, retention))

    excess_returns = []
    pv_excess_returns = []
    bv = bvps

    for i in range(1, years + 1):
        # Excess return = (ROE - ke) * beginning BV
        excess = (roe - cost_of_equity) * bv
        pv = excess / ((1 + cost_of_equity) ** i)
        excess_returns.append(round(excess, 4))
        pv_excess_returns.append(round(pv, 4))
        # BV grows by retained earnings: ROE * BV * retention
        bv = bv * (1 + roe * retention)

    # Terminal value of excess returns
    terminal_excess = excess_returns[-1] * (1 + growth_rate)
    terminal_value = terminal_excess / (cost_of_equity - growth_rate)
    pv_terminal = terminal_value / ((1 + cost_of_equity) ** years)

    intrinsic_value = bvps + sum(pv_excess_returns) + pv_terminal

    return {
        "intrinsic_value_per_share": round(intrinsic_value, 2),
        "current_bvps": round(bvps, 2),
        "excess_returns": excess_returns,
        "pv_excess_returns": pv_excess_returns,
        "pv_terminal": round(pv_terminal, 2),
        "projection_years": years,
    }
