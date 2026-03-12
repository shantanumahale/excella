# API Design — FastAPI REST

All data access and analytical outputs go through FastAPI. Base path: `/api/v1`.

## Endpoints

### Screener (core feature)
- `POST /api/v1/screener` — filter companies by any combination of 142 metrics across 12 JSONB categories. Supports operators: `gt`, `gte`, `lt`, `lte`, `eq`, `between`, `not_null`. Parameterized SQL with CTE sub-select for latest metrics per company. Sorting and pagination.
- `GET /api/v1/screener/metrics` — metric catalogue (142 metrics organized by 12 categories with display names and descriptions)

### Companies
- `GET /api/v1/companies` — list tracked companies (filter by sector, industry, exchange, search by ticker/name)
- `GET /api/v1/companies/{ticker}` — company detail with latest derived metrics (all 12 categories)

### Financial Statements & Metrics
- `GET /api/v1/companies/{ticker}/financials` — financial statements (filter by statement_type: income/balance/cashflow, period_type: annual/quarterly)
- `GET /api/v1/companies/{ticker}/metrics` — derived metrics history (paginated)
- `GET /api/v1/companies/{ticker}/metrics/latest` — most recent metrics snapshot (all 12 categories)

### Filings
- `GET /api/v1/companies/{ticker}/filings` — SEC filings list (filter by form_type: 10-K, 10-Q, 8-K). Returns EDGAR URLs, filing dates, accession numbers.

### Prices
- `GET /api/v1/prices/{ticker}` — daily OHLCV (query params: start, end, offset, limit)
- `GET /api/v1/prices/{ticker}/latest` — most recent EOD price
- `GET /api/v1/prices/{ticker}/returns` — calculated returns over 1d, 5d, 21d, 63d, 126d, 252d windows

### Macro (with Redis caching)
- `GET /api/v1/macro/series` — list all 23 tracked FRED series with metadata (cached TTL: 1h)
- `GET /api/v1/macro/series/latest` — latest value for all series (cached TTL: 5min)
- `GET /api/v1/macro/series/{series_id}` — observations with date range filtering (cached TTL: 1h)
- `GET /api/v1/macro/series/{series_id}/latest` — latest observation for specific series (cached TTL: 5min)

### Auth (JWT)
- `POST /api/v1/auth/signup` — create account (email, password, name). Password hashed with bcrypt.
- `POST /api/v1/auth/login` — get JWT bearer token (24-hour expiry, HS256)
- `GET /api/v1/auth/me` — current user profile (protected, requires Bearer token)

### Watchlists (protected, requires auth)
- `POST /api/v1/watchlists` — create watchlist (name, optional description)
- `GET /api/v1/watchlists` — list current user's watchlists
- `GET /api/v1/watchlists/{id}` — watchlist detail with companies
- `DELETE /api/v1/watchlists/{id}` — delete watchlist
- `POST /api/v1/watchlists/{id}/companies` — add ticker(s) to watchlist
- `DELETE /api/v1/watchlists/{id}/companies/{ticker}` — remove ticker from watchlist

### System
- `GET /api/v1/health` — health check
- `GET /api/v1/ingestion/status` — latest ingestion log entry per source (edgar, fred, yfinance)

## Common Patterns
- Pagination: `?offset=0&limit=50`
- Date filtering: `?start=2024-01-01&end=2024-12-31`
- JSON responses throughout
- Error format: `{"detail": "message"}`

## Future Endpoints (Not Yet Implemented)

### Valuation Engine
- `POST /api/v1/valuations` — run valuation for a company (body: ticker, method, assumptions)
- `GET /api/v1/valuations/{ticker}` — get valuation history
- `GET /api/v1/valuations/{ticker}/latest` — most recent valuation

### Portfolio Attribution & Scenario Analysis
- `POST /api/v1/portfolios` — create portfolio
- `GET /api/v1/portfolios/{id}` — get portfolio with current holdings
- `PUT /api/v1/portfolios/{id}/holdings` — update holdings
- `POST /api/v1/portfolios/{id}/attribution` — run attribution (body: period, benchmark, method)
- `GET /api/v1/portfolios/{id}/attribution` — get attribution results
- `POST /api/v1/portfolios/{id}/scenarios` — run scenario (body: scenario definition or scenario_id)
- `GET /api/v1/portfolios/{id}/scenarios` — get scenario results
