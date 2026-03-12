"""Financial statements and derived metrics endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Company, DerivedMetrics, FinancialStatement

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies/{ticker}", tags=["financials"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_company(ticker: str, db: Session) -> Company:
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# ---------------------------------------------------------------------------
# Financial statements
# ---------------------------------------------------------------------------

@router.get("/financials")
def list_financials(
    ticker: str,
    statement_type: Optional[str] = Query(
        None, pattern="^(income|balance|cashflow|all)$",
        description="Filter by statement type",
    ),
    period_type: Optional[str] = Query(
        None, pattern="^(annual|quarterly|all)$",
        description="Filter by period type",
    ),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    company = _resolve_company(ticker, db)

    q = db.query(FinancialStatement).filter(
        FinancialStatement.company_id == company.id
    )

    if statement_type and statement_type != "all":
        q = q.filter(FinancialStatement.statement_type == statement_type)

    if period_type and period_type != "all":
        if period_type == "annual":
            q = q.filter(FinancialStatement.fiscal_period == "FY")
        else:  # quarterly
            q = q.filter(FinancialStatement.fiscal_period != "FY")

    rows = (
        q.order_by(FinancialStatement.period_end.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "statement_type": r.statement_type,
            "fiscal_period": r.fiscal_period,
            "period_start": str(r.period_start) if r.period_start else None,
            "period_end": str(r.period_end),
            "source": r.source,
            "data": r.data,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Derived metrics history
# ---------------------------------------------------------------------------

@router.get("/metrics")
def list_metrics(
    ticker: str,
    period_type: Optional[str] = Query(
        None, pattern="^(annual|quarterly|all)$",
    ),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    company = _resolve_company(ticker, db)

    q = db.query(DerivedMetrics).filter(DerivedMetrics.company_id == company.id)

    if period_type and period_type != "all":
        if period_type == "annual":
            q = q.filter(DerivedMetrics.fiscal_period == "FY")
        else:
            q = q.filter(DerivedMetrics.fiscal_period != "FY")

    rows = q.order_by(DerivedMetrics.period_end.desc()).limit(limit).all()

    return [_metrics_row(r) for r in rows]


@router.get("/metrics/latest")
def latest_metrics(
    ticker: str,
    db: Session = Depends(get_db),
):
    company = _resolve_company(ticker, db)

    row = (
        db.query(DerivedMetrics)
        .filter(DerivedMetrics.company_id == company.id)
        .order_by(DerivedMetrics.period_end.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No metrics found")

    return _metrics_row(row)


def _metrics_row(r: DerivedMetrics) -> dict:
    return {
        "period_end": str(r.period_end),
        "fiscal_period": r.fiscal_period,
        "profitability": r.profitability,
        "liquidity": r.liquidity,
        "leverage": r.leverage,
        "efficiency": r.efficiency,
        "cashflow": r.cashflow,
        "growth": r.growth,
        "dupont": r.dupont,
        "valuation": r.valuation,
        "quality": r.quality,
        "forensic": r.forensic,
        "shareholder": r.shareholder,
        "per_share": r.per_share,
    }
