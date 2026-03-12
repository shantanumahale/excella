# Excella Financial Data Platform — Architecture Documentation

This document provides a comprehensive visual guide to the Excella platform architecture using Mermaid diagrams. Excella is a screener.in-style financial data platform that ingests data from SEC EDGAR, FRED, and yFinance, processes it through a normalization and enrichment pipeline, and exposes it via a FastAPI REST API with dynamic screener capabilities.

---

## 1. System Architecture

A high-level overview of the entire platform, showing how data flows from external sources through ingestion, storage, processing, and finally to the API layer.

```mermaid
flowchart TB
    subgraph Sources["Data Sources"]
        EDGAR["SEC EDGAR\n(Fundamentals via XBRL)"]
        FRED["FRED\n(23 Macro Series)"]
        YFIN["yFinance\n(EOD Prices)"]
    end

    subgraph Ingestion["Ingestion Layer"]
        CRON["CRON Scheduler"]
        RMQ["RabbitMQ\n(Task Queues)"]
        W1["Worker 1\n(EDGAR)"]
        W2["Worker 2\n(FRED)"]
        W3["Worker 3\n(yFinance)"]
    end

    subgraph RawStorage["Raw Data Storage"]
        S3["MinIO / S3\n(Raw Files)"]
        PG["PostgreSQL\n(Metadata & Filings)"]
        TS["TimescaleDB\n(Prices & Macro)"]
    end

    subgraph Pipeline["Processing Pipeline"]
        XBRL["XBRL Mapper"]
        NORM["Normalizer"]
        VAL["Validator"]
        ENR["Enricher"]
        MC["Metrics Compute"]
    end

    subgraph Refined["Refined Data"]
        DM["DerivedMetrics Table\n(12 JSONB Categories\nper Company per Period)"]
    end

    subgraph API["API Layer"]
        FAPI["FastAPI REST API"]
        REDIS["Redis\n(Cache)"]
        ES["Elasticsearch\n(Search)"]
    end

    Sources --> CRON
    CRON --> RMQ
    RMQ --> W1 & W2 & W3
    W1 --> S3 & PG
    W2 --> TS
    W3 --> TS
    RawStorage --> Pipeline
    XBRL --> NORM --> VAL --> ENR --> MC
    MC --> DM
    DM --> FAPI
    PG --> FAPI
    TS --> FAPI
    REDIS <--> FAPI
    ES <--> FAPI

    style Sources fill:#e8f4f8,stroke:#2196F3
    style Ingestion fill:#fff3e0,stroke:#FF9800
    style RawStorage fill:#e8f5e9,stroke:#4CAF50
    style Pipeline fill:#fce4ec,stroke:#E91E63
    style Refined fill:#f3e5f5,stroke:#9C27B0
    style API fill:#e0f2f1,stroke:#009688
```

---

## 2. Data Flow

A detailed left-to-right flow showing how each data source is processed independently before converging in the enrichment pipeline and API.

```mermaid
flowchart LR
    subgraph EDGAR_Flow["EDGAR Flow"]
        E1["SEC EDGAR API"] -->|"XBRL filings"| E2["EDGAR Worker"]
        E2 -->|"raw XML/JSON"| E3["MinIO S3 Bucket"]
        E2 -->|"filing metadata"| E4["PostgreSQL\ncompanies + filings"]
        E3 --> E5["XBRL Mapper"]
        E5 --> E6["Normalizer"]
        E6 --> E7["Validator"]
        E7 --> E8["Enricher"]
    end

    subgraph FRED_Flow["FRED Flow"]
        F1["FRED API"] -->|"23 macro series"| F2["FRED Worker"]
        F2 -->|"observations"| F3["TimescaleDB\nmacro_observations"]
        F2 -->|"series metadata"| F4["PostgreSQL\nfred_series"]
    end

    subgraph YFIN_Flow["yFinance Flow"]
        Y1["Yahoo Finance"] -->|"EOD prices"| Y2["yFinance Worker"]
        Y2 -->|"OHLCV data"| Y3["TimescaleDB\nstock_prices"]
    end

    subgraph Enrichment["Enrichment & Output"]
        E8 --> M["Metrics Compute\n(12 categories)"]
        M --> DM["DerivedMetrics\n(JSONB)"]
        DM --> API["FastAPI"]
        F3 --> API
        F4 --> API
        Y3 --> API
        E4 --> API
    end

    style EDGAR_Flow fill:#e3f2fd,stroke:#1565C0
    style FRED_Flow fill:#e8f5e9,stroke:#2E7D32
    style YFIN_Flow fill:#fff8e1,stroke:#F9A825
    style Enrichment fill:#fce4ec,stroke:#C62828
```

