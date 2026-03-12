# Data Pipeline — Raw to Refined

Transforms raw ingested EDGAR XBRL data into clean, normalized, analysis-ready financial statements and computed metrics.

## Pipeline Overview

```
Raw Filings (PostgreSQL — XBRL facts in JSONB)
        │
        ▼
┌───────────────────┐
│   XBRL Mapper     │  ← Map 100+ US-GAAP tags to canonical field names
└────────┬──────────┘
         ▼
┌───────────────────┐
│   Normalizer      │  ← Group by period, resolve duplicates, fill derived fields, filter ghost entries
└────────┬──────────┘
         ▼
┌───────────────────┐
│   Validator       │  ← Quality checks, accounting identity, outlier detection
└────────┬──────────┘
         ▼
┌───────────────────┐
│   Enricher        │  ← Fill missing derived line items, trigger metrics computation
└────────┬──────────┘
         ▼
┌───────────────────┐
│   Metrics Compute │  ← 12 categories, 142 metrics per company per period
└────────┬──────────┘
         ▼
Refined Data (DerivedMetrics — 12 JSONB columns + FinancialStatement records)
```

## Stage Details

### 1. XBRL Mapper (`xbrl_mapper.py`)
- Defines 100+ XBRL tag mappings across three statement types:
  - **Income statement:** ~50 tags (revenue, COGS, operating income, EBITDA, net income, EPS, etc.)
  - **Balance sheet:** ~30 tags (total assets, current assets, total liabilities, equity, etc.)
  - **Cash flow:** ~20 tags (OCF, CapEx, dividends, share repurchases, etc.)
- Filters by unit (USD only, ignores shares and other units)
- Returns resolved facts dict with canonical field names

### 2. Normalizer (`normalizer.py`)
- Groups XBRL facts by period (end_date, fiscal_year, fiscal_period)
- Resolves ambiguous/duplicate tags using form preference logic (10-K preferred over 10-Q)
- Fills missing derived fields:
  - `gross_profit` = revenue - cost_of_revenue
  - `operating_income` = gross_profit - R&D - SGA
  - `EBITDA` = operating_income + D&A
- **Ghost entry filtering:** Detects and removes EDGAR cumulative reporting periods that only carry peripheral fields (e.g., share counts) without core financial data. Uses `_has_core_fields` validation to ensure statements contain meaningful data (revenue/net_income for income, total_assets for balance, OCF for cashflow).
- Classifies normalized data into income, balance sheet, and cash flow statements

### 3. Validator (`validator.py`)
- **Required fields check:** Validates essential fields per statement type
  - Income: revenue or net_income
  - Balance sheet: total_assets
  - Cash flow: operating_cash_flow
- **Outlier detection:** Flags values exceeding 1e15 as suspicious
- **Sign validation:** Revenue, shares outstanding should be non-negative
- **Balance sheet identity:** Assets ≈ Liabilities + Equity (1% tolerance)
- **Time-series anomaly detection:** Flags 500%+ period-over-period swings
- **EPS reconciliation:** Checks basic vs diluted shares consistency
- Populates `validation_warnings` and `validation_errors` JSONB on FinancialStatement records

### 4. Enricher (`enricher.py`)
- Orchestrates the full raw → refined pipeline per company
- Loads filings with enrichable status (raw or parsed)
- Runs XBRL Mapper → Normalizer → Validator sequentially
- Fills missing derived line items with fallback calculations:
  - D&A from cashflow statement if not on income statement
  - Working capital from current assets/liabilities
- Persists validated FinancialStatement records
- Triggers metrics computation for each enriched period

### 5. Metrics Compute (`metrics/compute.py`)
- Loads current + prior period financial statements for growth calculations
- Runs all 12 metric modules sequentially:
  1. **Profitability** (16) — margins, returns, cost ratios
  2. **Liquidity** (11) — ratios, working capital, operating cycle
  3. **Leverage** (10) — debt ratios, coverage
  4. **Efficiency** (10) — turnover ratios, cycles
  5. **Cash Flow** (11) — FCF, OCF metrics, reinvestment
  6. **Growth** (15) — YoY growth rates, sustainable growth
  7. **DuPont** (10) — 3-factor + 5-factor decomposition
  8. **Valuation** (17) — multiples, yields, PEG, Graham number
  9. **Quality** (10) — accruals, earnings quality, organic revenue
  10. **Forensic** (14) — Altman Z-score, Piotroski F-score (9 signals), Beneish M-score (8 indices)
  11. **Shareholder** (9) — payout, buyback, capital allocation
  12. **Per Share** (13) — revenue, BV, FCF, OCF per share
- Upserts DerivedMetrics row with all 12 JSONB category columns
- Handles None values and division by zero gracefully via `_safe_div` pattern

## Execution Model

- Pipeline runs as a single enrichment job triggered by RabbitMQ `pipeline.enrich` queue
- Enricher processes all companies with enrichable filings in a single sweep
- Pipeline state tracked via Filing `status` field (raw → parsed → refined)
- FinancialStatement records include `is_valid`, `validation_warnings`, `validation_errors`
- **Idempotent** — reprocessing raw data produces the same refined output

## Storage Destinations

| Data Type | Refined Storage | Why |
|-----------|----------------|-----|
| Financial statements (fundamental) | PostgreSQL (JSONB) | Flexible schema for varying XBRL taxonomies |
| Derived metrics (12 categories) | PostgreSQL (12 JSONB columns) | Enables dynamic JSONB screener queries |
| Time-series (prices, macro) | TimescaleDB | Optimized for time-range queries, compression |
| Original raw files | S3 (configured, not active) | Immutable archive, re-processable |
