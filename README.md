# Excella

Financial data platform and equity screener. Ingests fundamentals (SEC EDGAR), macroeconomic data (FRED), and pricing data (yFinance), computes 100+ derived metrics, and serves them through a REST API and a modern Next.js frontend with dynamic screening, company analysis, peer comparison, and macro dashboards.

## Quick Start

```bash
# 1. Copy env file and configure
cp .env.example .env
# Edit .env — set FRED_API_KEY and EDGAR_USER_AGENT at minimum

# 2. Start all services
docker compose up -d

# 3. Access the app
#    http://localhost:3000          ← Frontend (Screener UI)
#    http://localhost:8000/docs     ← Swagger UI
#    http://localhost:8000/redoc    ← ReDoc
#    http://localhost:8000/api/v1/  ← API root
```

## Architecture

```
SEC EDGAR ──┐
FRED ───────┼──► Ingestion Workers ──► Raw Data ──► Pipeline ──► Refined Data ──► REST API ──► Frontend
yFinance ───┘     (RabbitMQ)           (S3+PG)    (normalize,    (DerivedMetrics    (FastAPI)    (Next.js)
                                                   validate,      12 JSONB cols)
                                                   compute)
```

**Data flow:** CRON scheduler publishes tasks to RabbitMQ → workers ingest from external APIs → raw data stored in S3/PostgreSQL/TimescaleDB → pipeline normalizes XBRL, validates, and computes metrics → refined data queryable via screener API → Next.js frontend renders interactive UI.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 16, React 19, Tailwind CSS v4, TanStack Table/Query |
| Backend | Python 3.12, FastAPI |
| Database | PostgreSQL + TimescaleDB (time-series) |
| Object Storage | S3 / MinIO |
| Search | Elasticsearch |
| Task Queue | RabbitMQ |
| Cache | Redis |
| Charts | TradingView Lightweight Charts (prices), Recharts (metrics) |
| Auth | JWT (PyJWT + bcrypt) |
| Scheduler | APScheduler (CRON triggers) |
| Runtime | Docker Compose (9 services) |

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| **Screener** | `/screener` | Dynamic filtering on 142 metrics across 12 categories, sortable/customizable columns, pagination |
| **Company Overview** | `/company/{ticker}` | Full profile, key metrics grid, forensic scores (Altman Z, Piotroski F, Beneish M) |
| **Financials** | `/company/{ticker}/financials` | Income statement, balance sheet, cash flow — annual & quarterly |
| **Metrics** | `/company/{ticker}/metrics` | Historical metrics charts by category with line charts |
| **Price** | `/company/{ticker}/price` | Candlestick OHLCV chart with volume, date range selector |
| **Filings** | `/company/{ticker}/filings` | SEC filing documents (10-K, 10-Q, 8-K) with EDGAR links |
| **Peer Comparison** | `/compare?tickers=AAPL,MSFT` | Side-by-side metrics comparison for up to 5 companies |
| **Macro Dashboard** | `/macro` | 23 FRED series grouped by theme (rates, inflation, GDP, market) |
| **Watchlist** | `/watchlist` | User watchlists with company tracking (requires auth) |
| **Login / Signup** | `/login`, `/signup` | JWT-based authentication |

## API Endpoints

### Screener (core feature)
- `POST /api/v1/screener` — filter companies by any combination of 100+ metrics
- `GET /api/v1/screener/metrics` — list all available metrics by category

### Companies
- `GET /api/v1/companies` — list (filter by sector, industry, search)
- `GET /api/v1/companies/{ticker}` — detail with latest metrics

### Financial Statements
- `GET /api/v1/companies/{ticker}/financials` — income, balance sheet, cashflow
- `GET /api/v1/companies/{ticker}/metrics` — derived metrics history
- `GET /api/v1/companies/{ticker}/metrics/latest` — most recent metrics
- `GET /api/v1/companies/{ticker}/filings` — SEC filings list

### Prices
- `GET /api/v1/prices/{ticker}` — daily OHLCV
- `GET /api/v1/prices/{ticker}/latest` — most recent price
- `GET /api/v1/prices/{ticker}/returns` — 1d/5d/21d/63d/126d/252d returns

### Macro
- `GET /api/v1/macro/series` — list tracked FRED series
- `GET /api/v1/macro/series/{series_id}` — observations
- `GET /api/v1/macro/series/{series_id}/latest` — latest value

### Auth
- `POST /api/v1/auth/signup` — create account
- `POST /api/v1/auth/login` — get JWT token
- `GET /api/v1/auth/me` — current user profile

### Watchlists
- `POST /api/v1/watchlists` — create watchlist
- `GET /api/v1/watchlists` — list user's watchlists
- `GET /api/v1/watchlists/{id}` — watchlist detail with companies
- `DELETE /api/v1/watchlists/{id}` — delete watchlist
- `POST /api/v1/watchlists/{id}/companies` — add tickers
- `DELETE /api/v1/watchlists/{id}/companies/{ticker}` — remove ticker

### System
- `GET /api/v1/health` — health check
- `GET /api/v1/ingestion/status` — latest ingestion run per source

## Screener Example

```bash
curl -X POST http://localhost:8000/api/v1/screener \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [
      {"metric": "profitability.roe", "operator": "gt", "value": 0.15},
      {"metric": "leverage.debt_to_equity", "operator": "lt", "value": 1.0},
      {"metric": "forensic.piotroski_f_score", "operator": "gte", "value": 7}
    ],
    "sort_by": "profitability.roe",
    "sort_order": "desc",
    "limit": 20
  }'
```

**Operators:** `gt`, `gte`, `lt`, `lte`, `eq`, `between`, `not_null`

