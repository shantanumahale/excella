"""Yahoo Finance ingestor – daily prices, corporate actions, and company info."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import yfinance as yf
from sqlalchemy import text

from app.db.models import Company
from app.db.session import engine
from app.ingestion.base import BaseIngestor

logger = logging.getLogger(__name__)


class YFinanceIngestor(BaseIngestor):
    """Ingest market data from Yahoo Finance via the yfinance library."""

    source_name = "yfinance"

    # -- Daily prices --

    def _upsert_daily_prices(self, ticker: str, hist) -> int:
        """Upsert OHLCV rows into the daily_prices hypertable.

        Args:
            ticker: The stock ticker symbol.
            hist: A pandas DataFrame returned by yfinance Ticker.history().

        Returns:
            Number of rows upserted.
        """
        if hist is None or hist.empty:
            logger.warning("No price history for %s", ticker)
            return 0

        rows = []
        for date_idx, row in hist.iterrows():
            # yfinance returns a tz-aware DatetimeIndex
            trade_date = date_idx.date() if hasattr(date_idx, "date") else date_idx
            rows.append(
                {
                    "ticker": ticker,
                    "time": str(trade_date),
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "adj_close": float(row.get("Adj Close", row.get("Close", 0))),
                    "volume": int(row.get("Volume", 0)),
                }
            )

        if not rows:
            return 0

        insert_sql = text("""
            INSERT INTO daily_prices (time, ticker, open, high, low, close, adj_close, volume)
            VALUES (:time, :ticker, :open, :high, :low, :close, :adj_close, :volume)
            ON CONFLICT (ticker, time) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                adj_close = EXCLUDED.adj_close,
                volume = EXCLUDED.volume
        """)

        with engine.begin() as conn:
            conn.execute(insert_sql, rows)

        logger.info("Upserted %d daily price rows for %s", len(rows), ticker)
        return len(rows)

    # -- Daily returns --

    def _compute_and_insert_returns(self, ticker: str, hist) -> int:
        """Compute 1-day simple returns and insert into daily_returns hypertable.

        Returns:
            Number of return rows inserted.
        """
        if hist is None or len(hist) < 2:
            return 0

        close = hist["Close"]
        returns = close.pct_change().dropna()

        rows = []
        for date_idx, ret_val in returns.items():
            trade_date = date_idx.date() if hasattr(date_idx, "date") else date_idx
            rows.append(
                {
                    "ticker": ticker,
                    "time": str(trade_date),
                    "return_1d": float(ret_val),
                }
            )

        if not rows:
            return 0

        insert_sql = text("""
            INSERT INTO daily_returns (time, ticker, return_1d)
            VALUES (:time, :ticker, :return_1d)
            ON CONFLICT (ticker, time) DO UPDATE SET
                return_1d = EXCLUDED.return_1d
        """)

        with engine.begin() as conn:
            conn.execute(insert_sql, rows)

        logger.info("Upserted %d daily return rows for %s", len(rows), ticker)
        return len(rows)

    # -- Corporate actions --

    def _upsert_corporate_actions(self, ticker: str, yf_ticker: yf.Ticker) -> int:
        """Fetch dividends and splits, upsert into the corporate_actions hypertable.

        Returns:
            Number of corporate action rows upserted.
        """
        count = 0

        # Dividends
        dividends = yf_ticker.dividends
        if dividends is not None and not dividends.empty:
            div_rows = []
            for date_idx, amount in dividends.items():
                action_date = (
                    date_idx.date() if hasattr(date_idx, "date") else date_idx
                )
                div_rows.append(
                    {
                        "ticker": ticker,
                        "time": str(action_date),
                        "action_type": "dividend",
                        "value": float(amount),
                    }
                )

            if div_rows:
                insert_sql = text("""
                    INSERT INTO corporate_actions (time, ticker, action_type, value)
                    VALUES (:time, :ticker, :action_type, :value)
                    ON CONFLICT (ticker, time, action_type) DO UPDATE SET
                        value = EXCLUDED.value
                """)
                with engine.begin() as conn:
                    conn.execute(insert_sql, div_rows)
                count += len(div_rows)
                logger.info("Upserted %d dividend rows for %s", len(div_rows), ticker)

        # Splits
        splits = yf_ticker.splits
        if splits is not None and not splits.empty:
            split_rows = []
            for date_idx, ratio in splits.items():
                action_date = (
                    date_idx.date() if hasattr(date_idx, "date") else date_idx
                )
                split_rows.append(
                    {
                        "ticker": ticker,
                        "time": str(action_date),
                        "action_type": "split",
                        "value": float(ratio),
                    }
                )

            if split_rows:
                insert_sql = text("""
                    INSERT INTO corporate_actions (time, ticker, action_type, value)
                    VALUES (:time, :ticker, :action_type, :value)
                    ON CONFLICT (ticker, time, action_type) DO UPDATE SET
                        value = EXCLUDED.value
                """)
                with engine.begin() as conn:
                    conn.execute(insert_sql, split_rows)
                count += len(split_rows)
                logger.info(
                    "Upserted %d split rows for %s", len(split_rows), ticker
                )

        return count

    # -- Company info --

    def _upsert_company_info(self, ticker: str, info: dict[str, Any]) -> None:
        """Upsert Company record from yfinance ticker.info."""
        if not info:
            return

        company = (
            self.db.query(Company).filter(Company.ticker == ticker).first()
        )
        if company is None:
            company = Company(
                ticker=ticker,
                cik=f"YF-{ticker}",
                name=info.get("longName") or info.get("shortName") or ticker,
            )
            self.db.add(company)

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

        self.db.commit()
        logger.info("Upserted company info for %s", ticker)

    # -- Public API --

    def ingest_ticker(self, ticker: str, period: str = "5d") -> dict[str, int]:
        """Ingest all available data for a single ticker.

        Args:
            ticker: Stock ticker symbol (e.g. "AAPL").
            period: yfinance period string – "5d" for daily runs, "max" for backfill.

        Returns:
            Summary dict with counts of ingested records.
        """
        log = self.log_start(detail=f"ticker={ticker} period={period}")
        result: dict[str, int] = {
            "prices": 0,
            "returns": 0,
            "corporate_actions": 0,
        }

        try:
            yf_ticker = yf.Ticker(ticker)

            # 1. Daily OHLCV
            hist = yf_ticker.history(period=period)
            result["prices"] = self._upsert_daily_prices(ticker, hist)

            # 2. Daily returns
            result["returns"] = self._compute_and_insert_returns(ticker, hist)

            # 3. Corporate actions (dividends + splits)
            result["corporate_actions"] = self._upsert_corporate_actions(
                ticker, yf_ticker
            )

            # 4. Company info
            try:
                info = yf_ticker.info
                self._upsert_company_info(ticker, info)
            except Exception as exc:
                # Company info is supplemental; don't fail the whole ingest
                logger.warning(
                    "Could not fetch company info for %s: %s", ticker, exc
                )

            total = sum(result.values())
            self.log_end(status="success", records_processed=total)

        except Exception as exc:
            logger.exception("Error ingesting ticker %s", ticker)
            self.log_end(
                status="failed",
                records_processed=0,
                error_message=str(exc),
            )
            raise

        return result

    def ingest_bulk(
        self, tickers: list[str], period: str = "5d"
    ) -> dict[str, Any]:
        """Ingest multiple tickers sequentially.

        Returns a summary with per-ticker results and overall counts.
        """
        results: dict[str, Any] = {
            "succeeded": [],
            "failed": [],
            "totals": {"prices": 0, "returns": 0, "corporate_actions": 0},
        }

        for ticker in tickers:
            try:
                r = self.ingest_ticker(ticker, period=period)
                for key in results["totals"]:
                    results["totals"][key] += r.get(key, 0)
                results["succeeded"].append(ticker)
            except Exception as exc:
                logger.error("Bulk ingest failed for %s: %s", ticker, exc)
                results["failed"].append(
                    {"ticker": ticker, "error": str(exc)}
                )

        logger.info(
            "Bulk yfinance ingest complete: %d succeeded, %d failed",
            len(results["succeeded"]),
            len(results["failed"]),
        )
        return results
