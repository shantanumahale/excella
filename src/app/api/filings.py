"""Filing listing endpoints for a given company."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, get_db
from app.db.models import Company, Filing

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies", tags=["filings"])


def _build_edgar_url(cik: str, accession_number: str) -> str:
    """Construct a full EDGAR filing URL from CIK and accession number."""
    acc_no_dashes = accession_number.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dashes}/{accession_number}-index.htm"
    )


@router.get(
    "/{ticker}/filings",
    summary="List filings for a company",
    description="Return SEC filings for the given ticker, with optional form_type filter. Paginated.",
)
def list_filings(
    ticker: str,
    pagination: PaginationParams = Depends(),
    form_type: Optional[str] = Query(None, description="Filter by SEC form type (e.g. 10-K, 10-Q, 8-K)"),
    db: Session = Depends(get_db),
):
    """List filings for a company identified by ticker."""
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    q = db.query(Filing).filter(Filing.company_id == company.id)

    if form_type:
        q = q.filter(Filing.form_type == form_type.upper())

    total = q.count()
    rows = (
        q.order_by(Filing.filing_date.desc())
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
                "accession_number": f.accession_number,
                "form_type": f.form_type,
                "filing_date": str(f.filing_date),
                "period_of_report": str(f.period_of_report) if f.period_of_report else None,
                "primary_document": f.primary_document,
                "description": f.description,
                "edgar_url": _build_edgar_url(company.cik, f.accession_number),
            }
            for f in rows
        ],
    }
