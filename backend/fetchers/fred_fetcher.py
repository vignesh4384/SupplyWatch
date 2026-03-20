"""Fetch economic indicators from FRED API."""

import asyncio
import logging
from datetime import datetime, timezone
import httpx
from config import FRED_API_KEY, FRED_INDICATORS

logger = logging.getLogger(__name__)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


async def fetch_single_series(client: httpx.AsyncClient, series_cfg: dict) -> dict | None:
    """Fetch latest 2 observations for a single FRED series."""
    try:
        resp = await client.get(FRED_BASE, params={
            "series_id": series_cfg["series_id"],
            "api_key": FRED_API_KEY,
            "sort_order": "desc",
            "limit": 2,
            "file_type": "json",
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        obs = data.get("observations", [])

        if not obs or obs[0].get("value") == ".":
            logger.warning(f"No data for {series_cfg['series_id']}")
            return None

        current_val = float(obs[0]["value"])
        prev_val = float(obs[1]["value"]) if len(obs) > 1 and obs[1].get("value") != "." else current_val
        change = round(((current_val - prev_val) / prev_val) * 100, 1) if prev_val != 0 else 0

        # Format date
        raw_date = obs[0]["date"]  # YYYY-MM-DD
        dt = datetime.strptime(raw_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%b %d").replace(" 0", " ")  # "Mar 17"

        # Score the indicator
        score, level = score_indicator(series_cfg, current_val)

        return {
            "id": series_cfg["id"],
            "name": series_cfg["name"],
            "category": series_cfg["category"],
            "value": round(current_val, 2),
            "unit": series_cfg["unit"],
            "change": change,
            "risk_level": level,
            "risk_score": score,
            "date": formatted_date,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"FRED fetch error for {series_cfg['series_id']}: {e}")
        return None


def score_indicator(cfg: dict, value: float) -> tuple[int, str]:
    """Convert raw value to 0-100 risk score based on thresholds."""
    high_t = cfg["high_threshold"]
    med_t = cfg["medium_threshold"]
    inverted = cfg.get("inverted", False)

    if inverted:
        # Lower values = higher risk (e.g., Consumer Sentiment)
        if value <= high_t:
            score = min(100, int(66 + (high_t - value) / high_t * 34))
        elif value <= med_t:
            score = int(41 + (med_t - value) / (med_t - high_t) * 25)
        else:
            score = max(0, int(value / med_t * 40))
            score = min(40, 40 - score + 40)  # Invert: high value = low score
    else:
        # Higher values = higher risk (e.g., oil price)
        if value >= high_t:
            score = min(100, int(66 + (value - high_t) / high_t * 34))
        elif value >= med_t:
            score = int(41 + (value - med_t) / (high_t - med_t) * 25)
        else:
            score = max(0, int(value / med_t * 40))

    if score >= 66:
        level = "HIGH"
    elif score >= 41:
        level = "MEDIUM"
    else:
        level = "LOW"

    return score, level


async def fetch_fred_indicators() -> list[dict]:
    """Fetch all FRED indicators concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_single_series(client, cfg) for cfg in FRED_INDICATORS]
        results = await asyncio.gather(*tasks)

    indicators = [r for r in results if r is not None]
    logger.info(f"FRED: fetched {len(indicators)}/{len(FRED_INDICATORS)} indicators")
    return indicators
