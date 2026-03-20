"""Compute domain scores and overall composite risk score."""

import logging
from datetime import datetime, timezone
from config import DOMAINS, risk_level, CRISIS_ZONES, GEOPOLITICAL_CRISIS_BOOST, MARITIME_CRISIS_BOOST, ENERGY_CRISIS_BOOST
import database

logger = logging.getLogger(__name__)


def compute_all():
    """Run full scoring pipeline: domain scores → overall score → save everything."""
    indicators = database.get_indicators()
    zones = database.get_zones()

    # Build lookup: indicator_id → risk_score
    ind_scores = {ind["id"]: ind.get("risk_score", 50) for ind in indicators}

    # Build lookup: zone category → list of scores
    zone_by_cat = {}
    for z in zones:
        cat = z["category"]
        if cat not in zone_by_cat:
            zone_by_cat[cat] = []
        zone_by_cat[cat].append(z["score"])

    # ── Compute domain scores ──
    domain_results = []
    now = datetime.now(timezone.utc).isoformat()

    for domain_name, cfg in DOMAINS.items():
        scores = []

        # Add indicator scores for this domain
        for ind_id in cfg.get("indicator_ids", []):
            if ind_id in ind_scores:
                scores.append(ind_scores[ind_id])

        # Add zone scores for this domain's category
        zone_cat = cfg.get("zone_category")
        if zone_cat and zone_cat in zone_by_cat:
            scores.extend(zone_by_cat[zone_cat])

        # If no data, give a default mid-range score
        if scores:
            domain_score = int(sum(scores) / len(scores))
        else:
            domain_score = 30  # Default LOW when no data

        # Apply crisis boosts when active crisis zones exist
        has_crisis = len(CRISIS_ZONES) > 0
        if has_crisis:
            if domain_name == "Geopolitical":
                domain_score = min(100, domain_score + GEOPOLITICAL_CRISIS_BOOST)
            elif domain_name == "Maritime":
                domain_score = min(100, domain_score + MARITIME_CRISIS_BOOST)
            elif domain_name == "Energy":
                domain_score = min(100, domain_score + ENERGY_CRISIS_BOOST)

        domain_results.append({
            "domain": domain_name,
            "score": domain_score,
            "level": risk_level(domain_score),
            "updated_at": now,
        })

    # Save domain scores
    database.save_domain_scores(domain_results)

    # ── Compute overall composite score ──
    total_weight = sum(cfg["weight"] for cfg in DOMAINS.values())
    if total_weight == 0:
        total_weight = 1

    weighted_sum = 0
    for dr in domain_results:
        weight = DOMAINS.get(dr["domain"], {}).get("weight", 0)
        weighted_sum += dr["score"] * weight

    overall_score = int(weighted_sum / total_weight)

    # Count risk levels across indicators + zones
    all_levels = [ind["risk_level"] for ind in indicators] + [z["risk_level"] for z in zones]
    high_count = sum(1 for l in all_levels if l == "HIGH")
    medium_count = sum(1 for l in all_levels if l == "MEDIUM")
    low_count = sum(1 for l in all_levels if l == "LOW")

    # Compute trend (vs previous history point)
    history = database.get_history(2)
    if len(history) >= 1:
        prev = history[-1]["score"]
        trend = round(((overall_score - prev) / max(prev, 1)) * 100, 1)
    else:
        trend = 0

    # Save summary
    summary = {
        "overall_score": overall_score,
        "level": risk_level(overall_score),
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "last_updated": now,
        "trend": trend,
    }
    database.save_summary(summary)

    # Append to history (overall + domain snapshots)
    date_str = datetime.now(timezone.utc).strftime("%b %d")
    database.append_history(date_str, overall_score)
    database.snapshot_domain_scores(date_str, domain_results)

    logger.info(f"Scoring complete: overall={overall_score} ({risk_level(overall_score)}), "
                f"H={high_count} M={medium_count} L={low_count}")

    return summary
