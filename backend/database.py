"""SQLite database layer for SupplyWatch."""

import sqlite3
import os
from datetime import datetime, timezone
from contextlib import contextmanager
from config import DB_PATH, STATIC_INDICATORS, TRADE_ROUTES, DOMAINS, risk_level as calc_risk_level, NAV_STATUS_LABELS

# If DB_PATH is absolute (e.g. /home/data/supplywatch.db on Azure), use it directly
DB_FILE = DB_PATH if os.path.isabs(DB_PATH) else os.path.join(os.path.dirname(__file__), DB_PATH)
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables and seed with initial data if empty."""
    with get_db() as db:
        with open(SCHEMA_FILE) as f:
            db.executescript(f.read())

        # Auto-migrate: add split count columns if missing
        existing_cols = {r[1] for r in db.execute("PRAGMA table_info(risk_summary)").fetchall()}
        for col in ["indicator_high_count", "indicator_medium_count", "indicator_low_count",
                     "zone_high_count", "zone_medium_count", "zone_low_count"]:
            if col not in existing_cols:
                db.execute(f"ALTER TABLE risk_summary ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0")

        # Seed static indicators if table is empty
        count = db.execute("SELECT COUNT(*) FROM indicators").fetchone()[0]
        if count == 0:
            now = datetime.now(timezone.utc).isoformat()
            for ind in STATIC_INDICATORS:
                db.execute(
                    "INSERT OR IGNORE INTO indicators (id, name, category, value, unit, change, risk_level, risk_score, date, fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (ind["id"], ind["name"], ind["category"], ind["value"], ind["unit"],
                     ind["change"], ind["risk_level"], 50, ind["date"], now)
                )

        # Seed domain scores if empty
        dcount = db.execute("SELECT COUNT(*) FROM domain_scores").fetchone()[0]
        if dcount == 0:
            for domain in DOMAINS:
                db.execute(
                    "INSERT INTO domain_scores (domain, score, level) VALUES (?,?,?)",
                    (domain, 50, "MEDIUM")
                )

        # Seed summary if empty
        scount = db.execute("SELECT COUNT(*) FROM risk_summary").fetchone()[0]
        if scount == 0:
            db.execute(
                "INSERT INTO risk_summary (id, overall_score, level, high_count, medium_count, low_count, indicator_high_count, indicator_medium_count, indicator_low_count, zone_high_count, zone_medium_count, zone_low_count, last_updated, trend) VALUES (1,50,'MEDIUM',0,5,5,0,3,3,0,2,2,?,0)",
                (datetime.now(timezone.utc).isoformat(),)
            )


# ── INDICATORS ──

def upsert_indicator(ind: dict):
    with get_db() as db:
        db.execute("""
            INSERT INTO indicators (id, name, category, value, unit, change, risk_level, risk_score, date, fetched_at)
            VALUES (:id, :name, :category, :value, :unit, :change, :risk_level, :risk_score, :date, :fetched_at)
            ON CONFLICT(id) DO UPDATE SET
                value=excluded.value, unit=excluded.unit, change=excluded.change,
                risk_level=excluded.risk_level, risk_score=excluded.risk_score,
                date=excluded.date, fetched_at=excluded.fetched_at
        """, ind)


def get_indicators() -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM indicators ORDER BY category, name").fetchall()
        return [dict(r) for r in rows]


# ── ALERTS ──

def upsert_alert(alert: dict):
    with get_db() as db:
        db.execute("""
            INSERT OR REPLACE INTO alerts (id, title, severity, source, timestamp, created_at)
            VALUES (:id, :title, :severity, :source, :timestamp, :created_at)
        """, alert)


def get_alerts(limit: int = 20) -> list[dict]:
    with get_db() as db:
        # Severity priority: critical > warning > info, then newest first
        rows = db.execute("""
            SELECT * FROM alerts
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'warning' THEN 2
                    WHEN 'info' THEN 3
                    ELSE 4
                END,
                created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── RISK ZONES ──

