# Analytical Engines

Two engines consume refined data and produce analytical outputs.

---

## Equity Valuation Engine

Consumes refined fundamental, macro, and price data to produce equity valuations.

### Inputs (from Refined Data)
- Financial statements (income statement, balance sheet, cash flow)
- Derived ratios (P/E, P/B, EV/EBITDA, ROE, margins, growth rates)
- Price data (current, historical)
- Macro data (risk-free rate, GDP growth, inflation)

### Valuation Approaches
- **DCF (Discounted Cash Flow):** Project FCF, discount at WACC derived from macro + company risk
- **Relative Valuation (Comps):** Compare multiples (P/E, EV/EBITDA) against sector/industry peers
- **Dividend Discount Model:** For dividend-paying equities
- **Asset-based:** Net asset value from balance sheet data

### Outputs
- Intrinsic value estimate per share
- Valuation range (bear / base / bull)
- Key assumption sensitivity
- Comparison to current market price (upside/downside %)

### Design
- Reads refined data from PostgreSQL + TimescaleDB
- Computation is stateless — given inputs, produces deterministic output
- Results stored in PostgreSQL
- Exposed via FastAPI endpoints

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