## Computed Metrics (12 categories, 142 metrics)

| Category | Metrics |
|----------|---------|
| **Profitability** | Gross/operating/net/EBITDA margins, ROA, ROE, ROCE, ROIC, R&D intensity, SGA ratio, SBC % |
| **Liquidity** | Current/quick/cash ratio, NWC, DIO, DSO, DPO, cash conversion cycle, defensive interval |
| **Leverage** | D/E, D/A, D/EBITDA, net debt, interest coverage, equity multiplier, debt-to-capital |
| **Efficiency** | Asset/inventory/receivables/payables/equity turnover, capex-to-revenue, capex-to-depreciation |
| **Cash Flow** | FCFF, FCFE, OCF margin, cash-to-net-income, cash ROIC, reinvestment rate |
| **Growth** | Revenue/profit/EPS/OCF/FCF/assets/equity YoY growth, sustainable growth rate, acquisition-adjusted |
| **DuPont** | 3-factor and 5-factor decomposition (tax burden, interest burden, margin, turnover, leverage) |
| **Valuation** | P/E, P/B, P/S, P/CF, EV/EBITDA, EV/EBIT, EV/Revenue, EV/FCF, PEG, Graham number, yields |
| **Quality** | Accruals ratio, Sloan ratio, earnings quality, revenue-vs-receivables divergence, organic flag |
| **Forensic** | Altman Z-score, Piotroski F-score (9 signals), Beneish M-score (8 indices), risk flags |
| **Shareholder** | Payout ratio, buyback ratio, shareholder yield, net debt paydown, capital allocation |
| **Per Share** | Revenue, book value, tangible BV, OCF, FCF, dividends, debt, cash per share |

## Data Sources

| Source | Data | Schedule |
|--------|------|----------|
| SEC EDGAR | XBRL company facts, filings (10-K, 10-Q, 8-K) | Daily 06:00 ET |
| FRED | 23 macro series (Treasury yields, CPI, GDP, unemployment, VIX, etc.) | Daily 07:00 ET |
| yFinance | Daily OHLCV, dividends, splits, company info | Daily 18:00 ET (after close) |

## Project Structure

```
excella/
├── docker-compose.yml          9 services
├── .env.example                Configuration template
├── scripts/
│   └── init_db.sql             TimescaleDB hypertables
├── src/                        Backend (Python/FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             FastAPI app with CORS + OpenAPI
│       ├── config.py           Pydantic settings
│       ├── worker.py           RabbitMQ consumer
│       ├── scheduler.py        CRON job publisher
│       ├── db/                 Models (Company, Filing, FinancialStatement, DerivedMetrics, User, Watchlist) + session
│       ├── ingestion/          EDGAR, FRED, yFinance workers
│       ├── pipeline/           XBRL mapper, normalizer, validator, enricher
│       ├── metrics/            12 computation modules + orchestrator
│       ├── api/                REST endpoints (screener, companies, financials, prices, macro, auth, filings, watchlists)
│       └── queue/              RabbitMQ broker
├── frontend/                   Frontend (Next.js/React)
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── app/                Pages (screener, company/[ticker], compare, macro, watchlist, auth)
│       ├── components/         UI primitives, screener, company, charts, compare, macro, layout
│       ├── hooks/              Data fetching hooks (use-screener, use-company, use-prices, etc.)
│       ├── lib/                API client, types, formatters, metric metadata, constants
│       └── providers/          React Query, Theme, Auth providers
├── product/                    Product docs
└── system-design/              Architecture docs + Mermaid diagrams
```

## Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| frontend | 3000 | Next.js screener UI |
| api | 8000 | FastAPI REST (Swagger at `/docs`) |
| worker | — | RabbitMQ consumer for ingestion + pipeline |
| scheduler | — | CRON job publisher |
| postgres | 5432 | PostgreSQL + TimescaleDB |
| redis | 6379 | Cache |
| rabbitmq | 5672 / 15672 | Task queue (management UI at 15672) |
| elasticsearch | 9200 | Full-text search |
| minio | 9000 / 9001 | S3-compatible object storage (console at 9001) |

## Seeding Data

After starting services, seed the database with MAG 7 companies and macro data:

```bash
# Full seed (EDGAR + FRED + yFinance + metrics enrichment) — inside Docker
docker compose exec api python seed_data.py

# Run individual steps
docker compose exec api python seed_data.py edgar fred enrich
docker compose exec api python seed_data.py yfinance

# If yFinance fails from Docker (Yahoo blocks container IPs),
# run the yFinance step from your host machine instead:
cd src && python seed_data.py yfinance

# Or use the standalone host-side yFinance seeder (no app dependencies):
pip install yfinance psycopg2-binary pandas
python scripts/seed_yfinance_host.py
```

**What gets seeded:**
- **EDGAR:** MAG 7 company facts + filings (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA)
- **FRED:** 23 macro series (Treasury yields, CPI, GDP, unemployment, VIX, etc.)
- **yFinance:** Daily OHLCV price history for all 7 tickers
- **Enrichment:** Computes all 142 derived metrics from the ingested financial data

## Development

```bash
# Run backend locally (without Docker)
cd src
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Run frontend locally
cd frontend
npm install
npm run dev
# Frontend at http://localhost:3000, proxies API calls to http://localhost:8000

# Run a single ingestion manually
python -c "
from app.ingestion.yfinance_ingestor import YFinanceIngestor
with YFinanceIngestor() as ing:
    ing.ingest_ticker('AAPL', period='max')
"

# Trigger pipeline enrichment
python -c "
from app.db.session import SessionLocal
from app.pipeline.enricher import enrich_all
db = SessionLocal()
enrich_all(db)
db.close()
"
```
