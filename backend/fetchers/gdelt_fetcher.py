"""Fetch geopolitical events from GDELT DOC 2.0 API."""

import logging
import hashlib
import asyncio
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

QUERIES = [
    {"q": "supply chain conflict blockade", "category": "geopolitical"},
    {"q": "trade sanction embargo tariff", "category": "geopolitical"},
    {"q": "shipping port disruption maritime", "category": "maritime"},
]


async def fetch_gdelt() -> tuple[list[dict], list[dict]]:
    """Fetch GDELT events. Returns (alerts, zones)."""
    alerts = []
    zones = []

    try:
        async with httpx.AsyncClient() as client:
            for qcfg in QUERIES:
                try:
                    resp = await client.get(GDELT_DOC_URL, params={
                        "query": qcfg["q"],
                        "mode": "ArtList",
                        "maxrecords": 10,
                        "format": "json",
                        "sort": "DateDesc",
                        "sourcelang": "english",
                    }, timeout=20)

                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    now = datetime.now(timezone.utc).isoformat()

                    for article in data.get("articles", [])[:5]:
                        title = article.get("title", "")
                        if not title:
                            continue
                        # Skip non-English titles (contain CJK or Cyrillic characters)
                        if any(ord(c) > 0x2000 for c in title):
                            continue

                        url = article.get("url", "")
                        tone = article.get("tone", 0)
                        seendate = article.get("seendate", "")
                        source_country = article.get("sourcecountry", "")

                        alert_id = f"gdelt_{hashlib.md5((title + url).encode()).hexdigest()[:8]}"

                        # Tone-based severity: negative = higher risk
                        tone_val = float(tone) if tone else 0
                        if tone_val < -5:
                            severity = "critical"
                            score = 80
                        elif tone_val < -2:
                            severity = "warning"
                            score = 55
                        else:
                            severity = "info"
                            score = 30

                        time_ago = format_gdelt_date(seendate)

                        alerts.append({
                            "id": alert_id,
                            "title": title[:200],
                            "severity": severity,
                            "source": "GDELT",
                            "timestamp": time_ago,
                            "created_at": now,
                        })

                except Exception as e:
                    logger.warning(f"GDELT query '{qcfg['q'][:30]}' failed: {e}")
                    continue

                # Rate limit: GDELT allows ~1 request per 5-10 seconds
                if qcfg != QUERIES[-1]:
                    await asyncio.sleep(6)

        logger.info(f"GDELT: {len(alerts)} alerts, {len(zones)} zones")
    except Exception as e:
        logger.error(f"GDELT fetch error: {e}")

    return alerts, zones


def format_gdelt_date(seendate: str) -> str:
    """Convert GDELT date (YYYYMMDDHHmmSS) to relative time."""
    if not seendate or len(seendate) < 8:
        return "recently"
    try:
        dt = datetime.strptime(seendate[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
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
