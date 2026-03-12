# Database Design

Four storage systems, each chosen for specific access patterns.

## PostgreSQL

Primary relational + document store. Uses JSONB columns for semi-structured data.

### Tables

**Companies**
- `id`, `cik`, `ticker`, `name`, `sector`, `industry`, `sic_code`, `fiscal_year_end`, `created_at`, `updated_at`

**Filings**
- `id`, `company_id` (FK), `accession_number`, `form_type`, `filing_date`, `period_of_report`, `s3_key` (raw file), `status` (raw/parsed/refined/error), `created_at`

**Financial Statements**
- `id`, `filing_id` (FK), `company_id` (FK), `period_start`, `period_end`, `fiscal_period` (Q1-Q4/FY), `statement_type` (income/balance/cashflow), `data` (JSONB — flexible for varying XBRL taxonomies), `created_at`

**Derived Metrics**
- `id`, `company_id` (FK), `period_end`, `fiscal_period`, `metrics` (JSONB — P/E, ROE, margins, growth rates, etc.), `created_at`

**Portfolios**
- `id`, `name`, `description`, `created_at`, `updated_at`

**Portfolio Holdings**
- `id`, `portfolio_id` (FK), `company_id` (FK), `weight`, `shares`, `as_of_date`

**Valuations**
- `id`, `company_id` (FK), `valuation_date`, `method` (dcf/comps/ddm), `result` (JSONB — intrinsic value, range, assumptions), `created_at`

**Attribution Results**
- `id`, `portfolio_id` (FK), `period_start`, `period_end`, `method`, `result` (JSONB), `created_at`

**Scenario Definitions**
- `id`, `name`, `type` (historical/custom/stress), `parameters` (JSONB), `created_at`

**Scenario Results**
- `id`, `portfolio_id` (FK), `scenario_id` (FK), `result` (JSONB), `run_date`, `created_at`

**Ingestion Log**
- `id`, `source` (edgar/fred/yfinance), `started_at`, `completed_at`, `status`, `records_processed`, `error_message`

**FRED Series Metadata**
- `id`, `series_id` (e.g., DGS10), `title`, `frequency`, `units`, `last_updated`

---

## TimescaleDB

Extension on PostgreSQL, used for all time-series data. Hypertables auto-partition by time.

### Hypertables

**daily_prices**
- `time` (timestamptz), `ticker`, `open`, `high`, `low`, `close`, `adj_close`, `volume`
- Hypertable chunked by `time` (monthly chunks)
- Indexes: `(ticker, time DESC)`

**daily_returns**
- `time`, `ticker`, `return_1d`, `return_5d`, `return_21d`, `return_63d`, `return_252d`

**fred_observations**
- `time`, `series_id`, `value`
- Hypertable chunked by `time`
- Indexes: `(series_id, time DESC)`

**corporate_actions**
- `time`, `ticker`, `action_type` (dividend/split), `value`, `details` (JSONB)

### Continuous Aggregates
- Weekly/monthly OHLCV rollups
- Rolling return windows

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

---

## Elasticsearch

Full-text search and analytics over filing content.

### Indices

**filings_fulltext**
- `filing_id`, `company_name`, `ticker`, `cik`, `form_type`, `filing_date`, `content` (extracted text), `sections` (nested — item 1, item 7, etc.)

### Use Cases
- Search filings by keyword (e.g., "supply chain disruption")
- Filter by form type, date range, company
- Aggregate mentions of terms over time
