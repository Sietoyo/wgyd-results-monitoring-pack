from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import pandas as pd


@dataclass
class ValidationResult:
    clean: pd.DataFrame
    exceptions: pd.DataFrame


REQUIRED_FIELDS = ["report_month", "team", "indicator_code", "value"]
VALID_REGIONS = {"North", "South", "East", "West"}


def validate(df: pd.DataFrame, valid_indicator_codes: set[str]) -> ValidationResult:
    """
    Rules:
    - ERROR: missing required fields, non-numeric value, negative value, indicator not in registry
    - WARNING: missing/invalid region, duplicate records, invalid date format, suspicious outliers
    """
    df = df.copy()
    issues = []

    def now_utc():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def log_issue(ix, field, issue, severity="error"):
        issues.append(
            {
                "report_month": df.at[ix, "report_month"] if "report_month" in df.columns else None,
                "team": df.at[ix, "team"] if "team" in df.columns else None,
                "indicator_code": df.at[ix, "indicator_code"] if "indicator_code" in df.columns else None,
                "field": field,
                "issue": issue,
                "severity": severity,
                "source_file": df.at[ix, "source_file"] if "source_file" in df.columns else None,
                "row_ref": str(ix),
                "created_at": now_utc(),
            }
        )

    # 1) Required fields
    for f in REQUIRED_FIELDS:
        missing = df[f].isna() | (df[f].astype("string").str.strip() == "")
        for ix in df[missing].index:
            log_issue(ix, f, "Missing required field", "error")

    # 2) Indicator must exist in registry
    bad_indicator = ~df["indicator_code"].astype("string").isin(valid_indicator_codes)
    for ix in df[bad_indicator].index:
        log_issue(ix, "indicator_code", "Indicator code not found in registry", "error")

    # 3) Value rules
    bad_value = df["value"].isna()
    for ix in df[bad_value].index:
        log_issue(ix, "value", "Value is not numeric", "error")

    negative = df["value"].fillna(0) < 0
    for ix in df[negative].index:
        log_issue(ix, "value", "Negative values not allowed", "error")

    # 4) Region quality (warning)
    if "region" in df.columns:
        missing_region = df["region"].isna() | (df["region"].astype("string").str.strip() == "")
        for ix in df[missing_region].index:
            log_issue(ix, "region", "Missing region (disaggregation incomplete)", "warning")

        invalid_region = (~missing_region) & (~df["region"].astype("string").isin(VALID_REGIONS))
        for ix in df[invalid_region].index:
            log_issue(ix, "region", f"Invalid region value: {df.at[ix, 'region']}", "warning")

    # 5) Date format check (warning)
    if "submitted_on" in df.columns:
        bad_date = df["submitted_on"].isna() | (
            ~df["submitted_on"].astype("string").str.match(r"^\d{4}-\d{2}-\d{2}$")
        )
        for ix in df[bad_date].index:
            log_issue(ix, "submitted_on", "Invalid date format (expected YYYY-MM-DD)", "warning")

    # 6) Duplicate detection (warning)
    # duplicates across key dimensions
    key_cols = ["report_month", "team", "indicator_code", "region", "gender", "age_band"]
    key_cols = [c for c in key_cols if c in df.columns]
    if key_cols:
        dup_mask = df.duplicated(subset=key_cols, keep="first")
        for ix in df[dup_mask].index:
            log_issue(ix, "record", f"Duplicate record detected on keys: {', '.join(key_cols)}", "warning")

    # 7) Outlier detection (warning) — simple thresholding
    # Flag unusually large values relative to team distribution
    if df["value"].notna().sum() > 10:
        v = df["value"].dropna()
        q1, q3 = v.quantile(0.25), v.quantile(0.75)
        iqr = q3 - q1
        upper = q3 + 3 * iqr  # lenient
        outlier_mask = df["value"] > upper
        for ix in df[outlier_mask].index:
            log_issue(ix, "value", f"Potential outlier value: {df.at[ix, 'value']} (upper bound ~ {round(float(upper),2)})", "warning")

    exceptions_df = pd.DataFrame(issues)

    # Reject rows that have ANY error
    error_rows = (
        set(exceptions_df.loc[exceptions_df["severity"] == "error", "row_ref"].astype(str).tolist())
        if not exceptions_df.empty
        else set()
    )
    reject_mask = df.index.astype(str).isin(error_rows)
    clean_df = df.loc[~reject_mask].copy()

    return ValidationResult(clean=clean_df, exceptions=exceptions_df)