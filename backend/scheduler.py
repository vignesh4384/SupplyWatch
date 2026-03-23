"""Scheduler for periodic data fetching and risk scoring."""

import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database
from fetchers.fred_fetcher import fetch_fred_indicators
from fetchers.gdacs_fetcher import fetch_gdacs
from fetchers.news_fetcher import fetch_news
from fetchers.gdelt_fetcher import fetch_gdelt
from fetchers.usgs_fetcher import fetch_usgs
from fetchers.yfinance_fetcher import fetch_yfinance_indicators
from fetchers.nasa_fetcher import fetch_nasa_eonet
from engine.aggregator import compute_all
from config import FETCH_INTERVAL, STATIC_INDICATORS, CRISIS_ZONES
from enrichment.vessel_type_enricher import enrich_unknown_vessels

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# ──────────────────────────────────────────────
# NEWS-BASED ROUTE RISK DETECTION
# Scan news headlines for route-specific keywords
# ──────────────────────────────────────────────
ROUTE_KEYWORDS = {
    "hormuz": {
        "keywords": ["hormuz", "iran", "persian gulf", "iranian", "tehran", "strait of hormuz",
                     "oil tanker attack", "gulf crisis", "iran war", "iran conflict", "iran israel"],
        "zone_id": "z_hormuz_news",
        "zone_name": "Strait of Hormuz — News Alert",
        "lat": 26.5, "lng": 56.5,
        "category": "maritime",
    },
    "redsea": {
        "keywords": ["red sea", "houthi", "bab el-mandeb", "suez", "yemen attack", "aden"],
        "zone_id": "z_redsea_news",
        "zone_name": "Red Sea — News Alert",
        "lat": 14.0, "lng": 42.0,
        "category": "maritime",
    },
    "taiwan": {
        "keywords": ["taiwan strait", "taiwan military", "china taiwan", "tsmc", "semiconductor taiwan"],
        "zone_id": "z_taiwan_news",
        "zone_name": "Taiwan Strait — News Alert",
        "lat": 24.0, "lng": 120.0,
        "category": "geopolitical",
    },
    "panama": {
        "keywords": ["panama canal", "panama drought", "panama transit"],
        "zone_id": "z_panama_news",
        "zone_name": "Panama Canal — News Alert",
        "lat": 9.0, "lng": -79.5,
        "category": "disaster",
    },
}


def analyze_news_for_routes(all_alerts: list[dict]) -> list[dict]:
    """Scan news headlines to detect route-specific risks and generate zones."""
    zones = []
    now = datetime.now(timezone.utc).isoformat()

    for route_key, rcfg in ROUTE_KEYWORDS.items():
        # Count how many alerts mention this route
        critical_hits = 0
        warning_hits = 0
        total_hits = 0
        matching_titles = []

        for alert in all_alerts:
            title_lower = alert.get("title", "").lower()
            if any(kw in title_lower for kw in rcfg["keywords"]):
                total_hits += 1
                matching_titles.append(alert["title"][:80])
                if alert.get("severity") == "critical":
                    critical_hits += 1
                elif alert.get("severity") == "warning":
                    warning_hits += 1

        if total_hits == 0:
            continue

        # Score based on frequency and severity of mentions
        # More mentions = higher risk, critical mentions weighted 3x
        score = min(100, 30 + critical_hits * 20 + warning_hits * 10 + total_hits * 5)
        risk_level = "HIGH" if score >= 66 else "MEDIUM" if score >= 41 else "LOW"

        desc = f"Detected {total_hits} news mentions. " + (matching_titles[0] if matching_titles else "")

        zones.append({
            "id": rcfg["zone_id"],
            "name": rcfg["zone_name"],
            "lat": rcfg["lat"],
            "lng": rcfg["lng"],
            "score": score,
            "risk_level": risk_level,
            "category": rcfg["category"],
            "description": desc[:300],
            "updated_at": now,
        })

        logger.info(f"News route detection: {route_key} → {total_hits} mentions, score={score} ({risk_level})")

    return zones


