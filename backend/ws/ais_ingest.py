"""AISstream WebSocket client — connects, filters, stores, and broadcasts vessel positions."""

import asyncio
import json
import logging
from datetime import datetime, timezone

import websockets

# Lazy import: global-land-mask + numpy are optional — if unavailable,
# the land filter is skipped but the rest of the app works fine.
try:
    from global_land_mask import globe
    _HAS_LAND_MASK = True
except ImportError:
    _HAS_LAND_MASK = False

import database
from config import (
    AISSTREAM_API_KEY,
    AIS_BOUNDING_BOXES,
    AIS_VESSEL_TYPE_WHITELIST,
    NAV_STATUS_LABELS,
    get_ship_type_label,
)

logger = logging.getLogger(__name__)

# Shared broadcast queue set — WebSocket relay route adds/removes subscriber queues
broadcast_subscribers: set[asyncio.Queue] = set()

# In-memory cache: MMSI → {ship_type, ship_type_label, name} — avoids DB hit per message
_type_cache: dict[str, dict] = {}

# Connection state
_running = False
_task: asyncio.Task | None = None


def _build_subscription_message() -> str:
    """Build the AISstream subscription message with bounding boxes."""
    bboxes = []
    for zone_cfg in AIS_BOUNDING_BOXES.values():
        sw = zone_cfg["sw"]
        ne = zone_cfg["ne"]
        bboxes.append([sw, ne])

    return json.dumps({
        "APIKey": AISSTREAM_API_KEY,
        "BoundingBoxes": bboxes,
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
    })


def _assign_zone(lat: float, lng: float) -> str | None:
    """Assign the most specific (highest priority) matching zone."""
    matches = []
    for zone_id, cfg in AIS_BOUNDING_BOXES.items():
        sw_lat, sw_lng = cfg["sw"]
        ne_lat, ne_lng = cfg["ne"]
        if sw_lat <= lat <= ne_lat and sw_lng <= lng <= ne_lng:
            matches.append((cfg["priority"], zone_id))

    if not matches:
        return None
    matches.sort()
    return matches[0][1]


def _is_deep_inland(lat: float, lng: float, offset: float = 0.15) -> bool:
    """Return True only if the point AND all surrounding points are on land.

    Uses a ~15 km coastal buffer so vessels in ports, harbors, narrow
    straits, and coastal waters are not rejected.  Only positions where
    every neighbour is also land (i.e. clearly deep inland) are filtered.
    """
    if not _HAS_LAND_MASK:
        return False  # Library not available — skip filtering

    if not globe.is_land(lat, lng):
        return False  # Already in water — no filtering needed

    # Check 4 cardinal neighbours at ~15 km offset
    for dlat, dlng in [(offset, 0), (-offset, 0), (0, offset), (0, -offset)]:
        if not globe.is_land(lat + dlat, lng + dlng):
            return False  # Near a coastline — allow it
    return True  # All neighbours are land — deep inland


def _is_dark_vessel(speed: float | None, nav_status: int | None) -> bool:
    """Detect dark/suspicious vessel: moving slowly but claiming underway status."""
    if speed is None or nav_status is None:
        return False
    # Speed < 1.5 kts and nav_status = 0 (under way using engine) in open water
    return speed < 1.5 and nav_status == 0


def _parse_position_report(msg: dict) -> dict | None:
    """Parse an AISstream PositionReport message into a vessel position dict."""
    meta = msg.get("MetaData", {})
    position = msg.get("Message", {}).get("PositionReport", {})

    if not position or not meta:
        return None

    ship_type = meta.get("ShipType", 0)

    mmsi = str(meta.get("MMSI", ""))
    if not mmsi:
        return None

    # If type is unknown, try resolving from in-memory cache or persistent registry
    if ship_type <= 0:
        cached = _type_cache.get(mmsi)
        if not cached:
            cached = database.lookup_vessel_registry(mmsi)
            if cached:
                _type_cache[mmsi] = cached
        if cached and cached["ship_type"] > 0:
            ship_type = cached["ship_type"]

    # Only reject if ship type IS known and NOT in whitelist.
    if ship_type > 0 and ship_type not in AIS_VESSEL_TYPE_WHITELIST:
        return None

    lat = position.get("Latitude")
    lng = position.get("Longitude")
    if lat is None or lng is None:
        return None

    # Reject positions deep inland — check if ALL nearby points are also land
    # (allows coastal/port vessels through, only blocks clearly-inland positions)
    if _is_deep_inland(lat, lng):
        return None

    speed = position.get("Sog")  # Speed over ground
    heading = position.get("Cog")  # Course over ground
    nav_status = position.get("NavigationalStatus")

    zone = _assign_zone(lat, lng)
    if zone is None:
        return None  # Outside all watch zones

    ship_type_label = get_ship_type_label(ship_type)
    is_dark = 1 if _is_dark_vessel(speed, nav_status) else 0

    timestamp = meta.get("time_utc", datetime.now(timezone.utc).isoformat())
    # Normalize timestamp to ISO 8601
    if isinstance(timestamp, str) and "T" not in timestamp:
        timestamp = timestamp.replace(" ", "T")
    if not timestamp.endswith("Z") and "+" not in timestamp:
        timestamp = timestamp + "Z"

    name = (meta.get("ShipName") or "").strip() or None
    if not name and mmsi in _type_cache:
        name = _type_cache[mmsi].get("name")

    return {
        "mmsi": mmsi,
        "name": name,
        "ship_type": ship_type,
        "ship_type_label": ship_type_label,
        "lat": lat,
        "lng": lng,
        "speed": speed,
        "heading": heading,
        "nav_status": nav_status,
        "zone": zone,
        "is_dark": is_dark,
        "recorded_at": timestamp,
    }


