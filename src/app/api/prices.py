"""Daily price and return endpoints (raw SQL on TimescaleDB hypertables)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.api.deps import DateRangeParams, PaginationParams
from app.db.session import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prices", tags=["prices"])


# ---------------------------------------------------------------------------
# GET /prices/{ticker}
# ---------------------------------------------------------------------------

@router.get("/{ticker}", summary="Daily OHLCV", description="Daily open/high/low/close/adj_close/volume data from TimescaleDB. Supports date range filtering and pagination.")
def daily_prices(
    ticker: str,
    pagination: PaginationParams = Depends(),
    dates: DateRangeParams = Depends(),
):
    """Return daily OHLCV rows for a ticker."""
    conditions = ["ticker = :ticker"]
    params: dict = {"ticker": ticker.upper(), "offset": pagination.offset, "limit": pagination.limit}

    if dates.start:
        conditions.append("time >= :start")
        params["start"] = dates.start
    if dates.end:
        conditions.append("time <= :end")
        params["end"] = dates.end

    where = " AND ".join(conditions)

    count_sql = text(f"SELECT count(*) FROM daily_prices WHERE {where}")
    data_sql = text(
        f"SELECT time, open, high, low, close, adj_close, volume "
        f"FROM daily_prices WHERE {where} "
        f"ORDER BY time DESC OFFSET :offset LIMIT :limit"
    )

    with engine.connect() as conn:
        total = conn.execute(count_sql, params).scalar()
        rows = conn.execute(data_sql, params).mappings().all()

    return {
        "ticker": ticker.upper(),
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
        "data": [dict(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# GET /prices/{ticker}/latest
# ---------------------------------------------------------------------------

@router.get("/{ticker}/latest", summary="Latest price")
def latest_price(ticker: str):
    """Most recent price row."""
    sql = text(
        "SELECT time, open, high, low, close, adj_close, volume "
        "FROM daily_prices WHERE ticker = :ticker "
        "ORDER BY time DESC LIMIT 1"
    )
    with engine.connect() as conn:
        row = conn.execute(sql, {"ticker": ticker.upper()}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="No price data found")

    return {"ticker": ticker.upper(), **dict(row)}


# ---------------------------------------------------------------------------
# GET /prices/{ticker}/returns
# ---------------------------------------------------------------------------

@router.get("/{ticker}/returns", summary="Price returns", description="Returns over 1d, 5d, 21d, 63d, 126d, 252d windows computed from adj_close.")
def price_returns(ticker: str):
    """Compute returns over standard windows from daily_prices."""
    # We pull the last 253 trading days (252 returns) in one shot.
    sql = text(
        "SELECT time, adj_close "
        "FROM daily_prices WHERE ticker = :ticker "
        "ORDER BY time DESC LIMIT 253"
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"ticker": ticker.upper()}).fetchall()

    if len(rows) < 2:
        raise HTTPException(status_code=404, detail="Insufficient price data")

    # rows are newest-first; index 0 = latest
    prices = [float(r[1]) for r in rows]
    latest_date = rows[0][0]

    def _ret(n: int) -> float | None:
        if len(prices) <= n:
            return None
        return round((prices[0] - prices[n]) / prices[n], 6)

    windows = {
        "1d": _ret(1),
        "5d": _ret(5),
        "21d": _ret(21),
        "63d": _ret(63),
        "126d": _ret(126),
        "252d": _ret(252),
    }

    return {
        "ticker": ticker.upper(),
        "date": latest_date,
        "returns": windows,
    }
