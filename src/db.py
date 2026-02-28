import sqlite3
from pathlib import Path
from typing import Optional

from src.config import settings


def ensure_sqlite_parent_dir():
    if settings.db_type != "sqlite":
        return
    p = Path(settings.sqlite_path)
    if p.parent:
        p.parent.mkdir(parents=True, exist_ok=True)


def sqlite_connect() -> sqlite3.Connection:
    ensure_sqlite_parent_dir()
    conn = sqlite3.connect(settings.sqlite_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def run_sql_file(path: str) -> None:
    if settings.db_type != "sqlite":
        raise RuntimeError("run_sql_file currently implemented for sqlite only in this MVP.")
    sql = Path(path).read_text(encoding="utf-8")
    conn = sqlite_connect()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()