"""Central API router — mounts all route groups."""

from __future__ import annotations

from fastapi import APIRouter

from app.api import auth, companies, filings, financials, macro, prices, screener, system, watchlists

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(companies.router)
api_router.include_router(filings.router)
api_router.include_router(financials.router)
api_router.include_router(prices.router)
api_router.include_router(macro.router)
api_router.include_router(screener.router)
api_router.include_router(watchlists.router)
api_router.include_router(system.router)
