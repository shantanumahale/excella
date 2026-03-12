"""Base ingestor class providing DB, Redis, S3, and logging infrastructure."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import boto3
import redis
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import IngestionLog
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class BaseIngestor:
    """Base class for all data ingestors.

    Provides a DB session, Redis client, S3 client, ingestion logging,
    and context manager support for clean resource lifecycle management.
    """

    source_name: str = "unknown"

    def __init__(self) -> None:
        self.db: Session = SessionLocal()
        self.redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )
        self.bucket = settings.s3_bucket
        self._log_record: Optional[IngestionLog] = None

    # -- Context manager --

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                "Ingestor %s exiting with error: %s", self.source_name, exc_val
            )
            if self._log_record is not None:
                self.log_end(
                    status="failed",
                    records_processed=0,
                    error_message=str(exc_val),
                )
        self.close()
        return False

    # -- Ingestion logging --

    def log_start(self, detail: str = "") -> IngestionLog:
        """Record the start of an ingestion run in the IngestionLog table."""
        record = IngestionLog(
            source=self.source_name,
            job_type=detail,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        self._log_record = record
        logger.info(
            "Ingestion started: source=%s detail=%s id=%s",
            self.source_name,
            detail,
            record.id,
        )
        return record

    def log_end(
        self,
        status: str = "success",
        records_processed: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Record the end of an ingestion run."""
        if self._log_record is None:
            logger.warning("log_end called without a prior log_start; skipping.")
            return
        self._log_record.status = status
        self._log_record.records_processed = records_processed
        self._log_record.error_message = error_message
        self._log_record.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info(
            "Ingestion finished: source=%s status=%s records=%d id=%s",
            self.source_name,
            status,
            records_processed,
            self._log_record.id,
        )
        self._log_record = None

    # -- S3 helper --

    def upload_to_s3(self, key: str, data: bytes) -> str:
        """Upload raw bytes to S3 and return the full key."""
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)
        logger.debug("Uploaded %d bytes to s3://%s/%s", len(data), self.bucket, key)
        return key

    # -- Cleanup --

    def close(self) -> None:
        """Release DB session, Redis, and S3 connections."""
        try:
            self.db.close()
        except Exception:
            logger.exception("Error closing DB session")
        try:
            self.redis.close()
        except Exception:
            logger.exception("Error closing Redis connection")
        # boto3 clients do not require explicit close
        logger.debug("Ingestor %s resources released.", self.source_name)
