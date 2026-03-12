"""FRED (Federal Reserve Economic Data) ingestor."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import text

from app.config import settings
from app.db.models import FredSeries
from app.db.session import engine
from app.ingestion.base import BaseIngestor

logger = logging.getLogger(__name__)

DEFAULT_SERIES: list[str] = [
    "DGS1",       # 1-Year Treasury
    "DGS2",       # 2-Year Treasury
    "DGS5",       # 5-Year Treasury
    "DGS10",      # 10-Year Treasury
    "DGS30",      # 30-Year Treasury
    "T10Y2Y",     # 10Y-2Y Treasury Spread
    "T10Y3M",     # 10Y-3M Treasury Spread
    "FEDFUNDS",   # Effective Federal Funds Rate
    "CPIAUCSL",   # CPI All Urban Consumers
    "CPILFESL",   # CPI Less Food and Energy
    "GDP",        # Nominal GDP
    "GDPC1",      # Real GDP
    "UNRATE",     # Unemployment Rate
    "PAYEMS",     # Total Nonfarm Payrolls
    "UMCSENT",    # U of Michigan Consumer Sentiment
    "VIXCLS",     # CBOE VIX
    "BAMLH0A0HYM2",  # ICE BofA HY OAS
    "DFF",        # Daily Federal Funds Rate
    "MORTGAGE30US",   # 30-Year Fixed Mortgage Rate
    "HOUST",      # Housing Starts
    "INDPRO",     # Industrial Production Index
    "PCE",        # Personal Consumption Expenditures
    "PCEPI",      # PCE Price Index
]

OBSERVATIONS_URL = (
    "https://api.stlouisfed.org/fred/series/observations"
    "?series_id={series_id}&api_key={api_key}&file_type=json"
)
SERIES_INFO_URL = (
    "https://api.stlouisfed.org/fred/series"
    "?series_id={series_id}&api_key={api_key}&file_type=json"
)


class FredIngestor(BaseIngestor):
    """Ingest economic time-series data from the FRED API."""

    source_name = "fred"

    def __init__(self) -> None:
        super().__init__()
        self._session = requests.Session()
        self._api_key = settings.fred_api_key

    # -- HTTP helpers --

    def _get(self, url: str) -> requests.Response:
        """GET with basic rate limiting."""
        time.sleep(0.1)
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        return resp

    # -- Core ingestion --

    def _upsert_series_metadata(
        self, series_id: str, info: dict[str, Any]
    ) -> FredSeries:
        """Upsert FredSeries model from FRED /series endpoint payload."""
        serieses = info.get("seriess", [])
        meta = serieses[0] if serieses else {}

        record = (
            self.db.query(FredSeries)
            .filter(FredSeries.series_id == series_id)
            .first()
        )
        if record is None:
            record = FredSeries(series_id=series_id)
            self.db.add(record)

        record.title = meta.get("title", "")
        record.frequency = meta.get("frequency_short", "")
        record.units = meta.get("units_short", "")
        record.seasonal_adjustment = meta.get("seasonal_adjustment_short", "")
        record.last_updated = meta.get("last_updated", "")
        record.notes = meta.get("notes", "")

        self.db.commit()
        self.db.refresh(record)
        logger.info("Upserted FredSeries metadata: %s", series_id)
        return record

    def _upsert_observations(
        self, series_id: str, observations: list[dict[str, Any]]
    ) -> int:
        """Bulk upsert observations into the fred_observations hypertable."""
        if not observations:
            return 0

        rows = []
        for obs in observations:
            date_str = obs.get("date")
            value_str = obs.get("value")
            if date_str is None:
                continue
            # FRED uses "." for missing values
            if value_str is None or value_str == ".":
                continue
            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue
            rows.append({"series_id": series_id, "time": date_str, "value": value})

        if not rows:
            return 0

        insert_sql = text("""
            INSERT INTO fred_observations (time, series_id, value)
            VALUES (:time, :series_id, :value)
            ON CONFLICT (series_id, time) DO UPDATE
                SET value = EXCLUDED.value
        """)

        batch_size = 500
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            with engine.begin() as conn:
                conn.execute(insert_sql, batch)

        logger.info(
            "Upserted %d observations for series %s", len(rows), series_id
        )
        return len(rows)

    # -- Public API --

    def ingest_series(self, series_id: str) -> int:
        """Ingest a single FRED series (metadata + observations).

        Returns the number of observation rows upserted.
        """
        log = self.log_start(detail=f"series={series_id}")
        count = 0

        try:
            # Fetch series metadata
            info_url = SERIES_INFO_URL.format(
                series_id=series_id, api_key=self._api_key
            )
            info_resp = self._get(info_url)
            info_json = info_resp.json()

            # Store raw metadata in S3 (non-fatal if S3 is unavailable)
            try:
                s3_key = f"fred/series_info/{series_id}.json"
                self.upload_to_s3(s3_key, info_resp.content)
            except Exception as s3_exc:
                logger.warning("S3 upload failed for %s metadata (non-fatal): %s", series_id, s3_exc)

            self._upsert_series_metadata(series_id, info_json)

            # Fetch observations
            obs_url = OBSERVATIONS_URL.format(
                series_id=series_id, api_key=self._api_key
            )
            obs_resp = self._get(obs_url)
            obs_json = obs_resp.json()

            # Store raw observations in S3 (non-fatal if S3 is unavailable)
            try:
                s3_key = f"fred/observations/{series_id}.json"
                self.upload_to_s3(s3_key, obs_resp.content)
            except Exception as s3_exc:
                logger.warning("S3 upload failed for %s observations (non-fatal): %s", series_id, s3_exc)

            observations = obs_json.get("observations", [])
            count = self._upsert_observations(series_id, observations)

            self.log_end(status="success", records_processed=count)

        except requests.HTTPError as exc:
            logger.error("HTTP error for series %s: %s", series_id, exc)
            self.log_end(
                status="failed",
                records_processed=0,
                error_message=str(exc),
            )
            raise
        except Exception as exc:
            logger.exception("Error ingesting series %s", series_id)
            self.log_end(
                status="failed",
                records_processed=0,
                error_message=str(exc),
            )
            raise

        return count

    def ingest_all(self) -> dict[str, Any]:
        """Ingest all default FRED series.

        Returns a summary with per-series status and total counts.
        """
        results: dict[str, Any] = {"succeeded": [], "failed": [], "total_observations": 0}

        for series_id in DEFAULT_SERIES:
            try:
                count = self.ingest_series(series_id)
                results["total_observations"] += count
                results["succeeded"].append(series_id)
            except Exception as exc:
                logger.error("Failed to ingest %s: %s", series_id, exc)
                results["failed"].append(
                    {"series_id": series_id, "error": str(exc)}
                )

        logger.info(
            "FRED ingest complete: %d succeeded, %d failed, %d total observations",
            len(results["succeeded"]),
            len(results["failed"]),
            results["total_observations"],
        )

        # Invalidate macro API cache so endpoints serve fresh data immediately
        try:
            from app.api.cache import cache_invalidate_pattern
            cleared = cache_invalidate_pattern(self.redis, "macro:*")
            logger.info("Cleared %d macro cache keys after FRED ingestion", cleared)
        except Exception:
            logger.warning("Failed to clear macro cache (non-fatal)", exc_info=True)

        return results

    def close(self) -> None:
        """Close HTTP session and base resources."""
        self._session.close()
        super().close()
