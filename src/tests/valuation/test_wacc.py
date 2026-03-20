"""Tests for WACC computation module."""

import pytest

from app.valuation.wacc import compute_wacc, compute_capital_weights, DEFAULT_EQUITY_RISK_PREMIUM


class TestComputeWACC:
    def test_all_equity_company(self):
        """100% equity: WACC = cost of equity."""
        result = compute_wacc(
            beta=1.0,
            risk_free_rate=0.04,
            erp=0.055,
            debt_weight=0.0,
            equity_weight=1.0,
        )
        expected_ke = 0.04 + 1.0 * 0.055  # 0.095
        assert abs(result["wacc"] - expected_ke) < 0.0001
        assert abs(result["cost_of_equity"] - expected_ke) < 0.0001
        assert result["equity_weight"] == 1.0
        assert result["debt_weight"] == 0.0

    def test_with_debt(self):
        """Mixed capital structure: WACC is blended."""
        result = compute_wacc(
            beta=1.2,
            risk_free_rate=0.04,
            erp=0.055,
            cost_of_debt=0.05,
            tax_rate=0.21,
            debt_weight=0.3,
            equity_weight=0.7,
        )
        ke = 0.04 + 1.2 * 0.055  # 0.106
        kd_after_tax = 0.05 * (1 - 0.21)  # 0.0395
        expected_wacc = 0.7 * ke + 0.3 * kd_after_tax
        assert abs(result["wacc"] - expected_wacc) < 0.0001

    def test_zero_beta(self):
        """Beta = 0: cost of equity = risk-free rate."""
        result = compute_wacc(beta=0.0, risk_free_rate=0.04)
        assert abs(result["cost_of_equity"] - 0.04) < 0.0001

    def test_high_beta(self):
        """High beta stock should have higher cost of equity."""
        low_beta = compute_wacc(beta=0.5, risk_free_rate=0.04)
        high_beta = compute_wacc(beta=2.0, risk_free_rate=0.04)
        assert high_beta["cost_of_equity"] > low_beta["cost_of_equity"]

    def test_default_values(self):
        """Should work with only required params."""
        result = compute_wacc(beta=1.0, risk_free_rate=0.04)
        assert result["wacc"] > 0
        assert result["debt_weight"] == 0.0


class TestCapitalWeights:
    def test_normal_case(self):
        debt_w, equity_w = compute_capital_weights(1_000_000, 500_000)
        assert abs(debt_w - 1/3) < 0.01
        assert abs(equity_w - 2/3) < 0.01

    def test_no_debt(self):
        debt_w, equity_w = compute_capital_weights(1_000_000, 0)
        assert debt_w == 0.0
        assert equity_w == 1.0

    def test_no_market_cap(self):
        debt_w, equity_w = compute_capital_weights(None, 500_000)
        assert debt_w == 0.0
        assert equity_w == 1.0

    def test_zero_market_cap(self):
        debt_w, equity_w = compute_capital_weights(0, 500_000)
        assert debt_w == 0.0
        assert equity_w == 1.0
