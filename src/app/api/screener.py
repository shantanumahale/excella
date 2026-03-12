"""Screener endpoint — the core feature of Excella.

Accepts filter criteria on derived-metrics JSONB columns and returns
matching companies with their metrics.  All filtering is done via
parameterised queries to prevent SQL injection.
"""

from __future__ import annotations

import logging
from typing import Any, List, Literal, Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screener", tags=["screener"])

# ---------------------------------------------------------------------------
# Allowed JSONB category columns on derived_metrics
# ---------------------------------------------------------------------------
METRIC_CATEGORIES = frozenset({
    "profitability", "liquidity", "leverage", "efficiency", "cashflow",
    "growth", "dupont", "valuation", "quality", "forensic", "shareholder",
    "per_share",
})

OPERATORS = {
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "eq": "=",
}

# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ScreenerFilter(BaseModel):
    metric: str = Field(..., description="Dot-path: category.metric_name")
    operator: Literal["gt", "gte", "lt", "lte", "eq", "between", "not_null"] = "gt"
    value: Optional[Union[float, int, List[Union[float, int]]]] = None

    @field_validator("metric")
    @classmethod
    def validate_metric_path(cls, v: str) -> str:
        parts = v.split(".")
        if len(parts) != 2:
            raise ValueError("metric must be 'category.metric_name'")
        if parts[0] not in METRIC_CATEGORIES:
            raise ValueError(f"Unknown category '{parts[0]}'")
        return v


class ScreenerRequest(BaseModel):
    filters: List[ScreenerFilter] = Field(default_factory=list)
    sort_by: Optional[str] = None
    sort_order: Literal["asc", "desc"] = "desc"
    offset: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=500)


# ---------------------------------------------------------------------------
# POST /screener
# ---------------------------------------------------------------------------

@router.post("")
def run_screener(body: ScreenerRequest, db: Session = Depends(get_db)):
    """
    Dynamic screening on derived_metrics JSONB columns.

    Strategy:
    - Sub-select the most-recent derived_metrics row per company.
    - Apply all filters using parameterised JSONB extraction.
    - Join with companies for display fields.
    """
    # -- build per-filter SQL fragments and parameter dict -----------------
    where_clauses: list[str] = []
    params: dict[str, Any] = {}

    for idx, f in enumerate(body.filters):
        category, key = f.metric.split(".")
        # Validate category is alphanumeric (defense-in-depth; already checked
        # by the pydantic validator against the allowlist).
        if category not in METRIC_CATEGORIES:
            raise HTTPException(400, f"Invalid category: {category}")

        # JSONB extraction: dm.<category> ->> '<key>'  cast to numeric
        # Column name is safe (from allowlist).  Key is passed as a param via
        # the ->> operator with a text literal that we embed safely.
        # We use the form:  (dm.category ->> :key_i)::numeric
        key_param = f"key_{idx}"
        jsonb_expr = f"(dm.{category} ->> :{key_param})::numeric"
        params[key_param] = key

        if f.operator == "not_null":
            where_clauses.append(f"dm.{category} ->> :{key_param} IS NOT NULL")
        elif f.operator == "between":
            if not isinstance(f.value, list) or len(f.value) != 2:
                raise HTTPException(400, "'between' requires a list of [low, high]")
            lo_param = f"lo_{idx}"
            hi_param = f"hi_{idx}"
            params[lo_param] = f.value[0]
            params[hi_param] = f.value[1]
            where_clauses.append(
                f"{jsonb_expr} BETWEEN :{lo_param} AND :{hi_param}"
            )
        else:
            sql_op = OPERATORS.get(f.operator)
            if sql_op is None:
                raise HTTPException(400, f"Unknown operator: {f.operator}")
            val_param = f"val_{idx}"
            params[val_param] = f.value
            where_clauses.append(f"{jsonb_expr} {sql_op} :{val_param}")

    # -- latest-row sub-query (most recent period_end per company) ---------
    latest_cte = (
        "WITH latest AS ("
        "  SELECT DISTINCT ON (company_id) *"
        "  FROM derived_metrics"
        "  ORDER BY company_id, period_end DESC"
        ")"
    )

    # -- assemble WHERE ----------------------------------------------------
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    # -- sorting -----------------------------------------------------------
    order_expr = "c.ticker"
    if body.sort_by:
        parts = body.sort_by.split(".")
        if len(parts) == 2 and parts[0] in METRIC_CATEGORIES:
            sort_key_param = "sort_key"
            params[sort_key_param] = parts[1]
            direction = "DESC" if body.sort_order == "desc" else "ASC"
            order_expr = f"(dm.{parts[0]} ->> :sort_key)::numeric {direction} NULLS LAST"

    # -- count query -------------------------------------------------------
    count_sql = text(
        f"{latest_cte} "
        f"SELECT count(*) FROM latest dm "
        f"JOIN companies c ON c.id = dm.company_id "
        f"{where_sql}"
    )

    # -- data query --------------------------------------------------------
    # Collect which category columns we need to return
    requested_categories: set[str] = set()
    for f in body.filters:
        requested_categories.add(f.metric.split(".")[0])
    if body.sort_by:
        sb_parts = body.sort_by.split(".")
        if len(sb_parts) == 2:
            requested_categories.add(sb_parts[0])

    # Always return all categories for completeness
    cat_select = ", ".join(f"dm.{cat}" for cat in sorted(METRIC_CATEGORIES))

    params["offset"] = body.offset
    params["limit"] = body.limit

    data_sql = text(
        f"{latest_cte} "
        f"SELECT c.ticker, c.name, c.sector, c.industry, c.market_cap, "
        f"  dm.period_end, dm.fiscal_period, {cat_select} "
        f"FROM latest dm "
        f"JOIN companies c ON c.id = dm.company_id "
        f"{where_sql} "
        f"ORDER BY {order_expr} "
        f"OFFSET :offset LIMIT :limit"
    )

    try:
        total = db.execute(count_sql, params).scalar()
        rows = db.execute(data_sql, params).mappings().all()
    except Exception:
        logger.exception("Screener query failed")
        raise HTTPException(500, "Screener query failed — check filter syntax")

    results = []
    for r in rows:
        metrics: dict[str, Any] = {}
        for cat in sorted(METRIC_CATEGORIES):
            val = r.get(cat)
            if val is not None:
                if isinstance(val, dict):
                    for k, v in val.items():
                        metrics[k] = v
                else:
                    metrics[cat] = val

        # Include market_cap from the company record if available
        market_cap = r.get("market_cap")
        if market_cap is not None:
            metrics["market_cap"] = market_cap

        results.append({
            "ticker": r["ticker"],
            "name": r["name"],
            "sector": r["sector"],
            "industry": r["industry"],
            "period_end": str(r["period_end"]),
            "fiscal_period": r["fiscal_period"],
            "metrics": metrics,
        })

    return {
        "total": total,
        "offset": body.offset,
        "limit": body.limit,
        "data": results,
    }


