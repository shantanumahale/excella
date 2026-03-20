"""Tests for Dividend Discount Model."""

import pytest

from app.valuation.ddm import compute_ddm


class TestComputeDDM:
    def test_gordon_growth_basic(self):
        """V = DPS*(1+g) / (ke-g) = 2*(1.03) / (0.10-0.03) = 29.43"""
        result = compute_ddm(dps=2.0, cost_of_equity=0.10, growth_rate=0.03)
        assert result is not None
        expected = 2.0 * 1.03 / (0.10 - 0.03)
        assert abs(result["intrinsic_value_per_share"] - expected) < 0.01
        assert result["model_type"] == "gordon_growth"

    def test_no_dividends_returns_none(self):
        result = compute_ddm(dps=None, cost_of_equity=0.10, growth_rate=0.03)
        assert result is None

    def test_zero_dividends_returns_none(self):
        result = compute_ddm(dps=0.0, cost_of_equity=0.10, growth_rate=0.03)
        assert result is None

    def test_ke_lte_growth_returns_none(self):
        result = compute_ddm(dps=2.0, cost_of_equity=0.03, growth_rate=0.05)
        assert result is None

    def test_ke_equals_growth_returns_none(self):
        result = compute_ddm(dps=2.0, cost_of_equity=0.05, growth_rate=0.05)
        assert result is None

    def test_two_stage_model(self):
        """Two-stage DDM with high growth below cost of equity."""
        result = compute_ddm(
            dps=2.0,
            cost_of_equity=0.12,
            growth_rate=0.03,
            high_growth_rate=0.08,
            high_growth_years=5,
        )
        assert result is not None
        assert result["model_type"] == "two_stage"
        # Two-stage should give higher value than single-stage with same terminal growth
        gordon = compute_ddm(dps=2.0, cost_of_equity=0.12, growth_rate=0.03)
        assert result["intrinsic_value_per_share"] > gordon["intrinsic_value_per_share"]

    def test_two_stage_ke_lte_high_growth_returns_none(self):
        """When cost_of_equity <= high_growth_rate, two-stage DDM returns None."""
        result = compute_ddm(
            dps=2.0,
            cost_of_equity=0.10,
            growth_rate=0.03,
            high_growth_rate=0.12,
            high_growth_years=5,
        )
        # 0.10 <= 0.12 → guard triggers → None
        assert result is None

    def test_dividend_yield_implied(self):
        result = compute_ddm(dps=2.0, cost_of_equity=0.10, growth_rate=0.03)
        assert result is not None
        assert result["dividend_yield_implied"] is not None
        assert result["dividend_yield_implied"] > 0
