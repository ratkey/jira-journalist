#!/usr/bin/env python3
"""Thin wrapper so the report can be run as `python generate_report.py ...`."""

import sys

from jira_report.cli import main

if __name__ == "__main__":
    sys.exit(main())
