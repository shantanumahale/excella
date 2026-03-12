# Data Pipeline — Raw to Refined

Transforms raw ingested data into clean, normalized, analysis-ready datasets.

## Pipeline Overview

```
Raw Data (S3 + PostgreSQL + TimescaleDB)
        │
        ▼
┌───────────────────┐
│   Parse & Extract │  ← XBRL/HTML/XML/SGML parsing, PDF text extraction
└────────┬──────────┘
         ▼
┌───────────────────┐
│   Normalize       │  ← Standardize units, date formats, ticker symbols, taxonomies
└────────┬──────────┘
         ▼
┌───────────────────┐
│   Validate        │  ← Data quality checks, completeness, outlier detection
└────────┬──────────┘
         ▼
┌───────────────────┐
│   Enrich          │  ← Derived metrics, cross-source joins, calculated fields
└────────┬──────────┘
         ▼
Refined Data (TimescaleDB + PostgreSQL + Elasticsearch)
```

## Stage Details

### 1. Parse & Extract
- **XBRL:** Parse inline XBRL and XBRL instance documents → extract financial facts (revenue, net income, EPS, total assets, etc.)
- **HTML/SGML:** Parse older EDGAR filings, extract tables and text
- **PDF:** Text extraction for supplementary filing documents
- **JSON/XML:** Parse FRED API responses and EDGAR JSON APIs
- **CSV/TSV:** Parse tabular data from bulk downloads

### 2. Normalize
- Map XBRL taxonomy tags to a canonical internal schema (e.g., `us-gaap:Revenues` → `revenue`)
- Standardize date formats to ISO 8601
- Normalize ticker symbols across sources
- Convert currency/unit representations to consistent formats
- Align fiscal periods (Q1-Q4, FY) across companies with different fiscal year ends

### 3. Validate
- Completeness checks — expected fields present, no unexpected nulls
- Accounting identity checks (assets = liabilities + equity)
- Time-series continuity — flag gaps in daily price data
- Outlier detection — flag values deviating significantly from historical norms
- Cross-source consistency — price data vs. reported fundamentals alignment

### 4. Enrich
- **Derived financial ratios:** P/E, P/B, EV/EBITDA, ROE, debt-to-equity, current ratio, etc.
- **Returns:** Daily, weekly, monthly, YTD, trailing returns from price data
- **Growth rates:** Revenue growth, earnings growth (QoQ, YoY)
- **Macro context:** Tag data points with concurrent macro conditions (rate environment, GDP growth phase)
- **Sector/industry classification:** Ensure consistent sector mapping

## Execution Model

- Pipeline stages run as **RabbitMQ workers**
- Each stage publishes a message to the next stage's queue on completion
- Failed items go to a **dead letter queue** for inspection and retry
- Pipeline state tracked in PostgreSQL (status per filing/ticker/date)
- **Idempotent** — reprocessing raw data produces the same refined output

## Storage Destinations

| Data Type | Refined Storage | Why |
|-----------|----------------|-----|
| Financial statements (fundamental) | PostgreSQL (JSONB) | Flexible schema for varying XBRL taxonomies |
| Time-series (prices, macro) | TimescaleDB | Optimized for time-range queries, compression |
| Filing full-text | Elasticsearch | Full-text search across filings |
| Derived ratios & metrics | PostgreSQL | Structured relational queries |
| Original raw files | S3 | Immutable archive, re-processable |
