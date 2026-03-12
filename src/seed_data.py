#!/usr/bin/env python3
"""Seed script — pre-pull MAG 7 companies + FRED macro data.

Run inside the API container:
    docker compose exec api python seed_data.py

Run individual steps:
    docker compose exec api python seed_data.py edgar fred enrich
    docker compose exec api python seed_data.py yfinance

If yFinance fails from Docker (common — Yahoo blocks container IPs),
run just the yFinance step from your host machine:
    cd src && python seed_data.py yfinance
"""

from __future__ import annotations

import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("seed")

# ── MAG 7 companies ──────────────────────────────────────────────────────────
MAG7_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

# CIKs for EDGAR (10-digit zero-padded)
MAG7_CIKS = {
    "AAPL":  "0000320193",
    "MSFT":  "0000789019",
    "GOOGL": "0001652044",
    "AMZN":  "0001018724",
    "NVDA":  "0001045810",
    "META":  "0001326801",
    "TSLA":  "0001318605",
}

# ── Key FRED series to seed ──────────────────────────────────────────────────
FRED_SERIES = [
    # Interest Rates
    "DGS1",       # 1-Year Treasury
    "DGS2",       # 2-Year Treasury
    "DGS5",       # 5-Year Treasury
    "DGS10",      # 10-Year Treasury
    "DGS20",      # 20-Year Treasury
    "DGS30",      # 30-Year Treasury
    "T10Y2Y",     # 10Y-2Y Spread
    "T10YIE",     # 10Y Breakeven Inflation
    "FEDFUNDS",   # Fed Funds Rate
    "DFF",        # Daily Federal Funds Rate
    # Inflation
    "CPIAUCSL",   # CPI All Urban Consumers
    "CPILFESL",   # CPI Less Food and Energy
    "PCEPI",      # PCE Price Index
    # Economic Activity
    "GDP",        # Nominal GDP
    "GDPC1",      # Real GDP
    "UNRATE",     # Unemployment
    "PAYEMS",     # Total Nonfarm Payrolls
    "INDPRO",     # Industrial Production Index
    "UMCSENT",    # Consumer Sentiment
    # Market
    "VIXCLS",     # VIX
    "BAMLH0A0HYM2",  # ICE BofA HY OAS
    "SP500",      # S&P 500
]


def seed_yfinance():
    """Pull price data for MAG 7 using yf.download() batch API."""
    logger.info("=" * 60)
    logger.info("STEP 1: yFinance — MAG 7 prices")
    logger.info("=" * 60)

    import yfinance as yf
    import pandas as pd
    from sqlalchemy import text
    from app.db.models import Company
    from app.db.session import engine, SessionLocal

    # ── Test connectivity first ──
    logger.info("> Testing Yahoo Finance connectivity ...")
    try:
        test = yf.download("AAPL", period="5d", progress=False)
        if test is None or test.empty:
            logger.error("  Yahoo Finance returned no data — likely rate-limited or blocked.")
            logger.error("  If running from Docker, try from host instead:")
            logger.error("    cd src && python seed_data.py yfinance")
            return
        logger.info("  Connectivity OK — got %d rows for AAPL test", len(test))
    except Exception as exc:
        logger.error("  Cannot reach Yahoo Finance: %s", exc)
        logger.error("  If running from Docker, try from host instead:")
        logger.error("    cd src && python seed_data.py yfinance")
        return

    time.sleep(3)

    # ── Batch download all price history ──
    logger.info("> Batch downloading prices for: %s", ", ".join(MAG7_TICKERS))
    try:
        data = yf.download(
            MAG7_TICKERS,
            period="max",
            group_by="ticker",
            auto_adjust=False,
            threads=False,
            progress=True,
        )
    except Exception as exc:
        logger.error("  FAIL batch download: %s", exc)
        return

    if data is None or data.empty:
        logger.error("  No data returned from batch download")
        return

    logger.info("  Downloaded %d total rows", len(data))

    insert_price_sql = text("""
        INSERT INTO daily_prices (time, ticker, open, high, low, close, adj_close, volume)
        VALUES (:time, :ticker, :open, :high, :low, :close, :adj_close, :volume)
        ON CONFLICT (ticker, time) DO UPDATE SET
            open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
            close = EXCLUDED.close, adj_close = EXCLUDED.adj_close, volume = EXCLUDED.volume
    """)

    insert_return_sql = text("""
        INSERT INTO daily_returns (time, ticker, return_1d)
        VALUES (:time, :ticker, :return_1d)
        ON CONFLICT (ticker, time) DO UPDATE SET return_1d = EXCLUDED.return_1d
    """)

    for ticker in MAG7_TICKERS:
        try:
            # Extract single-ticker data from multi-level columns
            if isinstance(data.columns, pd.MultiIndex):
                ticker_data = data[ticker].dropna(how="all")
            else:
                ticker_data = data.dropna(how="all")

            if ticker_data.empty:
                logger.warning("  No price data for %s", ticker)
                continue

            # Build price rows
            price_rows = []
            for date_idx, row in ticker_data.iterrows():
                trade_date = date_idx.date() if hasattr(date_idx, "date") else date_idx
                c = row.get("Close")
                if c is None or pd.isna(c):
                    continue
                price_rows.append({
                    "ticker": ticker,
                    "time": str(trade_date),
                    "open": float(row.get("Open", 0)) if not pd.isna(row.get("Open")) else 0.0,
                    "high": float(row.get("High", 0)) if not pd.isna(row.get("High")) else 0.0,
                    "low": float(row.get("Low", 0)) if not pd.isna(row.get("Low")) else 0.0,
                    "close": float(c),
                    "adj_close": float(row.get("Adj Close", c)) if not pd.isna(row.get("Adj Close")) else float(c),
                    "volume": int(row.get("Volume", 0)) if not pd.isna(row.get("Volume")) else 0,
                })

            if price_rows:
                # Insert in batches of 5000 to avoid huge transactions
                batch_size = 5000
                for start in range(0, len(price_rows), batch_size):
                    batch = price_rows[start:start + batch_size]
                    with engine.begin() as conn:
                        conn.execute(insert_price_sql, batch)
                logger.info("  OK %s: %d price rows", ticker, len(price_rows))

            # Compute and insert daily returns
            closes = ticker_data["Close"].dropna()
            if len(closes) > 1:
                returns = closes.pct_change().dropna()
                return_rows = []
                for date_idx, ret_val in returns.items():
                    trade_date = date_idx.date() if hasattr(date_idx, "date") else date_idx
                    if not pd.isna(ret_val):
                        return_rows.append({
                            "ticker": ticker,
                            "time": str(trade_date),
                            "return_1d": float(ret_val),
                        })
                if return_rows:
                    for start in range(0, len(return_rows), batch_size):
                        batch = return_rows[start:start + batch_size]
                        with engine.begin() as conn:
                            conn.execute(insert_return_sql, batch)
                    logger.info("  OK %s: %d return rows", ticker, len(return_rows))

        except Exception as exc:
            logger.error("  FAIL processing %s: %s", ticker, exc)

    # ── Company info (individual with delays) ──
    logger.info("> Fetching company info ...")
    db = SessionLocal()
    for i, ticker in enumerate(MAG7_TICKERS):
        if i > 0:
            time.sleep(5)
        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info or {}
            if not info or ("shortName" not in info and "longName" not in info):
                logger.warning("  No company info for %s (may be rate-limited)", ticker)
                # Still create a minimal company record so EDGAR can match
                company = db.query(Company).filter(Company.ticker == ticker).first()
                if company is None:
                    company = Company(ticker=ticker, cik=f"YF-{ticker}", name=ticker)
                    db.add(company)
                    db.commit()
                continue

            company = db.query(Company).filter(Company.ticker == ticker).first()
            if company is None:
                company = Company(
                    ticker=ticker,
                    cik=f"YF-{ticker}",
                    name=info.get("longName") or info.get("shortName") or ticker,
                )
                db.add(company)

            company.name = info.get("longName") or info.get("shortName") or company.name
            company.sector = info.get("sector")
            company.industry = info.get("industry")
            company.market_cap = info.get("marketCap")
            company.exchange = info.get("exchange")
            company.currency = info.get("currency")
            company.country = info.get("country")
            company.website = info.get("website")
            company.description = info.get("longBusinessSummary")
            company.employees = info.get("fullTimeEmployees")
            db.commit()
            logger.info("  OK %s company info", ticker)
        except Exception as exc:
            logger.warning("  Skipping company info for %s: %s", ticker, exc)
            # Still create minimal company record
            try:
                company = db.query(Company).filter(Company.ticker == ticker).first()
                if company is None:
                    company = Company(ticker=ticker, cik=f"YF-{ticker}", name=ticker)
                    db.add(company)
                    db.commit()
            except Exception:
                pass
    db.close()


