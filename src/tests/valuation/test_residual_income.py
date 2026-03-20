"""Tests for Residual Income valuation model."""

import pytest

from app.valuation.residual_income import compute_residual_income


class TestComputeResidualIncome:
    def test_basic_computation(self):
        result = compute_residual_income(
            bvps=50.0,
            roe=0.15,
            cost_of_equity=0.10,
            growth_rate=0.03,
            years=5,
        )
        assert result is not None
        # When ROE > ke, intrinsic value should exceed book value
        assert result["intrinsic_value_per_share"] > 50.0
        assert result["current_bvps"] == 50.0
        assert len(result["excess_returns"]) == 5
        assert len(result["pv_excess_returns"]) == 5
        assert result["projection_years"] == 5

    def test_roe_below_ke(self):
        """When ROE < ke, excess returns are negative, IV < BVPS."""
        result = compute_residual_income(
            bvps=50.0,
            roe=0.05,
            cost_of_equity=0.10,
            growth_rate=0.03,
            years=5,
        )
        assert result is not None
        assert result["intrinsic_value_per_share"] < 50.0

    def test_none_bvps_returns_none(self):
        result = compute_residual_income(bvps=None, roe=0.15, cost_of_equity=0.10)
        assert result is None

    def test_zero_bvps_returns_none(self):
        result = compute_residual_income(bvps=0.0, roe=0.15, cost_of_equity=0.10)
        assert result is None

    def test_none_roe_returns_none(self):
        result = compute_residual_income(bvps=50.0, roe=None, cost_of_equity=0.10)
        assert result is None

    def test_ke_lte_growth_returns_none(self):
        result = compute_residual_income(
            bvps=50.0, roe=0.15, cost_of_equity=0.03, growth_rate=0.05,
        )
        assert result is None

    def test_excess_returns_positive_when_roe_exceeds_ke(self):
        result = compute_residual_income(
            bvps=50.0,
            roe=0.20,
            cost_of_equity=0.10,
            years=3,
        )
        assert result is not None
        assert all(er > 0 for er in result["excess_returns"])

    def test_more_years_changes_value(self):
        short = compute_residual_income(bvps=50.0, roe=0.15, cost_of_equity=0.10, years=3)
        long = compute_residual_income(bvps=50.0, roe=0.15, cost_of_equity=0.10, years=10)
        assert short is not None and long is not None
        # More years of excess returns should generally increase value
        assert long["intrinsic_value_per_share"] != short["intrinsic_value_per_share"]

    def test_retention_ratio_from_financials(self):
        """Higher retention → more BV growth → higher intrinsic value (when ROE > ke)."""
        low_retention = compute_residual_income(
            bvps=50.0, roe=0.20, cost_of_equity=0.10, retention_ratio=0.3,
        )
        high_retention = compute_residual_income(
            bvps=50.0, roe=0.20, cost_of_equity=0.10, retention_ratio=0.8,
        )
        assert low_retention is not None and high_retention is not None
        assert high_retention["intrinsic_value_per_share"] > low_retention["intrinsic_value_per_share"]

    def test_none_retention_defaults_to_half(self):
        """retention_ratio=None should behave like 0.5."""
        default = compute_residual_income(bvps=50.0, roe=0.15, cost_of_equity=0.10, retention_ratio=None)
        explicit = compute_residual_income(bvps=50.0, roe=0.15, cost_of_equity=0.10, retention_ratio=0.5)
        assert default is not None and explicit is not None
        assert default["intrinsic_value_per_share"] == explicit["intrinsic_value_per_share"]
