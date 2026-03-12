"""System health and ingestion-status endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


@router.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


@router.get("/ingestion/status")
def ingestion_status(db: Session = Depends(get_db)):
    """Return the most recent ingestion log entry per source."""
    query = text("""
        SELECT DISTINCT ON (source)
            source, job_type, started_at, completed_at, status,
            records_processed, error_message
        FROM ingestion_log
        ORDER BY source, started_at DESC
    """)
    rows = db.execute(query).mappings().all()
    return [dict(r) for r in rows]