def upsert_zone(zone: dict):
    with get_db() as db:
        db.execute("""
            INSERT INTO risk_zones (id, name, lat, lng, score, risk_level, category, description, updated_at)
            VALUES (:id, :name, :lat, :lng, :score, :risk_level, :category, :description, :updated_at)
            ON CONFLICT(id) DO UPDATE SET
                score=excluded.score, risk_level=excluded.risk_level,
                description=excluded.description, updated_at=excluded.updated_at
        """, zone)


def get_zones() -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM risk_zones ORDER BY score DESC").fetchall()
        return [dict(r) for r in rows]


# ── DOMAIN SCORES ──

def save_domain_scores(domains: list[dict]):
    with get_db() as db:
        for d in domains:
            db.execute("""
                INSERT INTO domain_scores (domain, score, level, updated_at) VALUES (:domain, :score, :level, :updated_at)
                ON CONFLICT(domain) DO UPDATE SET score=excluded.score, level=excluded.level, updated_at=excluded.updated_at
            """, d)


def get_domain_scores() -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT domain, score, level FROM domain_scores ORDER BY score DESC").fetchall()
        return [dict(r) for r in rows]


# ── SUMMARY ──

def save_summary(summary: dict):
    with get_db() as db:
        db.execute("""
            INSERT INTO risk_summary (id, overall_score, level, high_count, medium_count, low_count,
                indicator_high_count, indicator_medium_count, indicator_low_count,
                zone_high_count, zone_medium_count, zone_low_count,
                last_updated, trend)
            VALUES (1, :overall_score, :level, :high_count, :medium_count, :low_count,
                :indicator_high_count, :indicator_medium_count, :indicator_low_count,
                :zone_high_count, :zone_medium_count, :zone_low_count,
                :last_updated, :trend)
            ON CONFLICT(id) DO UPDATE SET
                overall_score=excluded.overall_score, level=excluded.level,
                high_count=excluded.high_count, medium_count=excluded.medium_count,
                low_count=excluded.low_count,
                indicator_high_count=excluded.indicator_high_count,
                indicator_medium_count=excluded.indicator_medium_count,
                indicator_low_count=excluded.indicator_low_count,
                zone_high_count=excluded.zone_high_count,
                zone_medium_count=excluded.zone_medium_count,
                zone_low_count=excluded.zone_low_count,
                last_updated=excluded.last_updated, trend=excluded.trend
        """, summary)


def get_summary() -> dict:
    with get_db() as db:
        row = db.execute("SELECT * FROM risk_summary WHERE id=1").fetchone()
        return dict(row) if row else {}


# ── HISTORY ──

def append_history(date_str: str, score: int):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO risk_history (date, score) VALUES (?, ?)",
            (date_str, score)
        )


def get_history(days: int = 30) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT date, score FROM risk_history ORDER BY date DESC LIMIT ?", (days,)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


# ── DOMAIN HISTORY ──

def snapshot_domain_scores(date_str: str, domains: list[dict]):
    """Save a daily snapshot of all domain scores for historical tracking."""
    with get_db() as db:
        for d in domains:
            db.execute("""
                INSERT OR REPLACE INTO domain_history (snapshot_date, domain, score, level)
                VALUES (?, ?, ?, ?)
            """, (date_str, d["domain"], d["score"], d["level"]))


def get_domain_history(weeks: int = 8) -> list[dict]:
    """Retrieve domain score snapshots grouped by date, most recent first."""
    with get_db() as db:
        rows = db.execute("""
            SELECT snapshot_date, domain, score, level
            FROM domain_history
            ORDER BY snapshot_date ASC
        """).fetchall()

        # Group by unique dates and take the last N weeks worth
        all_rows = [dict(r) for r in rows]

        # Get unique dates in order
        dates = list(dict.fromkeys(r["snapshot_date"] for r in all_rows))
        recent_dates = dates[-(weeks):] if len(dates) > weeks else dates

        return [r for r in all_rows if r["snapshot_date"] in recent_dates]


# ── ROUTES ──

