"""Filter tickets by time window/status and group them for the report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from jira_report.models import EXCLUDED_STATUS, IssueType, Ticket


@dataclass(frozen=True, slots=True)
class ReportData:
    """Tickets bucketed exactly the way the report renders them."""

    window_start: datetime
    window_end: datetime
    in_progress_by_assignee: dict[str, list[Ticket]] = field(default_factory=dict)
    done_by_type: dict[IssueType, list[Ticket]] = field(default_factory=dict)

    @property
    def total_tickets(self) -> int:
        in_progress = sum(len(t) for t in self.in_progress_by_assignee.values())
        done = sum(len(t) for t in self.done_by_type.values())
        return in_progress + done


def build_report_data(
    tickets: Iterable[Ticket],
    window_start: datetime,
    window_end: datetime,
) -> ReportData:
    """Filter `tickets` to `[window_start, window_end]` and group them.

    Backlog tickets are dropped entirely. "En curso" tickets are grouped by
    assignee; every other status is treated as done and grouped by type.
    """
    in_progress_by_assignee: dict[str, list[Ticket]] = {}
    done_by_type: dict[IssueType, list[Ticket]] = {}

    for ticket in tickets:
        if ticket.status == EXCLUDED_STATUS:
            continue

        window_date = ticket.window_date
        if window_date is None or not (window_start <= window_date <= window_end):
            continue

        if ticket.is_in_progress:
            in_progress_by_assignee.setdefault(ticket.assignee, []).append(ticket)
        else:
            done_by_type.setdefault(ticket.issue_type, []).append(ticket)

    for bucket in in_progress_by_assignee.values():
        bucket.sort(key=lambda t: t.window_date, reverse=True)
    for bucket in done_by_type.values():
        bucket.sort(key=lambda t: t.window_date, reverse=True)

    return ReportData(
        window_start=window_start,
        window_end=window_end,
        in_progress_by_assignee=dict(sorted(in_progress_by_assignee.items())),
        done_by_type=done_by_type,
    )
