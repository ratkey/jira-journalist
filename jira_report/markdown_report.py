"""Render `ReportData` as a Markdown document."""

from __future__ import annotations

from dataclasses import replace

from jira_report.grouping import ReportData
from jira_report.models import IssueType, Ticket
from jira_report.render_options import (
    DisplayOptions,
    due_date_value,
    progress_value,
    ticket_details,
)


def _ticket_line(
    ticket: Ticket,
    options: DisplayOptions,
    extra_details: list[str] | None = None,
) -> str:
    line = f"- **[{ticket.key}]** {ticket.summary}"
    details = [*(extra_details or []), *ticket_details(ticket, options)]
    if details:
        line += f" _({', '.join(details)})_"
    return line


def _render_in_progress(data: ReportData, options: DisplayOptions) -> list[str]:
    lines = ["## En curso", ""]
    if not data.in_progress_by_assignee:
        return [*lines, "_Sin tickets en curso en este periodo._", ""]

    # Due date is rendered as `extra_details` here, so it is excluded from
    # `ticket_details` to avoid a duplicate.
    remaining_options = replace(options, show_due_date=False)

    for assignee, tickets in data.in_progress_by_assignee.items():
        lines.append(f"### {assignee}")
        lines.append("")
        for ticket in tickets:
            due_date = due_date_value(ticket) if options.show_due_date else None
            extra = [
                value
                for value in (progress_value(ticket, data.window_end), due_date)
                if value is not None
            ]
            lines.append(_ticket_line(ticket, remaining_options, extra))
        lines.append("")
    return lines


def _render_done(data: ReportData, options: DisplayOptions) -> list[str]:
    lines = ["## Terminados", ""]
    sections = (
        (IssueType.FEATURE, "Historias"),
        (IssueType.BUG, "Errores"),
    )

    any_done = any(data.done_by_type.get(issue_type) for issue_type, _ in sections)
    if not any_done:
        return [*lines, "_Sin tickets terminados en este periodo._", ""]

    for issue_type, heading in sections:
        tickets = data.done_by_type.get(issue_type, [])
        if not tickets:
            continue
        lines.append(f"### {heading}")
        lines.append("")
        lines.extend(_ticket_line(t, options) for t in tickets)
        lines.append("")
    return lines


def render(data: ReportData, options: DisplayOptions = DisplayOptions()) -> str:
    """Build the full Markdown report as a string."""
    in_progress_count = sum(len(t) for t in data.in_progress_by_assignee.values())
    done_count = sum(len(t) for t in data.done_by_type.values())

    lines = [
        "# Reporte de Jira",
        "",
        f"Periodo: {data.window_start.strftime('%Y-%m-%d')} a "
        f"{data.window_end.strftime('%Y-%m-%d')}",
        "",
        f"- Total de tickets: {data.total_tickets}",
        f"- En curso: {in_progress_count}",
        f"- Terminados: {done_count}",
        "",
        *_render_in_progress(data, options),
        *_render_done(data, options),
    ]
    return "\n".join(lines).rstrip() + "\n"