def seed_edgar():
    """Pull SEC EDGAR fundamentals for MAG 7."""
    logger.info("=" * 60)
    logger.info("STEP 2: SEC EDGAR — MAG 7 fundamentals")
    logger.info("=" * 60)

    from app.ingestion.edgar import EdgarIngestor

    with EdgarIngestor() as ing:
        for i, (ticker, cik) in enumerate(MAG7_CIKS.items()):
            try:
                logger.info("> Ingesting %s (CIK %s) [%d/%d] ...", ticker, cik, i + 1, len(MAG7_CIKS))
                result = ing.ingest_company(cik)
                logger.info(
                    "  OK %s: %d filings, %d statement rows",
                    ticker, result["filings"], result["statements"],
                )
            except Exception as exc:
                logger.error("  FAIL %s (CIK %s): %s", ticker, cik, exc)


def seed_fred():
    """Pull FRED macro series."""
    logger.info("=" * 60)
    logger.info("STEP 3: FRED — key macro series")
    logger.info("=" * 60)

    from app.ingestion.fred import FredIngestor

    with FredIngestor() as ing:
        for series_id in FRED_SERIES:
            try:
                logger.info("> Ingesting %s ...", series_id)
                count = ing.ingest_series(series_id)
                logger.info("  OK %s: %d observations", series_id, count)
            except Exception as exc:
                logger.error("  FAIL %s: %s", series_id, exc)


def seed_enrichment():
    """Run the metrics enrichment pipeline for all seeded companies."""
    logger.info("=" * 60)
    logger.info("STEP 4: Enrichment — compute derived metrics")
    logger.info("=" * 60)

    from app.db.session import SessionLocal
    from app.pipeline.enricher import enrich_all

    db = SessionLocal()
    try:
        enrich_all(db)
        logger.info("  OK Enrichment complete")
    except Exception as exc:
        logger.error("  FAIL Enrichment: %s", exc)
    finally:
        db.close()


def main():
    from app.db.session import create_tables
    logger.info("Creating DB tables if needed ...")
    create_tables()

    # Allow running individual steps
    steps = sys.argv[1:] if len(sys.argv) > 1 else ["yfinance", "edgar", "fred", "enrich"]

    if "yfinance" in steps:
        seed_yfinance()
    if "edgar" in steps:
        seed_edgar()
    if "fred" in steps:
        seed_fred()
    if "enrich" in steps:
        seed_enrichment()

    logger.info("=" * 60)
    logger.info("SEED COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
