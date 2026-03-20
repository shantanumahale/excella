"""Dividend Discount Model (DDM) valuation."""

from __future__ import annotations


def compute_ddm(
    dps: float | None,
    cost_of_equity: float,
    growth_rate: float,
    high_growth_rate: float | None = None,
    high_growth_years: int = 0,
) -> dict | None:
    """Compute intrinsic value using Gordon Growth / two-stage DDM.

    Args:
        dps: Current dividends per share (annual).
        cost_of_equity: Required return on equity (decimal).
        growth_rate: Long-term sustainable dividend growth rate.
        high_growth_rate: Initial high-growth rate for two-stage model.
        high_growth_years: Number of years at high growth rate.

    Returns:
        dict with intrinsic_value_per_share, model_type, etc. or None if not applicable.
    """
    if dps is None or dps <= 0:
        return None
    if cost_of_equity <= growth_rate:
        return None

    # Two-stage DDM
    if high_growth_rate is not None and high_growth_years > 0 and high_growth_rate != growth_rate:
        if cost_of_equity <= high_growth_rate:
            return None

        pv_high_growth = 0.0
        dividend = dps
        for i in range(1, high_growth_years + 1):
            dividend = dividend * (1 + high_growth_rate)
            pv_high_growth += dividend / ((1 + cost_of_equity) ** i)

        # Terminal value at end of high-growth phase
        terminal_dividend = dividend * (1 + growth_rate)
        terminal_value = terminal_dividend / (cost_of_equity - growth_rate)
        pv_terminal = terminal_value / ((1 + cost_of_equity) ** high_growth_years)

        intrinsic_value = pv_high_growth + pv_terminal

        return {
            "intrinsic_value_per_share": round(intrinsic_value, 2),
            "model_type": "two_stage",
            "dividend_yield_implied": round(dps / intrinsic_value, 4) if intrinsic_value > 0 else None,
            "high_growth_rate": high_growth_rate,
            "high_growth_years": high_growth_years,
            "stable_growth_rate": growth_rate,
        }

    # Gordon Growth Model: V = DPS * (1+g) / (ke - g)
    intrinsic_value = dps * (1 + growth_rate) / (cost_of_equity - growth_rate)

    return {
        "intrinsic_value_per_share": round(intrinsic_value, 2),
        "model_type": "gordon_growth",
        "dividend_yield_implied": round(dps / intrinsic_value, 4) if intrinsic_value > 0 else None,
        "stable_growth_rate": growth_rate,
    }
