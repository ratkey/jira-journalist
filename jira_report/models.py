"""Domain types for Jira tickets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
        """Date used to test whether this ticket falls in the report window.

        In-progress tickets are checked against their start date (when work
        began); everything else is checked against its due date.
        """
        return self.start_date if self.is_in_progress else self.due_date

    def progress(self, as_of: datetime) -> float | None:
        """Percentage of the start-to-due window elapsed as of `as_of`.

        Returns None when either date is missing. Clamped to [0, 100] so
        overdue or not-yet-started tickets still produce a sane number.
        """
        if self.start_date is None or self.due_date is None:
            return None

        total = (self.due_date - self.start_date).total_seconds()
        if total <= 0:
            return 100.0

        elapsed = (as_of - self.start_date).total_seconds()
        return max(0.0, min(100.0, elapsed / total * 100))
