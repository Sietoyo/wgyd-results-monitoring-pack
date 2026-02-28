from pathlib import Path
import pandas as pd

from src.db import sqlite_connect

EXPORT_DIR = Path("data/outputs/powerbi")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

QUERIES = {
    "gold_indicator_mart": "SELECT * FROM gold_indicator_mart;",
    "vw_indicator_summary_national": "SELECT * FROM vw_indicator_summary_national;",
    "vw_indicator_trend_national": """
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
    """,
    "dq_exceptions": "SELECT * FROM dq_exceptions;",
    "dq_exceptions_monthly": """
        SELECT report_month, severity, COUNT(*) AS n
        FROM dq_exceptions
        GROUP BY report_month, severity;
    """,
    "dim_indicator_registry": "SELECT * FROM dim_indicator_registry;",
    "late_reporting_flags": """
        SELECT report_month, team, COUNT(*) AS flagged_rows
        FROM raw_submissions
        WHERE submitted_on IS NULL OR LENGTH(submitted_on) < 10
        GROUP BY report_month, team;
    """,
}

def main():
    conn = sqlite_connect()
    try:
        for name, q in QUERIES.items():
            df = pd.read_sql_query(q, conn)
            out = EXPORT_DIR / f"{name}.csv"
            df.to_csv(out, index=False)
            print(f"Exported: {out} ({len(df)} rows)")
    finally:
        conn.close()
    print("Power BI exports ready:", EXPORT_DIR.resolve())

if __name__ == "__main__":
    main()