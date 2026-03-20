"""Fetch real-time commodity prices from Yahoo Finance (free, no API key)."""

import logging
from datetime import datetime, timezone
import yfinance as yf
from config import risk_level as calc_risk_level

logger = logging.getLogger(__name__)

# Yahoo Finance tickers → SupplyWatch indicator mapping
YAHOO_TICKERS = [
    {"ticker": "BZ=F", "id": "brent", "name": "Brent Crude Oil", "unit": "USD/bbl", "category": "energy",
     "high_threshold": 100, "medium_threshold": 80},
    {"ticker": "CL=F", "id": "wti", "name": "WTI Crude Oil", "unit": "USD/bbl", "category": "energy",
     "high_threshold": 95, "medium_threshold": 75},
    {"ticker": "NG=F", "id": "natgas", "name": "Natural Gas", "unit": "USD/MMBtu", "category": "energy",
     "high_threshold": 5.0, "medium_threshold": 3.0},
    {"ticker": "RB=F", "id": "gasoline", "name": "US Gasoline", "unit": "USD/gal", "category": "energy",
     "high_threshold": 4.0, "medium_threshold": 3.0},
    {"ticker": "HG=F", "id": "copper", "name": "Copper", "unit": "USD/ton", "category": "raw_materials",
     "high_threshold": 9500, "medium_threshold": 8000, "multiplier": 2204.62},  # USD/lb → USD/metric-ton (1 ton = 2204.62 lbs)
    {"ticker": "ALI=F", "id": "aluminum", "name": "Aluminum", "unit": "USD/ton", "category": "raw_materials",
     "high_threshold": 2800, "medium_threshold": 2200, "multiplier": 1},  # already USD/ton
]


def fetch_yfinance_indicators() -> list[dict]:
    """Fetch real-time prices from Yahoo Finance. Synchronous (yfinance uses requests internally)."""
    indicators = []
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%b %d").replace(" 0", " ")

    for cfg in YAHOO_TICKERS:
        try:
            ticker = yf.Ticker(cfg["ticker"])
            hist = ticker.history(period="5d")

            if hist.empty:
                logger.warning(f"No data for {cfg['ticker']}")
                continue

            current_price = float(hist["Close"].iloc[-1])
            prev_price = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price

            # Apply multiplier if needed (e.g., copper lbs → ton)
            multiplier = cfg.get("multiplier", 1)
            current_val = round(current_price * multiplier, 2)
            prev_val = round(prev_price * multiplier, 2)

            change = round(((current_val - prev_val) / prev_val) * 100, 1) if prev_val != 0 else 0

            # Score
            score, level = score_value(cfg, current_val)

            indicators.append({
                "id": cfg["id"],
                "name": cfg["name"],
                "category": cfg["category"],
                "value": current_val,
                "unit": cfg["unit"],
                "change": change,
                "risk_level": level,
                "risk_score": score,
                "date": date_str,
                "fetched_at": now.isoformat(),
            })

            logger.debug(f"YF {cfg['ticker']}: ${current_val} ({change:+.1f}%) → {level}")

        except Exception as e:
            logger.warning(f"YFinance {cfg['ticker']} failed: {e}")
            continue

    logger.info(f"YFinance: fetched {len(indicators)}/{len(YAHOO_TICKERS)} real-time prices")
    return indicators


def score_value(cfg: dict, value: float) -> tuple[int, str]:
    """Score a value against thresholds."""
    high_t = cfg["high_threshold"]
    med_t = cfg["medium_threshold"]

    if value >= high_t:
        score = min(100, int(66 + (value - high_t) / high_t * 34))
    elif value >= med_t:
        score = int(41 + (value - med_t) / (high_t - med_t) * 25)
    else:
        score = max(0, int(value / med_t * 40))

    level = "HIGH" if score >= 66 else "MEDIUM" if score >= 41 else "LOW"
    return score, level
