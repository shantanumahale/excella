"""Comparable companies (Comps) valuation model."""

from __future__ import annotations

import logging
from statistics import median

from sqlalchemy.orm import Session

from app.db.models import Company, DerivedMetrics

logger = logging.getLogger(__name__)

MIN_PEERS = 3

# Multiples used for comps analysis
COMP_MULTIPLES = ["pe_ratio", "ev_to_ebitda", "price_to_sales", "price_to_book", "ev_to_revenue"]


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def compute_comps(
    db: Session,
    company_id: int,
    sector: str | None,
    industry: str | None,
) -> dict | None:
    """Compute comparable company valuation.

    Finds peers by industry (then sector fallback), computes median multiples,
    and applies them to the target company's fundamentals.

    Returns:
        dict with peer_count, peers, multiples, implied_values, or None if insufficient data.
    """
    if not sector:
        return None

    target_company = db.query(Company).filter(Company.id == company_id).first()
    if not target_company:
        return None

    # Find peers: same industry first, fall back to sector
    peers = _find_peers(db, company_id, sector, industry)
    if not peers:
        return None

    # Load latest metrics for each peer
    peer_data = []
    for peer in peers:
        latest = (
            db.query(DerivedMetrics)
            .filter(DerivedMetrics.company_id == peer.id)
            .order_by(DerivedMetrics.period_end.desc())
            .first()
        )
        if latest and latest.valuation:
            peer_data.append({
                "ticker": peer.ticker,
                "name": peer.name,
                "multiples": {m: latest.valuation.get(m) for m in COMP_MULTIPLES},
            })

    if not peer_data:
        return None

    # Compute median multiples
    medians = {}
    for multiple in COMP_MULTIPLES:
        values = [
            p["multiples"][multiple]
            for p in peer_data
            if p["multiples"].get(multiple) is not None and p["multiples"][multiple] > 0
        ]
        medians[multiple] = round(median(values), 4) if values else None

    # Load target's latest metrics for implied value computation
    target_metrics = (
        db.query(DerivedMetrics)
        .filter(DerivedMetrics.company_id == company_id)
        .order_by(DerivedMetrics.period_end.desc())
        .first()
    )

    implied_values = {}
    if target_metrics:
        val = target_metrics.valuation or {}
        ps = target_metrics.per_share or {}
        cf = target_metrics.cashflow or {}

        shares = None
        if val.get("market_cap") and val.get("pe_ratio"):
            eps = _safe_div(val["market_cap"], val["pe_ratio"])
            if eps:
                shares = _safe_div(val["market_cap"], val.get("pe_ratio")) # market_cap / pe = earnings, earnings/eps = shares...
                # Actually: market_cap = price * shares, pe = price / eps -> price = pe * eps -> shares = market_cap / price
                # Simpler: use eps from per_share
                pass

        # P/E implied: median_PE * EPS
        eps = ps.get("net_income_per_share")
        if medians.get("pe_ratio") and eps and eps > 0:
            implied_values["pe_implied"] = round(medians["pe_ratio"] * eps, 2)

        # P/S implied: median_P/S * revenue_per_share
        rps = ps.get("revenue_per_share_ps")
        if medians.get("price_to_sales") and rps and rps > 0:
            implied_values["ps_implied"] = round(medians["price_to_sales"] * rps, 2)

        # P/B implied: median_P/B * book_value_per_share
        bvps = ps.get("book_value_per_share_ps")
        if medians.get("price_to_book") and bvps and bvps > 0:
            implied_values["pb_implied"] = round(medians["price_to_book"] * bvps, 2)

    return {
        "peer_count": len(peer_data),
        "peers": peer_data,
        "multiples": medians,
        "implied_values": implied_values,
    }


def _find_peers(
    db: Session,
    company_id: int,
    sector: str | None,
    industry: str | None,
) -> list[Company]:
    """Find peer companies, preferring industry match, falling back to sector."""
    # Try industry first
    if industry:
        peers = (
            db.query(Company)
            .filter(
                Company.industry == industry,
                Company.id != company_id,
            )
            .limit(20)
            .all()
        )
        if len(peers) >= MIN_PEERS:
            return peers

    # Fall back to sector
    if sector:
        peers = (
            db.query(Company)
            .filter(
                Company.sector == sector,
                Company.id != company_id,
            )
            .limit(20)
            .all()
        )
        return peers

    return []
