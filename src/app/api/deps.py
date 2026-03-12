"""FastAPI dependencies shared across route modules."""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

import redis
from fastapi import Query

from app.config import settings
from app.db.session import get_db  # noqa: F401  — re-export

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Return a module-level sync Redis client (lazy-initialised)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis_client


# ---------------------------------------------------------------------------
# Common query-parameter models
# ---------------------------------------------------------------------------


@dataclass
class PaginationParams:
    offset: int = Query(0, ge=0, description="Number of records to skip")
    limit: int = Query(50, ge=1, le=5000, description="Max records to return")


@dataclass
class DateRangeParams:
    start: Optional[date] = Query(None, description="Start date (inclusive)")
    end: Optional[date] = Query(None, description="End date (inclusive)")
