"""Tests for beta computation module."""

from unittest.mock import MagicMock, patch
from datetime import date, timedelta

import numpy as np
import pytest

from app.valuation.beta import compute_beta, _fallback_beta, MIN_DATA_POINTS


class TestFallbackBeta:
    def test_returns_beta_one(self):
        result = _fallback_beta(252, 10)
        assert result["beta"] == 1.0
        assert result["is_fallback"] is True
        assert result["r_squared"] is None

    def test_preserves_data_points(self):
        result = _fallback_beta(252, 42)
        assert result["data_points"] == 42
        assert result["lookback_days"] == 252


class TestComputeBeta:
    def _mock_db_with_prices(self, stock_returns, market_returns, n_days=252):
        """Create a mock DB that returns aligned price series."""
        db = MagicMock()
        base_date = date.today() - timedelta(days=n_days + 30)

        # Generate prices from returns (start at 100)
        stock_prices = [100.0]
        for r in stock_returns:
            stock_prices.append(stock_prices[-1] * np.exp(r))

        market_prices = [100.0]
        for r in market_returns:
            market_prices.append(market_prices[-1] * np.exp(r))

        dates = [base_date + timedelta(days=i) for i in range(len(stock_prices))]

        stock_rows = [(d, p) for d, p in zip(dates, stock_prices)]
        market_rows = [(d, p) for d, p in zip(dates, market_prices)]

        def mock_execute(query, params=None):
            result = MagicMock()
            ticker = params.get("ticker", "") if params else ""
            if ticker == "TEST":
                result.fetchall.return_value = stock_rows
            elif ticker == "SPY":
                result.fetchall.return_value = market_rows
            else:
                result.fetchall.return_value = []
            return result

        db.execute = mock_execute
        return db

    def test_perfect_correlation_beta_one(self):
        """When stock returns = market returns, beta should be ~1.0."""
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, 200)
        db = self._mock_db_with_prices(returns, returns)

        result = compute_beta(db, "TEST", "SPY")

        assert not result["is_fallback"]
        assert abs(result["beta"] - 1.0) < 0.01
        assert result["r_squared"] > 0.99

    def test_high_beta_stock(self):
        """Stock with 2x market sensitivity should have beta ~2.0."""
        np.random.seed(42)
        market_returns = np.random.normal(0.0005, 0.01, 200)
        stock_returns = 2.0 * market_returns + np.random.normal(0, 0.001, 200)
        db = self._mock_db_with_prices(stock_returns, market_returns)

        result = compute_beta(db, "TEST", "SPY")

        assert not result["is_fallback"]
        assert abs(result["beta"] - 2.0) < 0.15

    def test_insufficient_data_fallback(self):
        """Should return fallback when < MIN_DATA_POINTS aligned prices."""
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, 30)  # too few
        db = self._mock_db_with_prices(returns, returns, n_days=30)

        result = compute_beta(db, "TEST", "SPY")

        assert result["is_fallback"] is True
        assert result["beta"] == 1.0

    def test_no_stock_data_fallback(self):
        """Should return fallback when no stock price data."""
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        db.execute = MagicMock(return_value=mock_result)

        result = compute_beta(db, "NODATA", "SPY")

        assert result["is_fallback"] is True
        assert result["beta"] == 1.0
