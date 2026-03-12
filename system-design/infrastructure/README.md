# Infrastructure

Everything runs in Docker. Orchestrated via Docker Compose.

## Docker Services

```yaml
services:
  # Application
  api            # FastAPI REST server (:8000)
  worker         # Single RabbitMQ consumer — routes messages to EDGAR/FRED/yFinance/Pipeline handlers
  scheduler      # APScheduler CRON job publisher
  frontend       # Next.js screener UI (:3000)

  # Data Stores
  postgres       # PostgreSQL + TimescaleDB (:5432)
  redis          # Cache (:6379)
  rabbitmq       # Task queue (:5672, management UI :15672)
  elasticsearch  # Full-text search (:9200) — configured, not yet integrated
  minio          # S3-compatible object storage (:9000, console :9001) — configured, not yet active
```

## CRON Scheduler

Runs inside a dedicated container. Uses APScheduler to publish messages to RabbitMQ queues on schedule. All times are **US/Eastern**.

| Job | Schedule | Queue | Description |
|-----|----------|-------|-------------|
| SEC Filings | Daily 06:00 ET | `ingest.edgar` | Fetch recent EDGAR filings via XBRL companyfacts API |
| FRED Data | Daily 07:00 ET | `ingest.fred` | Pull all 23 macro series observations |
| EOD Prices | Daily 18:00 ET (after close) | `ingest.yfinance` | Pull daily OHLCV for all tracked tickers |
| Pipeline Enrichment | Daily 20:00 ET | `pipeline.enrich` | Process filings through normalize → validate → enrich → compute metrics |

## RabbitMQ

Task queue for decoupling scheduling from execution.

### Queues
- `ingest.edgar` — SEC EDGAR ingestion tasks
- `ingest.fred` — FRED ingestion tasks
- `ingest.yfinance` — yFinance ingestion tasks
- `pipeline.enrich` — Full enrichment pipeline (normalize + validate + compute metrics)

### Patterns
- Single worker process consumes all queues, routing messages to appropriate handlers
- Workers consume and ack on success
- Durable queues with persistent message delivery
- Single prefetch for ordered processing

### Message Format
```json
{
  "action": "ingest_bulk",
  "payload": {"ciks": "recent"},
  "timestamp": "2024-01-01T06:00:00"
}
```

## Redis

In-memory cache for macro endpoint responses. Graceful degradation if Redis is unavailable.

### Cache Keys
- `macro:series:list` — all FRED series metadata (TTL: 3600s)
- `macro:series:all_latest` — latest value for all series (TTL: 300s)
- `macro:obs:{series_id}:{offset}:{limit}:{start}:{end}` — series observations (TTL: 3600s)
- `macro:latest:{series_id}` — latest observation for a specific series (TTL: 300s)

## Networking
- All services on a shared Docker network
- `api` exposed on port 8000, `frontend` on port 3000
- `rabbitmq` management UI on port 15672, `minio` console on port 9001
- Databases accessible only within the Docker network
- Health checks defined for all services; API/worker/scheduler depend on database/cache/queue readiness
