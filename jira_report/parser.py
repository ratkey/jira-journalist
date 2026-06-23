"""Read a Jira CSV export into a list of `Ticket` objects."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from jira_report.models import UNASSIGNED, IssueType, Ticket

# Jira exports dates as "2026/06/23".
_DATE_FMT = "%Y/%m/%d"


def parse_jira_date(raw: str) -> datetime:
    """Parse a Jira export date such as "2026/06/23"."""
    return datetime.strptime(raw.strip(), _DATE_FMT)


def _relevant_issue_type(raw: str) -> IssueType | None:
    """Map the raw CSV value to an `IssueType`, or None if it should be ignored."""
    try:
        return IssueType(raw)
    except ValueError:
        return None


def _first_set_date(row: dict[str, str], *columns: str) -> datetime | None:
    """Parse the first non-blank date among `columns`, in order."""
    for column in columns:
        raw = row[column].strip()
        if raw:
            return parse_jira_date(raw)
    return None


def _start_date(row: dict[str, str]) -> datetime | None:
    """Start date, falling back to Jira's inferred start date when not set explicitly."""
    return _first_set_date(row, "Fecha de inicio", "Fecha de inicio deducida")


def _due_date(row: dict[str, str]) -> datetime | None:
    """Due date, falling back to Jira's inferred due date when not set explicitly."""
    return _first_set_date(row, "Fecha de vencimiento", "Fecha de vencimiento deducida")


def load_tickets(csv_path: Path) -> Iterator[Ticket]:
    """Yield `Ticket`s for rows whose type is a feature or a bug.

    Rows with any other issue type (Epic, Spike, Subtarea, ...) are silently
    skipped, since this report only distinguishes features and bugs.
    """
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            issue_type = _relevant_issue_type(row["Tipo de Incidencia"])
            if issue_type is None:
                continue

            start_date = _start_date(row)
            due_date = _due_date(row)
            if start_date is None and due_date is None:
                continue

            yield Ticket(
                key=row["Clave"],
                summary=row["Resumen"].strip(),
                issue_type=issue_type,
                status=row["Estado"].strip(),
                assignee=row["Persona asignada"].strip() or UNASSIGNED,
                start_date=start_date,
                due_date=due_date,
            )
