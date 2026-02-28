import os
import random
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

from src.config import settings


def ensure_dirs(months):
    Path(settings.raw_submissions_dir).mkdir(parents=True, exist_ok=True)
    Path("data/indicator_registry").mkdir(parents=True, exist_ok=True)
    for m in months:
        Path(settings.raw_submissions_dir, m).mkdir(parents=True, exist_ok=True)


def build_indicator_registry() -> pd.DataFrame:
    # WGYD-themed example indicators (youth, women, GBV, enterprise)
    rows = [
        {
            "indicator_code": "YTH_EMP_001",
            "indicator_name": "Youth employment placements supported",
            "definition": "Number of youth (15–35) placed into paid employment through supported programs.",
            "unit": "count",
            "disagg_required": "gender,age_band,region",
            "data_source": "Programme partner submissions",
            "baseline": 0,
            "target": 1200,
            "frequency": "monthly",
            "owner": "WGYD M&E",
        },
        {
            "indicator_code": "WEE_BIZ_002",
            "indicator_name": "Women-led SMEs receiving business support",
            "definition": "Number of women-led SMEs receiving training, grants, or advisory support.",
            "unit": "count",
            "disagg_required": "region",
            "data_source": "Programme partner submissions",
            "baseline": 0,
            "target": 600,
            "frequency": "monthly",
            "owner": "WGYD M&E",
        },
        {
            "indicator_code": "GBV_SRV_003",
            "indicator_name": "GBV survivors receiving services",
            "definition": "Number of GBV survivors who accessed at least one formal support service.",
            "unit": "count",
            "disagg_required": "gender,age_band,region",
            "data_source": "Service provider submissions",
            "baseline": 0,
            "target": 900,
            "frequency": "monthly",
            "owner": "WGYD GBV Desk",
        },
        {
            "indicator_code": "YTH_TRN_004",
            "indicator_name": "Youth completing skills training",
            "definition": "Number of youth completing an accredited skills training supported by the program.",
            "unit": "count",
            "disagg_required": "gender,age_band,region",
            "data_source": "Training provider submissions",
            "baseline": 0,
            "target": 1500,
            "frequency": "monthly",
            "owner": "WGYD Youth Desk",
        },
        {
            "indicator_code": "WLD_LDR_005",
            "indicator_name": "Women participating in leadership programs",
            "definition": "Number of women participating in leadership/mentorship programs supported by WGYD initiatives.",
            "unit": "count",
            "disagg_required": "region",
            "data_source": "Programme partner submissions",
            "baseline": 0,
            "target": 800,
            "frequency": "monthly",
            "owner": "WGYD Gender Desk",
        },
    ]
    return pd.DataFrame(rows)


def save_registry_xlsx(df: pd.DataFrame, out_path: str):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="indicator_registry")


def make_months():
    # Use the report_month and generate 3 months ending at report_month
    # Format: YYYY-MM
    end = datetime.strptime(settings.report_month, "%Y-%m")
    months = []
    year = end.year
    month = end.month
    for _ in range(3):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return sorted(months)


def generate_team_submission(registry: pd.DataFrame, month: str, team_name: str) -> pd.DataFrame:
    # Create rows per indicator x disaggregation combo (small but realistic)
    regions = ["North", "South", "East", "West"]
    genders = ["Female", "Male"]
    age_bands = ["15-19", "20-24", "25-29", "30-35"]

    rows = []
    for _, ind in registry.iterrows():
        code = ind["indicator_code"]
        # messy: some teams omit some disaggregations
        for region in random.sample(regions, k=random.randint(2, 4)):
            gender = random.choice(genders)
            age_band = random.choice(age_bands)
            # value generation
            base = random.randint(10, 90)
            value = base + random.randint(-5, 25)

            rows.append(
                {
                    "report_month": month,
                    "team": team_name,
                    "indicator_code": code,
                    "region": region,
                    "gender": gender,
                    "age_band": age_band,
                    "value": max(0, value),
                    "submitted_on": f"{month}-" + str(random.randint(1, 28)).zfill(2),
                }
            )

    df = pd.DataFrame(rows)

    # Inject realistic mess:
    # 1) inconsistent column naming by team
    if team_name in ["Team_B", "Team_D"]:
        df = df.rename(columns={"report_month": "month", "indicator_code": "indicator", "submitted_on": "submission_date"})
    if team_name in ["Team_C"]:
        df = df.rename(columns={"value": "reported_value", "age_band": "age_group"})

    # 2) missing values
    if random.random() < 0.5:
        ix = df.sample(frac=0.03, random_state=random.randint(1, 999)).index
        df.loc[ix, "region"] = None

    # 3) duplicate rows
    if random.random() < 0.5 and len(df) > 10:
        df = pd.concat([df, df.sample(5, random_state=random.randint(1, 999))], ignore_index=True)

    # 4) odd date formats
    if "submission_date" in df.columns and random.random() < 0.7:
        df["submission_date"] = df["submission_date"].astype(str).str.replace("-", "/")

    # 5) spelling inconsistencies
    if "region" in df.columns and random.random() < 0.6:
        df.loc[df["region"] == "North", "region"] = random.choice(["NORTH", "Nrth", "North "])

    return df


def save_team_excel(df: pd.DataFrame, out_file: Path):
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="submission")


def main():
    random.seed(42)

    months = make_months()
    teams = ["Team_A", "Team_B", "Team_C", "Team_D", "Team_E"]

    ensure_dirs(months)

    registry = build_indicator_registry()
    save_registry_xlsx(registry, settings.indicator_registry_path)
    print(f"Saved indicator registry: {settings.indicator_registry_path}")

    for month in months:
        for t in teams:
            df = generate_team_submission(registry, month, t)
            fname = f"{t}_submission_{month}.xlsx"
            out_path = Path(settings.raw_submissions_dir) / month / fname
            save_team_excel(df, out_path)

    print(f"Generated messy submissions for months: {months} in {settings.raw_submissions_dir}")
    print("Done.")


if __name__ == "__main__":
    main()