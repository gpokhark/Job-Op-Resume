#!/usr/bin/env python3
"""
Appends one row to output/resume_log.csv after a resume is generated.
Called by convert_resume.ps1 after PDF generation.

Usage:
  uv run python scripts/log_resume.py \
    --file   "Pokharkar_Resume_Honda_2026-05-10.html" \
    --company "Honda" \
    --role   "ADAS Test Engineer" \
    --url    "https://careers.honda.com/..." \
    --fill   96.9 \
    --pages  1 \
    --iterations 1 \
    --date   "2026-05-10"
"""

import argparse
import csv
import sys
from pathlib import Path

HEADERS = ["Date", "Company", "Role", "Job_URL", "Fill_Pct", "Pages", "Iterations", "Resume_File"]
LOG_PATH = Path(__file__).parent.parent / "output" / "resume_log.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file",       required=True)
    ap.add_argument("--company",    required=True)
    ap.add_argument("--role",       default="Not specified")
    ap.add_argument("--url",        default="Not specified")
    ap.add_argument("--fill",       default="?")
    ap.add_argument("--pages",      default="?")
    ap.add_argument("--iterations", default="?")
    ap.add_argument("--date",       required=True)
    args = ap.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    write_header = not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0

    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(HEADERS)
        writer.writerow([
            args.date,
            args.company,
            args.role,
            args.url,
            args.fill,
            args.pages,
            args.iterations,
            args.file,
        ])

    print(f"Logged: {args.company} | {args.role} | {args.fill}% | {args.iterations} iteration(s)")


if __name__ == "__main__":
    main()
