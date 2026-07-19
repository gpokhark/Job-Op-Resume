#!/usr/bin/env python3
"""
Renders an HTML resume in headless Chromium and reports whether it fits one
US Letter page (0.5" margins all sides). Optionally saves the generated PDF.

Usage:
  uv run python scripts/measure_resume.py <resume.html> [--save-pdf <out.pdf>]

Output (stdout): JSON — read by the resume-generator skill to decide whether
                 to trim, expand, or accept the draft before saving the final file.
"""

import sys
import json
import argparse
import tempfile
from pathlib import Path

# US Letter at 96 dpi with 0.5in margins on all sides:
#   content height = (11 - 1.0) * 96 = 960 px
#   content width  = (8.5 - 1.0) * 96 = 720 px
PAGE_HEIGHT_PX = 960
LINE_HEIGHT_PX = 18   # ~10.5pt body, 1.25 line-height in Chromium rendering
GOOD_FILL_MIN  = 88   # % — below this is visible white space at the bottom


def measure(html_path: Path, pdf_output: Path | None = None) -> dict:
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader

    html_url = html_path.resolve().as_uri()
    delete_pdf = pdf_output is None

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Height=1 forces scrollHeight to reflect true content height, not viewport.
        # Width=816 matches US Letter at 96 dpi (8.5in) so line wrapping is accurate.
        page = browser.new_page(viewport={"width": 816, "height": 1})
        page.goto(html_url, wait_until="networkidle")

        # True rendered content height — accurate because viewport is artificially short
        content_height = page.evaluate("document.documentElement.scrollHeight")

        pdf_path = str(pdf_output) if pdf_output else tempfile.mktemp(suffix=".pdf")
        page.pdf(
            path=pdf_path,
            format="Letter",
            margin={"top": "0.5in", "bottom": "0.5in",
                    "left": "0.5in", "right": "0.5in"},
            print_background=True,
        )
        browser.close()

    page_count = len(PdfReader(pdf_path).pages)

    if delete_pdf:
        Path(pdf_path).unlink(missing_ok=True)

    delta_px    = content_height - PAGE_HEIGHT_PX
    delta_lines = round(abs(delta_px) / LINE_HEIGHT_PX)
    fill_pct    = round(content_height / PAGE_HEIGHT_PX * 100, 1)

    if page_count > 1:
        status   = "overflow"
        guidance = (
            f"OVERFLOW: {page_count} pages. Content is {delta_px}px too tall "
            f"(~{delta_lines} lines over). Trim bullets or shorten existing ones to fit."
        )
    elif fill_pct < GOOD_FILL_MIN:
        status   = "underflow"
        guidance = (
            f"UNDERFLOW: 1 page but only {fill_pct}% full "
            f"({abs(delta_px)}px empty at bottom, ~{delta_lines} lines short). "
            f"Expand bullets or add content to fill the page."
        )
    else:
        status   = "ok"
        guidance = (
            f"OK: 1 page, {fill_pct}% full "
            f"({abs(delta_px)}px remaining — good fill, no changes needed)."
        )

    return {
        "status":           status,
        "pages":            page_count,
        "fill_pct":         fill_pct,
        "content_height_px": content_height,
        "page_height_px":   PAGE_HEIGHT_PX,
        "delta_px":         delta_px,
        "delta_lines":      delta_lines,
        "guidance":         guidance,
    }


def main():
    ap = argparse.ArgumentParser(description="Measure HTML resume page fill.")
    ap.add_argument("html",       help="Path to the HTML resume file")
    ap.add_argument("--save-pdf", metavar="PDF", help="Also save the rendered PDF here")
    args = ap.parse_args()

    html_path = Path(args.html)
    if not html_path.exists():
        print(json.dumps({"error": f"File not found: {html_path}"}))
        sys.exit(1)

    result = measure(html_path, Path(args.save_pdf) if args.save_pdf else None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
