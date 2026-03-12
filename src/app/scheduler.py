"""Scheduler entry point — ``python -m app.scheduler``.

Uses APScheduler with CronTrigger to publish messages to RabbitMQ queues
on a fixed daily schedule (all times US/Eastern).
"""

from __future__ import annotations

import logging
import signal
from typing import Any

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.queue.broker import (
    QUEUE_EDGAR,
    QUEUE_ENRICH,
    QUEUE_FRED,
    QUEUE_YFINANCE,
    publish,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TIMEZONE = "US/Eastern"

# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------


def job_ingest_yfinance() -> None:
    """Daily 18:00 ET — ingest all tickers from Yahoo Finance."""
    logger.info("Scheduler: triggering yfinance bulk ingest")
    publish(QUEUE_YFINANCE, {"action": "ingest_bulk", "payload": {"tickers": "all"}})


def job_ingest_edgar() -> None:
    """Daily 06:00 ET — ingest recent EDGAR filings."""
    logger.info("Scheduler: triggering edgar bulk ingest (recent)")
    publish(QUEUE_EDGAR, {"action": "ingest_bulk", "payload": {"ciks": "recent"}})


def job_ingest_fred() -> None:
    """Daily 07:00 ET — ingest all FRED series."""
    logger.info("Scheduler: triggering fred ingest_all")
    publish(QUEUE_FRED, {"action": "ingest_all", "payload": {}})


def job_enrich_all() -> None:
    """Daily 20:00 ET — enrich all companies."""
    logger.info("Scheduler: triggering pipeline enrich_all")
    publish(QUEUE_ENRICH, {"action": "enrich_all", "payload": {}})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    scheduler = BlockingScheduler()

    scheduler.add_job(
        job_ingest_yfinance,
        CronTrigger(hour=18, minute=0, timezone=TIMEZONE),
        id="ingest_yfinance",
        name="YFinance daily ingest",
        replace_existing=True,
    )
    scheduler.add_job(
        job_ingest_edgar,
        CronTrigger(hour=6, minute=0, timezone=TIMEZONE),
        id="ingest_edgar",
        name="EDGAR daily ingest",
        replace_existing=True,
    )
    scheduler.add_job(
        job_ingest_fred,
        CronTrigger(hour=7, minute=0, timezone=TIMEZONE),
        id="ingest_fred",
        name="FRED daily ingest",
        replace_existing=True,
    )
    scheduler.add_job(
        job_enrich_all,
        CronTrigger(hour=20, minute=0, timezone=TIMEZONE),
        id="enrich_all",
        name="Pipeline enrich all",
        replace_existing=True,
    )

    def _shutdown(signum: int, frame: Any) -> None:
        sig_name = signal.Signals(signum).name
        logger.info("Received %s — shutting down scheduler", sig_name)
        scheduler.shutdown(wait=False)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("Scheduler starting with %d jobs", len(scheduler.get_jobs()))
    for job in scheduler.get_jobs():
        logger.info("  %s — next run: %s", job.name, job.next_run_time)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
