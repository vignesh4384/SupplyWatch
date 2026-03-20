"""Fetch natural events from NASA EONET API — wildfires, volcanoes, storms, floods, sea ice."""

import os
import logging
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx

load_dotenv()
logger = logging.getLogger(__name__)

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

# EONET category IDs → SupplyWatch risk mapping
CATEGORY_CONFIG = {
    "wildfires": {"label": "Wildfire", "base_score": 55, "severity_boost": 15},
    "volcanoes": {"label": "Volcanic Eruption", "base_score": 70, "severity_boost": 20},
    "severeStorms": {"label": "Severe Storm", "base_score": 65, "severity_boost": 15},
    "floods": {"label": "Flood", "base_score": 60, "severity_boost": 10},
    "seaLakeIce": {"label": "Sea Ice Event", "base_score": 40, "severity_boost": 10},
    "earthquakes": {"label": "Earthquake", "base_score": 65, "severity_boost": 20},
    "landslides": {"label": "Landslide", "base_score": 50, "severity_boost": 15},
    "drought": {"label": "Drought", "base_score": 45, "severity_boost": 10},
}

# Regions near major shipping lanes/ports get higher scores
SUPPLY_CHAIN_HOTSPOTS = [
    {"name": "Suez/Red Sea", "lat": 28, "lng": 35, "radius": 15, "boost": 20},
    {"name": "Strait of Malacca", "lat": 2, "lng": 102, "radius": 10, "boost": 15},
    {"name": "Panama Canal", "lat": 9, "lng": -80, "radius": 8, "boost": 20},
    {"name": "Gulf of Mexico", "lat": 25, "lng": -90, "radius": 12, "boost": 15},
    {"name": "South China Sea", "lat": 15, "lng": 115, "radius": 12, "boost": 15},
    {"name": "Bay of Bengal", "lat": 15, "lng": 88, "radius": 10, "boost": 10},
    {"name": "Mediterranean", "lat": 36, "lng": 18, "radius": 12, "boost": 10},
    {"name": "North Sea", "lat": 56, "lng": 3, "radius": 8, "boost": 10},
]


def proximity_boost(lat: float, lng: float) -> int:
    """Check if event is near a supply chain hotspot and return score boost."""
    for hotspot in SUPPLY_CHAIN_HOTSPOTS:
        dist = abs(lat - hotspot["lat"]) + abs(lng - hotspot["lng"])
        if dist < hotspot["radius"]:
            return hotspot["boost"]
    return 0


async def fetch_nasa_eonet() -> tuple[list[dict], list[dict]]:
    """Fetch active natural events from NASA EONET. Returns (alerts, zones)."""
    alerts = []
    zones = []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(EONET_URL, params={
                "status": "open",
                "limit": 20,
                "api_key": NASA_API_KEY,
            }, timeout=20)
            resp.raise_for_status()
            data = resp.json()

        now = datetime.now(timezone.utc).isoformat()

        for event in data.get("events", []):
            title = event.get("title", "Unknown Event")
            event_id = event.get("id", "")
            categories = event.get("categories", [])
            geometries = event.get("geometries", [])

            if not geometries:
                continue

            # Get category
            cat_id = categories[0].get("id", "other") if categories else "other"
            cat_config = CATEGORY_CONFIG.get(cat_id, {"label": cat_id, "base_score": 45, "severity_boost": 10})

            # Get latest coordinates
            latest_geom = geometries[-1]
            coords = latest_geom.get("coordinates", [])

            if not coords:
                continue

            # EONET uses [lng, lat] format
            if isinstance(coords[0], list):
                # Polygon — use first point
                lng, lat = coords[0][0], coords[0][1]
            else:
                lng, lat = coords[0], coords[1]

            # Calculate risk score
            base_score = cat_config["base_score"]
            sc_boost = proximity_boost(lat, lng)
            score = min(100, base_score + sc_boost)
            risk_level = "HIGH" if score >= 66 else "MEDIUM" if score >= 41 else "LOW"

            # Determine severity for alert
            if score >= 70:
                severity = "critical"
            elif score >= 50:
                severity = "warning"
            else:
                severity = "info"

            zone_id = f"nasa_{hashlib.md5(event_id.encode()).hexdigest()[:8]}"

            # Time formatting
            geom_date = latest_geom.get("date", "")
            time_ago = format_nasa_date(geom_date)

            # Create zone
            zones.append({
                "id": zone_id,
                "name": f"{cat_config['label']} — {title[:60]}",
                "lat": lat,
                "lng": lng,
                "score": score,
                "risk_level": risk_level,
                "category": "disaster",
                "description": f"NASA EONET: {title}. Category: {cat_config['label']}. "
                              f"{'Near major shipping lane. ' if sc_boost > 0 else ''}"
                              f"Risk score: {score}/100.",
                "updated_at": now,
            })

            # Create alert for significant events (score >= 55)
            if score >= 55:
                alerts.append({
                    "id": zone_id,
                    "title": f"{cat_config['label']}: {title[:150]}",
                    "severity": severity,
                    "source": "NASA",
                    "timestamp": time_ago,
                    "created_at": now,
                })

        logger.info(f"NASA EONET: {len(alerts)} alerts, {len(zones)} zones from {len(data.get('events', []))} events")

    except Exception as e:
        logger.error(f"NASA EONET fetch error: {e}")

    return alerts, zones


def format_nasa_date(iso_str: str) -> str:
    """Convert ISO date to relative time."""
    if not iso_str:
        return "recently"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        hours = int(delta.total_seconds() / 3600)
        if hours < 1:
            return "just now"
        elif hours < 24:
            return f"{hours} hours ago"
        else:
            days = hours // 24
            return f"{days} day{'s' if days > 1 else ''} ago"
    except Exception:
        return "recently"
