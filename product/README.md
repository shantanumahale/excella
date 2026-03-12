# Excella — Product Overview

## What It Is

Excella is a financial data platform that ingests fundamental, macroeconomic, and pricing data from public sources, refines it into analysis-ready datasets, and powers two analytical engines:

1. **Equity Valuation Engine** — values individual equities using refined fundamental + macro + price data
2. **Portfolio Attribution and Scenario Analysis Engine** — decomposes portfolio returns and runs scenario/stress tests

## Data Flow

```
SEC EDGAR (fundamentals) ──┐
FRED (macro data) ─────────┼──► Raw Data ──► Refined Data ──┬──► Equity Valuation Engine
yFinance (price data) ─────┘                                └──► Portfolio Attribution & Scenario Analysis Engine
```

## Data Sources

| Source | Data Type | Examples |
|--------|-----------|---------|
| SEC EDGAR | Fundamentals | 10-K, 10-Q, 8-K filings; XBRL financial statements |
| FRED | Macroeconomic | Interest rates, GDP, CPI, unemployment, yield curves |
| yFinance | Pricing | Daily OHLCV, splits, dividends, market cap |

## Supported Data Formats

HTML, XBRL, JSON, XML, TXT, SGML, PDF, ZIP, TAR.GZ, CSV, TSV

## Core Capabilities

### Data Ingestion & Refinement
- Scheduled daily ingestion of EOD price data (yFinance)
- Scheduled SEC EDGAR filing ingestion (new/amended filings)
- FRED macro data pulls
- Raw → Refined transformation pipeline (parsing, normalization, validation, storage)

### Equity Valuation Engine
- Consumes refined fundamental, macro, and price data
- Produces equity valuations

### Portfolio Attribution & Scenario Analysis Engine
- Consumes refined data
- Decomposes portfolio performance (attribution)
- Runs scenario and stress test analyses

## Tech Stack Summary

- **Language:** Python
- **API:** FastAPI (REST)
- **Databases:** PostgreSQL (with JSONB/NoSQL), TimescaleDB (time-series), S3 (file/object storage), Elasticsearch (search/analytics)
- **Queue:** RabbitMQ (task queue)
- **Cache:** Redis
- **Scheduler:** CRON (daily EOD prices, SEC filings)
- **Runtime:** Docker
