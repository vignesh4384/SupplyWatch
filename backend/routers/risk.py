"""API routes for SupplyWatch — all responses use camelCase to match frontend TypeScript interfaces."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import database
from engine.aggregator import compute_all
from services.ai_analyst import ask_analyst

router = APIRouter(prefix="/api")


def to_camel(d: dict, mappings: dict | None = None) -> dict:
    """Convert snake_case dict keys to camelCase for frontend compatibility."""
    if mappings is None:
        mappings = {
            "overall_score": "overallScore",
            "high_count": "highCount",
            "medium_count": "mediumCount",
            "low_count": "lowCount",
            "indicator_high_count": "indicatorHighCount",
            "indicator_medium_count": "indicatorMediumCount",
            "indicator_low_count": "indicatorLowCount",
            "zone_high_count": "zoneHighCount",
            "zone_medium_count": "zoneMediumCount",
            "zone_low_count": "zoneLowCount",
            "last_updated": "lastUpdated",
            "risk_level": "riskLevel",
            "risk_score": "riskScore",
            "fetched_at": "fetchedAt",
            "created_at": "createdAt",
            "updated_at": "updatedAt",
        }
    return {mappings.get(k, k): v for k, v in d.items()}


@router.get("/risk/summary")
async def get_summary():
    raw = database.get_summary()
    return to_camel(raw)


@router.get("/risk/indicators")
async def get_indicators():
    rows = database.get_indicators()
    result = []
    for r in rows:
        item = to_camel(r)
        # Remove internal fields not needed by frontend
        item.pop("fetchedAt", None)
        item.pop("riskScore", None)
        result.append(item)
    return result


@router.get("/risk/zones")
async def get_zones():
    rows = database.get_zones()
    result = []
    for r in rows:
        item = to_camel(r)
        item.pop("updatedAt", None)
        result.append(item)
    return result


@router.get("/alerts")
async def get_alerts(limit: int = 20):
    rows = database.get_alerts(limit)
    result = []
    for r in rows:
        item = to_camel(r)
        item.pop("createdAt", None)
        result.append(item)
    return result


@router.get("/routes")
async def get_routes():
    return database.get_routes()


@router.get("/risk/history")
async def get_history(days: int = 30):
    return database.get_history(days)


@router.get("/risk/domains")
async def get_domains():
    rows = database.get_domain_scores()
    return [{"domain": r["domain"], "score": r["score"], "level": r["level"]} for r in rows]


@router.get("/risk/domains/history")
async def get_domain_history(weeks: int = 8):
    """Return historical domain score snapshots for the heatmap."""
    rows = database.get_domain_history(weeks)
    # Group by domain for frontend consumption
    by_domain: dict[str, list] = {}
    for r in rows:
        domain = r["domain"]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append({
            "date": r["snapshot_date"],
            "score": r["score"],
            "level": r["level"],
        })
    return by_domain


@router.get("/health")
async def health():
    import os
    db_path = database.DB_FILE
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    summary = database.get_summary()
    return {
        "status": "ok",
        "lastUpdated": summary.get("last_updated", "never"),
        "dbSizeKB": round(db_size / 1024, 1),
        "indicators": len(database.get_indicators()),
        "alerts": len(database.get_alerts(100)),
        "zones": len(database.get_zones()),
    }


# ── MANUAL OVERRIDE ENDPOINTS ──

class ZoneOverride(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    score: int
    risk_level: str = "HIGH"
    category: str = "geopolitical"
    description: str = ""

class DomainOverride(BaseModel):
    domain: str
    score: int

@router.post("/override/zone")
async def override_zone(zone: ZoneOverride):
    """Manually set a risk zone score (for when automated feeds are inaccurate)."""
    from datetime import datetime, timezone
    database.upsert_zone({
        "id": zone.id,
        "name": zone.name,
        "lat": zone.lat,
        "lng": zone.lng,
        "score": zone.score,
        "risk_level": zone.risk_level,
        "category": zone.category,
        "description": zone.description,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    compute_all()  # Recalculate scores
    return {"status": "ok", "zone": zone.id, "score": zone.score}

@router.post("/override/domain")
async def override_domain(override: DomainOverride):
    """Manually override a domain score."""
    from datetime import datetime, timezone
    from config import risk_level
    database.save_domain_scores([{
        "domain": override.domain,
        "score": override.score,
        "level": risk_level(override.score),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }])
    return {"status": "ok", "domain": override.domain, "score": override.score}


# ── AI ANALYST ──

class AskQuestion(BaseModel):
    question: str

@router.post("/ask")
async def ask_ai(body: AskQuestion):
    """Ask the AI analyst a question about current supply chain risks."""
    answer = await ask_analyst(body.question)
    return {"question": body.question, "answer": answer}