---

## 3. Ingestion Sequence

A sequence diagram showing the interaction pattern when the CRON scheduler triggers an ingestion job. This pattern is the same for all three workers, though the external API and storage targets differ.

```mermaid
sequenceDiagram
    participant CRON as CRON Scheduler
    participant RMQ as RabbitMQ
    participant W as Worker
    participant EXT as External API
    participant S3 as MinIO S3
    participant PG as PostgreSQL
    participant TSDB as TimescaleDB
    participant LOG as IngestionLog

    CRON->>RMQ: Publish task message<br/>(source, params, timestamp)
    RMQ->>W: Deliver task from queue

    W->>LOG: Create log entry (status: STARTED)

    loop For each item in batch
        W->>EXT: Request data (API call)
        EXT-->>W: Return raw data

        alt EDGAR Filing
            W->>S3: Store raw XBRL file
            W->>PG: Upsert company record
            W->>PG: Insert filing metadata
        else FRED Series
            W->>PG: Upsert fred_series metadata
            W->>TSDB: Bulk insert macro observations
        else yFinance Prices
            W->>TSDB: Bulk insert EOD price records
        end
    end

    W->>LOG: Update log entry (status: COMPLETED,<br/>records_processed, duration)
    W->>RMQ: Acknowledge message

    Note over CRON,LOG: On failure, the worker sets<br/>status: FAILED with error details<br/>and the message is requeued
```

---

## 4. Pipeline Processing

The data enrichment pipeline that transforms raw EDGAR filings into normalized, validated, and enriched financial metrics stored as JSONB in the DerivedMetrics table.

```mermaid
flowchart TB
    RAW["Raw XBRL Filing\n(from MinIO S3)"]

    subgraph Stage1["Stage 1: XBRL Mapping"]
        XM["XBRL Mapper"]
        XM1["Parse XBRL taxonomy tags"]
        XM2["Map to standardized field names"]
        XM3["Extract values + units + periods"]
        XM --> XM1 --> XM2 --> XM3
    end

    subgraph Stage2["Stage 2: Normalization"]
        NM["Normalizer"]
        NM1["Unify fiscal periods\n(Q1-Q4, FY)"]
        NM2["Currency conversion\nto USD"]
        NM3["Scale normalization\n(thousands → units)"]
        NM --> NM1 --> NM2 --> NM3
    end

    subgraph Stage3["Stage 3: Validation"]
        VL["Validator"]
        VL1["Balance sheet equation check\nA = L + E"]
        VL2["Cross-statement consistency"]
        VL3["Outlier detection\n& range checks"]
        VL4["Flag warnings / reject invalid"]
        VL --> VL1 --> VL2 --> VL3 --> VL4
    end

    subgraph Stage4["Stage 4: Enrichment"]
        EN["Enricher"]
        EN1["Compute derived line items\n(e.g., EBITDA, FCF, working capital)"]
        EN2["Calculate period-over-period\ngrowth rates"]
        EN3["Generate trailing twelve\nmonths (TTM)"]
        EN --> EN1 --> EN2 --> EN3
    end

    subgraph Stage5["Stage 5: Metrics Compute"]
        MC["Metrics Compute Engine"]
        MC1["Profitability ratios"]
        MC2["Liquidity ratios"]
        MC3["Leverage ratios"]
        MC4["+ 9 more categories"]
        MC --> MC1 & MC2 & MC3 & MC4
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
        uuid id PK
        varchar cik UK
        varchar ticker UK
        varchar name
        varchar sic_code
        varchar sector
        varchar industry
        varchar exchange
        timestamp created_at
        timestamp updated_at
    }

    Filing {
        uuid id PK
        uuid company_id FK
        varchar accession_number UK
        varchar form_type
        date period_end
        date filed_date
        varchar fiscal_year
        varchar fiscal_period
        varchar s3_key
        varchar status
        timestamp created_at
    }

    FinancialStatement {
        uuid id PK
        uuid filing_id FK
        varchar statement_type
        jsonb line_items
        varchar currency
        bigint scale
        boolean is_restated
        timestamp created_at
    }

    DerivedMetrics {
        uuid id PK
        uuid company_id FK
        varchar fiscal_year
        varchar fiscal_period
        date period_end
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
        jsonb shareholder_returns
        jsonb per_share
        timestamp computed_at
    }

    FredSeries {
        uuid id PK
        varchar series_id UK
        varchar title
        varchar frequency
        varchar units
        varchar seasonal_adjustment
        date observation_start
        date observation_end
        timestamp last_synced
    }

    MacroObservation {
        uuid series_id FK
        timestamptz date PK
        double value
        varchar status
    }

    StockPrice {
        uuid company_id FK
        timestamptz date PK
        double open
        double high
        double low
        double close
        double adj_close
        bigint volume
    }

    IngestionLog {
        uuid id PK
        varchar source
        varchar task_type
        varchar status
        integer records_processed
        integer records_failed
        jsonb error_details
        timestamp started_at
        timestamp completed_at
    }

    Company ||--o{ Filing : "has many"
    Company ||--o{ DerivedMetrics : "has many"
    Company ||--o{ StockPrice : "has prices"
    Filing ||--o{ FinancialStatement : "contains"
    FredSeries ||--o{ MacroObservation : "has observations"
```

