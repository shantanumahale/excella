# Database Design

Four storage systems, each chosen for specific access patterns.

## PostgreSQL

Primary relational + document store. Uses JSONB columns for semi-structured data.

### Tables

**Companies**
- `id`, `cik`, `ticker`, `name`, `sector`, `industry`, `sic_code`, `sic_description`, `fiscal_year_end`, `exchange`, `ein`, `state_of_incorporation`, `country`, `currency`, `website`, `description`, `market_cap`, `employees`, `created_at`, `updated_at`

**Filings**
- `id`, `company_id` (FK), `accession_number`, `form_type`, `filing_date`, `period_of_report`, `primary_document`, `description`, `primary_doc_url`, `s3_key` (raw file), `status` (raw/parsed/refined/error), `created_at`

**Financial Statements**
- `id`, `filing_id` (FK, optional), `company_id` (FK), `period_start`, `period_end`, `fiscal_year`, `fiscal_period` (Q1-Q4/FY), `statement_type` (income/balance/cashflow), `data` (JSONB — canonical fields like revenue, net_income, total_assets), `source` (edgar/manual), `period_type` (annual/quarterly), `is_valid`, `validation_warnings` (JSONB), `validation_errors` (JSONB), `created_at`
- Unique constraint: `(company_id, period_end, fiscal_period, statement_type)`

**Derived Metrics**
- `id`, `company_id` (FK), `period_end`, `fiscal_period`
- 12 JSONB columns (one per metric category):
  - `profitability` — 16 metrics (margins, ROA, ROE, ROCE, ROIC, cost ratios)
  - `liquidity` — 11 metrics (current/quick/cash ratio, NWC, DIO, DSO, DPO, CCC)
  - `leverage` — 10 metrics (D/E, D/A, D/EBITDA, interest coverage, net debt)
  - `efficiency` — 10 metrics (asset/inventory/receivables/payables turnover)
  - `cashflow` — 11 metrics (FCFF, FCFE, OCF margin, reinvestment rate)
  - `growth` — 15 metrics (YoY revenue/earnings/EPS/OCF/FCF/assets growth)
  - `dupont` — 10 metrics (3-factor + 5-factor decomposition)
  - `valuation` — 17 metrics (P/E, P/B, P/S, EV/EBITDA, PEG, yields)
  - `quality` — 10 metrics (accruals, Sloan ratio, earnings quality)
  - `forensic` — 14 metrics (Altman Z-score, Piotroski F-score, Beneish M-score, risk flags)
  - `shareholder` — 9 metrics (payout, buyback, shareholder yield)
  - `per_share` — 13 metrics (revenue, BV, FCF, OCF, dividends per share)
- `created_at`
- Unique constraint: `(company_id, period_end, fiscal_period)`

**Users**
- `id`, `email` (unique, indexed), `hashed_password` (bcrypt), `name`, `is_active`, `created_at`, `updated_at`

**Watchlists**
- `id`, `user_id` (FK), `name`, `description`, `created_at`

**Watchlist Companies** (join table)
- `id`, `watchlist_id` (FK), `company_id` (FK), `added_at`
- Unique constraint: `(watchlist_id, company_id)`

**Screener Presets**
- `id`, `user_id` (FK), `name`, `filters` (JSON — saved ScreenerFilter list), `created_at`

**Ingestion Log**
- `id`, `source` (edgar/fred/yfinance), `job_type`, `started_at`, `completed_at`, `status` (running/success/error), `records_processed`, `error_message`

**FRED Series Metadata**
- `id`, `series_id` (e.g., DGS10), `title`, `frequency`, `units`, `seasonal_adjustment`, `notes`, `last_updated`

---

## TimescaleDB

Extension on PostgreSQL, used for all time-series data. Hypertables auto-partition by time.

### Hypertables

**daily_prices**
- `time` (timestamptz), `ticker`, `open`, `high`, `low`, `close`, `adj_close`, `volume`
- Hypertable chunked by `time` (monthly chunks)
- Indexes: `(ticker, time DESC)`

**daily_returns**
- `time`, `ticker`, `return_1d`

**fred_observations**
- `time`, `series_id`, `value`
- Hypertable chunked by `time`
- Indexes: `(series_id, time DESC)`

---

## S3

Object storage for raw files. Immutable archive — never modified after write.

### Bucket Structure
```
excella-raw/
├── edgar/
│   └── {cik}/{accession_number}/
│       ├── filing.html
│       ├── filing.xml
│       ├── R1.htm ... (XBRL viewer files)
│       └── {attachment files}
├── fred/
│   └── {series_id}/{date}.json
└── yfinance/
    └── {ticker}/{date}.csv
```

> **Note:** S3/MinIO is configured but not actively used for file storage in the current implementation. Raw XBRL facts are stored directly in PostgreSQL JSONB.

---

## Elasticsearch

Full-text search and analytics over filing content.

### Indices

**filings_fulltext**
- `filing_id`, `company_name`, `ticker`, `cik`, `form_type`, `filing_date`, `content` (extracted text), `sections` (nested — item 1, item 7, etc.)

> **Note:** Elasticsearch is configured in docker-compose but not yet integrated into the ingestion or API flow.

---

## Future Tables (Not Yet Implemented)

The following tables are planned for the Equity Valuation and Portfolio Attribution engines:

- **Portfolios** — `id`, `name`, `description`, `created_at`, `updated_at`
- **Portfolio Holdings** — `id`, `portfolio_id` (FK), `company_id` (FK), `weight`, `shares`, `as_of_date`
- **Valuations** — `id`, `company_id` (FK), `valuation_date`, `method` (dcf/comps/ddm), `result` (JSONB), `created_at`
- **Attribution Results** — `id`, `portfolio_id` (FK), `period_start`, `period_end`, `method`, `result` (JSONB), `created_at`
- **Scenario Definitions** — `id`, `name`, `type` (historical/custom/stress), `parameters` (JSONB), `created_at`
- **Scenario Results** — `id`, `portfolio_id` (FK), `scenario_id` (FK), `result` (JSONB), `run_date`, `created_at`