async def refresh_all_data():
    """Main refresh cycle: fetch all sources → store → score → save."""
    logger.info("=== Starting data refresh cycle ===")
    start = datetime.now(timezone.utc)

    # 1. Fetch all sources concurrently
    fred_task = fetch_fred_indicators()
    gdacs_task = fetch_gdacs()
    news_task = fetch_news()
    gdelt_task = fetch_gdelt()
    usgs_task = fetch_usgs()
    nasa_task = fetch_nasa_eonet()

    results = await asyncio.gather(
        fred_task, gdacs_task, news_task, gdelt_task, usgs_task, nasa_task,
        return_exceptions=True
    )

    fred_indicators = results[0] if not isinstance(results[0], Exception) else []
    gdacs_alerts, gdacs_zones = results[1] if not isinstance(results[1], Exception) else ([], [])
    news_alerts = results[2] if not isinstance(results[2], Exception) else []
    gdelt_alerts, gdelt_zones = results[3] if not isinstance(results[3], Exception) else ([], [])
    usgs_alerts, usgs_zones = results[4] if not isinstance(results[4], Exception) else ([], [])
    nasa_alerts, nasa_zones = results[5] if not isinstance(results[5], Exception) else ([], [])

    # Log any errors
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            sources = ["FRED", "GDACS", "NewsAPI", "GDELT", "USGS", "NASA"]
            logger.error(f"{sources[i]} fetch failed: {r}")

    # 2. Save FRED indicators (baseline)
    for ind in fred_indicators:
        database.upsert_indicator(ind)

    # 2b. Fetch real-time prices from Yahoo Finance (overrides FRED for commodities)
    try:
        yf_indicators = await asyncio.to_thread(fetch_yfinance_indicators)
        for ind in yf_indicators:
            database.upsert_indicator(ind)
        logger.info(f"YFinance: updated {len(yf_indicators)} real-time prices")
    except Exception as e:
        logger.warning(f"YFinance fetch failed (using FRED fallback): {e}")

    # 3. Ensure static indicators exist (for series not on FRED)
    now = datetime.now(timezone.utc).isoformat()
    for sind in STATIC_INDICATORS:
        existing = None
        for ind in database.get_indicators():
            if ind["id"] == sind["id"]:
                existing = ind
                break
        if not existing:
            database.upsert_indicator({
                **sind,
                "risk_score": 50,
                "fetched_at": now,
            })

    # 4. Save all alerts
    all_alerts = gdacs_alerts + news_alerts + gdelt_alerts + usgs_alerts + nasa_alerts
    for alert in all_alerts:
        database.upsert_alert(alert)

    # 5. Save all zones from automated feeds
    all_zones = gdacs_zones + gdelt_zones + usgs_zones + nasa_zones
    for zone in all_zones:
        database.upsert_zone(zone)

    # 6. NEWS-BASED ROUTE RISK DETECTION
    # Analyze all collected alerts to detect route-specific risks
    news_route_zones = analyze_news_for_routes(all_alerts + gdelt_alerts)
    for zone in news_route_zones:
        database.upsert_zone(zone)
    if news_route_zones:
        logger.info(f"News route detection: created {len(news_route_zones)} route risk zones")

    # 7. CRISIS OVERRIDE ZONES
    # Inject known crisis zones that automated feeds miss
    for cz in CRISIS_ZONES:
        database.upsert_zone({
            **cz,
            "updated_at": now,
        })
    logger.info(f"Crisis zones: injected {len(CRISIS_ZONES)} manual override zones")

    # 8. Run risk scoring engine
    summary = compute_all()

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(f"=== Refresh complete in {elapsed:.1f}s === "
                f"indicators={len(fred_indicators)}, alerts={len(all_alerts)}, "
                f"zones={len(all_zones) + len(news_route_zones) + len(CRISIS_ZONES)}, "
                f"overall={summary['overall_score']}")


def vessel_ttl_cleanup():
    """Remove vessel positions older than 7 days."""
    database.cleanup_old_positions()


def start_scheduler():
    """Start the periodic scheduler."""
    scheduler.add_job(
        refresh_all_data,
        "interval",
        minutes=FETCH_INTERVAL,
        id="refresh_all",
        replace_existing=True,
    )
    scheduler.add_job(
        vessel_ttl_cleanup,
        "interval",
        hours=1,
        id="vessel_ttl_cleanup",
        replace_existing=True,
    )
    scheduler.add_job(
        enrich_unknown_vessels,
        "interval",
        minutes=10,
        id="vessel_type_enrichment",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started: refresh every {FETCH_INTERVAL} minutes, vessel TTL cleanup every hour, vessel type enrichment every 10 minutes")
