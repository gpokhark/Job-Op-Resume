# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo is a job-application workflow: scrape job listings, then generate tailored, ATS-compatible resumes as `.md` → `.docx` → `.pdf`. The two skills drive the workflow end-to-end; the Python/PowerShell scripts handle document rendering.

## Skills (slash commands)

| Command | Model | What it does |
|---|---|---|
| `/job-scraper <url>` | Haiku | Fetches a job listing via ScraplingServer MCP, extracts structured fields, writes `JD_<Company>_<Title>_<YYYY-MM-DD>.txt` to project root |
| `/resume-generator for JD in @<file.txt>` | (default) | Reads `resume/main_resume_*.md` (most recent date), tailors a 1-page resume, writes `resume/<LastName>_Resume_<Company>_<Date>.md` |

Skill definitions live in `.claude/skills/`. The job-scraper skill uses `mcp__ScraplingServer__get` first, escalating to `mcp__ScraplingServer__fetch` (Playwright, `wait:2000`) and `mcp__ScraplingServer__stealthy_fetch` for JS-heavy or bot-protected sites.

## Conversion pipeline

Saving any `*_Resume_*.md` file triggers the PostToolUse hook automatically:

```
*.md  →  scripts/build_resume.py  →  *.docx  →  docx2pdf (Word COM)  →  *.pdf
```

- **`scripts/build_resume.py`** — python-docx template approach: opens `resume/Gaurav_Resume_1_2025-11-16.docx` as a style template, clears the body XML (keeping `sectPr`), then rebuilds content by classifying each markdown line and applying the matching Word style (`Title`, `Heading 1/2/3`, `List Paragraph`, `Normal`). Strips trailing `\` (pandoc hard-break marker) before processing.
- **`scripts/convert_resume.ps1`** — PostToolUse hook script. Reads tool event JSON from stdin, extracts `file_path`, skips non-resume files, calls `build_resume.py` then `docx2pdf`.
- Page size: US Letter 8.5×11", 0.5" margins all sides. Right tab stop at 10800 twips (7.5") for date alignment.

To manually run conversion (e.g. to test a change to `build_resume.py`):
```powershell
uv run python scripts/build_resume.py resume\<file>.md resume\<file>.docx
uv run python -c "from docx2pdf import convert; convert(r'resume\<file>.docx', r'resume\<file>.pdf')"
```

## Dependencies and environment

All Python dependencies are managed with `uv`. The `.venv` is project-local.

```powershell
uv sync          # install/update deps
uv add <pkg>     # add a package
```

Key packages: `python-docx`, `docx2pdf`, `scrapling[ai]` (from GitHub HEAD — PyPI version lacks MCP support). The `ai` extra pulls in `mcp`, `click`, `markdownify`, and the `fetchers` extra (Playwright/Patchright). After `uv sync`, run `uv run scrapling install` once to download the Playwright/Patchright browser binaries — required for `fetch`/`stealthy_fetch`.

The ScraplingServer MCP is configured in `.mcp.json` using `uv run scrapling mcp` (not an absolute binary path), so it works unmodified on Windows, macOS, and Linux — `uv` resolves the project-local `.venv` from the working directory. It is project-scoped and must be accessed via `ToolSearch` → deferred tool load before calling `mcp__ScraplingServer__*` tools.

## Resume markdown format

The markdown format used by `build_resume.py` line classifiers:

```markdown
# **FULL NAME**                          → Title style (name)
email | phone | linkedin | github        → Normal centered (contact)
# **SECTION HEADING**                    → Heading 1
## **Role Title	Start – End**           → Heading 2 (tab separates title from date)
### *Company, State, Country*            → Heading 3
* Bullet text                            → List Paragraph
**Degree**, *University*	Date          → Normal with right tab (education)
line ending with \                       → hard line break (no extra spacing); \ is stripped by build_resume.py
```

Section headings recognized by regex: `SUMMARY`, `PROFESSIONAL`, `EDUCATION`, `FSAE`, `PROJECTS`, `SOFTWARE`.

## File naming conventions

| Type | Pattern | Location |
|---|---|---|
| Source resume | `main_resume_<YYYY-MM-DD>.md` | `resume/` |
| Review evidence (IEEE/SAE) | `Review_Evidence_<YYYY-MM-DD>.md` | `resume/` |
| Job description | `JD_<Company>_<Title>_<YYYY-MM-DD>.txt` | `output/<Company_Name>/` |
| Tailored resume | `<LastName>_Resume_<Company>_<Date>.md` | `output/<Company_Name>/` |

`<Company_Name>` is the company name with spaces replaced by underscores and special characters stripped (e.g., `output/Apple/`, `output/Woven_By_Toyota/`). The JD file also includes a `Job URL:` field in its header so the source link is preserved alongside the extracted content. Skills always pick the file with the most recent date in the name.

## MCP server

ScraplingServer is configured in `.mcp.json` (project scope) via `uv run scrapling mcp`. If it shows as disconnected, run `uv sync` (rebuilds `.venv`) and `uv run scrapling install` (installs Playwright/Patchright browser binaries). MCP tool schemas are deferred — use `ToolSearch` with `select:mcp__ScraplingServer__get` (etc.) before calling them.
