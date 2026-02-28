from pathlib import Path
import pandas as pd
from src.config import settings


def list_submission_files(report_month: str) -> list[Path]:
    month_dir = Path(settings.raw_submissions_dir) / report_month
    # accept both excel and csv
    files = list(month_dir.glob("*.xlsx")) + list(month_dir.glob("*.csv"))
    return sorted(files)


def read_submission(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    # default: excel
    return pd.read_excel(path, sheet_name="submission")