def _handle_static_data(msg: dict) -> None:
    """Handle ShipStaticData (AIS message type 5) to update vessel type info."""
    meta = msg.get("MetaData", {})
    static = msg.get("Message", {}).get("ShipStaticData", {})
    if not static or not meta:
        return

    mmsi = str(meta.get("MMSI", ""))
    if not mmsi:
        return

    ship_type = static.get("Type", 0)
    if ship_type <= 0:
        return

    ship_type_label = get_ship_type_label(ship_type)
    name = (static.get("Name") or meta.get("ShipName") or "").strip() or None

    # Update all recent positions for this MMSI with the correct ship type
    with database.get_db() as db:
        db.execute("""
            UPDATE vessel_positions
            SET ship_type = ?, ship_type_label = ?, name = COALESCE(?, name)
            WHERE mmsi = ? AND (ship_type <= 0 OR ship_type IS NULL)
        """, (ship_type, ship_type_label, name, mmsi))

    # Persist to vessel registry and update in-memory cache
    database.upsert_vessel_registry(mmsi, ship_type, ship_type_label, name, source="ais")
    _type_cache[mmsi] = {"ship_type": ship_type, "ship_type_label": ship_type_label, "name": name}

    logger.debug("AISstream: static data for MMSI %s → type=%d (%s) name=%s", mmsi, ship_type, ship_type_label, name)


def _to_geojson_feature(pos: dict) -> dict:
    """Convert a vessel position dict to a GeoJSON Feature."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [pos["lng"], pos["lat"]],  # GeoJSON: lng first
        },
        "properties": {
            "mmsi": pos["mmsi"],
            "name": pos["name"] or "Unknown",
            "ship_type": pos["ship_type"],
            "ship_type_label": pos["ship_type_label"],
            "speed": pos["speed"],
            "heading": pos["heading"],
            "nav_status": pos["nav_status"],
            "nav_status_label": NAV_STATUS_LABELS.get(pos["nav_status"], "Unknown"),
            "zone": pos["zone"],
            "is_dark": bool(pos["is_dark"]),
            "recorded_at": pos["recorded_at"],
        },
    }


async def _broadcast(feature: dict):
    """Send a GeoJSON feature to all connected WebSocket subscribers."""
    dead = set()
    for queue in broadcast_subscribers:
        try:
            queue.put_nowait(feature)
        except asyncio.QueueFull:
            dead.add(queue)
    if dead:
        logger.warning("Dropping %d slow WebSocket client(s) (queue full, max=500)", len(dead))
    broadcast_subscribers.difference_update(dead)


async def _connect_and_stream():
    """Main AISstream connection loop with auto-reconnect."""
    backoff = [5, 10, 30, 60]
    attempt = 0
    uri = "wss://stream.aisstream.io/v0/stream"

    while _running:
        try:
            logger.info("AISstream: connecting to %s", uri)
            async with websockets.connect(uri, ping_interval=30, ping_timeout=10) as ws:
                # Send subscription
                sub_msg = _build_subscription_message()
                await ws.send(sub_msg)
                logger.info("AISstream: connected and subscribed to %d bounding boxes", len(AIS_BOUNDING_BOXES))
                attempt = 0  # Reset backoff on successful connection

                async for raw in ws:
                    if not _running:
                        break
                    try:
                        msg = json.loads(raw)
                        msg_type = msg.get("MessageType", "")

                        if msg_type == "PositionReport":
                            pos = _parse_position_report(msg)
                            if pos:
                                database.insert_vessel_position(pos)
                                feature = _to_geojson_feature(pos)
                                await _broadcast(feature)
                        elif msg_type == "ShipStaticData":
                            _handle_static_data(msg)
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.warning("AISstream: error processing message: %s", e)

        except asyncio.CancelledError:
            logger.info("AISstream: task cancelled")
            return
        except Exception as e:
            if not _running:
                return
            delay = backoff[min(attempt, len(backoff) - 1)]
            logger.warning("AISstream: disconnected (%s), reconnecting in %ds", e, delay)
            attempt += 1
            await asyncio.sleep(delay)


async def start():
    """Start the AISstream ingestion as a background task."""
    global _running, _task

    if not AISSTREAM_API_KEY:
        logger.warning("AISstream: AISSTREAM_API_KEY not set, vessel tracking disabled")
        return

    _running = True
    _task = asyncio.create_task(_connect_and_stream())
    logger.info("AISstream: ingestion task started")


async def stop():
    """Stop the AISstream ingestion."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
    logger.info("AISstream: ingestion stopped")


def get_status() -> dict:
    """Return current AIS ingestion status for health checks."""
    return {
        "running": _running,
        "taskAlive": _task is not None and not _task.done(),
        "subscriberCount": len(broadcast_subscribers),
        "typeCacheSize": len(_type_cache),
    }
