#!/usr/bin/env python3
"""
PostToolUse hook: converts resume files to PDF. Cross-platform replacement
for convert_resume.ps1 (Windows-only).
  *_CV_*.html (or legacy *_Resume_*.html) -> measure_resume.measure() (Playwright) -> .pdf
  *_CV_*.md   (or legacy *_Resume_*.md)   -> build_resume.build_docx() -> .docx -> docx2pdf -> .pdf
Receives Claude tool event JSON on stdin.

Note: docx2pdf drives Microsoft Word (COM on Windows, AppleScript on macOS)
and has no Linux support. If Word isn't available, the .docx is still
produced and the PDF step is skipped with a message.
"""

import sys
import json
import re
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))


def main():
    stdin_content = sys.stdin.read()
    if not stdin_content.strip():
        return

    try:
        event = json.loads(stdin_content)
    except json.JSONDecodeError:
        return

    file_path = event.get("tool_input", {}).get("file_path")
    if not file_path:
        return

    file_path = Path(file_path)
    if not file_path.exists():
        return

    if re.search(r"_(?:CV|Resume)_.*\.html$", file_path.name):
        convert_html(file_path)
    elif re.search(r"_(?:CV|Resume)_.*\.md$", file_path.name):
        convert_md(file_path)


def convert_html(file_path: Path):
    import measure_resume

    pdf_path = file_path.with_suffix(".pdf")
    try:
        result = measure_resume.measure(file_path, pdf_path)
    except Exception as e:
        print(f"Resume HTML->PDF failed for: {file_path} ({e})")
        return

    fill = result.get("fill_pct", "?")
    pages = result.get("pages", "?")
    status = result.get("status", "unknown")

    if not pdf_path.exists():
        print(f"Resume HTML->PDF failed for: {file_path}")
        return

    print(f"Resume converted: {file_path.stem} -> pdf | {pages} page(s), {fill}% full [{status}]")
    log_resume(file_path, fill, pages)


def log_resume(file_path: Path, fill, pages):
    folder = file_path.parent
    company = folder.name

    role = "Not specified"
    job_url = "Not specified"
    jd_files = sorted(folder.glob("JD_*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if jd_files:
        lines = jd_files[0].read_text(encoding="utf-8").splitlines()
        if lines:
            role = lines[0].strip()
        for line in lines[:15]:
            if line.startswith("Job URL:"):
                job_url = line.split("Job URL:", 1)[1].strip()
                break

    iter_file = folder / "_iterations.json"
    iterations = "?"
    if iter_file.exists():
        try:
            iterations = json.loads(iter_file.read_text(encoding="utf-8")).get("iterations", "?")
        except Exception:
            pass
        iter_file.unlink(missing_ok=True)

    import log_resume as log_resume_mod
    saved_argv = sys.argv
    sys.argv = [
        "log_resume.py",
        "--file", file_path.name,
        "--company", company,
        "--role", role,
        "--url", job_url,
        "--fill", str(fill),
        "--pages", str(pages),
        "--iterations", str(iterations),
        "--date", date.today().isoformat(),
    ]
    try:
        log_resume_mod.main()
    finally:
        sys.argv = saved_argv


def convert_md(file_path: Path):
    import build_resume

    docx_path = file_path.with_suffix(".docx")
    pdf_path = file_path.with_suffix(".pdf")

    try:
        build_resume.build_docx(file_path, docx_path)
    except Exception as e:
        print(f"Resume conversion failed for: {file_path} ({e})")
        return

    results = []
    if docx_path.exists():
        results.append("docx")

    try:
        from docx2pdf import convert
        convert(str(docx_path), str(pdf_path))
        if pdf_path.exists():
            results.append("pdf")
    except Exception as e:
        print(f"docx->pdf conversion skipped ({e}). Requires Microsoft Word (Windows or macOS).")

    if results:
        print(f"Resume converted: {file_path.stem} -> {', '.join(results)}")
    else:
        print(f"Resume conversion failed for: {file_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"convert_resume.py error: {e}", file=sys.stderr)
    sys.exit(0)
