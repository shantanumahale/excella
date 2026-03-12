"""FRED macro-economic series endpoints (raw SQL on TimescaleDB hypertables)."""

from __future__ import annotations

import logging

import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.cache import (
    MACRO_ALL_LATEST_TTL,
    MACRO_OBSERVATIONS_TTL,
    MACRO_SERIES_LIST_TTL,
    MACRO_SINGLE_LATEST_TTL,
    cache_get,
    cache_set,
)
from app.api.deps import DateRangeParams, PaginationParams, get_db, get_redis
from app.db.models import FredSeries
from app.db.session import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("/series", summary="List FRED series", description="List all 23 tracked macroeconomic series (Treasury yields, CPI, GDP, unemployment, VIX, etc.).")
def list_series(
    db: Session = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """List all tracked FRED series."""
    cache_key = "macro:series:list"
    try:
        cached = cache_get(r, cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.warning("Redis read failed for %s", cache_key, exc_info=True)

    rows = db.query(FredSeries).order_by(FredSeries.series_id).all()
    result = [
        {
            "id": row.id,
            "series_id": row.series_id,
            "title": row.title,
            "frequency": row.frequency,
            "units": row.units,
            "seasonal_adjustment": row.seasonal_adjustment,
            "notes": row.notes,
            "last_updated": row.last_updated,
        }
        for row in rows
    ]

    try:
        cache_set(r, cache_key, result, MACRO_SERIES_LIST_TTL)
    except Exception:
        logger.warning("Redis write failed for %s", cache_key, exc_info=True)

    return result


@router.get("/series/latest", summary="Latest value for every tracked series")
def all_latest(r: redis.Redis = Depends(get_redis)):
    """Return the most recent observation for each series in a single query."""
    cache_key = "macro:series:all_latest"
    try:
        cached = cache_get(r, cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.warning("Redis read failed for %s", cache_key, exc_info=True)

    sql = text(
        "SELECT DISTINCT ON (series_id) series_id, time, value "
        "FROM fred_observations ORDER BY series_id, time DESC"
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    result = {r_["series_id"]: {"time": r_["time"], "value": r_["value"]} for r_ in rows}

    try:
        cache_set(r, cache_key, result, MACRO_ALL_LATEST_TTL)
    except Exception:
        logger.warning("Redis write failed for %s", cache_key, exc_info=True)

    return result


@router.get("/series/{series_id}")
def get_observations(
    series_id: str,
    pagination: PaginationParams = Depends(),
    dates: DateRangeParams = Depends(),
    r: redis.Redis = Depends(get_redis),
):
    """Return observations for a FRED series."""
    cache_key = (
        f"macro:obs:{series_id.upper()}:{pagination.offset}:{pagination.limit}"
        f":{dates.start}:{dates.end}"
    )
    try:
        cached = cache_get(r, cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.warning("Redis read failed for %s", cache_key, exc_info=True)

    conditions = ["series_id = :series_id"]
    params: dict = {
        "series_id": series_id.upper(),
        "offset": pagination.offset,
        "limit": pagination.limit,
    }

    if dates.start:
        conditions.append("time >= :start")
        params["start"] = dates.start
    if dates.end:
        conditions.append("time <= :end")
        params["end"] = dates.end

    where = " AND ".join(conditions)

    count_sql = text(f"SELECT count(*) FROM fred_observations WHERE {where}")
    data_sql = text(
        f"SELECT time, value FROM fred_observations WHERE {where} "
        f"ORDER BY time DESC OFFSET :offset LIMIT :limit"
    )

    with engine.connect() as conn:
        total = conn.execute(count_sql, params).scalar()
        rows = conn.execute(data_sql, params).mappings().all()

    if total == 0:
        raise HTTPException(status_code=404, detail="Series not found or has no observations")

    result = {
        "series_id": series_id.upper(),
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
        "data": [dict(row) for row in rows],
    }

    try:
        cache_set(r, cache_key, result, MACRO_OBSERVATIONS_TTL)
    except Exception:
        logger.warning("Redis write failed for %s", cache_key, exc_info=True)

    return result


@router.get("/series/{series_id}/latest")
def latest_observation(
    series_id: str,
    r: redis.Redis = Depends(get_redis),
):
    """Most recent observation for a FRED series."""
    cache_key = f"macro:latest:{series_id.upper()}"
    try:
        cached = cache_get(r, cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.warning("Redis read failed for %s", cache_key, exc_info=True)

    sql = text(
        "SELECT time, value FROM fred_observations "
        "WHERE series_id = :series_id ORDER BY time DESC LIMIT 1"
    )
    with engine.connect() as conn:
        row = conn.execute(sql, {"series_id": series_id.upper()}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="No observations found")

    result = {"series_id": series_id.upper(), **dict(row)}

    try:
        cache_set(r, cache_key, result, MACRO_SINGLE_LATEST_TTL)
    except Exception:
        logger.warning("Redis write failed for %s", cache_key, exc_info=True)

    return result
