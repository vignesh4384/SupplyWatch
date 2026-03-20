"""SupplyWatch FastAPI Backend — Supply Chain Risk Management API."""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from routers.risk import router as risk_router
from scheduler import start_scheduler, refresh_all_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, start scheduler, trigger first fetch."""
    logger.info("SupplyWatch API starting up...")
    database.init_db()
    start_scheduler()

    # Trigger first data fetch in background (don't block startup)
    asyncio.create_task(refresh_all_data())
    logger.info("Initial data fetch triggered in background")

    yield

    logger.info("SupplyWatch API shutting down...")


app = FastAPI(
    title="SupplyWatch API",
    description="Global Supply Chain Risk Management Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server + Azure gateway
import os
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5174,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(risk_router)


# Manual refresh endpoint
@app.post("/api/refresh")
async def manual_refresh():
    """Trigger an immediate data refresh cycle."""
    asyncio.create_task(refresh_all_data())
    return {"status": "refresh_started"}
