PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS indicators (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    change REAL DEFAULT 0,
    risk_level TEXT NOT NULL DEFAULT 'LOW',
    risk_score INTEGER NOT NULL DEFAULT 0,
    date TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    source TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS risk_zones (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    score INTEGER NOT NULL DEFAULT 50,
    risk_level TEXT NOT NULL DEFAULT 'MEDIUM',
    category TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS domain_scores (
    domain TEXT PRIMARY KEY,
    score INTEGER NOT NULL DEFAULT 50,
    level TEXT NOT NULL DEFAULT 'MEDIUM',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS risk_history (
    date TEXT PRIMARY KEY,
    score INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS domain_history (
    snapshot_date TEXT NOT NULL,
    domain TEXT NOT NULL,
    score INTEGER NOT NULL,
    level TEXT NOT NULL,
    PRIMARY KEY (snapshot_date, domain)
);

CREATE TABLE IF NOT EXISTS risk_summary (
    id INTEGER PRIMARY KEY DEFAULT 1,
    overall_score INTEGER NOT NULL DEFAULT 50,
    level TEXT NOT NULL DEFAULT 'MEDIUM',
    high_count INTEGER NOT NULL DEFAULT 0,
    medium_count INTEGER NOT NULL DEFAULT 0,
    low_count INTEGER NOT NULL DEFAULT 0,
    indicator_high_count INTEGER NOT NULL DEFAULT 0,
    indicator_medium_count INTEGER NOT NULL DEFAULT 0,
    indicator_low_count INTEGER NOT NULL DEFAULT 0,
    zone_high_count INTEGER NOT NULL DEFAULT 0,
    zone_medium_count INTEGER NOT NULL DEFAULT 0,
    zone_low_count INTEGER NOT NULL DEFAULT 0,
    last_updated TEXT NOT NULL DEFAULT (datetime('now')),
    trend REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS vessel_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mmsi TEXT NOT NULL,
    name TEXT,
    ship_type INTEGER,
    ship_type_label TEXT,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    speed REAL,
    heading REAL,
    nav_status INTEGER,
    zone TEXT,
    is_dark INTEGER DEFAULT 0,
    recorded_at TEXT NOT NULL,
    UNIQUE(mmsi, recorded_at)
);

CREATE INDEX IF NOT EXISTS idx_vp_mmsi ON vessel_positions(mmsi);
CREATE INDEX IF NOT EXISTS idx_vp_zone ON vessel_positions(zone);
CREATE INDEX IF NOT EXISTS idx_vp_recorded ON vessel_positions(recorded_at);
CREATE INDEX IF NOT EXISTS idx_vp_speed ON vessel_positions(speed);
