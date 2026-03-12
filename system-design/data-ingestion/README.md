# Data Ingestion

Three independent ingestors pull data from external sources into the raw data layer.

## SEC EDGAR Ingestion

**Source:** SEC EDGAR FULL-TEXT SEARCH API + EFTS + XBRL API
**Schedule:** CRON — periodic check for new/amended filings
**Data Formats:** HTML, XBRL, XML, SGML, TXT, PDF, ZIP, TAR.GZ

### Flow
1. CRON triggers SEC EDGAR worker via RabbitMQ
2. Worker queries EDGAR for new filings (10-K, 10-Q, 8-K, etc.)
3. Raw filing documents downloaded and stored in **S3** (original format)
4. Filing metadata (CIK, accession number, filing date, form type, company) stored in **PostgreSQL**
5. XBRL facts extracted and stored as raw structured data in **PostgreSQL (JSONB)**

### Key Endpoints
- `https://efts.sec.gov/LATEST/search-index?q=...` — full-text search
- `https://data.sec.gov/submissions/CIK{cik}.json` — company filings index
- `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` — XBRL facts

### Rate Limits
- SEC EDGAR: 10 requests/second, User-Agent header required
- Fair access policy compliance required

---

## FRED Ingestion

**Source:** FRED API (Federal Reserve Economic Data)
**Schedule:** CRON — daily or as series update
**Data Formats:** JSON, XML

### Flow
1. CRON triggers FRED worker via RabbitMQ
2. Worker pulls macro series (GDP, CPI, interest rates, unemployment, yield curves, etc.)
3. Raw JSON responses stored in **S3**
4. Series observations stored in **TimescaleDB** (time-series optimized)
5. Series metadata stored in **PostgreSQL**

### Key Series
- `DGS10`, `DGS2`, `DGS30` — Treasury yields
- `CPIAUCSL` — CPI
- `GDP`, `GDPC1` — GDP
- `UNRATE` — Unemployment
- `FEDFUNDS` — Fed funds rate
- `T10Y2Y` — 10Y-2Y spread

### API
- `https://api.stlouisfed.org/fred/series/observations` — series data
- Requires API key

---

## yFinance Ingestion

**Source:** yFinance Python library
**Schedule:** CRON — daily after market close (EOD)
**Data Formats:** CSV/DataFrame (via yfinance library)

### Flow
1. CRON triggers yFinance worker via RabbitMQ
2. Worker pulls EOD OHLCV data for tracked tickers
3. Raw price data stored in **TimescaleDB** (hypertable partitioned by time)
4. Corporate actions (splits, dividends) stored in **PostgreSQL**
5. Ticker metadata (sector, industry, market cap) stored in **PostgreSQL**

### Data Points
- Open, High, Low, Close, Adj Close, Volume
- Dividends, Stock Splits
- Market cap, sector, industry, P/E, EPS (info endpoint)

---

## Shared Patterns

- All ingestors are **RabbitMQ consumers** triggered by CRON-published messages
- Each ingestor writes to a **raw data** layer (S3 for files, PostgreSQL/TimescaleDB for structured)
- Each ingestor records ingestion metadata (timestamp, status, record count) for audit
- **Redis** caches recently fetched data to avoid redundant API calls
- **Idempotent** — re-running an ingestion for the same date/filing does not create duplicates
