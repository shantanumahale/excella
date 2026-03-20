"""Beta computation via OLS regression on log returns."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MIN_DATA_POINTS = 60


def _load_prices(db: Session, ticker: str, start_date: date) -> list[tuple[date, float]]:
    """Load (date, adj_close) pairs from daily_prices hypertable."""
    rows = db.execute(
        text(
            "SELECT time::date, adj_close FROM daily_prices "
            "WHERE ticker = :ticker AND time >= :start "
            "ORDER BY time ASC"
        ),
        {"ticker": ticker, "start": str(start_date)},
    ).fetchall()
    return [(row[0], float(row[1])) for row in rows if row[1] is not None]


def compute_beta(
    db: Session,
    ticker: str,
    market_ticker: str = "SPY",
    lookback_days: int = 252,
) -> dict:
    """Compute beta of a stock against a market benchmark.

    Uses log returns and OLS regression (covariance/variance method).

    Returns:
        dict with keys: beta, r_squared, alpha, lookback_days, data_points, is_fallback
    """
    start_date = date.today() - timedelta(days=lookback_days + 30)  # buffer for alignment

    stock_prices = _load_prices(db, ticker, start_date)
    market_prices = _load_prices(db, market_ticker, start_date)

    if not stock_prices or not market_prices:
        logger.warning("No price data for beta: %s or %s", ticker, market_ticker)
        return _fallback_beta(lookback_days, 0)

    # Build date-indexed dicts
    stock_map = dict(stock_prices)
    market_map = dict(market_prices)

    # Align on common dates
    common_dates = sorted(set(stock_map.keys()) & set(market_map.keys()))

    if len(common_dates) < 2:
        return _fallback_beta(lookback_days, len(common_dates))

    # Trim to lookback_days most recent
    common_dates = common_dates[-lookback_days:]

    # Compute log returns
    stock_values = np.array([stock_map[d] for d in common_dates])
    market_values = np.array([market_map[d] for d in common_dates])

    stock_log_returns = np.diff(np.log(stock_values))
    market_log_returns = np.diff(np.log(market_values))

    data_points = len(stock_log_returns)

    if data_points < MIN_DATA_POINTS:
        logger.warning(
            "Insufficient data points for beta: %d < %d for %s",
            data_points, MIN_DATA_POINTS, ticker,
        )
        return _fallback_beta(lookback_days, data_points)

    # OLS via covariance/variance
    cov_matrix = np.cov(stock_log_returns, market_log_returns)
    beta = float(cov_matrix[0, 1] / cov_matrix[1, 1])

    # R-squared
    correlation = np.corrcoef(stock_log_returns, market_log_returns)[0, 1]
    r_squared = float(correlation ** 2)

    # Alpha (annualized)
    alpha = float(
        (np.mean(stock_log_returns) - beta * np.mean(market_log_returns)) * 252
    )

    return {
        "beta": round(beta, 4),
        "r_squared": round(r_squared, 4),
        "alpha": round(alpha, 4),
        "lookback_days": lookback_days,
        "data_points": data_points,
        "is_fallback": False,
    }


def _fallback_beta(lookback_days: int, data_points: int) -> dict:
    """Return a fallback beta of 1.0 when insufficient data."""
    return {
        "beta": 1.0,
        "r_squared": None,
        "alpha": None,
        "lookback_days": lookback_days,
        "data_points": data_points,
        "is_fallback": True,
    }
