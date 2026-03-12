"""RabbitMQ broker — synchronous publish / consume using pika."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

import pika

from app.config import settings

logger = logging.getLogger(__name__)

# Canonical queue names
QUEUE_EDGAR = "ingest.edgar"
QUEUE_FRED = "ingest.fred"
QUEUE_YFINANCE = "ingest.yfinance"
QUEUE_ENRICH = "pipeline.enrich"

ALL_QUEUES = [QUEUE_EDGAR, QUEUE_FRED, QUEUE_YFINANCE, QUEUE_ENRICH]


def _connection() -> pika.BlockingConnection:
    params = pika.URLParameters(settings.rabbitmq_url)
    params.heartbeat = 600
    params.blocked_connection_timeout = 300
    return pika.BlockingConnection(params)


def _ensure_queues(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    """Declare all queues as durable so they survive broker restarts."""
    for q in ALL_QUEUES:
        channel.queue_declare(queue=q, durable=True)


def publish(queue: str, message: dict[str, Any]) -> None:
    """Publish a JSON message to *queue*."""
    conn = _connection()
    try:
        ch = conn.channel()
        _ensure_queues(ch)
        ch.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type="application/json",
            ),
        )
        logger.info("Published to %s: %s", queue, message.get("action", "?"))
    finally:
        conn.close()


def consume(queue: str, callback: Callable[[dict[str, Any]], None]) -> None:
    """
    Blocking consume from *queue*.

    ``callback`` receives the parsed JSON body.  If it raises, the message
    is nack-ed (and requeued once).
    """
    conn = _connection()
    ch = conn.channel()
    _ensure_queues(ch)
    ch.basic_qos(prefetch_count=1)

    def _on_message(
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        try:
            payload = json.loads(body)
            logger.info("Received from %s: %s", queue, payload.get("action", "?"))
            callback(payload)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.exception("Error processing message from %s", queue)
            # Nack with requeue=False to avoid infinite loops; message goes to DLQ
            # if one is configured, otherwise is discarded.
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    ch.basic_consume(queue=queue, on_message_callback=_on_message)

    logger.info("Consuming from %s …", queue)
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        ch.stop_consuming()
    finally:
        conn.close()
