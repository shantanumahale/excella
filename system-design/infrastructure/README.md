# Infrastructure

Everything runs in Docker. Orchestrated via Docker Compose.

## Docker Services

```yaml
services:
  # Application
  api            # FastAPI REST server
  worker-edgar   # SEC EDGAR ingestion worker
  worker-fred    # FRED ingestion worker
  worker-yfinance # yFinance ingestion worker
  worker-pipeline # Raw → Refined pipeline worker
  scheduler      # CRON scheduler

  # Data Stores
  postgres       # PostgreSQL + TimescaleDB
  redis          # Cache
  rabbitmq       # Task queue
  elasticsearch  # Full-text search
  minio          # S3-compatible object storage (local dev)
```

## CRON Scheduler

Runs inside a dedicated container. Publishes messages to RabbitMQ queues on schedule.

| Job | Schedule | Queue | Description |
|-----|----------|-------|-------------|
| EOD Prices | Daily 18:00 ET (after market close) | `ingest.yfinance` | Pull daily OHLCV for all tracked tickers |
| SEC Filings | Daily 06:00 ET | `ingest.edgar` | Check for new/amended filings |
| FRED Data | Daily 07:00 ET | `ingest.fred` | Pull updated macro series |
| Pipeline Sweep | Daily 20:00 ET | `pipeline.process` | Process any unrefined raw data |

## RabbitMQ

Task queue for decoupling scheduling from execution.

### Queues
- `ingest.edgar` — SEC EDGAR ingestion tasks
- `ingest.fred` — FRED ingestion tasks
- `ingest.yfinance` — yFinance ingestion tasks
- `pipeline.parse` — Parse & extract stage
- `pipeline.normalize` — Normalize stage
- `pipeline.validate` — Validate stage
- `pipeline.enrich` — Enrich stage
- `pipeline.dlq` — Dead letter queue for failed items

### Patterns
- Workers consume from their queue and ack on success
- Failed messages route to DLQ with retry metadata
- Each message includes correlation ID for tracing

## Redis

In-memory cache for hot data and deduplication.

### Cache Keys
- `price:{ticker}:latest` — most recent price (TTL: 1 hour)
- `fred:{series_id}:latest` — most recent observation (TTL: 6 hours)
- `valuation:{company_id}:latest` — most recent valuation result (TTL: 24 hours)
- `scenario:{portfolio_id}:{scenario_id}` — cached scenario result (TTL: 24 hours)
- `ingest:lock:{source}:{key}` — deduplication lock (TTL: matches schedule interval)

## Networking
- All services on a shared Docker network
- Only `api` exposed externally (port 8000)
- Databases accessible only within the Docker network
