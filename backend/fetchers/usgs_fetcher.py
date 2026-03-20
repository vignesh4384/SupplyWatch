"""Fetch earthquake data from USGS GeoJSON feed."""

import logging
import hashlib
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"


async def fetch_usgs() -> tuple[list[dict], list[dict]]:
    """Fetch M4.5+ earthquakes from last 24h. Returns (alerts, zones)."""
    alerts = []
    zones = []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(USGS_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json()

        now = datetime.now(timezone.utc).isoformat()

        for i, feature in enumerate(data.get("features", [])[:10]):
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [0, 0, 0])

            mag = props.get("mag", 0)
            place = props.get("place", "Unknown location")
            time_ms = props.get("time", 0)
            title = props.get("title", f"M{mag} Earthquake")

            lng, lat = coords[0], coords[1]
            eq_id = f"usgs_{hashlib.md5(str(time_ms).encode()).hexdigest()[:8]}"

            # Score: M5=60, M6=72, M7=84, M8=96
            score = min(100, int(mag * 12))
            risk_level = "HIGH" if score >= 66 else "MEDIUM" if score >= 41 else "LOW"

            # Time formatting
            try:
                dt = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc)
                delta = datetime.now(timezone.utc) - dt
                hours = int(delta.total_seconds() / 3600)
                time_ago = f"{hours} hours ago" if hours >= 1 else "just now"
            except Exception:
                time_ago = "recently"

            # Create zone for all earthquakes
            zones.append({
                "id": eq_id,
                "name": f"M{mag} — {place}",
                "lat": lat,
                "lng": lng,
                "score": score,
                "risk_level": risk_level,
                "category": "disaster",
                "description": f"Magnitude {mag} earthquake near {place}. Depth: {coords[2]:.0f}km.",
                "updated_at": now,
            })

            # Create alerts for M5.5+
            if mag >= 5.5:
                severity = "critical" if mag >= 7.0 else "warning" if mag >= 6.0 else "info"
                alerts.append({
                    "id": eq_id,
                    "title": title[:200],
                    "severity": severity,
                    "source": "USGS",
                    "timestamp": time_ago,
                    "created_at": now,
                })

        logger.info(f"USGS: {len(alerts)} alerts, {len(zones)} zones from {len(data.get('features', []))} earthquakes")
    except Exception as e:
        logger.error(f"USGS fetch error: {e}")

    return alerts, zones
