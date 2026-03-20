"""Discounted Cash Flow (DCF) valuation model."""

from __future__ import annotations


def project_growth_rates(
    historical_growth: float | None,
    terminal_growth: float,
    years: int = 5,
) -> list[float]:
    """Generate growth rates that linearly mean-revert from historical to terminal.

    If historical_growth is None, uses terminal_growth for all years.
    """
    if historical_growth is None:
        return [terminal_growth] * years
    if years <= 1:
        return [terminal_growth]

    rates = []
    for i in range(years):
        weight = i / (years - 1)
        rate = historical_growth * (1 - weight) + terminal_growth * weight
        rates.append(rate)
    return rates


def compute_dcf(
    fcff_current: float | None,
    growth_rates: list[float],
    wacc: float,
    terminal_growth: float,
    shares_outstanding: float | None,
    net_debt: float | None,
    method: str = "perpetuity",
    exit_multiple: float | None = None,
) -> dict | None:
    """Multi-stage DCF valuation.

    Args:
        fcff_current: Current free cash flow to firm.
        growth_rates: Projected growth rates for each future year.
        wacc: Weighted average cost of capital.
        terminal_growth: Long-term sustainable growth rate.
        shares_outstanding: Diluted shares outstanding.
        net_debt: Net debt (total debt - cash). Subtracted from EV to get equity value.
        method: "perpetuity" (Gordon growth) or "exit_multiple".
        exit_multiple: EV/FCFF exit multiple (used when method="exit_multiple").

    Returns:
        dict with intrinsic_value_per_share, enterprise_value, etc. or None if invalid.
    """
    if fcff_current is None or fcff_current <= 0:
        return None
    if wacc <= terminal_growth:
        return None
    if shares_outstanding is None or shares_outstanding <= 0:
        return None

    # Project FCFF
    projected_fcff = []
    fcff = fcff_current
    for rate in growth_rates:
        fcff = fcff * (1 + rate)
        projected_fcff.append(round(fcff, 2))

    # Terminal value
    n = len(growth_rates)
    terminal_fcff = projected_fcff[-1] if projected_fcff else fcff_current
    if method == "exit_multiple" and exit_multiple is not None:
        terminal_value = terminal_fcff * exit_multiple
    else:
        # Gordon growth model
        terminal_value = terminal_fcff * (1 + terminal_growth) / (wacc - terminal_growth)

    # Present values
    pv_fcff = []
    for i, cf in enumerate(projected_fcff):
        pv = cf / ((1 + wacc) ** (i + 1))
        pv_fcff.append(round(pv, 2))

    pv_terminal = terminal_value / ((1 + wacc) ** n)

    enterprise_value = sum(pv_fcff) + pv_terminal
    equity_value = enterprise_value - (net_debt or 0)
    intrinsic_value_per_share = equity_value / shares_outstanding

    return {
        "intrinsic_value_per_share": round(intrinsic_value_per_share, 2),
        "enterprise_value": round(enterprise_value, 2),
        "equity_value": round(equity_value, 2),
        "projected_fcff": projected_fcff,
        "terminal_value": round(terminal_value, 2),
        "pv_fcff": pv_fcff,
        "pv_terminal": round(pv_terminal, 2),
        "projection_years": n,
        "method": method,
    }
