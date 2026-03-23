"""Background enrichment: resolve unknown vessel types by MMSI lookup via free web sources."""

import asyncio
import logging
import re

import httpx

import database
from config import get_ship_type_label

logger = logging.getLogger(__name__)

RATE_LIMIT_SECONDS = 3.0
BATCH_SIZE = 20

# Map web-displayed vessel type strings to AIS type codes
_WEB_TYPE_MAP = {
    # Cargo variants (AIS 70-79)
    "cargo": 70,
    "container": 70,
    "bulk carrier": 70,
    "general cargo": 70,
    "container ship": 70,
    "reefer": 72,
    "ro-ro cargo": 74,
    "vehicles carrier": 74,
    "heavy load carrier": 70,
    # Tanker variants (AIS 80-89)
    "tanker": 80,
    "crude oil tanker": 80,
    "oil tanker": 80,
    "chemical tanker": 80,
    "oil/chemical tanker": 80,
    "products tanker": 80,
    "lng tanker": 84,
    "lpg tanker": 84,
    # Passenger variants (AIS 60-69)
    "passenger": 60,
    "cruise": 60,
    "ferry": 60,
    "passenger ship": 60,
    # Special types
    "tug": 1003,
    "offshore supply": 1016,
    "offshore": 1016,
}


def _match_vessel_type(type_str: str) -> int | None:
    """Match a vessel type string to an AIS type code."""
    normalized = type_str.lower().strip()
    # Sort by key length descending so more specific matches win (e.g. "lng tanker" before "tanker")
    for key, code in sorted(_WEB_TYPE_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if key in normalized:
            return code
    return None


def _parse_myshiptracking(html: str) -> tuple[int | None, str | None]:
    """Parse vessel type and name from MyShipTracking HTML page."""
    name = None
    ship_type = None

    # Extract name from title: "VESSEL NAME - Type (IMO: ..., MMSI: ...)"
    title_match = re.search(r'<title>\s*([^<]+?)(?:\s*-\s*)', html)
    if title_match:
        name = title_match.group(1).strip()

    # Extract type from title after the dash: "NAME - Cargo A (IMO..."
    type_from_title = re.search(r'<title>[^-]+-\s*([^(]+)', html)
    if type_from_title:
        type_str = type_from_title.group(1).strip()
        ship_type = _match_vessel_type(type_str)

    # Also try: "is a Cargo A" or "is a Tanker" pattern in body text
    if not ship_type:
        is_a_match = re.search(r'is a\s+\*?\*?([A-Za-z /]+)', html)
        if is_a_match:
            ship_type = _match_vessel_type(is_a_match.group(1))

    # Also try h2 tag which often contains the type
    if not ship_type:
        h2_match = re.search(r'<h2[^>]*>\s*([^<]+)\s*</h2>', html)
        if h2_match:
            ship_type = _match_vessel_type(h2_match.group(1))

    return ship_type, name


async def _lookup_vessel_type(client: httpx.AsyncClient, mmsi: str) -> tuple[int | None, str | None]:
    """Look up vessel type by MMSI via MyShipTracking (free, no auth required)."""
    url = f"https://www.myshiptracking.com/vessels/mmsi-{mmsi}"
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            logger.debug("Vessel enrichment: HTTP %d for MMSI %s", resp.status_code, mmsi)
            return None, None
        return _parse_myshiptracking(resp.text)
    except httpx.HTTPError as e:
        logger.debug("Vessel enrichment: request failed for MMSI %s: %s", mmsi, e)
        return None, None


async def enrich_unknown_vessels():
    """Look up unknown vessels via external source and update registry + positions."""
    unknowns = database.get_unknown_mmsis(limit=BATCH_SIZE)
    if not unknowns:
        return

    logger.info("Vessel enrichment: %d unknown MMSIs to look up", len(unknowns))
    resolved = 0

    async with httpx.AsyncClient(
        timeout=10.0,
        headers={"User-Agent": "Mozilla/5.0 (compatible; SupplyWatch/1.0)"},
        follow_redirects=True,
    ) as client:
        for mmsi in unknowns:
            try:
                ship_type, name = await _lookup_vessel_type(client, mmsi)
                if ship_type and ship_type > 0:
                    label = get_ship_type_label(ship_type)
                    database.upsert_vessel_registry(mmsi, ship_type, label, name, source="external")
                    database.backfill_vessel_type(mmsi, ship_type, label, name)
                    resolved += 1
                    logger.debug("Vessel enrichment: MMSI %s → %s (%s)", mmsi, label, name)
                else:
                    # Mark as looked up to avoid re-querying
                    database.upsert_vessel_registry(mmsi, 0, "Unknown", name, source="external")
            except Exception as e:
                logger.debug("Vessel enrichment: error for MMSI %s: %s", mmsi, e)

            await asyncio.sleep(RATE_LIMIT_SECONDS)

    logger.info("Vessel enrichment: resolved %d/%d vessels", resolved, len(unknowns))
