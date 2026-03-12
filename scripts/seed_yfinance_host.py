#!/usr/bin/env python3
"""Standalone yFinance seeder — runs from host machine, connects directly to Docker DB.

Usage:
    cd excella
    pip install yfinance psycopg2-binary pandas
    python scripts/seed_yfinance_host.py
"""

import logging
import time

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import yfinance as yf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger("seed_yf")

# Docker PostgreSQL connection (mapped to host port 5432)
DB_DSN = "host=localhost port=5432 dbname=excella user=excella password=excella_dev"

MAG7_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]


def get_conn():
    return psycopg2.connect(DB_DSN)


def seed_prices():
    """Batch download and insert price data."""
    logger.info("Testing Yahoo Finance connectivity ...")
    test = yf.download("AAPL", period="5d", progress=False)
    if test is None or test.empty:
        logger.error("Yahoo Finance returned no data — likely blocked.")
        return False
    logger.info("Connectivity OK — got %d rows for AAPL test", len(test))

    time.sleep(2)

    logger.info("Batch downloading prices for: %s", ", ".join(MAG7_TICKERS))
    data = yf.download(
        MAG7_TICKERS,
        period="max",
        group_by="ticker",
        auto_adjust=False,
        threads=False,
        progress=True,
    )

    if data is None or data.empty:
        logger.error("No data returned from batch download")
        return False

    logger.info("Downloaded %d total rows", len(data))

    conn = get_conn()
    cur = conn.cursor()

    for ticker in MAG7_TICKERS:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                ticker_data = data[ticker].dropna(how="all")
            else:
                ticker_data = data.dropna(how="all")

            if ticker_data.empty:
                logger.warning("No price data for %s", ticker)
                continue

            # Build price rows
            price_rows = []
            for date_idx, row in ticker_data.iterrows():
                trade_date = date_idx.date() if hasattr(date_idx, "date") else date_idx
                c = row.get("Close")
                if c is None or pd.isna(c):
                    continue
                price_rows.append((
                    str(trade_date),
                    ticker,
                    float(row.get("Open", 0)) if not pd.isna(row.get("Open")) else 0.0,
                    float(row.get("High", 0)) if not pd.isna(row.get("High")) else 0.0,
                    float(row.get("Low", 0)) if not pd.isna(row.get("Low")) else 0.0,
                    float(c),
                    float(row.get("Adj Close", c)) if not pd.isna(row.get("Adj Close")) else float(c),
                    int(row.get("Volume", 0)) if not pd.isna(row.get("Volume")) else 0,
                ))

            if price_rows:
                execute_values(
                    cur,
                    """INSERT INTO daily_prices (time, ticker, open, high, low, close, adj_close, volume)
                       VALUES %s
                       ON CONFLICT (ticker, time) DO UPDATE SET
                           open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                           close = EXCLUDED.close, adj_close = EXCLUDED.adj_close, volume = EXCLUDED.volume""",
                    price_rows,
                    page_size=5000,
                )
                conn.commit()
                logger.info("OK %s: %d price rows", ticker, len(price_rows))

            # Compute and insert daily returns
            closes = ticker_data["Close"].dropna()
            if len(closes) > 1:
                returns = closes.pct_change().dropna()
                return_rows = []
                for date_idx, ret_val in returns.items():
                    trade_date = date_idx.date() if hasattr(date_idx, "date") else date_idx
                    if not pd.isna(ret_val):
                        return_rows.append((str(trade_date), ticker, float(ret_val)))

                if return_rows:
                    execute_values(
                        cur,
                        """INSERT INTO daily_returns (time, ticker, return_1d)
                           VALUES %s
                           ON CONFLICT (ticker, time) DO UPDATE SET return_1d = EXCLUDED.return_1d""",
                        return_rows,
                        page_size=5000,
                    )
                    conn.commit()
                    logger.info("OK %s: %d return rows", ticker, len(return_rows))

        except Exception as exc:
            logger.error("FAIL processing %s: %s", ticker, exc)
            conn.rollback()

    cur.close()
    conn.close()
    return True


def seed_company_info():
    """Fetch company info with delays between tickers."""
    logger.info("Fetching company info ...")
    conn = get_conn()
    cur = conn.cursor()

    for i, ticker in enumerate(MAG7_TICKERS):
        if i > 0:
            time.sleep(5)
        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info or {}

            name = info.get("longName") or info.get("shortName") or ticker
            sector = info.get("sector")
            industry = info.get("industry")
            market_cap = info.get("marketCap")
            exchange = info.get("exchange")
            currency = info.get("currency")
            country = info.get("country")
            website = info.get("website")
            description = info.get("longBusinessSummary")
            employees = info.get("fullTimeEmployees")

            cur.execute(
                """UPDATE companies SET
                       name = COALESCE(%s, name),
                       sector = COALESCE(%s, sector),
                       industry = COALESCE(%s, industry),
                       market_cap = COALESCE(%s, market_cap),
                       exchange = COALESCE(%s, exchange),
                       currency = COALESCE(%s, currency),
                       country = COALESCE(%s, country),
                       website = COALESCE(%s, website),
                       description = COALESCE(%s, description),
                       employees = COALESCE(%s, employees)
                   WHERE ticker = %s""",
                (name, sector, industry, market_cap, exchange, currency,
                 country, website, description, employees, ticker),
            )
            conn.commit()
            logger.info("OK %s company info: %s", ticker, name)

        except Exception as exc:
            logger.warning("Skipping company info for %s: %s", ticker, exc)
            conn.rollback()

    cur.close()
    conn.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("yFinance seeder (standalone host script)")
    logger.info("=" * 60)

    if seed_prices():
        seed_company_info()

    logger.info("=" * 60)
    logger.info("DONE")
    logger.info("=" * 60)
