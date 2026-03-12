# Excella Financial Data Platform — Architecture Documentation

This document provides a comprehensive visual guide to the Excella platform architecture using Mermaid diagrams. Excella is a screener.in-style financial data platform that ingests data from SEC EDGAR, FRED, and yFinance, processes it through a normalization and enrichment pipeline, and exposes it via a FastAPI REST API with dynamic screener capabilities and a Next.js frontend.

---

## 1. System Architecture

A high-level overview of the entire platform, showing how data flows from external sources through ingestion, storage, processing, and finally to the API layer and frontend.

```mermaid
flowchart TB
    subgraph Sources["Data Sources"]
        EDGAR["SEC EDGAR\n(Fundamentals via XBRL)"]
        FRED["FRED\n(23 Macro Series)"]
        YFIN["yFinance\n(EOD Prices)"]
    end

    subgraph Ingestion["Ingestion Layer"]
        CRON["APScheduler\n(CRON Jobs)"]
        RMQ["RabbitMQ\n(Task Queues)"]
        WORKER["Worker\n(Single Process)"]
    end

    subgraph RawStorage["Raw Data Storage"]
        PG["PostgreSQL\n(Companies, Filings,\nStatements)"]
        TS["TimescaleDB\n(Prices & Macro)"]
    end

    subgraph Pipeline["Processing Pipeline"]
        XBRL["XBRL Mapper"]
        NORM["Normalizer\n(+ Ghost Entry Filter)"]
        VAL["Validator"]
        ENR["Enricher"]
        MC["Metrics Compute\n(12 categories, 142 metrics)"]
    end

    subgraph Refined["Refined Data"]
        DM["DerivedMetrics Table\n(12 JSONB Categories\nper Company per Period)"]
    end

    subgraph API["API Layer"]
        FAPI["FastAPI REST API\n(Screener, Auth,\nWatchlists)"]
        REDIS["Redis\n(Cache)"]
    end

    subgraph Frontend["Frontend"]
        NEXT["Next.js\n(Screener UI, Company\nAnalysis, Macro Dashboard)"]
    end

    Sources --> CRON
    CRON --> RMQ
    RMQ --> WORKER
    WORKER --> PG
    WORKER --> TS
    RawStorage --> Pipeline
    XBRL --> NORM --> VAL --> ENR --> MC
    MC --> DM
    DM --> FAPI
    PG --> FAPI
    TS --> FAPI
    REDIS <--> FAPI
    FAPI --> NEXT

    style Sources fill:#e8f4f8,stroke:#2196F3
    style Ingestion fill:#fff3e0,stroke:#FF9800
    style RawStorage fill:#e8f5e9,stroke:#4CAF50
    style Pipeline fill:#fce4ec,stroke:#E91E63
    style Refined fill:#f3e5f5,stroke:#9C27B0
    style API fill:#e0f2f1,stroke:#009688
    style Frontend fill:#e8eaf6,stroke:#3F51B5
```

---

## 2. Data Flow

A detailed left-to-right flow showing how each data source is processed independently before converging in the enrichment pipeline and API.

```mermaid
flowchart LR
    subgraph EDGAR_Flow["EDGAR Flow"]
        E1["SEC EDGAR API"] -->|"XBRL company facts"| E2["Worker\n(EDGAR Handler)"]
        E2 -->|"company + filing\nmetadata"| E4["PostgreSQL\ncompanies + filings"]
        E4 --> E5["XBRL Mapper"]
        E5 --> E6["Normalizer\n(+ ghost entry filter)"]
        E6 --> E7["Validator"]
        E7 --> E8["Enricher"]
    end

    subgraph FRED_Flow["FRED Flow"]
        F1["FRED API"] -->|"23 macro series"| F2["Worker\n(FRED Handler)"]
        F2 -->|"observations"| F3["TimescaleDB\nfred_observations"]
        F2 -->|"series metadata"| F4["PostgreSQL\nfred_series"]
    end

    subgraph YFIN_Flow["yFinance Flow"]
        Y1["Yahoo Finance"] -->|"EOD prices"| Y2["Worker\n(yFinance Handler)"]
        Y2 -->|"OHLCV + returns"| Y3["TimescaleDB\ndaily_prices +\ndaily_returns"]
    end

    subgraph Enrichment["Enrichment & Output"]
        E8 --> M["Metrics Compute\n(12 categories\n142 metrics)"]
        M --> DM["DerivedMetrics\n(12 JSONB cols)"]
        DM --> API["FastAPI"]
        F3 --> API
        F4 --> API
        Y3 --> API
        E4 --> API
        API --> FE["Next.js\nFrontend"]
    end

    style EDGAR_Flow fill:#e3f2fd,stroke:#1565C0
    style FRED_Flow fill:#e8f5e9,stroke:#2E7D32
    style YFIN_Flow fill:#fff8e1,stroke:#F9A825
    style Enrichment fill:#fce4ec,stroke:#C62828
```

