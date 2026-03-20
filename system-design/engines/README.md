# Analytical Engines

Two engines consume refined data and produce analytical outputs.

---

## Equity Valuation Engine

**Status: Implemented** (`src/app/valuation/`)

Consumes refined fundamental, macro, and price data to produce intrinsic value estimates.

### Inputs (from Refined Data)
- **Financial statements** — income, balance sheet, cash flow (shares outstanding, interest expense, revenue)
- **Derived metrics** — 12 categories from `DerivedMetrics` (ROE, FCFF, growth rates, leverage, per-share data)
- **Price data** — daily adj_close from `daily_prices` hypertable (stock + SPY benchmark)
- **Macro data** — 10-Year Treasury yield (DGS10) from `fred_observations` for risk-free rate

### Valuation Models

| Model | Module | What it does |
|-------|--------|-------------|
| **DCF** | `valuation/dcf.py` | Projects FCFF with linear mean-reversion growth, discounts at WACC, perpetuity or exit-multiple terminal value |
| **Comps** | `valuation/comps.py` | Finds industry/sector peers, computes median P/E, EV/EBITDA, P/S, P/B, applies to target fundamentals |
| **DDM** | `valuation/ddm.py` | Gordon Growth or two-stage model for dividend-paying companies |
| **Residual Income** | `valuation/residual_income.py` | PV of excess returns (ROE - ke) × BV, uses actual retention ratio from financials |

### Supporting Computations

| Module | Purpose |
|--------|---------|
| `valuation/beta.py` | OLS regression on log returns vs SPY (252-day), fallback beta=1.0 |
| `valuation/wacc.py` | CAPM cost of equity + blended WACC with actual cost of debt (interest_expense / total_debt) |
| `valuation/engine.py` | Orchestrator: loads data → beta → WACC → runs all 4 models → consensus summary |

### Assumption Sources

| Assumption | Source | Fallback |
|------------|--------|----------|
| Risk-free rate | FRED DGS10 (live) | 4.0% |
| Beta | OLS regression vs SPY | 1.0 (if < 60 data points) |
| Cost of debt | interest_expense / total_debt from income statement | risk_free + 2% spread |
| Tax rate | effective_tax_rate from profitability metrics | 21% (US corporate) |
| Equity risk premium | Damodaran long-term average | 5.5% (constant) |
| Terminal growth | Default | 2.5% (overridable) |
| Shares outstanding | shares_diluted from income statement | revenue / revenue_per_share |
| Retention ratio | retention_ratio from shareholder metrics | 50% |
| Capital weights | market_cap vs total_debt | 100% equity |

### Outputs
- Intrinsic value estimate per share (per model + median consensus)
- Margin of safety vs current market price
- Model-by-model breakdown with intermediate values
- WACC × terminal growth sensitivity matrix
- Peer comparison table with implied values
- Historical intrinsic value vs price time series

### Modes of Operation
- **Pre-computed**: Runs automatically in the metrics pipeline (`compute.py`), stored in `valuation_models` JSONB column on `DerivedMetrics`
- **On-demand**: POST to `/companies/{ticker}/valuation/dcf` with custom assumptions, returns real-time results without DB persistence

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/companies/{ticker}/valuation` | GET | Pre-computed valuation summary |
| `/companies/{ticker}/valuation/dcf` | POST | Custom DCF with user assumptions |
| `/companies/{ticker}/valuation/sensitivity` | GET | WACC × growth rate matrix |
| `/companies/{ticker}/valuation/comps` | GET | Peer group details + implied values |
| `/companies/{ticker}/valuation/history` | GET | Historical intrinsic value vs price |

### Frontend
- **Valuation tab** on company page (`/company/[ticker]/valuation`)
- Components: ValuationSummary (hero card), DCFPanel (editable inputs), SensitivityTable, CompsTable, ValuationHistoryChart
- Hook: `useValuation`, `useCustomDCF`, `useValuationSensitivity`, `useValuationComps`, `useValuationHistory`

### Design
- Reads refined data from PostgreSQL + TimescaleDB
- Computation is stateless — given inputs, produces deterministic output
- Each model is error-isolated (try/except); partial results still returned
- Results stored in `derived_metrics.valuation_models` JSONB column
- Exposed via FastAPI endpoints under `/companies/{ticker}/valuation/*`
- 58 unit tests in `src/tests/valuation/`

---

## Portfolio Attribution & Scenario Analysis Engine

Decomposes portfolio performance and runs scenario/stress tests.

### Inputs (from Refined Data)
- Portfolio holdings (positions, weights)
- Price returns (daily, period)
- Benchmark returns
- Sector/industry classifications
- Macro factor data

### Attribution
- **Brinson-style attribution:** Allocation effect, selection effect, interaction effect
- **Sector attribution:** Performance contribution by sector
- **Factor attribution:** Exposure to common factors (value, growth, momentum, size, quality)

### Scenario Analysis
- **Historical scenarios:** Replay portfolio through past market events (e.g., 2008, COVID)
- **Custom scenarios:** User-defined shocks to rates, prices, sectors
- **Stress testing:** Extreme moves in key risk factors
- **Macro scenario mapping:** Link macro variable changes to portfolio impact

### Outputs
- Attribution breakdown (by sector, factor, security)
- Scenario P&L impact
- Risk exposure summary

### Design
- Reads refined data from PostgreSQL + TimescaleDB
- Portfolio definitions stored in PostgreSQL
- Scenario definitions stored in PostgreSQL (JSONB for flexible parameters)
- Results cached in Redis for frequently-run scenarios
- Exposed via FastAPI endpoints
