"""Watchlist CRUD endpoints — requires authentication."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.deps import get_db
from app.db.models import (
    Company,
    DerivedMetrics,
    User,
    Watchlist,
    WatchlistCompany,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/watchlists", tags=["watchlists"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class CreateWatchlistRequest(BaseModel):
    name: str
    description: Optional[str] = None


class AddCompaniesRequest(BaseModel):
    tickers: list[str]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a watchlist")
def create_watchlist(
    body: CreateWatchlistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new watchlist for the authenticated user."""
    wl = Watchlist(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
    )
    db.add(wl)
    db.commit()
    db.refresh(wl)

    return {
        "id": wl.id,
        "name": wl.name,
        "description": wl.description,
        "created_at": wl.created_at.isoformat() if wl.created_at else None,
    }


@router.get("", summary="List user watchlists")
def list_watchlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all watchlists belonging to the authenticated user."""
    rows = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.created_at.desc())
        .all()
    )

    return {
        "data": [
            {
                "id": wl.id,
                "name": wl.name,
                "description": wl.description,
                "company_count": len(wl.companies),
                "created_at": wl.created_at.isoformat() if wl.created_at else None,
            }
            for wl in rows
        ],
    }


@router.get("/{watchlist_id}", summary="Get watchlist with companies")
def get_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a watchlist including its companies and their latest metrics."""
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if wl.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watchlist")

    companies_data = []
    for wc in wl.companies:
        company = wc.company

        latest_metrics = (
            db.query(DerivedMetrics)
            .filter(DerivedMetrics.company_id == company.id)
            .order_by(DerivedMetrics.period_end.desc())
            .first()
        )

        metrics_summary = None
        if latest_metrics:
            metrics_summary = {
                "period_end": str(latest_metrics.period_end),
                "fiscal_period": latest_metrics.fiscal_period,
                "profitability": latest_metrics.profitability,
                "valuation": latest_metrics.valuation,
                "growth": latest_metrics.growth,
            }

        companies_data.append({
            "ticker": company.ticker,
            "name": company.name,
            "sector": company.sector,
            "industry": company.industry,
            "exchange": company.exchange,
            "added_at": wc.added_at.isoformat() if wc.added_at else None,
            "latest_metrics": metrics_summary,
        })

    return {
        "id": wl.id,
        "name": wl.name,
        "description": wl.description,
        "created_at": wl.created_at.isoformat() if wl.created_at else None,
        "companies": companies_data,
    }


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a watchlist")
def delete_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a watchlist (only if owned by the current user)."""
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if wl.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watchlist")

    db.delete(wl)
    db.commit()


@router.post("/{watchlist_id}/companies", status_code=status.HTTP_201_CREATED,
             summary="Add companies to watchlist")
def add_companies(
    watchlist_id: int,
    body: AddCompaniesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add one or more companies (by ticker) to a watchlist."""
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if wl.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watchlist")

    added = []
    not_found = []
    already_exists = []

    for ticker in body.tickers:
        company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
        if not company:
            not_found.append(ticker)
            continue

        existing = (
            db.query(WatchlistCompany)
            .filter(
                WatchlistCompany.watchlist_id == watchlist_id,
                WatchlistCompany.company_id == company.id,
            )
            .first()
        )
        if existing:
            already_exists.append(ticker.upper())
            continue

        wc = WatchlistCompany(watchlist_id=watchlist_id, company_id=company.id)
        db.add(wc)
        added.append(ticker.upper())

    db.commit()

    return {
        "added": added,
        "not_found": not_found,
        "already_exists": already_exists,
    }


@router.delete("/{watchlist_id}/companies/{ticker}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove a company from watchlist")
def remove_company(
    watchlist_id: int,
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a single company (by ticker) from a watchlist."""
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if wl.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watchlist")

    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    wc = (
        db.query(WatchlistCompany)
        .filter(
            WatchlistCompany.watchlist_id == watchlist_id,
            WatchlistCompany.company_id == company.id,
        )
        .first()
    )
    if not wc:
        raise HTTPException(status_code=404, detail="Company not in this watchlist")

    db.delete(wc)
    db.commit()