def get_routes() -> list[dict]:
    """Routes are static config enriched with zone-based risk scores.

    Proximity logic: only zones within 10 degrees of a route point affect that route.
    Uses weighted scoring: closer zones have more impact than distant ones.
    """
    zones = get_zones()

    routes = []
    for rt in TRADE_ROUTES:
        nearby_scores = []
        for zone in zones:
            min_dist = float('inf')
            for point in rt["points"]:
                dist = abs(zone["lat"] - point[0]) + abs(zone["lng"] - point[1])
                min_dist = min(min_dist, dist)

            # Only zones within 10 degrees affect this route
            if min_dist < 10:
                # Weight: closer zones count more (1.0 at dist=0, 0.5 at dist=10)
                weight = 1.0 - (min_dist / 20)
                nearby_scores.append(zone["score"] * weight)

        if nearby_scores:
            # Use weighted average, not max — avoids over-inflation
            route_score = int(sum(nearby_scores) / len(nearby_scores))
        else:
            route_score = 25  # Default safe

        level = calc_risk_level(route_score)
        status = "critical" if route_score >= 80 else "disrupted" if route_score >= 45 else "normal"

        routes.append({
            "id": rt["id"],
            "name": rt["name"],
            "description": rt["description"],
            "status": status,
            "riskScore": route_score,
            "points": rt["points"],
        })
    return routes


# ── VESSEL POSITIONS ──

def insert_vessel_position(pos: dict):
    """Insert a vessel position, silently skip duplicates. Detect zone transitions."""
    with get_db() as db:
        # Check previous zone for this vessel to detect transitions
        new_zone = pos.get("zone")
        if new_zone:
            prev = db.execute(
                "SELECT zone FROM vessel_positions WHERE mmsi = ? ORDER BY recorded_at DESC LIMIT 1",
                (pos["mmsi"],)
            ).fetchone()
            if prev and prev["zone"] and prev["zone"] != new_zone:
                db.execute("""
                    INSERT INTO vessel_zone_transitions (mmsi, name, ship_type_label, from_zone, to_zone, transited_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pos["mmsi"], pos.get("name"), pos.get("ship_type_label"),
                      prev["zone"], new_zone, pos["recorded_at"]))
            elif not prev and new_zone:
                # First sighting — record as entry (from_zone = NULL)
                db.execute("""
                    INSERT INTO vessel_zone_transitions (mmsi, name, ship_type_label, from_zone, to_zone, transited_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pos["mmsi"], pos.get("name"), pos.get("ship_type_label"),
                      None, new_zone, pos["recorded_at"]))

        db.execute("""
            INSERT OR IGNORE INTO vessel_positions
            (mmsi, name, ship_type, ship_type_label, lat, lng, speed, heading, nav_status, zone, is_dark, recorded_at)
            VALUES (:mmsi, :name, :ship_type, :ship_type_label, :lat, :lng, :speed, :heading, :nav_status, :zone, :is_dark, :recorded_at)
        """, pos)


