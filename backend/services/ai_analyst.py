"""AI-powered supply chain risk analyst using Claude API."""

import os
import json
import logging
from dotenv import load_dotenv
from anthropic import Anthropic

import database

_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(_env_path, override=True)
logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

SYSTEM_PROMPT = """You are SupplyWatch AI Analyst — an expert supply chain risk intelligence advisor embedded in a global supply chain control tower dashboard.

Your role:
- Answer questions about current supply chain risks, trade routes, commodity prices, and geopolitical events
- Provide concise, executive-level analysis (2-4 sentences max)
- Reference specific data points from the dashboard context provided
- Explain WHY metrics are at their current levels, connecting data to real-world events
- Be direct and actionable — this is for C-suite decision makers

Style:
- Professional, confident tone
- Use specific numbers and data points
- Connect indicators to real-world causes
- Suggest implications or actions when relevant
- Never hedge excessively — give a clear assessment

IMPORTANT: Keep responses SHORT (2-4 sentences). Executives don't want essays."""


def build_context() -> str:
    """Build a snapshot of current dashboard data for the AI context."""
    summary = database.get_summary()
    indicators = database.get_indicators()
    zones = database.get_zones()
    domains = database.get_domain_scores()
    alerts = database.get_alerts(10)
    routes = database.get_routes()

    ctx = {
        "overall_risk": {
            "score": summary.get("overall_score", 0),
            "level": summary.get("level", "UNKNOWN"),
            "high_count": summary.get("high_count", 0),
            "medium_count": summary.get("medium_count", 0),
            "low_count": summary.get("low_count", 0),
        },
        "domains": [{"name": d["domain"], "score": d["score"], "level": d["level"]} for d in domains],
        "indicators": [
            {"name": i["name"], "value": i["value"], "unit": i["unit"],
             "change": i["change"], "risk": i["risk_level"], "category": i["category"]}
            for i in indicators
        ],
        "trade_routes": [
            {"name": r["name"], "status": r["status"], "score": r["riskScore"], "description": r["description"]}
            for r in routes
        ],
        "risk_zones": [
            {"name": z["name"], "score": z["score"], "risk": z["risk_level"],
             "category": z["category"], "description": z["description"]}
            for z in zones[:15]  # Top 15 zones
        ],
        "recent_alerts": [
            {"title": a["title"], "severity": a["severity"], "source": a["source"]}
            for a in alerts
        ],
    }
    return json.dumps(ctx, indent=2)


async def ask_analyst(question: str) -> str:
    """Ask the AI analyst a question about current supply chain risks."""
    if not ANTHROPIC_API_KEY:
        return "AI analyst unavailable — Anthropic API key not configured."

    try:
        context = build_context()

        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"""Here is the current SupplyWatch dashboard data:

{context}

User question: {question}"""
                }
            ],
        )

        response = message.content[0].text
        logger.info(f"AI Analyst: Q='{question[:50]}...' → {len(response)} chars")
        return response

    except Exception as e:
        logger.error(f"AI Analyst error: {e}")
        return f"Analysis unavailable: {str(e)[:100]}"
