# System Design

## Implementation Status

**Built:** Data pipeline (ingestion → raw → refined) + screener API + auth + watchlists + frontend
**Future:** Equity Valuation Engine, Portfolio Attribution & Scenario Analysis Engine

## Project Structure

```
src/app/
├── main.py                    FastAPI app
├── config.py                  Settings from env
├── worker.py                  RabbitMQ consumer
├── scheduler.py               APScheduler CRON jobs
├── db/
│   ├── session.py             Engine + SessionLocal
│   └── models.py              10 models (Company, Filing, FinancialStatement,
│                              DerivedMetrics, FredSeries, IngestionLog,
│                              User, Watchlist, WatchlistCompany, ScreenerPreset)
├── ingestion/
│   ├── base.py                Base (DB, S3, Redis, audit log)
│   ├── edgar.py               SEC EDGAR XBRL companyfacts
│   ├── fred.py                FRED API (23 macro series)
│   └── yfinance_ingestor.py   EOD prices + returns
├── pipeline/
│   ├── xbrl_mapper.py         US-GAAP → canonical field mapping
│   ├── normalizer.py          Raw JSON → structured statements + ghost entry filtering
│   ├── validator.py           Quality + accounting identity checks
│   └── enricher.py            Full raw → refined orchestration
├── metrics/                   12 computation modules (142 metrics)
│   ├── compute.py             Orchestrator
│   ├── profitability.py       Margins, ROA/ROE/ROCE/ROIC
│   ├── liquidity.py           Ratios, NWC, CCC
│   ├── leverage.py            D/E, coverage, net debt
│   ├── efficiency.py          Turnover ratios
│   ├── cashflow.py            FCFF, FCFE, reinvestment
│   ├── growth.py              YoY growth, sustainable growth
│   ├── dupont.py              3-factor + 5-factor
│   ├── valuation.py           P/E, EV/EBITDA, yields, PEG
│   ├── quality.py             Accruals, Sloan, earnings quality
│   ├── forensic.py            Altman Z, Piotroski F, Beneish M
│   ├── shareholder.py         Payout, buyback, yield
│   └── per_share.py           Revenue/BV/FCF per share
├── api/
│   ├── router.py              Route mounting
│   ├── deps.py                Dependencies (pagination, date range, DB, Redis)
│   ├── cache.py               Redis TTL constants + helpers
│   ├── companies.py           Company listing + detail
│   ├── financials.py          Statements + metrics + metrics/latest
│   ├── prices.py              OHLCV + returns
│   ├── macro.py               FRED series (with Redis caching)
│   ├── screener.py            Dynamic JSONB filtering
│   ├── filings.py             SEC filing listing
│   ├── auth.py                JWT signup/login/me
│   ├── watchlists.py          User watchlist CRUD
│   └── system.py              Health + ingestion status
└── queue/
    └── broker.py              Sync pika RabbitMQ
```

## Sections

- [data-ingestion/](data-ingestion/) — SEC EDGAR, FRED, yFinance ingestion
- [data-pipeline/](data-pipeline/) — Raw → Refined transformation
- [engines/](engines/) — Equity Valuation, Portfolio Attribution (future)
- [database/](database/) — PostgreSQL, TimescaleDB, S3, Elasticsearch schemas
- [infrastructure/](infrastructure/) — Docker, CRON, RabbitMQ, Redis
- [api/](api/) — FastAPI REST endpoints + screener + auth + watchlists
