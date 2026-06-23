"""Command-line entry point: CSV in, Markdown report out."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from jira_report import mail_report, markdown_report
from jira_report.grouping import build_report_data
from jira_report.parser import load_tickets
from jira_report.render_options import DisplayOptions

_DATE_FMT = "%Y-%m-%d"


def _parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, _DATE_FMT)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date {value!r}, expected format YYYY-MM-DD"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown report from a Jira CSV export.",
    )
    parser.add_argument("csv_path", type=Path, help="Path to the Jira CSV export.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/output"),
        help="Directory where the Markdown report is written (default: %(default)s).",
    )
    parser.add_argument(
        "--start",
        type=_parse_date,
        help="Window start date (YYYY-MM-DD). Defaults to --end minus --days.",
    )
    parser.add_argument(
        "--end",
        type=_parse_date,
        help="Window end date (YYYY-MM-DD), inclusive. Defaults to today.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Size of the window in days when --start is not given (default: %(default)s).",
    )
    parser.add_argument(
        "--show-type",
        action="store_true",
        help="Include the issue type (Feature/Bug) next to each ticket. Off by default.",
    )
    parser.add_argument(
        "--show-status",
        action="store_true",
        help="Include the Jira status next to each ticket. Off by default.",
    )
    parser.add_argument(
        "--hide-due-date",
        action="store_true",
        help="Hide the due date next to each ticket. Shown by default.",
    )
    parser.add_argument(
        "--no-mail",
        action="store_true",
        help="Skip generating the mail-friendly HTML version.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.csv_path.exists():
        print(f"Error: CSV file not found: {args.csv_path}", file=sys.stderr)
        return 1

    window_end = args.end or datetime.now().replace(
        hour=23, minute=59, second=59, microsecond=0
    )
    window_start = args.start or (window_end - timedelta(days=args.days))

    tickets = load_tickets(args.csv_path)
    data = build_report_data(tickets, window_start=window_start, window_end=window_end)
    options = DisplayOptions(
        show_type=args.show_type,
        show_status=args.show_status,
        show_due_date=not args.hide_due_date,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = (
        f"report_{window_start.strftime(_DATE_FMT)}_to_"
        f"{window_end.strftime(_DATE_FMT)}"
    )

    markdown_path = args.output_dir / f"{stem}.md"
    markdown_path.write_text(markdown_report.render(data, options), encoding="utf-8")
    print(f"Report written to {markdown_path}")

    if not args.no_mail:
        mail_path = args.output_dir / f"{stem}.mail.html"
        mail_path.write_text(mail_report.render(data, options), encoding="utf-8")
        print(f"Mail-friendly report written to {mail_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
