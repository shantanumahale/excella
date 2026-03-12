#!/usr/bin/env python3
"""Seed script — pre-pull MAG 7 companies + FRED macro data.

Run inside the API container:
    docker compose exec api python seed_data.py

Or locally (with services running):
    cd src && python seed_data.py
"""

from __future__ import annotations

import logging
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
    "DGS2",       # 2-Year Treasury
    "DGS10",      # 10-Year Treasury
    "T10Y2Y",     # 10Y-2Y Spread
    "FEDFUNDS",   # Fed Funds Rate
    "CPIAUCSL",   # CPI
    "GDP",        # Nominal GDP
    "UNRATE",     # Unemployment
    "VIXCLS",     # VIX
]

# Delay between yFinance requests to avoid 429 rate limiting
YF_DELAY_SECONDS = 8


def seed_yfinance():
    """Pull price data + company info for MAG 7 via yFinance."""
    logger.info("=" * 60)
    logger.info("STEP 1: yFinance — MAG 7 prices (period=max)")
    logger.info("  Using %ds delay between tickers to avoid rate limits", YF_DELAY_SECONDS)
    logger.info("=" * 60)

    from app.ingestion.yfinance_ingestor import YFinanceIngestor

    with YFinanceIngestor() as ing:
        for i, ticker in enumerate(MAG7_TICKERS):
            if i > 0:
                logger.info("  Waiting %ds before next ticker ...", YF_DELAY_SECONDS)
                time.sleep(YF_DELAY_SECONDS)
            try:
                logger.info("> Ingesting %s (%d/%d) ...", ticker, i + 1, len(MAG7_TICKERS))
                result = ing.ingest_ticker(ticker, period="max")
                logger.info(
                    "  OK %s: %d prices, %d returns, %d corp actions",
                    ticker,
                    result["prices"],
                    result["returns"],
                    result["corporate_actions"],
                )
            except Exception as exc:
                logger.error("  FAIL %s: %s", ticker, exc)


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
                    ticker,
                    result["filings"],
                    result["statements"],
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

    seed_yfinance()
    seed_edgar()
    seed_fred()
    seed_enrichment()

    logger.info("=" * 60)
    logger.info("SEED COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
