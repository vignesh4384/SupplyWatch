"""SupplyWatch FastAPI Backend — Supply Chain Risk Management API."""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import database
from routers.risk import router as risk_router
from routers.vessels import router as vessels_router
from routers.ai_assistant import router as ai_assistant_router
from scheduler import start_scheduler, refresh_all_data
from ws.ais_ingest import broadcast_subscribers, start as start_ais, stop as stop_ais

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

    # Start AISstream vessel ingestion
    await start_ais()

    # Background cleanup: remove old on-land vessel positions (non-blocking)
    async def _land_cleanup():
        try:
            removed = database.cleanup_land_positions()
            if removed:
                logger.info("Background: purged %d on-land vessel positions", removed)
        except Exception as e:
            logger.warning("Land cleanup skipped: %s", e)
    asyncio.create_task(_land_cleanup())

    yield

    # Stop AISstream on shutdown
    await stop_ais()
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
app.include_router(vessels_router)
app.include_router(ai_assistant_router)


# WebSocket relay — pushes live vessel positions to Leaflet clients
logger = logging.getLogger(__name__)

@app.websocket("/ws/vessels/live")
async def vessel_live_feed(websocket: WebSocket):
    """Stream live vessel GeoJSON features to connected map clients."""
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=500)
    broadcast_subscribers.add(queue)
    client_id = id(queue)
    logger.info("WS client %s connected (total: %d)", client_id, len(broadcast_subscribers))
    try:
        while True:
            try:
                feature = await asyncio.wait_for(queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                # Keepalive ping — also detects dead connections
                await websocket.send_json({"type": "ping"})
                continue
            await websocket.send_json(feature)
    except WebSocketDisconnect:
        logger.info("WS client %s disconnected normally", client_id)
    except Exception as e:
        logger.warning("WS client %s error: %s", client_id, e)
    finally:
        broadcast_subscribers.discard(queue)
        logger.info("WS client %s removed (remaining: %d)", client_id, len(broadcast_subscribers))


# Manual refresh endpoint
@app.post("/api/refresh")
async def manual_refresh():
    """Trigger an immediate data refresh cycle."""
    asyncio.create_task(refresh_all_data())
    return {"status": "refresh_started"}
