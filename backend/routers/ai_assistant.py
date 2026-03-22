"""AI-powered maritime risk assistant using Claude API with tool use."""

import json
import logging
import os
from datetime import datetime, timezone

from anthropic import AsyncAnthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

SYSTEM_PROMPT = """You are a maritime supply chain risk analyst for Supply Watch.
Your role is to analyse live AIS vessel data and risk events to provide
actionable intelligence for procurement and tendering decisions.

Rules:
- Always cite specific vessel names, MMSIs, zones, and timestamps
- Quantify risk where possible (e.g. "3 tankers slow in Hormuz")
- Link vessel behaviour to supply chain impact explicitly
- If data is insufficient, say so — do not speculate
- Keep answers concise — max 200 words unless detail is requested
- Always end with a recommended action for the procurement team"""

# Tool definitions for Claude
TOOLS = [
    {
        "name": "get_vessels_in_zone",
        "description": "Returns live vessel positions and counts for a named zone over the last N hours.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone": {
                    "type": "string",
                    "enum": ["hormuz", "red_sea", "arabian_sea", "gulf_aden", "all"],
                    "description": "Zone to query",
                },
                "hours": {
                    "type": "integer",
                    "description": "Look-back window in hours (default 24, max 168)",
                    "default": 24,
                },
            },
            "required": ["zone"],
        },
    },
    {
        "name": "get_dark_vessels",
        "description": "Returns vessels flagged as dark or suspicious (AIS gap, unexpected slow speed) in a zone or globally.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone": {
                    "type": "string",
                    "description": "Zone to filter (omit for global)",
                },
                "hours": {
                    "type": "integer",
                    "description": "Look-back window in hours (default 6)",
                    "default": 6,
                },
            },
        },
    },
    {
        "name": "get_slow_vessels",
        "description": "Returns vessels moving below a speed threshold in a zone. Useful for detecting congestion and queuing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone": {
                    "type": "string",
                    "description": "Zone to query",
                },
                "max_speed": {
                    "type": "number",
                    "description": "Speed threshold in knots (default 2.0)",
                    "default": 2.0,
                },
                "hours": {
                    "type": "integer",
                    "description": "Look-back window in hours (default 6)",
                    "default": 6,
                },
            },
            "required": ["zone"],
        },
    },
    {
        "name": "get_risk_events",
        "description": "Returns active risk events (geopolitical zones, maritime alerts, disaster zones) filterable by category and minimum score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ["maritime", "geopolitical", "disaster", "economic", "all"],
                    "description": "Risk domain to filter",
                    "default": "all",
                },
                "min_risk_score": {
                    "type": "integer",
                    "description": "Minimum risk score threshold (default 50)",
                    "default": 50,
                },
            },
        },
    },
]


def _execute_tool(name: str, args: dict) -> str:
    """Execute a tool and return JSON results."""
    if name == "get_vessels_in_zone":
        zone = args.get("zone", "all")
        hours = min(args.get("hours", 24), 168)
        if zone == "all":
            counts = database.get_vessel_counts(hours=hours)
            total = sum(c["vessel_count"] for c in counts)
            return json.dumps({"zone": "all", "hours": hours, "total_vessels": total, "breakdown": counts})
        else:
            vessels = database.get_vessels_by_zone(zone=zone, hours=hours)
            unique_mmsis = set(v["mmsi"] for v in vessels)
            return json.dumps({
                "zone": zone, "hours": hours,
                "unique_vessels": len(unique_mmsis),
                "total_positions": len(vessels),
                "vessels": vessels[:50],  # Limit to avoid token overflow
            })

    elif name == "get_dark_vessels":
        zone = args.get("zone")
        hours = min(args.get("hours", 6), 48)
        vessels = database.get_dark_vessels(zone=zone, hours=hours)
        return json.dumps({"zone": zone or "all", "hours": hours, "count": len(vessels), "vessels": vessels[:30]})

    elif name == "get_slow_vessels":
        zone = args.get("zone", "hormuz")
        max_speed = args.get("max_speed", 2.0)
        hours = min(args.get("hours", 6), 48)
        vessels = database.get_slow_vessels(zone=zone, max_speed=max_speed, hours=hours)
        return json.dumps({"zone": zone, "max_speed": max_speed, "hours": hours, "count": len(vessels), "vessels": vessels[:30]})

    elif name == "get_risk_events":
        domain = args.get("domain", "all")
        min_score = args.get("min_risk_score", 50)
        zones = database.get_zones()
        if domain != "all":
            zones = [z for z in zones if z.get("category") == domain]
        zones = [z for z in zones if z.get("score", 0) >= min_score]
        alerts = database.get_alerts(limit=15)
        return json.dumps({"domain": domain, "min_score": min_score, "risk_zones": zones, "recent_alerts": alerts})

    return json.dumps({"error": f"Unknown tool: {name}"})


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    tools_used: list[str]
    sources: list[str]


@router.post("/ask", response_model=AskResponse)
async def ask_ai_assistant(req: AskRequest):
    """Ask the AI maritime risk assistant a question using Claude with tool use."""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI assistant unavailable — ANTHROPIC_API_KEY not configured")

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    tools_used = []
    sources = []

    messages = [{"role": "user", "content": req.question}]

    try:
        # Initial call — Claude may request tool use
        response = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Process tool use loop (max 3 iterations)
        for _ in range(3):
            if response.stop_reason != "tool_use":
                break

            # Collect tool calls and results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_args = block.input
                    tools_used.append(tool_name)
                    sources.append(f"vessel_positions ({tool_name})")

                    result = _execute_tool(tool_name, tool_args)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Continue conversation with tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            response = await client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

        # Extract final text response
        answer = ""
        for block in response.content:
            if hasattr(block, "text"):
                answer += block.text

        if not answer:
            answer = "I was unable to generate an analysis. Please try rephrasing your question."

        logger.info("AI Assistant: Q='%s' → %d chars, tools=%s", req.question[:50], len(answer), tools_used)

        return AskResponse(
            answer=answer,
            tools_used=list(set(tools_used)),
            sources=list(set(sources)),
        )

    except Exception as e:
        logger.error("AI Assistant error: %s", e)
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)[:200]}")
