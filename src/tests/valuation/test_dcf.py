"""Tests for DCF valuation model."""

import pytest

from app.valuation.dcf import compute_dcf, project_growth_rates


class TestProjectGrowthRates:
    def test_linear_mean_reversion(self):
        rates = project_growth_rates(0.20, 0.03, years=5)
        assert len(rates) == 5
        assert abs(rates[0] - 0.20) < 0.001  # starts at historical
        assert abs(rates[-1] - 0.03) < 0.001  # ends at terminal

    def test_none_historical_uses_terminal(self):
        rates = project_growth_rates(None, 0.03, years=5)
        assert all(abs(r - 0.03) < 0.001 for r in rates)

    def test_single_year(self):
        rates = project_growth_rates(0.20, 0.03, years=1)
        assert len(rates) == 1
        assert abs(rates[0] - 0.03) < 0.001

    def test_monotonic_decrease(self):
        rates = project_growth_rates(0.20, 0.03, years=5)
        for i in range(len(rates) - 1):
            assert rates[i] >= rates[i + 1]


class TestComputeDCF:
    def test_basic_dcf(self):
        """Known inputs should produce valid intrinsic value."""
        result = compute_dcf(
            fcff_current=1_000_000,
            growth_rates=[0.10, 0.08, 0.06, 0.04, 0.03],
            wacc=0.10,
            terminal_growth=0.025,
            shares_outstanding=100_000,
            net_debt=500_000,
        )
        assert result is not None
        assert result["intrinsic_value_per_share"] > 0
        assert result["enterprise_value"] > 0
        assert result["equity_value"] > 0
        assert len(result["projected_fcff"]) == 5
        assert len(result["pv_fcff"]) == 5
        assert result["terminal_value"] > 0
        assert result["method"] == "perpetuity"

    def test_negative_fcff_returns_none(self):
        result = compute_dcf(
            fcff_current=-500_000,
            growth_rates=[0.10],
            wacc=0.10,
            terminal_growth=0.025,
            shares_outstanding=100_000,
            net_debt=0,
        )
        assert result is None

    def test_none_fcff_returns_none(self):
        result = compute_dcf(
            fcff_current=None,
            growth_rates=[0.10],
            wacc=0.10,
            terminal_growth=0.025,
            shares_outstanding=100_000,
            net_debt=0,
        )
        assert result is None

    def test_wacc_lte_terminal_growth_returns_none(self):
        result = compute_dcf(
            fcff_current=1_000_000,
            growth_rates=[0.10],
            wacc=0.02,
            terminal_growth=0.03,
            shares_outstanding=100_000,
            net_debt=0,
        )
        assert result is None

    def test_no_shares_returns_none(self):
        result = compute_dcf(
            fcff_current=1_000_000,
            growth_rates=[0.10],
            wacc=0.10,
            terminal_growth=0.025,
            shares_outstanding=None,
            net_debt=0,
        )
        assert result is None

    def test_exit_multiple_method(self):
        result = compute_dcf(
            fcff_current=1_000_000,
            growth_rates=[0.10, 0.08],
            wacc=0.10,
            terminal_growth=0.025,
            shares_outstanding=100_000,
            net_debt=0,
            method="exit_multiple",
            exit_multiple=15.0,
        )
        assert result is not None
        assert result["method"] == "exit_multiple"
        assert result["terminal_value"] > 0

    def test_net_debt_reduces_equity_value(self):
        no_debt = compute_dcf(
            fcff_current=1_000_000,
            growth_rates=[0.10],
            wacc=0.10,
            terminal_growth=0.025,
            shares_outstanding=100_000,
            net_debt=0,
        )
        with_debt = compute_dcf(
            fcff_current=1_000_000,
            growth_rates=[0.10],
            wacc=0.10,
            terminal_growth=0.025,
            shares_outstanding=100_000,
            net_debt=2_000_000,
        )
        assert no_debt is not None and with_debt is not None
        assert with_debt["intrinsic_value_per_share"] < no_debt["intrinsic_value_per_share"]

    def test_higher_wacc_lowers_value(self):
        low_wacc = compute_dcf(
            fcff_current=1_000_000,
            growth_rates=[0.10, 0.08, 0.06],
            wacc=0.08,
            terminal_growth=0.025,
            shares_outstanding=100_000,
            net_debt=0,
        )
        high_wacc = compute_dcf(
            fcff_current=1_000_000,
            growth_rates=[0.10, 0.08, 0.06],
            wacc=0.15,
            terminal_growth=0.025,
            shares_outstanding=100_000,
            net_debt=0,
        )
        assert low_wacc is not None and high_wacc is not None
        assert high_wacc["intrinsic_value_per_share"] < low_wacc["intrinsic_value_per_share"]