---

## 3. Ingestion Sequence

A sequence diagram showing the interaction pattern when the CRON scheduler triggers an ingestion job. The single worker process routes messages to the appropriate handler based on queue name.

```mermaid
sequenceDiagram
    participant CRON as APScheduler
    participant RMQ as RabbitMQ
    participant W as Worker
    participant EXT as External API
    participant PG as PostgreSQL
    participant TSDB as TimescaleDB
    participant LOG as IngestionLog

    CRON->>RMQ: Publish task message<br/>(action, payload, timestamp)
    RMQ->>W: Deliver task from queue

    W->>LOG: Create log entry (status: running)

    loop For each item in batch
        W->>EXT: Request data (API call)
        EXT-->>W: Return raw data

        alt EDGAR Filing
            W->>PG: Upsert company record
            W->>PG: Upsert filing metadata (status: raw)
        else FRED Series
            W->>PG: Upsert fred_series metadata
            W->>TSDB: Bulk insert macro observations
        else yFinance Prices
            W->>TSDB: Upsert daily_prices + daily_returns
        end
    end

    W->>LOG: Update log entry (status: success,<br/>records_processed, duration)
    W->>RMQ: Acknowledge message

    Note over CRON,LOG: On failure, the worker sets<br/>status: error with error_message<br/>and the message is requeued
```

---

## 4. Pipeline Processing

The data enrichment pipeline that transforms raw EDGAR XBRL data into normalized, validated, and enriched financial metrics stored as JSONB in the DerivedMetrics table.

```mermaid
flowchart TB
    RAW["Raw XBRL Facts\n(from PostgreSQL JSONB)"]

    subgraph Stage1["Stage 1: XBRL Mapping"]
        XM["XBRL Mapper"]
        XM1["Parse 100+ US-GAAP tags"]
        XM2["Map to canonical field names"]
        XM3["Filter by unit (USD only)"]
        XM --> XM1 --> XM2 --> XM3
    end

    subgraph Stage2["Stage 2: Normalization"]
        NM["Normalizer"]
        NM1["Group facts by period\n(end_date, fiscal_year, fiscal_period)"]
        NM2["Resolve duplicates\n(10-K preferred over 10-Q)"]
        NM3["Fill derived fields\n(gross profit, EBITDA)"]
        NM4["Filter ghost entries\n(core field validation)"]
        NM --> NM1 --> NM2 --> NM3 --> NM4
    end

    subgraph Stage3["Stage 3: Validation"]
        VL["Validator"]
        VL1["Required fields check\n(revenue, total_assets, OCF)"]
        VL2["Balance sheet identity\nA ≈ L + E (1% tolerance)"]
        VL3["Outlier detection\n(> 1e15 flagged)"]
        VL4["Sign validation +\ntime-series anomaly (500%+ swing)"]
        VL --> VL1 --> VL2 --> VL3 --> VL4
    end

    subgraph Stage4["Stage 4: Enrichment"]
        EN["Enricher"]
        EN1["Fill missing derived line items\n(EBITDA, working capital, D&A)"]
        EN2["Persist FinancialStatement\nrecords with validation results"]
        EN --> EN1 --> EN2
    end

    subgraph Stage5["Stage 5: Metrics Compute"]
        MC["Metrics Compute Engine\n(12 modules, 142 metrics)"]
        MC1["Profitability (16)"]
        MC2["Liquidity (11)"]
        MC3["Leverage (10)"]
        MC4["Efficiency (10)"]
        MC5["Cash Flow (11)"]
        MC6["Growth (15)"]
        MC7["DuPont (10)"]
        MC8["Valuation (17)"]
        MC9["Quality (10)"]
        MC10["Forensic (14)\nAltman Z / Piotroski F / Beneish M"]
        MC11["Shareholder (9)"]
        MC12["Per Share (13)"]
        MC --> MC1 & MC2 & MC3 & MC4 & MC5 & MC6
        MC --> MC7 & MC8 & MC9 & MC10 & MC11 & MC12
    end

    OUTPUT["DerivedMetrics Table\n12 JSONB category columns\nper company per period"]

    RAW --> Stage1 --> Stage2 --> Stage3 --> Stage4 --> Stage5 --> OUTPUT

    style Stage1 fill:#e3f2fd,stroke:#1565C0
    style Stage2 fill:#e8f5e9,stroke:#2E7D32
    style Stage3 fill:#fff8e1,stroke:#F9A825
    style Stage4 fill:#fce4ec,stroke:#C62828
    style Stage5 fill:#f3e5f5,stroke:#6A1B9A
    style OUTPUT fill:#e0f7fa,stroke:#00838F
```

