"""SupplyWatch configuration: FRED mappings, risk thresholds, domain weights, trade routes."""

import os
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "./supplywatch.db")
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))

# ──────────────────────────────────────────────
# FRED Series → Frontend Indicator Mappings
# ──────────────────────────────────────────────
FRED_INDICATORS = [
    {"series_id": "DCOILBRENTEU", "id": "brent", "name": "Brent Crude Oil", "unit": "USD/bbl", "category": "energy",
     "high_threshold": 100, "medium_threshold": 80, "inverted": False},
    {"series_id": "DCOILWTICO", "id": "wti", "name": "WTI Crude Oil", "unit": "USD/bbl", "category": "energy",
     "high_threshold": 95, "medium_threshold": 75, "inverted": False},
    {"series_id": "DHHNGSP", "id": "natgas", "name": "Natural Gas", "unit": "USD/MMBtu", "category": "energy",
     "high_threshold": 5.0, "medium_threshold": 3.0, "inverted": False},
    {"series_id": "GASREGW", "id": "gasoline", "name": "US Gasoline", "unit": "USD/gal", "category": "energy",
     "high_threshold": 4.0, "medium_threshold": 3.0, "inverted": False},
    {"series_id": "PCOPPUSDM", "id": "copper", "name": "Copper", "unit": "USD/ton", "category": "raw_materials",
     "high_threshold": 9500, "medium_threshold": 8000, "inverted": False},
    {"series_id": "PALUMUSDM", "id": "aluminum", "name": "Aluminum", "unit": "USD/ton", "category": "raw_materials",
     "high_threshold": 2800, "medium_threshold": 2200, "inverted": False},
    {"series_id": "PIORECRUSDM", "id": "ironore", "name": "Iron Ore", "unit": "USD/ton", "category": "raw_materials",
     "high_threshold": 150, "medium_threshold": 100, "inverted": False},
    {"series_id": "CPIAUCSL", "id": "cpi", "name": "US CPI", "unit": "%", "category": "inflation",
     "high_threshold": 4.0, "medium_threshold": 3.0, "inverted": False},
    {"series_id": "PPIACO", "id": "ppi", "name": "PPI All Commodities", "unit": "index", "category": "inflation",
     "high_threshold": 250, "medium_threshold": 220, "inverted": False},
    {"series_id": "UMCSENT", "id": "sentiment", "name": "Consumer Sentiment", "unit": "index", "category": "economic",
     "high_threshold": 60, "medium_threshold": 70, "inverted": True},  # Lower = worse
    {"series_id": "INDPRO", "id": "indpro", "name": "Industrial Production", "unit": "index", "category": "economic",
     "high_threshold": 95, "medium_threshold": 100, "inverted": True},  # Lower = worse
]

# Indicators not on FRED — use static/manual values
STATIC_INDICATORS = [
    {"id": "bdi", "name": "Baltic Dry Index", "unit": "index", "category": "freight",
     "value": 1847, "change": -2.1, "date": "Mar 17", "risk_level": "MEDIUM"},
    {"id": "scfi", "name": "Shanghai SCFI", "unit": "index", "category": "freight",
     "value": 1023, "change": -0.5, "date": "Mar 14", "risk_level": "LOW"},
    {"id": "aircargo", "name": "Air Cargo Rate", "unit": "USD/kg", "category": "freight",
     "value": 3.42, "change": 5.3, "date": "Mar 14", "risk_level": "MEDIUM"},
    {"id": "steel", "name": "Steel HRC", "unit": "USD/ton", "category": "raw_materials",
     "value": 680, "change": 2.4, "date": "Mar 14", "risk_level": "MEDIUM"},
    {"id": "hicp", "name": "EU HICP", "unit": "%", "category": "inflation",
     "value": 2.8, "change": -0.2, "date": "Feb 2026", "risk_level": "LOW"},
    {"id": "pmi", "name": "US PMI", "unit": "index", "category": "economic",
     "value": 51.2, "change": 0.4, "date": "Mar 2026", "risk_level": "MEDIUM"},
]

# ──────────────────────────────────────────────
# Domain Definitions + Weights
# ──────────────────────────────────────────────
DOMAINS = {
    "Geopolitical": {"weight": 0.20, "indicator_ids": [], "zone_category": "geopolitical"},
    "Maritime":     {"weight": 0.20, "indicator_ids": ["bdi", "scfi"], "zone_category": "maritime"},
    "Energy":       {"weight": 0.15, "indicator_ids": ["brent", "wti", "natgas", "gasoline"], "zone_category": None},
    "Raw Materials": {"weight": 0.15, "indicator_ids": ["copper", "aluminum", "ironore", "steel"], "zone_category": None},
    "Weather":      {"weight": 0.15, "indicator_ids": [], "zone_category": "disaster"},
    "Trade Policy": {"weight": 0.10, "indicator_ids": [], "zone_category": None},
    "Cyber":        {"weight": 0.05, "indicator_ids": [], "zone_category": None},
    "Labour":       {"weight": 0.00, "indicator_ids": [], "zone_category": None},
}

# Risk level thresholds
def risk_level(score: int) -> str:
    if score >= 66: return "HIGH"
    if score >= 41: return "MEDIUM"
    return "LOW"