> **Note:** `StockPrice` and `MacroObservation` are TimescaleDB hypertables partitioned by date for efficient time-range queries. All other tables reside in standard PostgreSQL.

---

## 6. Metrics Taxonomy

A mind map showing all 12 metric categories and the individual metrics computed within each.

```mermaid
mindmap
  root((DerivedMetrics\n12 Categories))
    Profitability
      Gross Margin
      Operating Margin
      Net Margin
      EBITDA Margin
      ROA
      ROE
      ROIC
    Liquidity
      Current Ratio
      Quick Ratio
      Cash Ratio
      Working Capital Ratio
    Leverage
      Debt to Equity
      Debt to Assets
      Interest Coverage
      Equity Multiplier
      Debt to EBITDA
    Efficiency
      Asset Turnover
      Inventory Turnover
      Receivables Turnover
      Payables Turnover
      Cash Conversion Cycle
    Cash Flow
      Operating CF Ratio
      FCF Yield
      FCF to Net Income
      CapEx to Revenue
      Cash Flow Coverage
    Growth
      Revenue Growth
      Earnings Growth
      EBITDA Growth
      FCF Growth
      Book Value Growth
    DuPont Analysis
      Net Profit Margin
      Asset Turnover
      Equity Multiplier
      3-Factor ROE
      5-Factor Decomposition
    Valuation
      P/E Ratio
      P/B Ratio
      P/S Ratio
      EV/EBITDA
      EV/Revenue
      PEG Ratio
    Quality
      Accruals Ratio
      Earnings Persistence
      Cash Earnings Quality
      Revenue Quality
    Forensic
      Altman Z-Score
      Piotroski F-Score
      Beneish M-Score
    Shareholder Returns
      Dividend Yield
      Dividend Payout Ratio
      Buyback Yield
      Total Shareholder Return
    Per Share
      EPS
      Book Value per Share
      Revenue per Share
      FCF per Share
      Dividends per Share
```

---

## 7. Docker Services

All containers in the Docker Compose stack and how they connect. Arrows indicate dependency or communication direction.