---

## 5. Database Schema

An entity-relationship diagram showing the core tables, their columns, and how they relate. Hypertables (TimescaleDB) are noted for time-series data.

```mermaid
erDiagram
    Company {
        int id PK
        varchar cik UK
        varchar ticker UK
        varchar name
        varchar sic_code
        varchar sector
        varchar industry
        varchar exchange
        varchar currency
        float market_cap
        int employees
        timestamp created_at
        timestamp updated_at
    }

    Filing {
        int id PK
        int company_id FK
        varchar accession_number UK
        varchar form_type
        date filing_date
        date period_of_report
        varchar s3_key
        varchar status
        timestamp created_at
    }

    FinancialStatement {
        int id PK
        int filing_id FK
        int company_id FK
        date period_start
        date period_end
        int fiscal_year
        varchar fiscal_period
        varchar statement_type
        jsonb data
        varchar source
        varchar period_type
        boolean is_valid
        jsonb validation_warnings
        jsonb validation_errors
        timestamp created_at
    }

    DerivedMetrics {
        int id PK
        int company_id FK
        date period_end
        varchar fiscal_period
        jsonb profitability
        jsonb liquidity
        jsonb leverage
        jsonb efficiency
        jsonb cashflow
        jsonb growth
        jsonb dupont
        jsonb valuation
        jsonb quality
        jsonb forensic
        jsonb shareholder
        jsonb per_share
        timestamp created_at
    }

    User {
        int id PK
        varchar email UK
        varchar hashed_password
        varchar name
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    Watchlist {
        int id PK
        int user_id FK
        varchar name
        text description
        timestamp created_at
    }

    WatchlistCompany {
        int id PK
        int watchlist_id FK
        int company_id FK
        timestamp added_at
    }

    ScreenerPreset {
        int id PK
        int user_id FK
        varchar name
        json filters
        timestamp created_at
    }

    FredSeries {
        int id PK
        varchar series_id UK
        varchar title
        varchar frequency
        varchar units
        varchar seasonal_adjustment
        timestamp last_updated
    }

    FredObservation {
        varchar series_id FK
        timestamptz time PK
        double value
    }

    DailyPrice {
        varchar ticker
        timestamptz time PK
        double open
        double high
        double low
        double close
        double adj_close
        bigint volume
    }

    DailyReturn {
        varchar ticker
        timestamptz time PK
        double return_1d
    }

    IngestionLog {
        int id PK
        varchar source
        varchar job_type
        varchar status
        integer records_processed
        text error_message
        timestamp started_at
        timestamp completed_at
    }

    Company ||--o{ Filing : "has many"
    Company ||--o{ FinancialStatement : "has many"
    Company ||--o{ DerivedMetrics : "has many"
    Company ||--o{ DailyPrice : "has prices"
    Company ||--o{ WatchlistCompany : "tracked in"
    Filing ||--o{ FinancialStatement : "contains"
    FredSeries ||--o{ FredObservation : "has observations"
    User ||--o{ Watchlist : "owns"
    User ||--o{ ScreenerPreset : "owns"
    Watchlist ||--o{ WatchlistCompany : "contains"
```

