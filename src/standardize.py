from __future__ import annotations

from pathlib import Path
import pandas as pd


STANDARD_COLS = [
    "report_month",
    "team",
    "indicator_code",
    "region",
    "gender",
    "age_band",
    "value",
    "submitted_on",
]


COLUMN_ALIASES = {
    # month field
    "month": "report_month",
    "report_month": "report_month",
    # indicator field
    "indicator": "indicator_code",
    "indicator_code": "indicator_code",
    # value field
    "reported_value": "value",
    "value": "value",
    # age
    "age_group": "age_band",
    "age_band": "age_band",
    # submitted date
    "submission_date": "submitted_on",
    "submitted_on": "submitted_on",
}


def _normalize_colnames(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def standardize_submission(df: pd.DataFrame, source_file: Path) -> pd.DataFrame:
    df = _normalize_colnames(df)

    # rename known aliases
    rename_map = {c: COLUMN_ALIASES[c] for c in df.columns if c in COLUMN_ALIASES}
    df = df.rename(columns=rename_map)

    # ensure all standard columns exist
    for c in STANDARD_COLS:
        if c not in df.columns:
            df[c] = None

    # keep only standard cols (in order)
    df = df[STANDARD_COLS].copy()

    # clean whitespace & normalize region variants
    df["region"] = df["region"].astype("string").str.strip()
    df["region"] = df["region"].replace(
        {
            "NORTH": "North",
            "Nrth": "North",
            "North ": "North",
        }
    )

    # parse submitted_on (accept YYYY-MM-DD or YYYY/MM/DD)
    df["submitted_on"] = df["submitted_on"].astype("string").str.replace("/", "-", regex=False)

    # numeric value
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # add metadata columns for loading
    df["source_file"] = source_file.name

    return df