def get_live_vessels(minutes: int = 15) -> list[dict]:
    """Latest position per MMSI. Shows all vessels whose last known position
    is within a monitored zone (zone IS NOT NULL), regardless of when they
    last reported — so anchored/dark vessels stay visible. Only vessels that
    moved outside all zones (zone IS NULL) or have no data within the retention
    window are excluded."""
    with get_db() as db:
        rows = db.execute("""
            SELECT vp.* FROM vessel_positions vp
            INNER JOIN (
                SELECT mmsi, MAX(recorded_at) as max_ts
                FROM vessel_positions
                GROUP BY mmsi
            ) latest ON vp.mmsi = latest.mmsi AND vp.recorded_at = latest.max_ts
            WHERE vp.zone IS NOT NULL
            ORDER BY vp.recorded_at DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_vessels_by_zone(zone: str, hours: int = 24) -> list[dict]:
    """All positions in a zone for the last N hours."""
    with get_db() as db:
        rows = db.execute("""
            SELECT * FROM vessel_positions
            WHERE zone = ? AND recorded_at >= datetime('now', ? || ' hours')
            ORDER BY recorded_at DESC
        """, (zone, f"-{hours}")).fetchall()
        return [dict(r) for r in rows]


def get_dark_vessels(zone: str | None = None, hours: int = 6) -> list[dict]:
    """Unique vessels whose latest position is flagged dark/suspicious."""
    with get_db() as db:
        if zone:
            rows = db.execute("""
                SELECT vp.* FROM vessel_positions vp
                INNER JOIN (
                    SELECT mmsi, MAX(recorded_at) as max_ts
                    FROM vessel_positions
                    WHERE zone = ? AND recorded_at >= datetime('now', ? || ' hours')
                    GROUP BY mmsi
                ) latest ON vp.mmsi = latest.mmsi AND vp.recorded_at = latest.max_ts
                WHERE vp.is_dark = 1
                ORDER BY vp.recorded_at DESC
            """, (zone, f"-{hours}")).fetchall()
        else:
            rows = db.execute("""
                SELECT vp.* FROM vessel_positions vp
                INNER JOIN (
                    SELECT mmsi, MAX(recorded_at) as max_ts
                    FROM vessel_positions
                    WHERE recorded_at >= datetime('now', ? || ' hours')
                    GROUP BY mmsi
                ) latest ON vp.mmsi = latest.mmsi AND vp.recorded_at = latest.max_ts
                WHERE vp.is_dark = 1
                ORDER BY vp.recorded_at DESC
            """, (f"-{hours}",)).fetchall()
        return [dict(r) for r in rows]


def get_slow_vessels(zone: str | None = None, max_speed: float = 2.0, hours: int = 6) -> list[dict]:
    """Vessels moving below a speed threshold."""
    with get_db() as db:
        if zone:
            rows = db.execute("""
                SELECT vp.* FROM vessel_positions vp
                INNER JOIN (
                    SELECT mmsi, MAX(recorded_at) as max_ts
                    FROM vessel_positions
                    WHERE zone = ? AND speed < ? AND speed IS NOT NULL
                    AND recorded_at >= datetime('now', ? || ' hours')
                    GROUP BY mmsi
                ) latest ON vp.mmsi = latest.mmsi AND vp.recorded_at = latest.max_ts
                ORDER BY vp.speed ASC
            """, (zone, max_speed, f"-{hours}")).fetchall()
        else:
            rows = db.execute("""
                SELECT vp.* FROM vessel_positions vp
                INNER JOIN (
                    SELECT mmsi, MAX(recorded_at) as max_ts
                    FROM vessel_positions
                    WHERE speed < ? AND speed IS NOT NULL
                    AND recorded_at >= datetime('now', ? || ' hours')
                    GROUP BY mmsi
                ) latest ON vp.mmsi = latest.mmsi AND vp.recorded_at = latest.max_ts
                ORDER BY vp.speed ASC
            """, (max_speed, f"-{hours}")).fetchall()
        return [dict(r) for r in rows]


def get_vessel_counts(zone: str | None = None, hours: int = 24) -> list[dict]:
    """Count vessels by zone and ship type label."""
    with get_db() as db:
        if zone:
            rows = db.execute("""
                SELECT zone, ship_type_label, COUNT(DISTINCT mmsi) as vessel_count
                FROM vessel_positions
                WHERE zone = ? AND recorded_at >= datetime('now', ? || ' hours')
                GROUP BY zone, ship_type_label
                ORDER BY vessel_count DESC
            """, (zone, f"-{hours}")).fetchall()
        else:
            rows = db.execute("""
                SELECT zone, ship_type_label, COUNT(DISTINCT mmsi) as vessel_count
                FROM vessel_positions
                WHERE recorded_at >= datetime('now', ? || ' hours')
                GROUP BY zone, ship_type_label
                ORDER BY zone, vessel_count DESC
            """, (f"-{hours}",)).fetchall()
        return [dict(r) for r in rows]


def get_zone_transitions(zone: str | None = None, direction: str = "both", hours: int = 96) -> list[dict]:
    """Get zone transitions. direction: 'entered', 'exited', or 'both'."""
    with get_db() as db:
        if zone and direction == "exited":
            rows = db.execute("""
                SELECT mmsi, name, ship_type_label, from_zone, to_zone, transited_at
                FROM vessel_zone_transitions
                WHERE from_zone = ? AND transited_at >= datetime('now', ? || ' hours')
                ORDER BY transited_at DESC
            """, (zone, f"-{hours}")).fetchall()
        elif zone and direction == "entered":
            rows = db.execute("""
                SELECT mmsi, name, ship_type_label, from_zone, to_zone, transited_at
                FROM vessel_zone_transitions
                WHERE to_zone = ? AND transited_at >= datetime('now', ? || ' hours')
                ORDER BY transited_at DESC
            """, (zone, f"-{hours}")).fetchall()
        elif zone:
            rows = db.execute("""
                SELECT mmsi, name, ship_type_label, from_zone, to_zone, transited_at
                FROM vessel_zone_transitions
                WHERE (from_zone = ? OR to_zone = ?) AND transited_at >= datetime('now', ? || ' hours')
                ORDER BY transited_at DESC
            """, (zone, zone, f"-{hours}")).fetchall()
        else:
            rows = db.execute("""
                SELECT mmsi, name, ship_type_label, from_zone, to_zone, transited_at
                FROM vessel_zone_transitions
                WHERE transited_at >= datetime('now', ? || ' hours')
                ORDER BY transited_at DESC
            """, (f"-{hours}",)).fetchall()
        return [dict(r) for r in rows]


def get_zone_transition_counts(zone: str, hours: int = 96) -> dict:
    """Get entry/exit counts for a zone over the time window."""
    with get_db() as db:
        entered = db.execute("""
            SELECT COUNT(DISTINCT mmsi) as count
            FROM vessel_zone_transitions
            WHERE to_zone = ? AND transited_at >= datetime('now', ? || ' hours')
        """, (zone, f"-{hours}")).fetchone()
        exited = db.execute("""
            SELECT COUNT(DISTINCT mmsi) as count
            FROM vessel_zone_transitions
            WHERE from_zone = ? AND transited_at >= datetime('now', ? || ' hours')
        """, (zone, f"-{hours}")).fetchone()
        return {
            "zone": zone,
            "hours": hours,
            "entered": entered["count"] if entered else 0,
            "exited": exited["count"] if exited else 0,
        }


def get_vessel_history(mmsi: str, hours: int = 24) -> list[dict]:
    """Position trail for one vessel."""
    with get_db() as db:
        rows = db.execute("""
            SELECT lat, lng, speed, heading, zone, recorded_at
            FROM vessel_positions
            WHERE mmsi = ? AND recorded_at >= datetime('now', ? || ' hours')
            ORDER BY recorded_at ASC
        """, (mmsi, f"-{hours}")).fetchall()
        return [dict(r) for r in rows]


def get_vessel_risk_score(zone: str) -> dict:
    """Compute a composite vessel-derived risk score for a zone (0-100)."""
    dark = get_dark_vessels(zone=zone, hours=6)
    slow = get_slow_vessels(zone=zone, max_speed=3.0, hours=6)
    counts = get_vessel_counts(zone=zone, hours=24)
    total_vessels = sum(c["vessel_count"] for c in counts)

    dark_count = len(dark)
    slow_count = len(slow)

    # Compute traffic drop % vs 7-day average
    with get_db() as db:
        row = db.execute("""
            SELECT COUNT(DISTINCT mmsi) as avg_count
            FROM vessel_positions
            WHERE zone = ? AND recorded_at >= datetime('now', '-7 days')
        """, (zone,)).fetchone()
        weekly_unique = row["avg_count"] if row else 0
        daily_avg = weekly_unique / 7 if weekly_unique > 0 else 0

    traffic_drop_pct = 0
    if daily_avg > 0:
        traffic_drop_pct = max(0, ((daily_avg - total_vessels) / daily_avg) * 100)

    score = min(100, int(
        (dark_count * 15) +
        (slow_count * 5) +
        (traffic_drop_pct * 0.3)
    ))

    return {
        "zone": zone,
        "score": score,
        "components": {
            "dark_vessel_count": dark_count,
            "slow_vessel_count": slow_count,
            "total_vessels_24h": total_vessels,
            "traffic_drop_pct": round(traffic_drop_pct, 1),
        },
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def cleanup_old_positions():
    """Delete vessel positions older than 7 days."""
    with get_db() as db:
        result = db.execute(
            "DELETE FROM vessel_positions WHERE recorded_at < datetime('now', '-7 days')"
        )
        if result.rowcount > 0:
            import logging
            logging.getLogger(__name__).info(f"TTL cleanup: removed {result.rowcount} old vessel positions")
