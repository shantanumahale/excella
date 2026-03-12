# Excella — Product Overview

## What It Is

Excella is a financial data platform and equity screener that ingests fundamental, macroeconomic, and pricing data from public sources, refines it into analysis-ready datasets, computes 142 derived metrics across 12 categories, and serves them through a REST API and a modern Next.js frontend with dynamic screening, company analysis, peer comparison, and macro dashboards.

## Core Feature: Dynamic Screener

The screener is the centerpiece of Excella — filter companies by any combination of 142 metrics using operators (greater than, less than, between, etc.) with instant results. Similar to screener.in but built on JSONB for maximum flexibility.

## Data Flow

```
SEC EDGAR (fundamentals) ──┐
FRED (macro data) ─────────┼──► Raw Data ──► Pipeline ──► Refined Data ──► REST API ──► Frontend
yFinance (price data) ─────┘               (normalize,    (142 metrics,     (FastAPI)    (Next.js)
                                            validate,      12 JSONB cols)
                                            compute)
```

## Data Sources

| Source | Data Type | Examples | Schedule |
|--------|-----------|---------|----------|
| SEC EDGAR | Fundamentals | 10-K, 10-Q filings; XBRL financial statements (100+ tags) | Daily 06:00 ET |
| FRED | Macroeconomic | 23 series: Treasury yields, CPI, GDP, unemployment, VIX, etc. | Daily 07:00 ET |
| yFinance | Pricing | Daily OHLCV, computed returns | Daily 18:00 ET |

## Core Capabilities

### Data Ingestion & Refinement
- Scheduled daily ingestion from SEC EDGAR (XBRL company facts), FRED (23 macro series), yFinance (EOD prices)
- XBRL tag mapping (100+ US-GAAP tags to canonical field names)
- Raw → Refined pipeline: normalize, validate (accounting identity checks, outlier detection), enrich
- Ghost entry filtering to remove spurious EDGAR cumulative periods
- Pipeline enrichment computes 142 derived metrics daily at 20:00 ET

### Equity Screener (Built)
- Filter companies by any combination of 142 metrics across 12 categories
- Operators: `gt`, `gte`, `lt`, `lte`, `eq`, `between`, `not_null`
- Parameterized SQL on JSONB columns for fast, flexible queries
- Sortable by any metric, with pagination
- Metric catalogue API for UI-driven filter building

### Computed Metrics (12 categories, 142 metrics)

| Category | Count | Highlights |
|----------|-------|-----------|
| Profitability | 16 | Margins (gross/operating/net/EBITDA), ROA, ROE, ROCE, ROIC |
| Liquidity | 11 | Current/quick/cash ratio, cash conversion cycle, DIO/DSO/DPO |
| Leverage | 10 | D/E, D/A, D/EBITDA, interest coverage, net debt |
| Efficiency | 10 | Asset/inventory/receivables turnover, CapEx ratios |
| Cash Flow | 11 | FCFF, FCFE, OCF margin, cash ROIC, reinvestment rate |
| Growth | 15 | YoY revenue/earnings/EPS/OCF/FCF growth, sustainable growth rate |
| DuPont | 10 | 3-factor + 5-factor decomposition |
| Valuation | 17 | P/E, P/B, EV/EBITDA, PEG, Graham number, yields |
| Quality | 10 | Accruals ratio, Sloan ratio, earnings quality score |
| Forensic | 14 | Altman Z-score, Piotroski F-score (9 signals), Beneish M-score (8 indices) |
| Shareholder | 9 | Payout ratio, buyback ratio, shareholder yield |
| Per Share | 13 | Revenue, book value, FCF, OCF, dividends per share |

### Authentication & Personalization (Built)
- JWT-based auth (signup, login, 24-hour tokens)
- User watchlists for tracking companies
- Screener presets for saving filter configurations

### Frontend (Built)

| Page | Description |
|------|-------------|
| Screener | Dynamic filtering on 142 metrics, sortable columns, pagination |
| Company Overview | Full profile, key metrics grid, forensic scores (Altman Z, Piotroski F, Beneish M) |
| Financials | Income statement, balance sheet, cash flow — annual & quarterly |
| Metrics | Historical metrics charts by category |
| Price | Candlestick OHLCV chart with volume, date range selector |
| Filings | SEC filing documents with EDGAR links |
| Peer Comparison | Side-by-side metrics for up to 5 companies |
| Macro Dashboard | 23 FRED series grouped by theme (rates, inflation, GDP, market) |
| Watchlist | User watchlists with company tracking (requires auth) |
| Login / Signup | JWT-based authentication |

### Equity Valuation Engine (Future)
- Consumes refined fundamental + macro + price data
- Produces equity valuations (DCF, comps, DDM, asset-based)

### Portfolio Attribution & Scenario Analysis Engine (Future)
- Decomposes portfolio performance (Brinson-style attribution)
- Runs scenario and stress test analyses

## Tech Stack Summary

- **Frontend:** Next.js 16, React 19, Tailwind CSS v4, TanStack Table/Query, TradingView Charts, Recharts
- **Backend:** Python 3.12, FastAPI
- **Auth:** JWT (PyJWT + bcrypt)
- **Databases:** PostgreSQL + TimescaleDB (time-series), JSONB for metrics
- **Object Storage:** S3 / MinIO (configured)
- **Search:** Elasticsearch (configured)
- **Queue:** RabbitMQ (4 task queues)
- **Cache:** Redis (macro endpoint caching)
- **Scheduler:** APScheduler (4 daily CRON jobs, US/Eastern)
- **Runtime:** Docker Compose (9 services)