# ──────────────────────────────────────────────
# Trade Routes (static geography)
# ──────────────────────────────────────────────
TRADE_ROUTES = [
    {"id": "r1", "name": "Suez Canal", "description": "Asia — Europe via Red Sea",
     "points": [[30,32],[13.5,43.5],[12,45],[5,50],[0,55],[-5,60],[10,70],[22,80],[30,105],[35,120]]},
    {"id": "r2", "name": "Strait of Hormuz", "description": "Persian Gulf — Indian Ocean",
     "points": [[26.5,56.5],[25,58],[24,60],[22,63],[18,68],[12,72]]},
    {"id": "r3", "name": "Cape of Good Hope", "description": "Asia — Europe (alternate)",
     "points": [[0,50],[-10,40],[-25,30],[-34,18],[-34,25],[-30,35],[-20,40],[-5,50],[10,55],[25,60]]},
    {"id": "r4", "name": "Trans-Pacific", "description": "East Asia — North America",
     "points": [[35,120],[33,140],[30,160],[28,180],[30,-170],[33,-155],[35,-140],[36,-125]]},
]

# Zone IDs that affect each route's risk
ROUTE_ZONE_MAPPING = {
    "r1": ["z_redsea", "z_suez"],
    "r2": ["z_hormuz"],
    "r3": ["z_guinea", "z_cape"],
    "r4": [],
}

# News severity keywords
CRITICAL_KEYWORDS = ["attack", "crisis", "war", "blockade", "shutdown", "collapse", "explosion", "strike",
                     "conflict", "bomb", "missile", "invasion", "escalation", "military", "closed", "closure"]
WARNING_KEYWORDS = ["risk", "tariff", "delay", "shortage", "sanction", "dispute", "congestion", "restriction",
                    "tension", "threat", "warning", "disruption", "reroute", "diversion", "protest"]

# ──────────────────────────────────────────────
# CRISIS OVERRIDE ZONES
# These are manually maintained high-priority zones
# that override automated feeds when geopolitical
# reality is ahead of data sources.
# Update these when major crises start/end.
# ──────────────────────────────────────────────
CRISIS_ZONES = [
    {
        "id": "z_hormuz_crisis",
        "name": "Strait of Hormuz — Iran Closure",
        "lat": 26.5, "lng": 56.5,
        "score": 95,
        "risk_level": "HIGH",
        "category": "geopolitical",
        "description": "Strait of Hormuz closed by Iran amid Iran-Israel-US conflict. 20% of global oil transits through this chokepoint. Major shipping rerouting underway.",
    },
    {
        "id": "z_redsea_crisis",
        "name": "Red Sea / Bab el-Mandeb",
        "lat": 13.0, "lng": 43.0,
        "score": 92,
        "risk_level": "HIGH",
        "category": "maritime",
        "description": "Houthi attacks on commercial shipping continue. Vessels rerouting via Cape of Good Hope adding 10-14 days transit time.",
    },
    {
        "id": "z_iran_conflict",
        "name": "Persian Gulf — Iran-Israel Conflict Zone",
        "lat": 28.0, "lng": 52.0,
        "score": 98,
        "risk_level": "HIGH",
        "category": "geopolitical",
        "description": "Active military conflict between Iran, Israel, and US forces. Major energy supply disruption risk. Oil infrastructure under threat.",
    },
    {
        "id": "z_suez_risk",
        "name": "Suez Canal — Elevated Risk",
        "lat": 30.5, "lng": 32.3,
        "score": 58,
        "risk_level": "MEDIUM",
        "category": "maritime",
        "description": "Suez Canal operational but with elevated risk. Insurance premiums rising due to regional instability. Transit delays possible.",
    },
    {
        "id": "z_ukraine",
        "name": "Black Sea / Ukraine",
        "lat": 46.0, "lng": 33.0,
        "score": 88,
        "risk_level": "HIGH",
        "category": "geopolitical",
        "description": "Ongoing Russia-Ukraine conflict affecting grain exports and Black Sea shipping lanes.",
    },
    {
        "id": "z_scs",
        "name": "South China Sea",
        "lat": 15.0, "lng": 115.0,
        "score": 70,
        "risk_level": "HIGH",
        "category": "geopolitical",
        "description": "Territorial disputes and military exercises. Key shipping lane for global trade.",
    },
    {
        "id": "z_taiwan",
        "name": "Taiwan Strait",
        "lat": 24.0, "lng": 120.0,
        "score": 75,
        "risk_level": "HIGH",
        "category": "geopolitical",
        "description": "Elevated tensions. Critical semiconductor supply chain risk. Military exercises increasing.",
    },
    {
        "id": "z_panama",
        "name": "Panama Canal — Water Crisis",
        "lat": 9.0, "lng": -79.5,
        "score": 58,
        "risk_level": "MEDIUM",
        "category": "disaster",
        "description": "Water levels critically low. Transit restrictions in effect. Vessels experiencing extended wait times.",
    },
]

# Geopolitical boost: when crisis zones exist, boost domain scores
GEOPOLITICAL_CRISIS_BOOST = 40  # Added to the Geopolitical domain base score
MARITIME_CRISIS_BOOST = 30       # Added to Maritime domain base score
ENERGY_CRISIS_BOOST = 25         # Added to Energy domain base score
