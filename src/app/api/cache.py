"""Lightweight Redis cache helpers for API endpoints."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)

# TTLs in seconds
MACRO_SERIES_LIST_TTL = 21600    # 6 hours – metadata rarely changes
MACRO_ALL_LATEST_TTL = 3600      # 1 hour
MACRO_OBSERVATIONS_TTL = 7200    # 2 hours – historical data is immutable
MACRO_SINGLE_LATEST_TTL = 3600   # 1 hour


def cache_get(r: redis.Redis, key: str) -> Optional[Any]:
    """Return deserialised cached value, or None on miss."""
    raw = r.get(key)
    if raw is None:
        return None
    return json.loads(raw)


def cache_set(r: redis.Redis, key: str, value: Any, ttl: int) -> None:
    """Serialise and store *value* with a TTL (seconds)."""
    r.setex(key, ttl, json.dumps(value, default=str))


def cache_invalidate_pattern(r: redis.Redis, pattern: str) -> int:
    """Delete all keys matching a glob *pattern*. Returns count deleted."""
    cursor, total = 0, 0
    while True:
        cursor, keys = r.scan(cursor=cursor, match=pattern, count=200)
        if keys:
            total += r.delete(*keys)
        if cursor == 0:
            break
    return total
