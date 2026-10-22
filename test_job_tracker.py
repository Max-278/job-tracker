"""Tests for job_tracker.py - run with: python3 test_job_tracker.py

Each test uses its own temporary database, so the suite never touches a real
applications.db.
"""
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import job_tracker as jt  # noqa: E402


def test_add_and_list():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        id1 = jt.add("Acme Recruitment", "Warehouse Operative", "applied", "online assessment booked", db)
        id2 = jt.add("City Parcels", "Parcel Sorter", "saved", "", db)
        assert (id1, id2) == (1, 2)
        rows = jt.list_apps(db_path=db)
        assert len(rows) == 2
        assert rows[0][1] == "City Parcels"  # newest first (same date -> id DESC)
        applied = jt.list_apps("applied", db)
        assert len(applied) == 1 and applied[0][1] == "Acme Recruitment"
    print("PASS add and list (with status filter)")


def test_update_status():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        app_id = jt.add("Acme Recruitment", "Warehouse Operative", "applied", "", db)
        assert jt.update_status(app_id, "assessment", db) == 1
        assert jt.list_apps(db_path=db)[0][4] == "assessment"
        assert jt.update_status(999, "offer", db) == 0  # unknown id changes nothing
    print("PASS update_status (and unknown id is a no-op)")


def test_export_csv_is_excel_compatible():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        jt.add("A, B & Co", "Analyst", "applied", 'note with "quotes"', db)
        out = Path(d) / "out.csv"
        n = jt.export_csv(out, db)
        assert n == 1
        with open(out, newline="") as f:
            rows = list(csv.reader(f))
        assert rows[0] == ["id", "company", "role", "date_added", "status", "notes"]
        assert rows[1][1] == "A, B & Co" and rows[1][5] == 'note with "quotes"'
    print("PASS export_csv handles commas and quotes correctly")


def test_export_neutralises_spreadsheet_formulas():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        jt.add("=1+1", "Analyst", "applied", "-2+3", db)
        jt.add("@echo", "Dev", "saved", "+cmd", db)
        out = Path(d) / "o.csv"
        jt.export_csv(out, db)
        with open(out, newline="") as f:
            rows = list(csv.reader(f))
        companies = {r[1] for r in rows[1:]}
        notes = {r[5] for r in rows[1:]}
        assert companies == {"'=1+1", "'@echo"}, companies
        assert notes == {"'-2+3", "'+cmd"}, notes
    print("PASS export neutralises spreadsheet formulas")


def test_empty_company_or_role_rejected():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        for bad in (("", "Analyst"), ("  ", "Analyst"), ("Acme", "")):
            try:
                jt.add(*bad, "saved", "", db)
                raise AssertionError(f"accepted {bad!r}")
            except ValueError:
                pass
    print("PASS empty company/role rejected")


def test_status_constraint_rejects_bad_status():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        try:
            jt.add("X", "Y", "hired", "", db)  # not a valid status
            raise AssertionError("invalid status accepted")
        except Exception as e:
            assert "CHECK" in str(e) or "constraint" in str(e).lower()
    print("PASS invalid status rejected by database constraint")


def test_cli_smoke():
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ, JOB_TRACKER_DB=str(Path(d) / "cli.db"))
        r1 = subprocess.run([sys.executable, str(HERE / "job_tracker.py"),
                             "add", "Acme Recruitment", "Operative", "--status", "applied"],
                            capture_output=True, text=True, env=env)
        assert r1.returncode == 0 and "Added #1" in r1.stdout
        r2 = subprocess.run([sys.executable, str(HERE / "job_tracker.py"), "list"],
                            capture_output=True, text=True, env=env)
        assert "Acme Recruitment - Operative" in r2.stdout
        r3 = subprocess.run([sys.executable, str(HERE / "job_tracker.py"), "update", "1", "interview"],
                            capture_output=True, text=True, env=env)
        assert r3.returncode == 0
        r4 = subprocess.run([sys.executable, str(HERE / "job_tracker.py"), "export", str(Path(d) / "x.csv")],
                            capture_output=True, text=True, env=env)
        assert "Exported 1 application(s)" in r4.stdout
        r5 = subprocess.run([sys.executable, str(HERE / "job_tracker.py"), "update", "99", "offer"],
                            capture_output=True, text=True, env=env)
        assert r5.returncode != 0  # unknown id fails cleanly
    print("PASS CLI end-to-end (add, list, update, export, bad id)")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception:
            failed += 1
            import traceback
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    sys.exit(1 if failed else 0)
