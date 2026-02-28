-- Trend: indicator totals by month (national)
DROP VIEW IF EXISTS vw_indicator_trend_national;
CREATE VIEW vw_indicator_trend_national AS
SELECT
  g.report_month,
  g.indicator_code,
  r.indicator_name,
  SUM(g.actual_value) AS actual_value,
  MAX(g.target) AS target,
  CASE WHEN MAX(g.target) IS NULL OR MAX(g.target)=0 THEN NULL
       ELSE ROUND(SUM(g.actual_value) * 1.0 / MAX(g.target), 4)
  END AS progress_to_target
FROM gold_indicator_mart g
JOIN dim_indicator_registry r USING (indicator_code)
GROUP BY g.report_month, g.indicator_code, r.indicator_name;

-- Data quality counts by month
DROP VIEW IF EXISTS vw_dq_exceptions_monthly;
CREATE VIEW vw_dq_exceptions_monthly AS
SELECT
  report_month,
  severity,
  COUNT(*) AS n
FROM dq_exceptions
GROUP BY report_month, severity;

-- Suspected late/invalid submission dates by month and team
DROP VIEW IF EXISTS vw_late_reporting_flags;
CREATE VIEW vw_late_reporting_flags AS
SELECT
  report_month,
  team,
  COUNT(*) AS flagged_rows
FROM raw_submissions
WHERE submitted_on IS NULL OR LENGTH(submitted_on) < 10
GROUP BY report_month, team;