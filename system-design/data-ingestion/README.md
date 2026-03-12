# Data Ingestion

Three independent ingestors pull data from external sources into the raw data layer.

## SEC EDGAR Ingestion

**Source:** SEC EDGAR XBRL Company Facts API
**Schedule:** CRON — daily 06:00 ET
**Worker:** `EdgarIngestor` in `ingestion/edgar.py`

### Flow
1. CRON publishes `{"action": "ingest_bulk", "payload": {"ciks": "recent"}}` to `ingest.edgar` queue
2. Worker fetches company facts JSON from `data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
3. XBRL Mapper resolves 100+ US-GAAP tags to canonical field names (revenue, COGS, EBIT, net_income, total_assets, etc.)
4. Facts grouped by period (end_date, fiscal_year, fiscal_period)
5. Multiple statement instances per period resolved via form preference (10-K > 10-Q)
6. Company record upserted in PostgreSQL
7. Filing metadata (accession number, form type, filing date, period) stored in PostgreSQL with status="raw"
8. Ingestion event logged to IngestionLog table

### Key Endpoints
- `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` — XBRL company facts
- `https://data.sec.gov/submissions/CIK{cik}.json` — company filings index

### XBRL Tag Coverage
- **Income statement:** ~50 tags (Revenues, CostOfRevenue, OperatingIncome, NetIncomeLoss, EPS, R&D, SGA, SBC, etc.)
- **Balance sheet:** ~30 tags (Assets, CurrentAssets, Liabilities, StockholdersEquity, Debt, Cash, etc.)
- **Cash flow:** ~20 tags (OperatingCashFlow, CapitalExpenditures, Dividends, ShareRepurchases, etc.)

### Rate Limits
- SEC EDGAR: 10 requests/second, User-Agent header required
- Fair access policy compliance required

---

## FRED Ingestion

**Source:** FRED API (Federal Reserve Economic Data)
**Schedule:** CRON — daily 07:00 ET
**Worker:** `FredIngestor` in `ingestion/fred.py`

### Flow
1. CRON publishes `{"action": "ingest_all", "payload": {}}` to `ingest.fred` queue
2. Worker fetches series metadata from `/fred/series` endpoint
3. Upserts FredSeries model in PostgreSQL
4. Fetches observations from `/fred/series/observations` endpoint
5. Bulk inserts into `fred_observations` TimescaleDB hypertable
6. Rate limiting: 0.1s delay between requests

### Tracked Series (23 total)

| Category | Series |
|----------|--------|
| Treasury yields | DGS1, DGS2, DGS5, DGS10, DGS30 |
| Spreads | T10Y2Y, T10Y3M |
| Rates | FEDFUNDS, DFF, MORTGAGE30US |
| Inflation | CPIAUCSL, CPILFESL, PCE, PCEPI |
| Employment | UNRATE, PAYEMS |
| Sentiment | UMCSENT |
| Markets | VIXCLS, BAMLH0A0HYM2 |
| Activity | GDP, GDPC1, HOUST, INDPRO |

### API
- `https://api.stlouisfed.org/fred/series` — series metadata
- `https://api.stlouisfed.org/fred/series/observations` — series data
- Requires API key (`FRED_API_KEY`)

---

## yFinance Ingestion

**Source:** yFinance Python library (unofficial Yahoo Finance scraper)
**Schedule:** CRON — daily 18:00 ET (after US market close)
**Worker:** `YFinanceIngestor` in `ingestion/yfinance_ingestor.py`

### Flow
1. CRON publishes `{"action": "ingest_bulk", "payload": {"tickers": "all"}}` to `ingest.yfinance` queue
2. Worker downloads historical daily prices via `yfinance.download()`
3. Extracts OHLCV data (open, high, low, close, adj_close, volume)
4. Computes 1-day simple returns (pct_change)
5. Upserts into `daily_prices` TimescaleDB hypertable
6. Upserts into `daily_returns` TimescaleDB hypertable
7. Bulk ingestion for all tracked tickers

### Data Points
- Open, High, Low, Close, Adj Close, Volume
- Computed 1-day returns

### Notes
- yFinance may be IP-blocked from Docker containers. Use the host-side seeder (`scripts/seed_yfinance_host.py`) as a fallback.

---

## Shared Patterns

- All ingestors extend `BaseIngestor` abstract class with logging, error handling, and ingestion tracking
- All ingestors are **RabbitMQ consumers** triggered by CRON-published messages via the single `worker.py` process
- Each ingestor records ingestion metadata (timestamp, status, record count) in IngestionLog for audit
- **Idempotent** — re-running an ingestion for the same date/filing does not create duplicates (upsert patterns used throughout)
