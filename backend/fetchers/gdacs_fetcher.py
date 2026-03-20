"""Fetch disaster alerts from GDACS RSS feed."""

import logging
import hashlib
from datetime import datetime, timezone
import httpx
import feedparser

logger = logging.getLogger(__name__)

GDACS_URL = "https://www.gdacs.org/xml/rss.xml"

SEVERITY_MAP = {
    "red": "critical",
    "orange": "warning",
    "green": "info",
    "yellow": "info",
}


async def fetch_gdacs() -> tuple[list[dict], list[dict]]:
    """Fetch GDACS RSS feed. Returns (alerts, zones)."""
    alerts = []
    zones = []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(GDACS_URL, timeout=20)
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        now = datetime.now(timezone.utc).isoformat()

        for i, entry in enumerate(feed.entries[:15]):
            title = entry.get("title", "Unknown Event")
            summary = entry.get("summary", "")
            severity_raw = entry.get("gdacs_severity", {})
            if isinstance(severity_raw, dict):
                sev_text = severity_raw.get("value", "green").lower()
            else:
                sev_text = str(severity_raw).lower() if severity_raw else "green"

            severity = SEVERITY_MAP.get(sev_text, "info")
            alert_id = f"gdacs_{hashlib.md5(title.encode()).hexdigest()[:8]}"

            # Time ago formatting
            pub_date = entry.get("published", "")
            time_ago = format_time_ago(pub_date)

            alerts.append({
                "id": alert_id,
                "title": title[:200],
                "severity": severity,
                "source": "GDACS",
                "timestamp": time_ago,
                "created_at": now,
            })

            # Extract coordinates for risk zones
            georss = entry.get("georss_point", entry.get("geo_lat", None))
            if georss and isinstance(georss, str) and " " in georss:
                parts = georss.split()
                try:
                    lat, lng = float(parts[0]), float(parts[1])
                    score = 85 if severity == "critical" else 60 if severity == "warning" else 35
                    zones.append({
                        "id": f"z_gdacs_{i}",
                        "name": title[:80],
                        "lat": lat,
                        "lng": lng,
                        "score": score,
                        "risk_level": "HIGH" if score >= 66 else "MEDIUM" if score >= 41 else "LOW",
                        "category": "disaster",
                        "description": summary[:300] if summary else title,
                        "updated_at": now,
                    })
                except (ValueError, IndexError):
                    pass

        logger.info(f"GDACS: {len(alerts)} alerts, {len(zones)} zones")
    except Exception as e:
        logger.error(f"GDACS fetch error: {e}")

    return alerts, zones


def format_time_ago(pub_date_str: str) -> str:
    """Convert publication date to relative time string."""
    if not pub_date_str:
        return "recently"
    try:
        from email.utils import parsedate_to_datetime
        pub_dt = parsedate_to_datetime(pub_date_str)
        delta = datetime.now(timezone.utc) - pub_dt
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
