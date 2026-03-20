"""Tests for the valuation engine orchestrator."""

from unittest.mock import MagicMock, patch
from datetime import date

import pytest

from app.valuation.engine import run_valuation, precompute_valuation, _build_summary


class TestBuildSummary:
    def test_consensus_from_multiple_models(self):
        models = {
            "dcf": {"intrinsic_value_per_share": 150.0},
            "ddm": {"intrinsic_value_per_share": 120.0},
            "residual_income": {"intrinsic_value_per_share": 180.0},
        }
        summary = _build_summary(models, None)
        assert summary["model_count"] == 3
        assert summary["consensus_value"] == 150.0  # median of 120, 150, 180
        assert summary["range_low"] == 120.0
        assert summary["range_high"] == 180.0

    def test_single_model(self):
        models = {
            "dcf": {"intrinsic_value_per_share": 100.0},
            "ddm": None,
        }
        summary = _build_summary(models, None)
        assert summary["model_count"] == 1
        assert summary["consensus_value"] == 100.0

    def test_no_models(self):
        models = {"dcf": None, "ddm": None}
        summary = _build_summary(models, None)
        assert summary["model_count"] == 0
        assert summary["consensus_value"] is None
        assert summary["margin_of_safety"] is None

    def test_even_number_of_models(self):
        models = {
            "dcf": {"intrinsic_value_per_share": 100.0},
            "comps": {"intrinsic_value_per_share": 200.0},
        }
        summary = _build_summary(models, None)
        assert summary["consensus_value"] == 150.0  # average of 100, 200

    def test_skips_zero_values(self):
        models = {
            "dcf": {"intrinsic_value_per_share": 0},
            "ddm": {"intrinsic_value_per_share": 100.0},
        }
        summary = _build_summary(models, None)
        assert summary["model_count"] == 1  # only ddm counts

    def test_skips_none_intrinsic_value(self):
        models = {
            "dcf": {"intrinsic_value_per_share": None},
            "ddm": {"intrinsic_value_per_share": 100.0},
        }
        summary = _build_summary(models, None)
        assert summary["model_count"] == 1


class TestRunValuation:
    def _make_mock_db(self):
        db = MagicMock()

        # Company
        company = MagicMock()
        company.id = 1
        company.ticker = "TEST"
        company.sector = "Technology"
        company.industry = "Software"
        db.query.return_value.filter.return_value.first.return_value = company

        # DerivedMetrics
        metrics = MagicMock()
        metrics.valuation = {
            "market_cap": 1_000_000_000,
            "pe_ratio": 25.0,
            "price_to_sales": 10.0,
            "earnings_yield": 0.04,
        }
        metrics.cashflow = {
            "free_cash_flow_to_firm": 50_000_000,
            "free_cash_flow_to_firm_simplified": 45_000_000,
        }
        metrics.profitability = {
            "return_on_equity": 0.20,
            "effective_tax_rate": 0.21,
        }
        metrics.leverage = {
            "total_debt": 200_000_000,
            "net_debt": 100_000_000,
            "interest_coverage": 10.0,
        }
        metrics.growth = {
            "revenue_growth": 0.15,
            "dividend_growth": 0.05,
        }
        metrics.per_share = {
            "book_value_per_share_ps": 30.0,
            "net_income_per_share": 4.0,
            "revenue_per_share_ps": 40.0,
            "dividends_per_share_ps": 1.5,
        }
        metrics.shareholder = {
            "dividends_per_share": 1.5,
        }

        # Make the filter chain work for DerivedMetrics query
        dm_query = MagicMock()
        dm_query.order_by.return_value.first.return_value = metrics

        return db, company, metrics

    @patch("app.valuation.engine.compute_beta")
    @patch("app.valuation.engine.load_risk_free_rate")
    @patch("app.valuation.engine.compute_comps")
    def test_returns_all_model_keys(self, mock_comps, mock_rfr, mock_beta):
        mock_beta.return_value = {"beta": 1.1, "r_squared": 0.85, "alpha": 0.01, "is_fallback": False, "lookback_days": 252, "data_points": 200}
        mock_rfr.return_value = 0.04
        mock_comps.return_value = None

        db, company, metrics = self._make_mock_db()

        # Need to properly chain the query mocks
        db.query.return_value.filter.return_value.first.return_value = company
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = metrics

        result = run_valuation(db, 1)

        assert "ticker" in result
        assert "models" in result
        assert "dcf" in result["models"]
        assert "ddm" in result["models"]
        assert "comps" in result["models"]
        assert "residual_income" in result["models"]
        assert "summary" in result
        assert "beta" in result
        assert "wacc" in result

    def test_company_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = run_valuation(db, 999)
        assert result.get("error") == "Company not found"
