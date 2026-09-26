-- Telemetry Time-Series Edge Storage Schema
-- Mission 1 Contract for Predictive Hardware Failure Dashboard

CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                     -- UTC ISO-8601 formatted string (e.g. 2026-09-27T01:45:00.123456Z)
    cpu_usage_pct REAL NOT NULL,                 -- CPU usage percentage (0.0 - 100.0)
    memory_usage_pct REAL NOT NULL,              -- Memory usage percentage (0.0 - 100.0)
    temperature_c REAL,                          -- System or component temperature in Celsius (nullable)
    reallocated_sectors INTEGER,                 -- SMART 5: Reallocated Sectors Count (nullable)
    pending_sectors INTEGER,                     -- SMART 197: Current Pending Sector Count (nullable)
    read_error_rate REAL,                        -- SMART 1: Raw Read Error Rate (nullable)
    disk_temp_c REAL,                            -- SMART 194: Disk Temperature in Celsius (nullable)
    disk_status TEXT,                            -- SMART Health assessment: 'PASSED', 'FAILED', or 'UNKNOWN'
    load_avg_1m REAL,                            -- 1-minute load average (nullable on Windows)
    load_avg_5m REAL,                            -- 5-minute load average (nullable on Windows)
    load_avg_15m REAL,                           -- 15-minute load average (nullable on Windows)
    entity_class TEXT NOT NULL CHECK(entity_class IN ('HDD', 'RAM', 'CPU')),
    host_id TEXT NOT NULL                        -- Machine/Node identifier
);

-- Optimize for fast temporal queries and entity-sliced retrieval
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_entity_ts ON telemetry (entity_class, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_host_ts ON telemetry (host_id, timestamp DESC);
