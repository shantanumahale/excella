"""Worker entry point — ``python -m app.worker``.

Connects to RabbitMQ, consumes from all ingest.* and pipeline.* queues,
and routes messages to the appropriate ingestor / enricher handlers.
"""

from __future__ import annotations

import json
import logging
import signal
import threading
from typing import Any

import pika

from app.config import settings
from app.queue.broker import ALL_QUEUES, _connection, _ensure_queues

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded handlers — avoids import-time side effects
# ---------------------------------------------------------------------------

_edgar = None
_fred = None
_yfinance = None


def _get_edgar():
    global _edgar
    if _edgar is None:
        from app.ingestion.edgar import EdgarIngestor
        _edgar = EdgarIngestor()
    return _edgar


def _get_fred():
    global _fred
    if _fred is None:
        from app.ingestion.fred import FredIngestor
        _fred = FredIngestor()
    return _fred


def _get_yfinance():
    global _yfinance
    if _yfinance is None:
        from app.ingestion.yfinance_ingestor import YFinanceIngestor
        _yfinance = YFinanceIngestor()
    return _yfinance


# ---------------------------------------------------------------------------
# Message routing
# ---------------------------------------------------------------------------

def _handle_edgar(msg: dict[str, Any]) -> None:
    action = msg.get("action")
    payload = msg.get("payload", {})
    ingestor = _get_edgar()

    if action == "ingest_company":
        result = ingestor.ingest_company(payload["cik"])
        logger.info("Edgar ingest_company result: %s", result)
    elif action == "ingest_bulk":
        ciks = payload.get("ciks", [])
        result = ingestor.ingest_bulk(ciks)
        logger.info("Edgar ingest_bulk result: %s", result)
    else:
        logger.warning("Unknown edgar action: %s", action)


def _handle_fred(msg: dict[str, Any]) -> None:
    action = msg.get("action")
    payload = msg.get("payload", {})
    ingestor = _get_fred()

    if action == "ingest_series":
        result = ingestor.ingest_series(payload["series_id"])
        logger.info("Fred ingest_series result: %s", result)
    elif action == "ingest_all":
        result = ingestor.ingest_all()
        logger.info("Fred ingest_all result: %s", result)
    else:
        logger.warning("Unknown fred action: %s", action)


def _handle_yfinance(msg: dict[str, Any]) -> None:
    action = msg.get("action")
    payload = msg.get("payload", {})
    ingestor = _get_yfinance()

    if action == "ingest_ticker":
        result = ingestor.ingest_ticker(payload["ticker"])
        logger.info("YFinance ingest_ticker result: %s", result)
    elif action == "ingest_bulk":
        tickers = payload.get("tickers", [])
        result = ingestor.ingest_bulk(tickers)
        logger.info("YFinance ingest_bulk result: %s", result)
    else:
        logger.warning("Unknown yfinance action: %s", action)


def _handle_enrich(msg: dict[str, Any]) -> None:
    action = msg.get("action")
    payload = msg.get("payload", {})

    # Import enricher lazily
    from app.pipeline import enricher
    from app.db.session import SessionLocal

    if action == "enrich_company":
        db = SessionLocal()
        try:
            enricher.enrich_company(db, payload["company_id"])
            logger.info("Enriched company_id=%s", payload["company_id"])
        finally:
            db.close()
    elif action == "enrich_all":
        enricher.enrich_all()
        logger.info("Enrich-all completed")
    else:
        logger.warning("Unknown enrich action: %s", action)


HANDLERS = {
    "ingest.edgar": _handle_edgar,
    "ingest.fred": _handle_fred,
    "ingest.yfinance": _handle_yfinance,
    "pipeline.enrich": _handle_enrich,
}


# ---------------------------------------------------------------------------
# Unified callback
# ---------------------------------------------------------------------------

def _on_message(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    queue = method.routing_key
    try:
        msg = json.loads(body)
        logger.info("[%s] Received action=%s", queue, msg.get("action"))
        handler = HANDLERS.get(queue)
        if handler is None:
            logger.error("No handler registered for queue %s", queue)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        handler(msg)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        logger.exception("[%s] Failed to process message", queue)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

_shutdown_event = threading.Event()


def _signal_handler(signum: int, frame: Any) -> None:
    sig_name = signal.Signals(signum).name
    logger.info("Received %s — initiating graceful shutdown", sig_name)
    _shutdown_event.set()


def main() -> None:
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    logger.info("Worker starting — connecting to RabbitMQ")
    conn = _connection()
    channel = conn.channel()
    _ensure_queues(channel)
    channel.basic_qos(prefetch_count=1)

    for queue_name in ALL_QUEUES:
        channel.basic_consume(queue=queue_name, on_message_callback=_on_message)
        logger.info("Subscribed to %s", queue_name)

    logger.info("Worker ready — waiting for messages")
    try:
        while not _shutdown_event.is_set():
            conn.process_data_events(time_limit=1)
    except Exception:
        logger.exception("Worker loop error")
    finally:
        logger.info("Worker shutting down")
        try:
            channel.stop_consuming()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()
