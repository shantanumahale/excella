from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean, String, Integer, BigInteger, Float, Text, Date, DateTime,
    ForeignKey, Index, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Company ──────────────────────────────────────────────────────────────────

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cik: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(12), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    sic_code: Mapped[str | None] = mapped_column(String(10))
    sic_description: Mapped[str | None] = mapped_column(String(256))
    sector: Mapped[str | None] = mapped_column(String(128))
    industry: Mapped[str | None] = mapped_column(String(256))
    fiscal_year_end: Mapped[str | None] = mapped_column(String(5))  # "MM-DD"
    exchange: Mapped[str | None] = mapped_column(String(32))
    ein: Mapped[str | None] = mapped_column(String(20))
    state_of_incorporation: Mapped[str | None] = mapped_column(String(10))
    country: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(10))
    website: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    market_cap: Mapped[float | None] = mapped_column(Float)
    employees: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    filings: Mapped[list["Filing"]] = relationship(back_populates="company")
    financial_statements: Mapped[list["FinancialStatement"]] = relationship(back_populates="company")
    derived_metrics: Mapped[list["DerivedMetrics"]] = relationship(back_populates="company")


# ── Filing ───────────────────────────────────────────────────────────────────

class Filing(Base):
    __tablename__ = "filings"
    __table_args__ = (
        UniqueConstraint("accession_number", name="uq_filings_accession"),
        Index("ix_filings_company_form", "company_id", "form_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    accession_number: Mapped[str] = mapped_column(String(25), nullable=False)
    form_type: Mapped[str] = mapped_column(String(20), nullable=False)
    filing_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_of_report: Mapped[date | None] = mapped_column(Date)
    primary_document: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    primary_doc_url: Mapped[str | None] = mapped_column(Text)
    s3_key: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="raw")  # raw / parsed / refined / error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="filings")
    financial_statements: Mapped[list["FinancialStatement"]] = relationship(back_populates="filing")


# ── Financial Statement ──────────────────────────────────────────────────────

class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "period_end", "fiscal_period", "statement_type",
            name="uq_fin_stmt_period",
        ),
        Index("ix_fin_stmt_company_period", "company_id", "period_end"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    filing_id: Mapped[int | None] = mapped_column(ForeignKey("filings.id"))
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_year: Mapped[int | None] = mapped_column(Integer)
    fiscal_period: Mapped[str] = mapped_column(String(4), nullable=False)  # Q1 Q2 Q3 Q4 FY
    statement_type: Mapped[str] = mapped_column(String(20), nullable=False)  # income / balance / cashflow
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="edgar")  # edgar / manual
    period_type: Mapped[str] = mapped_column(String(10), default="annual")  # annual / quarterly
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_warnings: Mapped[list | None] = mapped_column(JSONB, default=list)
    validation_errors: Mapped[list | None] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="financial_statements")
    filing: Mapped["Filing | None"] = relationship(back_populates="financial_statements")


# ── Derived Metrics (the screener powerhouse) ────────────────────────────────

class DerivedMetrics(Base):
    __tablename__ = "derived_metrics"
    __table_args__ = (
        UniqueConstraint("company_id", "period_end", "fiscal_period", name="uq_derived_period"),
        Index("ix_derived_company_period", "company_id", "period_end"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(4), nullable=False)

    # Each category is a JSONB blob so we can evolve metrics without migrations
    profitability: Mapped[dict | None] = mapped_column(JSONB)
    liquidity: Mapped[dict | None] = mapped_column(JSONB)
    leverage: Mapped[dict | None] = mapped_column(JSONB)
    efficiency: Mapped[dict | None] = mapped_column(JSONB)
    cashflow: Mapped[dict | None] = mapped_column(JSONB)
    growth: Mapped[dict | None] = mapped_column(JSONB)
    dupont: Mapped[dict | None] = mapped_column(JSONB)
    valuation: Mapped[dict | None] = mapped_column(JSONB)
    quality: Mapped[dict | None] = mapped_column(JSONB)
    forensic: Mapped[dict | None] = mapped_column(JSONB)
    shareholder: Mapped[dict | None] = mapped_column(JSONB)
    per_share: Mapped[dict | None] = mapped_column(JSONB)
    valuation_models: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="derived_metrics")


# ── FRED Series Metadata ─────────────────────────────────────────────────────

class FredSeries(Base):
    __tablename__ = "fred_series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(256))
    frequency: Mapped[str | None] = mapped_column(String(32))
    units: Mapped[str | None] = mapped_column(String(128))
    seasonal_adjustment: Mapped[str | None] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text)
    last_updated: Mapped[str | None] = mapped_column(String(64))


# ── Ingestion Log ────────────────────────────────────────────────────────────

class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # edgar / fred / yfinance
    job_type: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running / success / error
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)


# ── User ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=func.now())

    watchlists: Mapped[list["Watchlist"]] = relationship(back_populates="user")
    screener_presets: Mapped[list["ScreenerPreset"]] = relationship(back_populates="user")


# ── Watchlist ─────────────────────────────────────────────────────────────

class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="watchlists")
    companies: Mapped[list["WatchlistCompany"]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan",
    )


# ── Watchlist ↔ Company join ─────────────────────────────────────────────

class WatchlistCompany(Base):
    __tablename__ = "watchlist_companies"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "company_id", name="uq_watchlist_company"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    watchlist: Mapped["Watchlist"] = relationship(back_populates="companies")
    company: Mapped["Company"] = relationship()


# ── Screener Preset ──────────────────────────────────────────────────────

class ScreenerPreset(Base):
    __tablename__ = "screener_presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="screener_presets")