> **Note:** `DailyPrice`, `DailyReturn`, and `FredObservation` are TimescaleDB hypertables partitioned by time for efficient time-range queries. All other tables reside in standard PostgreSQL.

---

## 6. Metrics Taxonomy

A mind map showing all 12 metric categories and the individual metrics computed within each.

```mermaid
mindmap
  root((DerivedMetrics\n12 Categories\n142 Metrics))
    Profitability 16
      Gross Margin
      Operating Margin
      Net Margin
      EBITDA Margin
      EBIT Margin
      ROA
      ROE
      ROCE
      ROIC
      NOPAT
      Tax Efficiency
      R&D Intensity
      SGA Ratio
      SBC Pct of Revenue
    Liquidity 11
      Current Ratio
      Quick Ratio
      Cash Ratio
      Defensive Interval
      NWC
      NWC Pct Revenue
      DIO
      DSO
      DPO
      Cash Conversion Cycle
    Leverage 10
      Total Debt
      Net Debt
      Debt to Equity
      Debt to Assets
      Debt to EBITDA
      Debt to Capital
      Long-term D/E
      Interest Coverage
      Equity Multiplier
      Financial Leverage
    Efficiency 10
      Asset Turnover
      Fixed Asset Turnover
      Inventory Turnover
      Receivables Turnover
      Payables Turnover
      Equity Turnover
      Capital Turnover
      Operating Cycle
      Cash Cycle
      CapEx Ratios
    Cash Flow 11
      FCFF
      FCFE
      Simplified FCFE
      OCF Margin
      OCF to Net Income
      CapEx to OCF
      CapEx to Depreciation
      Cash ROIC
      Reinvestment Rate
      Net Borrowing
    Growth 15
      Revenue Growth
      Gross Profit Growth
      Operating Income Growth
      EBITDA Growth
      Net Income Growth
      EPS Growth
      OCF Growth
      FCF Growth
      Asset Growth
      Equity Growth
      Dividend Growth
      Sustainable Growth Rate
      Acquisition Ratio
      Reinvestment Rate Growth
    DuPont Analysis 10
      3-Factor ROE
      Net Profit Margin
      Asset Turnover
      Equity Multiplier
      5-Factor ROE
      Tax Burden
      Interest Burden
      Operating Margin
      Tax Efficiency
      Interest Efficiency
    Valuation 17
      P/E Ratio
      P/B Ratio
      P/S Ratio
      P/CF Ratio
      EV/EBITDA
      EV/EBIT
      EV/Revenue
      EV/FCF
      Earnings Yield
      FCF Yield
      Dividend Yield
      PEG Ratio
      Graham Number
      Book Value per Share
      Tangible BV per Share
      Revenue per Share
    Quality 10
      Accruals Ratio
      Sloan Ratio
      Cash Flow to Earnings
      Earnings Quality Score
      Revenue vs Receivables
      Net Income vs OCF
      CapEx Consistency
      Organic Revenue Flag
      SGA Efficiency
      Depreciation to CapEx
    Forensic 14
      Altman Z-Score
      Z-Score Components
      Distress Classification
      Piotroski F-Score
      F-Score 9 Signals
      F-Score Strength
      Beneish M-Score
      M-Score 8 Indices
      Manipulation Risk
      Risk Flags
    Shareholder 9
      Payout Ratio
      Dividend Payout
      Retention Ratio
      Buyback Ratio
      Shareholder Yield
      Total Capital Returned
      Net Debt Paydown
      Dividends per Share
      Buyback per Share
    Per Share 13
      Revenue per Share
      Gross Profit per Share
      Operating Income per Share
      EBITDA per Share
      Net Income per Share
      Book Value per Share
      Tangible BV per Share
      OCF per Share
      FCF per Share
      Debt per Share
      Net Debt per Share
      Cash per Share
```

