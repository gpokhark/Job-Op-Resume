#!/usr/bin/env python3
"""
Renders an HTML resume in headless Chromium and reports whether it fits the
target US Letter page count (0.5" margins all sides). Optionally saves the
generated PDF.

Usage:
  uv run python scripts/measure_resume.py <resume.html> [--target-pages 1|1.5|2] [--save-pdf <out.pdf>]

Output (stdout): JSON — read by the resume-generator skill to decide whether
                 to trim, expand, or accept the draft before saving the final file.
"""

import sys
import json
import argparse
import math
import tempfile
from pathlib import Path

# US Letter at 96 dpi with 0.5in margins on all sides:
#   content height = (11 - 1.0) * 96 = 960 px
#   content width  = (8.5 - 1.0) * 96 = 720 px
PAGE_HEIGHT_PX = 960
LINE_HEIGHT_PX = 18   # ~10.5pt body, 1.25 line-height in Chromium rendering
GOOD_FILL_MIN  = 88   # % — below this is visible white space at the bottom of a full-page target

# For a half-page target (e.g. 1.5 pages), the last page is deliberately only
# partially filled by design — a full 88-100% last page would make it a 2-page resume.
HALF_PAGE_FILL_BAND = (35, 70)


def measure(html_path: Path, pdf_output: Path | None = None, target_pages: float = 1.0) -> dict:
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

    # Physical pages the target implies: 1 -> 1, 1.5 -> 2, 2 -> 2.
    expected_pages  = math.ceil(target_pages)
    is_half_target  = abs((target_pages * 2) - round(target_pages * 2)) < 1e-9 and (target_pages * 2) % 2 == 1

    # Legacy field, kept for backward compatibility with existing log rows —
    # NOT a real fill percentage once content spans more than one page.
    fill_pct = round(content_height / PAGE_HEIGHT_PX * 100, 1)

    # Fill of the last (partial) physical page — the number that actually
    # answers "does the page look empty."
    last_page_content_px = content_height - (page_count - 1) * PAGE_HEIGHT_PX
    last_page_fill_pct   = round(max(last_page_content_px, 0) / PAGE_HEIGHT_PX * 100, 1)

    delta_px    = content_height - expected_pages * PAGE_HEIGHT_PX
    delta_lines = round(abs(delta_px) / LINE_HEIGHT_PX)

    if page_count > expected_pages:
        status   = "overflow"
        guidance = (
            f"OVERFLOW: rendered {page_count} pages but target is {target_pages} "
            f"(expected {expected_pages}). Content is {abs(delta_px)}px too tall "
            f"(~{delta_lines} lines over). Trim bullets or shorten existing ones to fit."
        )
    elif page_count < expected_pages:
        status   = "underflow"
        guidance = (
            f"UNDERFLOW: rendered {page_count} page(s) but target is {target_pages} "
            f"(expected {expected_pages}). Content is {abs(delta_px)}px short "
            f"(~{delta_lines} lines) of even reaching the target page count. "
            f"Expand bullets or add content."
        )
    else:
        band_low, band_high = HALF_PAGE_FILL_BAND if is_half_target else (GOOD_FILL_MIN, 100)
        if last_page_fill_pct < band_low:
            status   = "underflow"
            short_px = round(band_low / 100 * PAGE_HEIGHT_PX - last_page_content_px)
            guidance = (
                f"UNDERFLOW: {page_count} page(s), last page only {last_page_fill_pct}% full "
                f"(target band {band_low}-{band_high}% for a {target_pages}-page resume). "
                f"Add ~{round(short_px / LINE_HEIGHT_PX)} lines to the last page."
            )
        elif last_page_fill_pct > band_high:
            status   = "overflow"
            over_px  = round(last_page_content_px - band_high / 100 * PAGE_HEIGHT_PX)
            guidance = (
                f"OVERFLOW: {page_count} page(s), last page {last_page_fill_pct}% full, "
                f"over the {band_high}% band for a {target_pages}-page resume by "
                f"~{round(over_px / LINE_HEIGHT_PX)} lines. Trim slightly."
            )
        else:
            status   = "ok"
            guidance = (
                f"OK: {page_count} page(s) matching the {target_pages}-page target, "
                f"last page {last_page_fill_pct}% full (good fill, no changes needed)."
            )

    return {
        "status":             status,
        "pages":              page_count,
        "target_pages":       target_pages,
        "last_page_fill_pct": last_page_fill_pct,
        "fill_pct":           fill_pct,
        "content_height_px":  content_height,
        "page_height_px":     PAGE_HEIGHT_PX,
        "delta_px":           delta_px,
        "delta_lines":        delta_lines,
        "guidance":           guidance,
    }


def main():
    ap = argparse.ArgumentParser(description="Measure HTML resume page fill.")
    ap.add_argument("html",       help="Path to the HTML resume file")
    ap.add_argument("--save-pdf", metavar="PDF", help="Also save the rendered PDF here")
    ap.add_argument("--target-pages", type=float, default=1.0,
                     help="Intended page count: 1, 1.5, or 2 (default 1)")
    args = ap.parse_args()

    html_path = Path(args.html)
    if not html_path.exists():
        print(json.dumps({"error": f"File not found: {html_path}"}))
        sys.exit(1)

    result = measure(html_path, Path(args.save_pdf) if args.save_pdf else None, args.target_pages)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