```mermaid
flowchart TB
    subgraph Infrastructure["Infrastructure Services"]
        PG["PostgreSQL + TimescaleDB\n:5432"]
        REDIS["Redis\n:6379"]
        RMQ["RabbitMQ\n:5672 / :15672 (mgmt)"]
        ES["Elasticsearch\n:9200"]
        MINIO["MinIO (S3)\n:9000 / :9001 (console)"]
    end

    subgraph Application["Application Services"]
        API["FastAPI\n:8000"]
        SCHED["CRON Scheduler"]
        W_EDGAR["Worker: EDGAR"]
        W_FRED["Worker: FRED"]
        W_YFIN["Worker: yFinance"]
    end

    API -->|"queries"| PG
    API -->|"caching"| REDIS
    API -->|"full-text search"| ES

    SCHED -->|"publishes tasks"| RMQ

    RMQ -->|"edgar queue"| W_EDGAR
    RMQ -->|"fred queue"| W_FRED
    RMQ -->|"yfin queue"| W_YFIN

    W_EDGAR -->|"store files"| MINIO
    W_EDGAR -->|"write metadata"| PG
    W_FRED -->|"write series"| PG
    W_FRED -->|"write observations"| PG
    W_YFIN -->|"write prices"| PG

    API -.->|"health checks"| RMQ
    API -.->|"health checks"| MINIO

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
        S1["POST /screen\nDynamic JSONB filter query\nacross all 12 metric categories"]
        S2["GET /filters\nAvailable filter fields & ranges"]
        S3["GET /presets\nPre-built screening strategies"]
    end

    subgraph Companies["/companies"]
        C1["GET /\nList with pagination + search"]
        C2["GET /{id}\nCompany detail"]
        C3["GET /{id}/overview\nSummary with latest metrics"]
    end

    subgraph Financials["/financials"]
        F1["GET /{company_id}/statements\nIncome, Balance, CashFlow"]
        F2["GET /{company_id}/metrics\nDerivedMetrics (all 12 JSONB)"]
        F3["GET /{company_id}/metrics/{category}\nSingle category time series"]
    end

    subgraph Prices["/prices"]
        P1["GET /{company_id}/daily\nEOD prices with date range"]
        P2["GET /{company_id}/returns\nCalculated returns"]
    end

    subgraph Macro["/macro"]
        M1["GET /series\nList all 23 FRED series"]
        M2["GET /series/{id}/observations\nTime series data"]
        M3["GET /dashboard\nKey macro indicators summary"]
    end

    subgraph System["/system"]
        SY1["GET /health\nService health checks"]
        SY2["GET /ingestion/status\nLatest ingestion log entries"]
    end

    FAPI --> Screener
    FAPI --> Companies
    FAPI --> Financials
    FAPI --> Prices
    FAPI --> Macro
    FAPI --> System

    style Screener fill:#e8eaf6,stroke:#283593
    style Companies fill:#e3f2fd,stroke:#1565C0
    style Financials fill:#e8f5e9,stroke:#2E7D32
    style Prices fill:#fff8e1,stroke:#F9A825
    style Macro fill:#fce4ec,stroke:#C62828
    style System fill:#f5f5f5,stroke:#616161
```

---

## 9. Scheduler Timeline

The daily CRON schedule for all automated tasks. Times are in UTC. Each job publishes messages to RabbitMQ which are then consumed by the appropriate worker.

```mermaid
gantt
    title Daily Ingestion & Processing Schedule (UTC)
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

| Time (UTC) | Job | Description |
|---|---|---|
| 06:00 | EDGAR Sync | Fetch new/amended SEC filings via EDGAR XBRL API. Stores raw files in S3, metadata in PostgreSQL. |
| 07:00 | FRED Sync | Update all 23 macro series with latest observations. Writes to TimescaleDB hypertable. |
| 18:00 | yFinance Sync | Pull end-of-day OHLCV prices after US market close. Writes to TimescaleDB hypertable. |
| 20:00 | Pipeline Run | Process any new/updated filings through the full pipeline (XBRL Mapper, Normalizer, Validator, Enricher, Metrics Compute). Updates DerivedMetrics JSONB. |

---

## Summary

The Excella platform follows a classic ETL architecture adapted for financial data:

1. **Extract** — Three specialized workers pull data from SEC EDGAR, FRED, and Yahoo Finance on a daily schedule via RabbitMQ task queues.
2. **Transform** — A four-stage pipeline (Map, Normalize, Validate, Enrich) converts raw XBRL filings into standardized financial data, then computes 12 categories of derived metrics.
3. **Load** — Results are stored in PostgreSQL (relational data), TimescaleDB (time-series), and MinIO/S3 (raw files), with Redis for caching and Elasticsearch for search.
4. **Serve** — A FastAPI REST API exposes all data with a dynamic screener that filters across JSONB metric columns, enabling screener.in-style financial analysis.