---

## 7. Docker Services

All containers in the Docker Compose stack and how they connect. The single worker process consumes from all RabbitMQ queues and routes to appropriate handlers.

```mermaid
flowchart TB
    subgraph Infrastructure["Infrastructure Services"]
        PG["PostgreSQL + TimescaleDB\n:5432"]
        REDIS["Redis\n:6379"]
        RMQ["RabbitMQ\n:5672 / :15672 (mgmt)"]
        ES["Elasticsearch\n:9200\n(configured, not active)"]
        MINIO["MinIO (S3)\n:9000 / :9001 (console)\n(configured, not active)"]
    end

    subgraph Application["Application Services"]
        API["FastAPI\n:8000"]
        SCHED["APScheduler\n(CRON Jobs)"]
        WORKER["Worker\n(EDGAR + FRED +\nyFinance + Pipeline)"]
        FE["Next.js Frontend\n:3000"]
    end

    FE -->|"API calls"| API
    API -->|"queries"| PG
    API -->|"caching"| REDIS

    SCHED -->|"publishes tasks"| RMQ

    RMQ -->|"ingest.edgar\ningest.fred\ningest.yfinance\npipeline.enrich"| WORKER

    WORKER -->|"write data"| PG

    style Infrastructure fill:#e0f2f1,stroke:#00796B
    style Application fill:#fff3e0,stroke:#E65100
```

---

## 8. API Routes

All FastAPI endpoint groups and their key routes. The screener endpoint supports dynamic JSONB filtering across all 12 metric categories.

```mermaid
flowchart LR
    FAPI["FastAPI\n/api/v1"]

    subgraph Screener["/screener"]
        S1["POST /screener\nDynamic JSONB filter query\n142 metrics, 12 categories\nOperators: gt/gte/lt/lte/eq/between/not_null"]
        S2["GET /screener/metrics\nMetric catalogue by category"]
    end

    subgraph Companies["/companies"]
        C1["GET /\nList with sector/industry/exchange\nfilter + search"]
        C2["GET /{ticker}\nCompany detail with\nlatest metrics (all 12 categories)"]
    end

    subgraph Financials["/companies/{ticker}"]
        F1["GET /financials\nIncome, Balance, CashFlow\n(annual & quarterly)"]
        F2["GET /metrics\nDerivedMetrics history (paginated)"]
        F3["GET /metrics/latest\nMost recent metrics snapshot"]
        F4["GET /filings\nSEC filings with EDGAR links"]
    end

    subgraph Prices["/prices/{ticker}"]
        P1["GET /\nDaily OHLCV with date range"]
        P2["GET /latest\nMost recent price"]
        P3["GET /returns\n1d/5d/21d/63d/126d/252d"]
    end

    subgraph Macro["/macro"]
        M1["GET /series\nList 23 FRED series"]
        M2["GET /series/latest\nLatest value for all series"]
        M3["GET /series/{id}\nObservations with date filter"]
        M4["GET /series/{id}/latest\nLatest observation"]
    end

    subgraph Auth["/auth"]
        A1["POST /signup\nCreate account (bcrypt)"]
        A2["POST /login\nGet JWT token (24h)"]
        A3["GET /me\nCurrent user profile"]
    end

    subgraph Watchlists["/watchlists"]
        W1["POST /\nCreate watchlist"]
        W2["GET /\nList user's watchlists"]
        W3["GET /{id}\nWatchlist detail"]
        W4["DELETE /{id}\nDelete watchlist"]
        W5["POST /{id}/companies\nAdd tickers"]
        W6["DELETE /{id}/companies/{ticker}\nRemove ticker"]
    end

    subgraph System["/system"]
        SY1["GET /health\nHealth check"]
        SY2["GET /ingestion/status\nLatest ingestion per source"]
    end

    FAPI --> Screener
    FAPI --> Companies
    FAPI --> Financials
    FAPI --> Prices
    FAPI --> Macro
    FAPI --> Auth
    FAPI --> Watchlists
    FAPI --> System

    style Screener fill:#e8eaf6,stroke:#283593
    style Companies fill:#e3f2fd,stroke:#1565C0
    style Financials fill:#e8f5e9,stroke:#2E7D32
    style Prices fill:#fff8e1,stroke:#F9A825
    style Macro fill:#fce4ec,stroke:#C62828
    style Auth fill:#f3e5f5,stroke:#6A1B9A
    style Watchlists fill:#e0f7fa,stroke:#00838F
    style System fill:#f5f5f5,stroke:#616161
```