# ---------------------------------------------------------------------------
# GET /screener/metrics  — available metric catalogue
# ---------------------------------------------------------------------------

# Static catalogue.  In a production system this would be auto-discovered from
# a sample row, but a curated list is more useful for frontend documentation.
METRIC_CATALOGUE: dict[str, list[str]] = {
    "profitability": [
        "gross_margin", "operating_margin", "net_margin", "ebitda_margin",
        "ebit_margin", "return_on_assets", "return_on_equity",
        "return_on_capital_employed", "return_on_invested_capital",
        "effective_tax_rate", "nopat", "invested_capital", "capital_employed",
        "rd_intensity", "sga_ratio", "sbc_pct_revenue",
    ],
    "liquidity": [
        "current_ratio", "quick_ratio", "cash_ratio",
        "net_working_capital", "nwc_pct_revenue",
        "days_inventory_outstanding", "days_sales_outstanding",
        "days_payable_outstanding", "cash_conversion_cycle",
        "defensive_interval",
    ],
    "leverage": [
        "total_debt", "net_debt", "debt_to_equity", "debt_to_assets",
        "debt_to_ebitda", "interest_coverage", "equity_multiplier",
        "debt_to_capital", "long_term_debt_to_equity",
        "financial_leverage_ratio",
    ],
    "efficiency": [
        "asset_turnover", "fixed_asset_turnover", "inventory_turnover",
        "receivables_turnover", "payables_turnover", "equity_turnover",
        "capital_expenditure_to_revenue", "capex_to_depreciation",
        "operating_cycle", "cash_cycle",
    ],
    "cashflow": [
        "free_cash_flow_to_firm", "free_cash_flow_to_firm_simplified",
        "free_cash_flow_to_equity", "net_borrowing",
        "operating_cash_flow_margin", "cash_flow_to_net_income",
        "capex_to_operating_cash_flow", "cash_return_on_invested_capital",
        "reinvestment_rate", "capex_to_depreciation", "nopat",
    ],
    "growth": [
        "revenue_growth", "gross_profit_growth", "operating_income_growth",
        "ebitda_growth", "net_income_growth", "eps_growth",
        "operating_cash_flow_growth", "free_cash_flow_growth",
        "total_assets_growth", "equity_growth", "dividend_growth",
        "sustainable_growth_rate", "is_acquisition_period",
        "acquisition_to_revenue", "reinvestment_rate_growth",
    ],
    "dupont": [
        "net_margin", "asset_turnover", "equity_multiplier", "roe_3factor",
        "tax_burden", "interest_burden", "operating_profit_margin",
        "roe_5factor", "tax_efficiency", "interest_efficiency",
    ],
    "valuation": [
        "market_cap", "enterprise_value", "pe_ratio", "price_to_book",
        "price_to_sales", "price_to_cash_flow", "ev_to_ebitda",
        "ev_to_ebit", "ev_to_revenue", "ev_to_fcf", "earnings_yield",
        "fcf_yield", "dividend_yield", "peg_ratio",
        "book_value_per_share", "tangible_book_value_per_share",
        "revenue_per_share", "graham_number",
    ],
    "quality": [
        "accruals_ratio", "sloan_ratio", "cash_flow_to_earnings",
        "earnings_quality_score", "revenue_vs_receivables_divergence",
        "net_income_vs_ocf_divergence", "capex_consistency",
        "organic_revenue_flag", "sga_efficiency", "depreciation_to_capex",
    ],
    "forensic": [
        "altman_z_score", "altman_z_components", "z_score_zone",
        "piotroski_f_score", "piotroski_signals", "piotroski_strength",
        "beneish_m_score", "beneish_components", "manipulation_risk",
        "risk_flags",
    ],
    "shareholder": [
        "payout_ratio", "dividend_payout_ratio", "retention_ratio",
        "buyback_ratio", "shareholder_yield", "total_capital_returned",
        "net_debt_paydown", "total_shareholder_return_allocation",
        "dividends_per_share", "buyback_per_share",
    ],
    "per_share": [
        "revenue_per_share", "gross_profit_per_share",
        "operating_income_per_share", "ebitda_per_share",
        "net_income_per_share", "book_value_per_share",
        "tangible_book_value_per_share", "operating_cash_flow_per_share",
        "free_cash_flow_per_share", "dividends_per_share",
        "total_debt_per_share", "net_debt_per_share", "cash_per_share",
    ],
}


@router.get("/metrics")
def available_metrics():
    """Return the full catalogue of filterable metrics organised by category."""
    return METRIC_CATALOGUE
