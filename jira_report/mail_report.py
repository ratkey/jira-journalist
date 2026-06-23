"""Render `ReportData` as a self-contained, mail-friendly HTML document.

Email clients strip <style> blocks and most CSS selectors, so every style
here is inlined on the element itself.
"""

from __future__ import annotations

from dataclasses import replace
from html import escape

from jira_report.grouping import ReportData
from jira_report.models import IssueType, Ticket
from jira_report.render_options import (
    DisplayOptions,
    due_date_value,
    progress_value,
    ticket_details,
)

_BODY_FONT = "font-family: Arial, Helvetica, sans-serif; color: #222222;"
_H1 = f'style="{_BODY_FONT} font-size: 20px; margin: 0 0 4px;"'
_H2 = f'style="{_BODY_FONT} font-size: 16px; margin: 16px 0 4px; color: #1a1a1a;"'
_H3 = f'style="{_BODY_FONT} font-size: 14px; margin: 12px 0 2px; color: #444444;"'
_P = f'style="{_BODY_FONT} font-size: 13px; margin: 2px 0;"'
_LI = f'style="{_BODY_FONT} font-size: 13px; margin: 2px 0;"'
_DETAIL = 'style="color: #777777; font-size: 12px;"'


def _ticket_item(
    ticket: Ticket,
    options: DisplayOptions,
    extra_details: list[str] | None = None,
) -> str:
    text = f"<b>[{escape(ticket.key)}]</b> {escape(ticket.summary)}"
    details = [*(extra_details or []), *ticket_details(ticket, options)]
    if details:
        suffix = ", ".join(escape(detail) for detail in details)
        text += f' <span {_DETAIL}>({suffix})</span>'
    return f"<li {_LI}>{text}</li>"


def _render_in_progress(data: ReportData, options: DisplayOptions) -> list[str]:
    lines = [f"<h2 {_H2}>En curso</h2>"]
    if not data.in_progress_by_assignee:
        return [*lines, f"<p {_P}><i>Sin tickets en curso en este periodo.</i></p>"]

    # Due date is rendered as `extra_details` here, so it is excluded from
    # `ticket_details` to avoid a duplicate.
    remaining_options = replace(options, show_due_date=False)

    for assignee, tickets in data.in_progress_by_assignee.items():
        lines.append(f"<h3 {_H3}>{escape(assignee)}</h3>")
        lines.append(f'<ul style="margin: 0 0 8px; padding-left: 20px;">')
        for ticket in tickets:
            due_date = due_date_value(ticket) if options.show_due_date else None
            extra = [
                value
                for value in (progress_value(ticket, data.window_end), due_date)
                if value is not None
            ]
            lines.append(_ticket_item(ticket, remaining_options, extra))
        lines.append("</ul>")
    return lines


def _render_done(data: ReportData, options: DisplayOptions) -> list[str]:
    lines = [f"<h2 {_H2}>Terminados</h2>"]
    sections = (
        (IssueType.FEATURE, "Funcionalidades"),
        (IssueType.BUG, "Errores"),
    )

    any_done = any(data.done_by_type.get(issue_type) for issue_type, _ in sections)
    if not any_done:
        return [*lines, f"<p {_P}><i>Sin tickets terminados en este periodo.</i></p>"]

    for issue_type, heading in sections:
        tickets = data.done_by_type.get(issue_type, [])
        if not tickets:
            continue
        lines.append(f"<h3 {_H3}>{escape(heading)}</h3>")
        lines.append(f'<ul style="margin: 0 0 8px; padding-left: 20px;">')
        lines.extend(_ticket_item(t, options) for t in tickets)
        lines.append("</ul>")
    return lines


def render(data: ReportData, options: DisplayOptions = DisplayOptions()) -> str:
    """Build a complete HTML document suitable for pasting into an email body."""
    in_progress_count = sum(len(t) for t in data.in_progress_by_assignee.values())
    done_count = sum(len(t) for t in data.done_by_type.values())

    window = (
        f"{data.window_start.strftime('%Y-%m-%d')} a "
        f"{data.window_end.strftime('%Y-%m-%d')}"
    )

    body = [
        f'<div style="{_BODY_FONT} max-width: 640px;">',
        f"<h1 {_H1}>Reporte de Jira</h1>",
        f"<p {_P}>Periodo: {window}</p>",
        f"<p {_P}>Total de tickets: {data.total_tickets} &middot; "
        f"En curso: {in_progress_count} &middot; Terminados: {done_count}</p>",
        *_render_in_progress(data, options),
        *_render_done(data, options),
        "</div>",
    ]
    return "\n".join(["<!DOCTYPE html>", "<html>", "<body>", *body, "</body>", "</html>", ""])
