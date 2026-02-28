-- SQLite schema for WGYD Monitoring Pack (raw -> clean -> gold)

-- RAW: store ingested submissions (as standardized fields)
DROP TABLE IF EXISTS raw_submissions;
CREATE TABLE raw_submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_month TEXT NOT NULL,
  team TEXT NOT NULL,
  indicator_code TEXT NOT NULL,
  region TEXT,
  gender TEXT,
  age_band TEXT,
  value REAL,
  submitted_on TEXT,
  source_file TEXT NOT NULL,
  loaded_at TEXT NOT NULL
);

-- INDICATOR REGISTRY
DROP TABLE IF EXISTS dim_indicator_registry;
CREATE TABLE dim_indicator_registry (
  indicator_code TEXT PRIMARY KEY,
  indicator_name TEXT NOT NULL,
  definition TEXT,
  unit TEXT,
  disagg_required TEXT,
  data_source TEXT,
  baseline REAL,
  target REAL,
  frequency TEXT,
  owner TEXT
);

-- EXCEPTIONS LOG (validation issues)
DROP TABLE IF EXISTS dq_exceptions;
CREATE TABLE dq_exceptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_month TEXT,
  team TEXT,
  indicator_code TEXT,
  field TEXT,
  issue TEXT,
  severity TEXT,
  source_file TEXT,
  row_ref TEXT,
  created_at TEXT NOT NULL
);

-- CLEAN: validated/standardized rows (only “accepted” records)
DROP TABLE IF EXISTS clean_submissions;
CREATE TABLE clean_submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_month TEXT NOT NULL,
  team TEXT NOT NULL,
  indicator_code TEXT NOT NULL,
  region TEXT,
  gender TEXT,
  age_band TEXT,
  value REAL,
  submitted_on TEXT,
  source_file TEXT NOT NULL,
  loaded_at TEXT NOT NULL
);

-- GOLD: indicator mart aggregated for reporting
DROP TABLE IF EXISTS gold_indicator_mart;
CREATE TABLE gold_indicator_mart (
  report_month TEXT NOT NULL,
  indicator_code TEXT NOT NULL,
  region TEXT,
  gender TEXT,
  age_band TEXT,
  actual_value REAL NOT NULL,
  baseline REAL,
  target REAL,
  progress_to_target REAL,
  PRIMARY KEY (report_month, indicator_code, region, gender, age_band)
);

-- Helpful view: indicator summary at national level (no disagg)
DROP VIEW IF EXISTS vw_indicator_summary_national;
CREATE VIEW vw_indicator_summary_national AS
SELECT
  g.report_month,
  g.indicator_code,
  r.indicator_name,
  SUM(g.actual_value) AS actual_value,
  MAX(g.baseline) AS baseline,
  MAX(g.target) AS target,
  CASE WHEN MAX(g.target) IS NULL OR MAX(g.target)=0 THEN NULL
       ELSE ROUND(SUM(g.actual_value) * 1.0 / MAX(g.target), 4)
  END AS progress_to_target
FROM gold_indicator_mart g
JOIN dim_indicator_registry r USING (indicator_code)
GROUP BY g.report_month, g.indicator_code, r.indicator_name;
