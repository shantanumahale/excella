"""FRED macro-economic series endpoints (raw SQL on TimescaleDB hypertables)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import DateRangeParams, PaginationParams, get_db
from app.db.models import FredSeries
from app.db.session import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("/series", summary="List FRED series", description="List all 23 tracked macroeconomic series (Treasury yields, CPI, GDP, unemployment, VIX, etc.).")
def list_series(db: Session = Depends(get_db)):
    """List all tracked FRED series."""
    rows = db.query(FredSeries).order_by(FredSeries.series_id).all()
    return [
        {
            "id": r.id,
            "series_id": r.series_id,
            "title": r.title,
            "frequency": r.frequency,
            "units": r.units,
            "seasonal_adjustment": r.seasonal_adjustment,
            "notes": r.notes,
            "last_updated": r.last_updated,
        }
        for r in rows
    ]


@router.get("/series/latest", summary="Latest value for every tracked series")
def all_latest():
    """Return the most recent observation for each series in a single query."""
    sql = text(
        "SELECT DISTINCT ON (series_id) series_id, time, value "
        "FROM fred_observations ORDER BY series_id, time DESC"
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    return {r["series_id"]: {"time": r["time"], "value": r["value"]} for r in rows}


@router.get("/series/{series_id}")
def get_observations(
    series_id: str,
    pagination: PaginationParams = Depends(),
    dates: DateRangeParams = Depends(),
):
    """Return observations for a FRED series."""
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

    return {
        "series_id": series_id.upper(),
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
        "data": [dict(r) for r in rows],
    }


@router.get("/series/{series_id}/latest")
def latest_observation(series_id: str):
    """Most recent observation for a FRED series."""
    sql = text(
        "SELECT time, value FROM fred_observations "
        "WHERE series_id = :series_id ORDER BY time DESC LIMIT 1"
    )
    with engine.connect() as conn:
        row = conn.execute(sql, {"series_id": series_id.upper()}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="No observations found")

    return {"series_id": series_id.upper(), **dict(row)}
