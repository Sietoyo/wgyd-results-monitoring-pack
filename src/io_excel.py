from pathlib import Path
import pandas as pd

from src.config import settings


def list_submission_files(report_month: str) -> list[Path]:
    month_dir = Path(settings.raw_submissions_dir) / report_month
    return sorted(month_dir.glob("*.xlsx"))


def read_submission_xlsx(path: Path) -> pd.DataFrame:
    # Reads the "submission" sheet created by our generator
    return pd.read_excel(path, sheet_name="submission")