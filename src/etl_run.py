from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import settings
from src.db import sqlite_connect
from src.io_inputs import list_submission_files, read_submission
from src.standardize import standardize_submission
from src.validate import validate
from src.brief_generate import generate_monthly_brief

def read_registry_codes() -> set[str]:
    reg = pd.read_excel(Path(settings.indicator_registry_path), sheet_name="indicator_registry")
    return set(reg["indicator_code"].astype(str).tolist())

def load_registry(conn):
    reg_path = Path(settings.indicator_registry_path)
    registry = pd.read_excel(reg_path, sheet_name="indicator_registry")
    registry.to_sql("dim_indicator_registry", conn, if_exists="replace", index=False)

def append_df(conn, table: str, df: pd.DataFrame):
    df.to_sql(table, conn, if_exists="append", index=False)

def rebuild_gold(conn):
    # Clear gold mart and rebuild from clean + registry
    conn.execute("DELETE FROM gold_indicator_mart;")

    query = """
    INSERT INTO gold_indicator_mart
    (report_month, indicator_code, region, gender, age_band, actual_value, baseline, target, progress_to_target)
    SELECT
      c.report_month,
      c.indicator_code,
      c.region,
      c.gender,
      c.age_band,
      SUM(COALESCE(c.value,0)) AS actual_value,
      r.baseline,
      r.target,
      CASE WHEN r.target IS NULL OR r.target = 0 THEN NULL
           ELSE ROUND(SUM(COALESCE(c.value,0)) * 1.0 / r.target, 4)
      END AS progress_to_target
    FROM clean_submissions c
    LEFT JOIN dim_indicator_registry r
      ON c.indicator_code = r.indicator_code
    GROUP BY c.report_month, c.indicator_code, c.region, c.gender, c.age_band, r.baseline, r.target;
    """
    conn.execute(query)
    conn.commit()

def run_month(report_month: str):
    loaded_at = datetime.utcnow().isoformat(timespec="seconds")
    valid_codes = read_registry_codes()
    

    files = list_submission_files(report_month)
    if not files:
        raise FileNotFoundError(f"No submissions found in {Path(settings.raw_submissions_dir)/report_month}")

    all_raw = []
    all_clean = []
    all_exceptions = []

    for f in files:
        df = read_submission(f)
        std = standardize_submission(df, f)
        std["loaded_at"] = loaded_at

        # validate
        res = validate(std, valid_codes)

        all_raw.append(std)
        all_clean.append(res.clean)
        if not res.exceptions.empty:
            all_exceptions.append(res.exceptions)

    raw_df = pd.concat(all_raw, ignore_index=True)
    clean_df = pd.concat(all_clean, ignore_index=True)
    exc_df = pd.concat(all_exceptions, ignore_index=True) if all_exceptions else pd.DataFrame(
        columns=["report_month","team","indicator_code","field","issue","severity","source_file","row_ref","created_at"]
    )

    # persist to DB
    conn = sqlite_connect()
    try:
        load_registry(conn)

        # clear month data to make reruns idempotent
        conn.execute("DELETE FROM raw_submissions WHERE report_month = ?;", (report_month,))
        conn.execute("DELETE FROM clean_submissions WHERE report_month = ?;", (report_month,))
        conn.execute("DELETE FROM dq_exceptions WHERE report_month = ?;", (report_month,))
        conn.commit()

        append_df(conn, "raw_submissions", raw_df)
        append_df(conn, "clean_submissions", clean_df)
        if not exc_df.empty:
            append_df(conn, "dq_exceptions", exc_df)

        rebuild_gold(conn)
    finally:
        conn.close()

    # Write exceptions report to file
    out_dir = Path(settings.output_exceptions_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"exceptions_{report_month}.csv"
    exc_df.to_csv(out_path, index=False)
    print(f"Month processed: {report_month}")
    print(f"Files read: {len(files)}")
    print(f"Raw rows loaded: {len(raw_df)}")
    print(f"Clean rows loaded: {len(clean_df)}")
    print(f"Exceptions logged: {len(exc_df)}")
    print(f"Exceptions report: {out_path}")

    brief_path = generate_monthly_brief(report_month)
    print(f"Monthly brief: {brief_path}")

if __name__ == "__main__":
    import sys
    month = sys.argv[1] if len(sys.argv) > 1 else settings.report_month
    run_month(month)
