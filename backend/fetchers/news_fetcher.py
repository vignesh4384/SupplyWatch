"""Fetch supply chain news headlines from NewsAPI."""

import logging
import hashlib
from datetime import datetime, timezone
import httpx
from config import NEWS_API_KEY, CRITICAL_KEYWORDS, WARNING_KEYWORDS

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"


async def fetch_news() -> list[dict]:
    """Fetch supply chain disruption news from NewsAPI."""
    alerts = []

    if not NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set, skipping news fetch")
        return alerts

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(NEWSAPI_URL, params={
                "q": "(supply chain AND (disruption OR crisis OR risk)) OR (shipping AND (attack OR blockade OR closure)) OR (oil AND (price OR shortage OR embargo)) OR (Hormuz OR Suez OR \"Red Sea\") OR (tariff AND trade AND war)",
                "sortBy": "relevancy",
                "pageSize": 15,
                "apiKey": NEWS_API_KEY,
                "language": "en",
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()

        now = datetime.now(timezone.utc).isoformat()

        for article in data.get("articles", []):
            title = article.get("title", "")
            if not title or title == "[Removed]":
                continue

            source_name = article.get("source", {}).get("name", "News")
            published = article.get("publishedAt", "")
            alert_id = f"news_{hashlib.md5(title.encode()).hexdigest()[:8]}"

            # Determine severity from title keywords
            title_lower = title.lower()
            if any(kw in title_lower for kw in CRITICAL_KEYWORDS):
                severity = "critical"
            elif any(kw in title_lower for kw in WARNING_KEYWORDS):
                severity = "warning"
            else:
                severity = "info"

            # Format time ago
            time_ago = format_published(published)

            alerts.append({
                "id": alert_id,
                "title": title[:200],
                "severity": severity,
                "source": "NewsAPI",
                "timestamp": time_ago,
                "created_at": now,
            })

        logger.info(f"NewsAPI: {len(alerts)} alerts")
    except Exception as e:
        logger.error(f"NewsAPI fetch error: {e}")

    return alerts


def format_published(iso_str: str) -> str:
    """Convert ISO timestamp to relative time."""
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
