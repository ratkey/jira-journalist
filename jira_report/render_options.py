"""Shared options controlling which ticket details get rendered."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from jira_report.models import Ticket

_DATE_FMT = "%Y-%m-%d"


@dataclass(frozen=True, slots=True)
class DisplayOptions:
    """Toggles for the optional per-ticket detail fields.

    `show_type` and `show_status` are off by default; `show_due_date` is on
    by default (it can be turned off with --hide-due-date).
    """

    show_type: bool = False
    show_status: bool = False
    show_due_date: bool = True

    @property
    def any_enabled(self) -> bool:
        return self.show_type or self.show_status or self.show_due_date


def ticket_details(ticket: Ticket, options: DisplayOptions) -> list[str]:
    """Return the detail strings enabled by `options`, in display order."""
    details: list[str] = []
    if options.show_type:
        details.append(f"tipo: {ticket.issue_type.label}")
    if options.show_status:
        details.append(f"estado: {ticket.status}")
    if options.show_due_date and ticket.due_date is not None:
        details.append(f"{ticket.due_date.strftime(_DATE_FMT)}")
    return details


def progress_value(ticket: Ticket, as_of: datetime) -> str | None:
    """ "65%" for an in-progress ticket, or None if not computable."""
    progress = ticket.progress(as_of)
    if progress is None:
        return None
    return f"{progress:.0f}%"


def due_date_value(ticket: Ticket) -> str | None:
    """ "fecha de vencimiento: 2026-06-28", or None if the ticket has no due date."""
    if ticket.due_date is None:
        return None
    return f"{ticket.due_date.strftime(_DATE_FMT)}"
