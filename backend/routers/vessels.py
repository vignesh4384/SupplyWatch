"""Vessel tracking REST API endpoints — AIS-derived data for dashboard and AI assistant."""

from fastapi import APIRouter, Query

import database

router = APIRouter(prefix="/api/v1/vessels", tags=["Vessels"])


@router.get("/live")
async def get_live_vessels(minutes: int = Query(15, ge=1, le=60)):
    """GeoJSON FeatureCollection — latest position per MMSI within time window."""
    vessels = database.get_live_vessels(minutes=minutes)
    features = []
    for v in vessels:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [v["lng"], v["lat"]]},
            "properties": {
                "mmsi": v["mmsi"],
                "name": v["name"] or "Unknown",
                "ship_type": v["ship_type"],
                "ship_type_label": v["ship_type_label"],
                "speed": v["speed"],
                "heading": v["heading"],
                "nav_status": v["nav_status"],
                "nav_status_label": database.NAV_STATUS_LABELS.get(v["nav_status"], "Unknown"),
                "zone": v["zone"],
                "is_dark": bool(v["is_dark"]),
                "recorded_at": v["recorded_at"],
            },
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/zone/{zone}")
async def get_vessels_in_zone(
    zone: str,
    hours: int = Query(24, ge=1, le=168),
):
    """All vessel positions in a zone for the last N hours."""
    vessels = database.get_vessels_by_zone(zone=zone, hours=hours)
    return {"zone": zone, "hours": hours, "count": len(vessels), "positions": vessels}


@router.get("/dark")
async def get_dark_vessels(
    zone: str | None = Query(None),
    hours: int = Query(6, ge=1, le=48),
):
    """Vessels flagged as dark/suspicious."""
    vessels = database.get_dark_vessels(zone=zone, hours=hours)
    return {"zone": zone or "all", "hours": hours, "count": len(vessels), "vessels": vessels}


@router.get("/slow")
async def get_slow_vessels(
    zone: str | None = Query(None),
    max_speed: float = Query(2.0, ge=0, le=10),
    hours: int = Query(6, ge=1, le=48),
):
    """Vessels moving below a speed threshold."""
    vessels = database.get_slow_vessels(zone=zone, max_speed=max_speed, hours=hours)
    return {"zone": zone or "all", "max_speed": max_speed, "hours": hours, "count": len(vessels), "vessels": vessels}


@router.get("/count")
async def get_vessel_counts(
    zone: str | None = Query(None),
    hours: int = Query(24, ge=1, le=168),
):
    """Vessel counts grouped by zone and ship type."""
    counts = database.get_vessel_counts(zone=zone, hours=hours)
    total = sum(c["vessel_count"] for c in counts)
    return {"zone": zone or "all", "hours": hours, "total": total, "breakdown": counts}


@router.get("/history/{mmsi}")
async def get_vessel_history(
    mmsi: str,
    hours: int = Query(24, ge=1, le=168),
):
    """Position trail for one vessel."""
    positions = database.get_vessel_history(mmsi=mmsi, hours=hours)
    return {
        "mmsi": mmsi,
        "hours": hours,
        "count": len(positions),
        "track": positions,
    }


@router.get("/risk-score")
async def get_vessel_risk_score(zone: str = Query(...)):
    """Composite vessel-derived risk score for a zone (0-100)."""
    return database.get_vessel_risk_score(zone=zone)