---

## 9. Scheduler Timeline

The daily CRON schedule for all automated tasks. Times are in US/Eastern. Each job publishes messages to RabbitMQ which are then consumed by the worker.

```mermaid
gantt
    title Daily Ingestion & Processing Schedule (US/Eastern)
    dateFormat HH:mm
    axisFormat %H:%M

    section EDGAR
    SEC EDGAR Filing Sync           :edgar, 06:00, 60min

    section FRED
    FRED Macro Series Sync          :fred, 07:00, 30min

    section yFinance
    EOD Price Ingestion             :yfin, 18:00, 45min

    section Pipeline
    Enrichment & Metrics Compute    :pipe, 20:00, 90min
```

**Schedule details:**

| Time (ET) | Job | Queue | Description |
|---|---|---|---|
| 06:00 | EDGAR Sync | `ingest.edgar` | Fetch recent SEC filings via EDGAR XBRL companyfacts API. Stores company + filing metadata in PostgreSQL. |
| 07:00 | FRED Sync | `ingest.fred` | Update all 23 macro series with latest observations. Writes to TimescaleDB hypertable. |
| 18:00 | yFinance Sync | `ingest.yfinance` | Pull end-of-day OHLCV prices after US market close. Writes to TimescaleDB hypertable. |
| 20:00 | Pipeline Run | `pipeline.enrich` | Process filings through normalize → validate → enrich → compute metrics. Updates DerivedMetrics JSONB. |

---

## 10. Auth & User Flow

Sequence diagram showing the JWT authentication flow and how protected resources (watchlists) are accessed.

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Next.js Frontend
    participant API as FastAPI
    participant DB as PostgreSQL

    U->>FE: Sign up (email, password, name)
    FE->>API: POST /auth/signup
    API->>DB: Insert User (bcrypt hashed password)
    DB-->>API: User created
    API-->>FE: 201 Created

    U->>FE: Log in (email, password)
    FE->>API: POST /auth/login
    API->>DB: Verify credentials
    DB-->>API: User found
    API-->>FE: JWT token (24h expiry, HS256)

    U->>FE: Create watchlist
    FE->>API: POST /watchlists<br/>Authorization: Bearer {token}
    API->>API: Verify JWT
    API->>DB: Insert Watchlist
    DB-->>API: Watchlist created
    API-->>FE: 201 Created

    U->>FE: Add ticker to watchlist
    FE->>API: POST /watchlists/{id}/companies<br/>Authorization: Bearer {token}
    API->>DB: Insert WatchlistCompany
    DB-->>API: Added
    API-->>FE: 200 OK
```

---

## Summary

The Excella platform follows a classic ETL architecture adapted for financial data:

1. **Extract** — A single worker process consumes from four RabbitMQ queues to pull data from SEC EDGAR, FRED, and Yahoo Finance on a daily US/Eastern schedule.
2. **Transform** — A five-stage pipeline (Map, Normalize, Validate, Enrich, Compute) converts raw XBRL filings into standardized financial data, filters ghost entries, validates quality, and computes 142 metrics across 12 categories.
3. **Load** — Results are stored in PostgreSQL (relational + JSONB), TimescaleDB (time-series), with Redis for API caching.
4. **Serve** — A FastAPI REST API exposes all data with a dynamic screener, JWT auth, watchlists, and comprehensive financial data endpoints. A Next.js frontend provides interactive screener UI, company analysis, peer comparison, macro dashboards, and user watchlists.
