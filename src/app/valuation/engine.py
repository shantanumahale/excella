"""Valuation engine orchestrator — assembles all valuation models."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import Company, DerivedMetrics, FinancialStatement
from app.valuation.beta import compute_beta
from app.valuation.comps import compute_comps
from app.valuation.dcf import compute_dcf, project_growth_rates
from app.valuation.ddm import compute_ddm
from app.valuation.residual_income import compute_residual_income
from app.valuation.wacc import (
    compute_capital_weights,
    compute_wacc,
    load_risk_free_rate,
    DEFAULT_EQUITY_RISK_PREMIUM,
)

logger = logging.getLogger(__name__)

DEFAULT_TERMINAL_GROWTH = 0.025
DEFAULT_PROJECTION_YEARS = 5


def run_valuation(
    db: Session,
    company_id: int,
    overrides: dict | None = None,
) -> dict:
    """Run full valuation with optional user overrides.

    Args:
        db: Database session.
        company_id: Target company ID.
        overrides: Optional dict to override default assumptions (growth_rate,
                   terminal_growth, wacc, projection_years, terminal_method, exit_multiple).

    Returns:
        dict with all model outputs, assumptions, and summary.
    """
    overrides = overrides or {}

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return {"error": "Company not found"}

    # Load latest derived metrics
    latest_metrics = (
        db.query(DerivedMetrics)
        .filter(DerivedMetrics.company_id == company_id)
        .order_by(DerivedMetrics.period_end.desc())
        .first()
    )

    if not latest_metrics:
        return {"error": "No metrics available"}

    val = latest_metrics.valuation or {}
    cf = latest_metrics.cashflow or {}
    prof = latest_metrics.profitability or {}
    lev = latest_metrics.leverage or {}
    growth = latest_metrics.growth or {}
    ps = latest_metrics.per_share or {}
    sh = latest_metrics.shareholder or {}

    result: dict = {"ticker": company.ticker, "models": {}}

    # ── Beta ──────────────────────────────────────────────────────────────
    beta_result = None
    try:
        beta_result = compute_beta(db, company.ticker)
        result["beta"] = beta_result
    except Exception:
        logger.exception("Beta computation failed for %s", company.ticker)
        result["beta"] = {"beta": 1.0, "is_fallback": True}

    beta_value = beta_result["beta"] if beta_result else 1.0

    # ── Risk-free rate ────────────────────────────────────────────────────
    risk_free_rate = overrides.get("risk_free_rate") or load_risk_free_rate(db)
    result["risk_free_rate"] = risk_free_rate

    # ── Capital structure ─────────────────────────────────────────────────
    market_cap = val.get("market_cap")
    total_debt = lev.get("total_debt")
    net_debt = lev.get("net_debt")
    debt_weight, equity_weight = compute_capital_weights(market_cap, total_debt)

    # Cost of debt: prefer interest_expense / total_debt from financials,
    # fall back to risk_free + 2% spread
    cost_of_debt = _compute_cost_of_debt(db, company_id, total_debt, risk_free_rate)

    # Effective tax rate
    tax_rate = prof.get("effective_tax_rate")

    # ── WACC ──────────────────────────────────────────────────────────────
    wacc_result = None
    try:
        wacc_override = overrides.get("wacc")
        if wacc_override:
            wacc_value = wacc_override
            wacc_result = {"wacc": wacc_value, "overridden": True}
        else:
            wacc_result = compute_wacc(
                beta=beta_value,
                risk_free_rate=risk_free_rate,
                erp=DEFAULT_EQUITY_RISK_PREMIUM,
                cost_of_debt=cost_of_debt,
                tax_rate=tax_rate,
                debt_weight=debt_weight,
                equity_weight=equity_weight,
            )
            wacc_value = wacc_result["wacc"]
        result["wacc"] = wacc_result
    except Exception:
        logger.exception("WACC computation failed for %s", company.ticker)
        wacc_value = 0.10  # fallback
        result["wacc"] = {"wacc": wacc_value, "is_fallback": True}

    # ── Shared assumptions ────────────────────────────────────────────────
    terminal_growth = overrides.get("terminal_growth", DEFAULT_TERMINAL_GROWTH)
    projection_years = overrides.get("projection_years", DEFAULT_PROJECTION_YEARS)
    terminal_method = overrides.get("terminal_method", "perpetuity")
    exit_multiple = overrides.get("exit_multiple")

    # Shares outstanding: read directly from latest income statement,
    # fall back to revenue / revenue_per_share derivation
    shares = _load_shares_outstanding(db, company_id, ps)

    # ── DCF ───────────────────────────────────────────────────────────────
    try:
        fcff = cf.get("free_cash_flow_to_firm") or cf.get("free_cash_flow_to_firm_simplified")
        historical_growth = growth.get("revenue_growth")
        growth_rates = project_growth_rates(
            overrides.get("growth_rate", historical_growth),
            terminal_growth,
            projection_years,
        )

        dcf_result = compute_dcf(
            fcff_current=fcff,
            growth_rates=growth_rates,
            wacc=wacc_value,
            terminal_growth=terminal_growth,
            shares_outstanding=shares,
            net_debt=net_debt,
            method=terminal_method,
            exit_multiple=exit_multiple,
        )
        result["models"]["dcf"] = dcf_result
    except Exception:
        logger.exception("DCF failed for %s", company.ticker)
        result["models"]["dcf"] = None

    # ── DDM ───────────────────────────────────────────────────────────────
    try:
        dps = sh.get("dividends_per_share") or ps.get("dividends_per_share_ps")
        cost_of_equity = wacc_result.get("cost_of_equity", wacc_value) if wacc_result else wacc_value
        div_growth = growth.get("dividend_growth")

        ddm_result = compute_ddm(
            dps=dps,
            cost_of_equity=cost_of_equity,
            growth_rate=overrides.get("dividend_growth", div_growth or terminal_growth),
        )
        result["models"]["ddm"] = ddm_result
    except Exception:
        logger.exception("DDM failed for %s", company.ticker)
        result["models"]["ddm"] = None

    # ── Comps ─────────────────────────────────────────────────────────────
    try:
        comps_result = compute_comps(
            db=db,
            company_id=company_id,
            sector=company.sector,
            industry=company.industry,
        )
        result["models"]["comps"] = comps_result
    except Exception:
        logger.exception("Comps failed for %s", company.ticker)
        result["models"]["comps"] = None

    # ── Residual Income ───────────────────────────────────────────────────
    try:
        bvps = ps.get("book_value_per_share_ps")
        roe = prof.get("return_on_equity")
        cost_of_equity = wacc_result.get("cost_of_equity", wacc_value) if wacc_result else wacc_value
        retention = sh.get("retention_ratio")

        ri_result = compute_residual_income(
            bvps=bvps,
            roe=roe,
            cost_of_equity=cost_of_equity,
            growth_rate=terminal_growth,
            years=projection_years,
            retention_ratio=retention,
        )
        result["models"]["residual_income"] = ri_result
    except Exception:
        logger.exception("Residual Income failed for %s", company.ticker)
        result["models"]["residual_income"] = None

    # ── Current price (for margin of safety) ─────────────────────────────
    current_price = _load_latest_price(db, company.ticker)
    result["current_price"] = current_price

    # ── Summary ───────────────────────────────────────────────────────────
    result["summary"] = _build_summary(result["models"], current_price)

    return result


def precompute_valuation(db: Session, company_id: int) -> dict:
    """Pipeline version — compute valuation with all defaults, no overrides."""
    return run_valuation(db, company_id)


def _build_summary(models: dict, current_price: float | None) -> dict:
    """Build consensus summary from all model outputs."""
    intrinsic_values = []

    for model_name, model_result in models.items():
        if model_result and isinstance(model_result, dict):
            iv = model_result.get("intrinsic_value_per_share")
            if iv is not None and iv > 0:
                intrinsic_values.append({"model": model_name, "value": iv})

    if not intrinsic_values:
        return {"consensus_value": None, "margin_of_safety": None, "model_count": 0}

    # Consensus = median of all model outputs
    values = sorted(v["value"] for v in intrinsic_values)
    n = len(values)
    if n % 2 == 0:
        consensus = (values[n // 2 - 1] + values[n // 2]) / 2
    else:
        consensus = values[n // 2]

    # Margin of safety: (intrinsic - price) / price
    margin_of_safety = None
    if current_price and current_price > 0:
        margin_of_safety = round((consensus - current_price) / current_price, 4)

    return {
        "consensus_value": round(consensus, 2),
        "margin_of_safety": margin_of_safety,
        "model_count": len(intrinsic_values),
        "model_values": intrinsic_values,
        "range_low": round(min(v["value"] for v in intrinsic_values), 2),
        "range_high": round(max(v["value"] for v in intrinsic_values), 2),
    }


# ---------------------------------------------------------------------------
# Data-loading helpers
# ---------------------------------------------------------------------------

def _load_latest_price(db: Session, ticker: str) -> float | None:
    """Load the most recent adj_close from the daily_prices hypertable."""
    try:
        result = db.execute(
            text(
                "SELECT adj_close FROM daily_prices "
                "WHERE ticker = :ticker "
                "ORDER BY time DESC LIMIT 1"
            ),
            {"ticker": ticker},
        ).fetchone()
        if result and result[0] is not None:
            return float(result[0])
    except Exception:
        logger.debug("Could not load price for %s", ticker, exc_info=True)
    return None


def _load_shares_outstanding(
    db: Session, company_id: int, per_share: dict,
) -> float | None:
    """Load diluted shares from the latest income statement.

    Falls back to deriving shares from revenue / revenue_per_share.
    """
    # Primary: read shares_diluted directly from the latest income statement
    try:
        stmt = (
            db.query(FinancialStatement)
            .filter(
                FinancialStatement.company_id == company_id,
                FinancialStatement.statement_type == "income",
                FinancialStatement.is_valid.is_(True),
            )
            .order_by(FinancialStatement.period_end.desc())
            .first()
        )
        if stmt and stmt.data:
            shares = stmt.data.get("shares_diluted") or stmt.data.get("shares_basic")
            if shares and shares > 0:
                return float(shares)
    except Exception:
        logger.debug("Could not load shares from income statement", exc_info=True)

    # Fallback: revenue / revenue_per_share
    rps = per_share.get("revenue_per_share_ps")
    if rps and rps > 0:
        # We need total revenue — look in income statement data
        try:
            stmt = (
                db.query(FinancialStatement)
                .filter(
                    FinancialStatement.company_id == company_id,
                    FinancialStatement.statement_type == "income",
                    FinancialStatement.is_valid.is_(True),
                )
                .order_by(FinancialStatement.period_end.desc())
                .first()
            )
            if stmt and stmt.data:
                revenue = stmt.data.get("revenue")
                if revenue and revenue > 0:
                    return revenue / rps
        except Exception:
            logger.debug("Could not derive shares from revenue/rps", exc_info=True)

    return None


def _compute_cost_of_debt(
    db: Session,
    company_id: int,
    total_debt: float | None,
    risk_free_rate: float,
) -> float | None:
    """Compute cost of debt from interest_expense / total_debt.

    Falls back to risk_free_rate + 2% spread if data is unavailable.
    """
    if total_debt and total_debt > 0:
        try:
            stmt = (
                db.query(FinancialStatement)
                .filter(
                    FinancialStatement.company_id == company_id,
                    FinancialStatement.statement_type == "income",
                    FinancialStatement.is_valid.is_(True),
                )
                .order_by(FinancialStatement.period_end.desc())
                .first()
            )
            if stmt and stmt.data:
                interest_expense = stmt.data.get("interest_expense")
                if interest_expense and interest_expense > 0:
                    cost = interest_expense / total_debt
                    # Sanity check: cost of debt should be between 0% and 30%
                    if 0 < cost < 0.30:
                        return cost
        except Exception:
            logger.debug("Could not compute cost of debt from financials", exc_info=True)

    # Fallback: risk-free + 200bp credit spread
    return risk_free_rate + 0.02
