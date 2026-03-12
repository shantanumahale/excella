"""Company listing and detail endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, get_db
from app.db.models import Company, DerivedMetrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", summary="List companies", description="List all tracked companies with optional filters by sector, industry, exchange, or name/ticker search. Paginated.")
def list_companies(
    pagination: PaginationParams = Depends(),
    sector: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    exchange: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by ticker or name"),
    db: Session = Depends(get_db),
):
    """List companies with optional filters. Paginated."""
    q = db.query(
        Company.id,
        Company.ticker,
        Company.name,
        Company.sector,
        Company.industry,
        Company.exchange,
    )

    if sector:
        q = q.filter(Company.sector.ilike(f"%{sector}%"))
    if industry:
        q = q.filter(Company.industry.ilike(f"%{industry}%"))
    if exchange:
        q = q.filter(Company.exchange.ilike(f"%{exchange}%"))
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (Company.ticker.ilike(pattern)) | (Company.name.ilike(pattern))
        )

    total = q.count()
    rows = (
        q.order_by(Company.ticker)
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    return {
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
        "data": [
            {
                "id": r.id,
                "ticker": r.ticker,
                "name": r.name,
                "sector": r.sector,
                "industry": r.industry,
                "exchange": r.exchange,
            }
            for r in rows
        ],
    }


@router.get("/{ticker}", summary="Company detail", description="Full company profile with latest derived metrics (all 12 categories).")
def get_company(ticker: str, db: Session = Depends(get_db)):
    """Full company detail with latest derived metrics snapshot."""
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    latest_metrics = (
        db.query(DerivedMetrics)
        .filter(DerivedMetrics.company_id == company.id)
        .order_by(DerivedMetrics.period_end.desc())
        .first()
    )

    metrics_dict = None
    if latest_metrics:
        metrics_dict = {
            "period_end": str(latest_metrics.period_end),
            "fiscal_period": latest_metrics.fiscal_period,
            "profitability": latest_metrics.profitability,
            "liquidity": latest_metrics.liquidity,
            "leverage": latest_metrics.leverage,
            "efficiency": latest_metrics.efficiency,
            "cashflow": latest_metrics.cashflow,
            "growth": latest_metrics.growth,
            "dupont": latest_metrics.dupont,
            "valuation": latest_metrics.valuation,
            "quality": latest_metrics.quality,
            "forensic": latest_metrics.forensic,
            "shareholder": latest_metrics.shareholder,
            "per_share": latest_metrics.per_share,
        }

    return {
        "id": company.id,
        "cik": company.cik,
        "ticker": company.ticker,
        "name": company.name,
        "sic_code": company.sic_code,
        "sector": company.sector,
        "industry": company.industry,
        "fiscal_year_end": company.fiscal_year_end,
        "exchange": company.exchange,
        "created_at": company.created_at.isoformat() if company.created_at else None,
        "updated_at": company.updated_at.isoformat() if company.updated_at else None,
        "latest_metrics": metrics_dict,
    }
