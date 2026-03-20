"""Valuation model endpoints — intrinsic value estimation."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Company, DerivedMetrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies/{ticker}", tags=["valuation"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_company(ticker: str, db: Session) -> Company:
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class DCFParams(BaseModel):
    growth_rate: Optional[float] = Field(None, description="Override revenue growth rate (decimal)")
    terminal_growth: float = Field(0.025, ge=0, lt=0.10, description="Terminal growth rate")
    wacc: Optional[float] = Field(None, gt=0, lt=0.50, description="Override WACC (decimal)")
    projection_years: int = Field(5, ge=1, le=15, description="Number of projection years")
    terminal_method: str = Field("perpetuity", pattern="^(perpetuity|exit_multiple)$")
    exit_multiple: Optional[float] = Field(None, gt=0, le=50, description="Exit multiple (EV/FCFF)")
    risk_free_rate: Optional[float] = Field(None, ge=0, lt=0.20)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/valuation")
def get_valuation(
    ticker: str,
    db: Session = Depends(get_db),
):
    """Get pre-computed valuation summary from the latest DerivedMetrics."""
    company = _resolve_company(ticker, db)

    row = (
        db.query(DerivedMetrics)
        .filter(DerivedMetrics.company_id == company.id)
        .order_by(DerivedMetrics.period_end.desc())
        .first()
    )
    if not row or not row.valuation_models:
        raise HTTPException(status_code=404, detail="No valuation data available")

    return {
        "ticker": company.ticker,
        "period_end": str(row.period_end),
        "valuation_models": row.valuation_models,
    }


@router.post("/valuation/dcf")
def custom_dcf(
    ticker: str,
    params: DCFParams,
    db: Session = Depends(get_db),
):
    """Run on-demand DCF with custom assumptions. Not persisted."""
    company = _resolve_company(ticker, db)

    from app.valuation.engine import run_valuation

    overrides = {}
    if params.growth_rate is not None:
        overrides["growth_rate"] = params.growth_rate
    if params.wacc is not None:
        overrides["wacc"] = params.wacc
    if params.risk_free_rate is not None:
        overrides["risk_free_rate"] = params.risk_free_rate
    overrides["terminal_growth"] = params.terminal_growth
    overrides["projection_years"] = params.projection_years
    overrides["terminal_method"] = params.terminal_method
    if params.exit_multiple is not None:
        overrides["exit_multiple"] = params.exit_multiple

    result = run_valuation(db, company.id, overrides=overrides)

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    return result


@router.get("/valuation/sensitivity")
def get_sensitivity(
    ticker: str,
    db: Session = Depends(get_db),
):
    """WACC x growth rate sensitivity matrix of intrinsic values."""
    company = _resolve_company(ticker, db)

    from app.valuation.engine import run_valuation

    # Get base valuation to extract assumptions
    base = run_valuation(db, company.id)
    if "error" in base:
        raise HTTPException(status_code=422, detail=base["error"])

    base_wacc = base.get("wacc", {}).get("wacc", 0.10)

    # Build sensitivity grid
    wacc_range = [round(base_wacc + delta, 4) for delta in [-0.02, -0.01, 0, 0.01, 0.02]]
    growth_range = [0.01, 0.02, 0.025, 0.03, 0.04]

    matrix = []
    for wacc_val in wacc_range:
        row = {"wacc": wacc_val, "values": {}}
        for g in growth_range:
            if wacc_val <= g:
                row["values"][str(g)] = None
                continue
            result = run_valuation(db, company.id, overrides={
                "wacc": wacc_val,
                "terminal_growth": g,
            })
            dcf = result.get("models", {}).get("dcf")
            row["values"][str(g)] = dcf.get("intrinsic_value_per_share") if dcf else None
        matrix.append(row)

    return {
        "ticker": company.ticker,
        "base_wacc": base_wacc,
        "wacc_range": wacc_range,
        "growth_range": growth_range,
        "matrix": matrix,
    }


@router.get("/valuation/comps")
def get_comps(
    ticker: str,
    db: Session = Depends(get_db),
):
    """Get detailed comparable companies analysis."""
    company = _resolve_company(ticker, db)

    from app.valuation.comps import compute_comps

    result = compute_comps(
        db=db,
        company_id=company.id,
        sector=company.sector,
        industry=company.industry,
    )

    if not result:
        raise HTTPException(status_code=404, detail="No comparable companies found")

    return {"ticker": company.ticker, **result}


@router.get("/valuation/history")
def get_valuation_history(
    ticker: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Historical intrinsic value vs price over time."""
    company = _resolve_company(ticker, db)

    rows = (
        db.query(DerivedMetrics)
        .filter(
            DerivedMetrics.company_id == company.id,
            DerivedMetrics.valuation_models.isnot(None),
        )
        .order_by(DerivedMetrics.period_end.desc())
        .limit(limit)
        .all()
    )

    history = []
    for row in rows:
        vm = row.valuation_models or {}
        summary = vm.get("summary", {})
        val = row.valuation or {}

        # Approximate price from earnings_yield
        price = None
        ey = val.get("earnings_yield")
        if ey and ey != 0:
            price = 1.0 / ey

        history.append({
            "period_end": str(row.period_end),
            "intrinsic_value": summary.get("consensus_value"),
            "price": price,
            "margin_of_safety": summary.get("margin_of_safety"),
            "model_count": summary.get("model_count"),
        })

    return {"ticker": company.ticker, "history": list(reversed(history))}
