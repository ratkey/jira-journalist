"""Domain types for Jira tickets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class IssueType(str, Enum):
    """The two issue types this report cares about."""

    FEATURE = "Historia"
    BUG = "Error"

    @property
    def label(self) -> str:
        return "Historia" if self is IssueType.FEATURE else "Error"


# Status that must never appear in the report.
EXCLUDED_STATUS = "Backlog"

# Status that marks a ticket as actively being worked on.
IN_PROGRESS_STATUS = "En curso"

UNASSIGNED = "Sin asignar"


@dataclass(frozen=True, slots=True)
class Ticket:
    key: str
    summary: str
    issue_type: IssueType
    status: str
    assignee: str
    start_date: datetime | None
    due_date: datetime | None

    @property
    def is_in_progress(self) -> bool:
        return self.status == IN_PROGRESS_STATUS

    @property
    def window_date(self) -> datetime | None:
        """Date used to sort this ticket within its report bucket.

        In-progress tickets are keyed on their start date (when work began);
        everything else on its due date.
        """
        return self.start_date if self.is_in_progress else self.due_date

    def overlaps_window(self, window_start: datetime, window_end: datetime) -> bool:
        """Whether this ticket's start→due span intersects the report window.

        Used for in-progress tickets: a long-running ticket that began before
        the window but is still being worked on (due on or after the window
        start) is active during the window and belongs in the report, not just
        tickets that happened to start inside it. Missing dates fall back to
        the other endpoint.
        """
        start = self.start_date or self.due_date
        end = self.due_date or self.start_date
        if start is None or end is None:
            return False
        return start <= window_end and end >= window_start

    def progress(self, as_of: datetime) -> float | None:
        """Percentage of the start-to-due window elapsed as of `as_of`.

        Returns None when either date is missing. Clamped to [0, 100] so
        overdue or not-yet-started tickets still produce a sane number.
        """
        if self.start_date is None or self.due_date is None:
            return None

        # Jira due dates are inclusive calendar days: a ticket due 06/30 has
        # until the end of 06/30. Extend the window to the end of the due day
        # so a ticket that starts today and is due tomorrow isn't reported as
        # 100% before its due day has even arrived.
        window_close = self.due_date + timedelta(days=1)

        total = (window_close - self.start_date).total_seconds()
        if total <= 0:
            return 100.0

        elapsed = (as_of - self.start_date).total_seconds()
        return max(0.0, min(100.0, elapsed / total * 100))
