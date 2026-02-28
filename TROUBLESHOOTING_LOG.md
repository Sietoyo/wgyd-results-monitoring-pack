# Troubleshooting Log — Bottlenecks & Fixes

## 1) Repo created in protected folder (system32)
**Symptom:** project directory appeared under C:\WINDOWS\system32  
**Cause:** terminal working directory at time of scaffold  
**Fix:** moved repo to Documents\Projects and continued from there

## 2) (placeholder) WeasyPrint install on Windows
**Symptom:** (paste error)
**Fix:** (what we do — likely switch to ReportLab or install dependencies)

## 3) (placeholder) Docker/Postgres connection issues
**Symptom:** (paste error)
**Fix:** (port conflict / credentials / container restart)

## 4) (placeholder) Power BI connector / refresh issues
**Symptom:** (paste error)
**Fix:** (ODBC driver / connection string / permissions)

## Permission reset command error (icacls quoting)
**Symptom:** `Invalid parameter "(OI)(CI)F"`
**Cause:** PowerShell parsing/quoting issue with icacls grant string
**Fix:** used PowerShell-safe quoting: `icacls . /grant "$($env:USERNAME):(OI)(CI)F" /T`

## Config mismatch after moving repo
**Symptom:** AttributeError: Settings has no attribute 'db_type'
**Cause:** src/config.py still using older Postgres-only Settings class
**Fix:** replaced config.py with SQLite-enabled config and added DB_TYPE/SQLITE_PATH to .env

## IndentationError in etl_run.py
**Symptom:** `IndentationError: expected an indented block after 'if' statement`
**Cause:** `import sys` not indented under `if __name__ == "__main__":`
**Fix:** corrected indentation of the main block and reran monthly ETL

## NameError: report_month not defined during batch runs
**Symptom:** NameError for report_month at module level
**Cause:** print and brief generation statements were outside run_month() due to indentation
**Fix:** moved those statements inside run_month() with 4-space indentation