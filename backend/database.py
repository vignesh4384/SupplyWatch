"""SQLite database layer for SupplyWatch."""

import sqlite3
import os
from datetime import datetime, timezone
from contextlib import contextmanager
from config import DB_PATH, STATIC_INDICATORS, TRADE_ROUTES, DOMAINS, risk_level as calc_risk_level

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
                "INSERT INTO risk_summary (id, overall_score, level, high_count, medium_count, low_count, last_updated, trend) VALUES (1,50,'MEDIUM',0,5,5,?,0)",
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
            INSERT INTO risk_summary (id, overall_score, level, high_count, medium_count, low_count, last_updated, trend)
            VALUES (1, :overall_score, :level, :high_count, :medium_count, :low_count, :last_updated, :trend)
            ON CONFLICT(id) DO UPDATE SET
                overall_score=excluded.overall_score, level=excluded.level,
                high_count=excluded.high_count, medium_count=excluded.medium_count,
                low_count=excluded.low_count, last_updated=excluded.last_updated, trend=excluded.trend
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
