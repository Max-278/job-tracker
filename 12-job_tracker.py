"""job_tracker.py - a small job application tracker.

Keeps your applications in a local SQLite database and exports them to a CSV
you can open in Excel. Runs locally; no accounts, nothing leaves your machine.

Usage:
  python3 job_tracker.py add "Acme Recruitment" "Warehouse Operative" --status applied --notes "online assessment booked"
  python3 job_tracker.py list
  python3 job_tracker.py list --status interview
  python3 job_tracker.py update 3 interview
  python3 job_tracker.py export applications.csv

Statuses: saved, applied, assessment, interview, offer, rejected, withdrawn.
"""
import argparse
import csv
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

DB = Path(os.environ.get("JOB_TRACKER_DB", Path(__file__).parent / "applications.db"))
STATUSES = ["saved", "applied", "assessment", "interview", "offer", "rejected", "withdrawn"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    date_added TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('saved','applied','assessment','interview','offer','rejected','withdrawn')),
    notes TEXT DEFAULT ''
);
"""


def connect(db_path=DB):
    con = sqlite3.connect(db_path)
    con.execute(SCHEMA)
    return con


def add(company, role, status, notes, db_path=DB):
    if not company.strip() or not role.strip():
        raise ValueError("Company and role must not be empty.")
    con = connect(db_path)
    with con:
        cur = con.execute(
            "INSERT INTO applications (company, role, date_added, status, notes) VALUES (?,?,?,?,?)",
            (company, role, date.today().isoformat(), status, notes))
    con.close()
    return cur.lastrowid


def list_apps(status=None, db_path=DB):
    con = connect(db_path)
    if status:
        rows = con.execute("SELECT * FROM applications WHERE status=? ORDER BY date_added DESC, id DESC", (status,))
    else:
        rows = con.execute("SELECT * FROM applications ORDER BY date_added DESC, id DESC")
    out = rows.fetchall()
    con.close()
    return out


def update_status(app_id, status, db_path=DB):
    con = connect(db_path)
    with con:
        cur = con.execute("UPDATE applications SET status=? WHERE id=?", (status, app_id))
    changed = cur.rowcount
    con.close()
    return changed


def _excel_safe(value):
    """Prefix text that Excel could interpret as a formula, so a company or
    note like '=1+1' or '-2+3' can never execute when the CSV is opened."""
    s = str(value)
    if s[:1] in ("=", "+", "-", "@"):
        return "'" + s
    return s


def export_csv(path, db_path=DB):
    rows = list_apps(db_path=db_path)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "company", "role", "date_added", "status", "notes"])
        w.writerows([_excel_safe(v) for v in row] for row in rows)
    return len(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description="Track job applications locally; export to Excel-compatible CSV.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add an application")
    a.add_argument("company")
    a.add_argument("role")
    a.add_argument("--status", default="saved", choices=STATUSES)
    a.add_argument("--notes", default="")

    l = sub.add_parser("list", help="list applications")
    l.add_argument("--status", choices=STATUSES)

    u = sub.add_parser("update", help="update an application's status")
    u.add_argument("id", type=int)
    u.add_argument("status", choices=STATUSES)

    e = sub.add_parser("export", help="export everything to CSV")
    e.add_argument("path")

    args = p.parse_args(argv)
    if args.cmd == "add":
        try:
            app_id = add(args.company, args.role, args.status, args.notes)
        except ValueError as exc:
            sys.exit(str(exc))
        print(f"Added #{app_id}: {args.role} at {args.company} ({args.status})")
    elif args.cmd == "list":
        rows = list_apps(args.status)
        if not rows:
            print("No applications found." if not args.status else f"No applications with status '{args.status}'.")
        for r in rows:
            print(f"#{r[0]}  {r[3]}  {r[1]} - {r[2]}  [{r[4]}]" + (f"  ({r[5]})" if r[5] else ""))
    elif args.cmd == "update":
        if update_status(args.id, args.status):
            print(f"Updated #{args.id} to '{args.status}'.")
        else:
            sys.exit(f"No application with id {args.id}.")
    elif args.cmd == "export":
        n = export_csv(args.path)
        print(f"Exported {n} application(s) to {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
