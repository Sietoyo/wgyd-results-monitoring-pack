from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.config import settings
from src.db import sqlite_connect


def _fetch_df(conn: sqlite3.Connection, query: str, params=()) -> pd.DataFrame:
    return pd.read_sql_query(query, conn, params=params)


def generate_monthly_brief(report_month: str) -> Path:
    out_dir = Path(settings.output_briefs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"monthly_brief_{report_month}.pdf"

    conn = sqlite_connect()
    try:
        summary = _fetch_df(
            conn,
            """
            SELECT report_month, indicator_code, indicator_name, actual_value, target, progress_to_target
            FROM vw_indicator_summary_national
            WHERE report_month = ?
            ORDER BY progress_to_target DESC
            """,
            (report_month,),
        )

        dq = _fetch_df(
            conn,
            """
            SELECT severity, COUNT(*) AS n
            FROM dq_exceptions
            WHERE report_month = ?
            GROUP BY severity
            ORDER BY severity
            """,
            (report_month,),
        )

        intake = _fetch_df(
            conn,
            """
            SELECT COUNT(DISTINCT team) AS teams_reporting,
                   COUNT(DISTINCT source_file) AS files_received,
                   COUNT(*) AS raw_rows
            FROM raw_submissions
            WHERE report_month = ?
            """,
            (report_month,),
        )

        clean_stats = _fetch_df(
            conn,
            """
            SELECT COUNT(*) AS clean_rows
            FROM clean_submissions
            WHERE report_month = ?
            """,
            (report_month,),
        )

        late = _fetch_df(
            conn,
            """
            SELECT team, COUNT(*) AS rows_submitted
            FROM raw_submissions
            WHERE report_month = ? AND (submitted_on IS NULL OR LENGTH(submitted_on) < 10)
            GROUP BY team
            ORDER BY rows_submitted DESC
            """,
            (report_month,),
        )
    finally:
        conn.close()

    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4
    y = height - 50

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"WGYD Monthly M&E Brief — {report_month}")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Auto-generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    y -= 25

    # Intake section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "1) Reporting Intake & Data Volume")
    y -= 14

    t = intake.iloc[0].to_dict() if not intake.empty else {}
    cs = clean_stats.iloc[0].to_dict() if not clean_stats.empty else {}
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Teams reporting: {int(t.get('teams_reporting', 0))} | Files received: {int(t.get('files_received', 0))}")
    y -= 14
    c.drawString(50, y, f"Rows loaded — Raw: {int(t.get('raw_rows', 0))} | Clean: {int(cs.get('clean_rows', 0))}")
    y -= 22

    # Data quality section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "2) Data Quality Summary (Exceptions Log)")
    y -= 14

    c.setFont("Helvetica", 10)
    if dq.empty:
        c.drawString(50, y, "No exceptions recorded for this month.")
        y -= 14
    else:
        for _, row in dq.iterrows():
            c.drawString(50, y, f"{str(row['severity']).title()}: {int(row['n'])}")
            y -= 14
    y -= 8

    if not late.empty:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, y, "Note: Some submissions have missing/short submission dates (possible late/invalid reporting).")
        y -= 14
        c.setFont("Helvetica", 9)
        for _, row in late.head(3).iterrows():
            c.drawString(60, y, f"- {row['team']}: {int(row['rows_submitted'])} rows flagged")
            y -= 12
        y -= 8

    # Results section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "3) Results Framework Summary (National Totals)")
    y -= 14

    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Top indicators by progress-to-target:")
    y -= 14

    top_n = summary.head(6) if not summary.empty else pd.DataFrame()
    if top_n.empty:
        c.drawString(50, y, "No summary rows available.")
        y -= 14
    else:
        for _, r in top_n.iterrows():
            prog = r["progress_to_target"]
            prog_txt = "N/A" if pd.isna(prog) else f"{float(prog)*100:.1f}%"
            line = (
                f"{r['indicator_code']} — {str(r['indicator_name'])[:52]} | "
                f"Actual: {r['actual_value']} | Target: {r['target']} | Progress: {prog_txt}"
            )
            c.drawString(50, y, line)
            y -= 12

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(
        50,
        40,
        "Auto-generated from standardized monthly submissions. Use the exceptions report for follow-up and remediation.",
    )

    c.showPage()
    c.save()
    return out_path