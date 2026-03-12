from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import engine, create_tables
from app.api.router import api_router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Excella",
    version="0.1.0",
    description=(
        "Financial data platform and equity screener. "
        "Ingests fundamentals (SEC EDGAR), macroeconomic data (FRED), "
        "and pricing data (yFinance), then computes 100+ derived metrics "
        "for screening and analysis."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "companies", "description": "Company listing and detail"},
        {"name": "financials", "description": "Financial statements and derived metrics"},
        {"name": "prices", "description": "Daily OHLCV prices and returns"},
        {"name": "macro", "description": "FRED macroeconomic series and observations"},
        {"name": "screener", "description": "Dynamic screening with 100+ financial metrics"},
        {"name": "system", "description": "Health checks and ingestion status"},
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    logger.info("Creating database tables ...")
    create_tables()
    logger.info("Excella API ready")


@app.on_event("shutdown")
async def shutdown():
    engine.dispose()
