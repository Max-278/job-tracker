# Job Application Tracker

A small command-line tool for tracking job applications: add roles as you
apply, update their status as things move, and export everything to a CSV you
can open in Excel.

Built with the Python standard library only - no installs, no accounts, and
your data stays in a local file on your machine.

## Why it exists

Job hunting means juggling dozens of applications across job boards, agencies
and emails. This keeps them in one place with a clear status for each, and
exports a spreadsheet-compatible record whenever you want it. Built as a
portfolio project demonstrating practical Python: CLI design, SQLite storage
with integrity constraints, and CSV export.

## Usage

```bash
# Add an application (status defaults to "saved")
python3 job_tracker.py add "Acme Recruitment" "Warehouse Operative" --status applied --notes "online assessment booked"

# See everything, or filter by status
python3 job_tracker.py list
python3 job_tracker.py list --status interview

# Move an application forward (use the #number from list)
python3 job_tracker.py update 1 assessment

# Export to Excel-compatible CSV
python3 job_tracker.py export applications.csv
```

Statuses: `saved`, `applied`, `assessment`, `interview`, `offer`, `rejected`,
`withdrawn`. The database rejects any other status, so the data stays clean.

Data lives in `applications.db` next to the script (set the `JOB_TRACKER_DB`
environment variable to use a different file).

Exported CSVs are safe to open in Excel: any text that starts with `=`, `+`,
`-` or `@` is prefixed so it cannot run as a spreadsheet formula.

## Tests

```bash
python3 test_job_tracker.py
```

Seven tests covering add/list with filters, status updates (including unknown
IDs failing cleanly), CSV export with commas and quotes, spreadsheet-formula
neutralisation, empty-field rejection, the status constraint, and a full
command-line run from add to export. Each test uses a temporary database -
the suite never touches your real `applications.db`.

## Project layout

- `job_tracker.py` - the tool
- `test_job_tracker.py` - test suite (7 tests)

## Scope and limitations

This is a personal, single-user command-line tracker, not a production web
app. There is no interface beyond the terminal, no reminders or integrations
with job boards or email, and no multi-device sync - the database is a single
local file. Deleting applications is not yet implemented (update a status
instead). It suits one person tracking their own search on one machine.

*Author: Varun Suresh*
