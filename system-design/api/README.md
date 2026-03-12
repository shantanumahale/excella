# API Design — FastAPI REST

All analytical outputs and data access go through FastAPI.

## Endpoints

### Data — Prices
- `GET /api/v1/prices/{ticker}` — daily prices (query params: start, end)
- `GET /api/v1/prices/{ticker}/latest` — most recent EOD price
- `GET /api/v1/prices/{ticker}/returns` — calculated returns (1d, 5d, 21d, etc.)

### Data — Fundamentals
- `GET /api/v1/companies` — list tracked companies (filter by sector, industry)
- `GET /api/v1/companies/{ticker}` — company metadata
- `GET /api/v1/companies/{ticker}/financials` — financial statements (query: period, statement_type)
- `GET /api/v1/companies/{ticker}/metrics` — derived ratios and metrics

### Data — Macro
- `GET /api/v1/macro/series` — list available FRED series
- `GET /api/v1/macro/series/{series_id}` — observations (query: start, end)

### Data — Filings
- `GET /api/v1/filings` — search filings (query: ticker, form_type, date range, keyword)
- `GET /api/v1/filings/{filing_id}` — filing metadata + S3 download link

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

### System
- `GET /api/v1/health` — health check
- `GET /api/v1/ingestion/status` — latest ingestion run status per source

## Common Patterns
- Pagination: `?offset=0&limit=50`
- Date filtering: `?start=2024-01-01&end=2024-12-31`
- JSON responses throughout
- Error format: `{"detail": "message", "code": "ERROR_CODE"}`
