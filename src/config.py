import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    # DB mode: "sqlite" (fast local) or "postgres"
    db_type: str = os.getenv("DB_TYPE", "sqlite").lower()
    sqlite_path: str = os.getenv("SQLITE_PATH", "./data/wgyd_monitoring.sqlite")

    # Postgres settings (used only if DB_TYPE=postgres)
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "wgyd_monitoring")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres")

    raw_submissions_dir: str = os.getenv("RAW_SUBMISSIONS_DIR", "./data/submissions_raw")
    indicator_registry_path: str = os.getenv("INDICATOR_REGISTRY_PATH", "./data/indicator_registry/indicator_registry.xlsx")

    output_exceptions_dir: str = os.getenv("OUTPUT_EXCEPTIONS_DIR", "./data/outputs/exceptions")
    output_briefs_dir: str = os.getenv("OUTPUT_BRIEFS_DIR", "./data/outputs/briefs")
    output_logs_dir: str = os.getenv("OUTPUT_LOGS_DIR", "./data/outputs/logs")

    report_month: str = os.getenv("REPORT_MONTH", "2025-12")

    @property
    def sqlalchemy_url(self) -> str:
        if self.db_type == "sqlite":
            # For relative paths, SQLAlchemy uses 3 slashes
            return f"sqlite:///{self.sqlite_path}"
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings()