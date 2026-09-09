# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo is a job-application workflow: scrape job listings, then generate tailored, ATS-compatible resumes as `.md`/`.html` → `.docx`/`.pdf`. Three skills drive the workflow end-to-end; the Python scripts handle document rendering.

## Skills (slash commands)

| Command | Model | What it does |
|---|---|---|
| `/job-scraper <url>` | Haiku | Fetches a job listing via ScraplingServer MCP (falling back to Playwright MCP for client-rendered/bot-protected sites), extracts structured fields, writes `output/<Company_Name>/JD_<Company>_<Title>_<YYYY-MM-DD>.txt`. Given multiple URLs at once, runs **Batch Fit-Scoring Mode**: one subagent per URL scrapes the JD and scores it against the latest `main_resume_*.md`, writing `output/<Company_Name>/fit-report.md`; results are consolidated into a ranking table. |
| `/resume-generator for JD in @<file.txt>` | (default) | Reads `resume/main_resume_*.md` (most recent date), tailors a resume (1 page by default; 1.5 or 2 page on request), drafts it as HTML, iterates against Playwright-measured page fill, and writes `output/<Company_Name>/<LastName>_CV_<Company>_<RoleToken>_<Date>.html` |
| `/outreach-writer` | (default) | Reads the tailored CV + JD for a company, writes a Dale Carnegie–style outreach email (`<LastName>_Email_<Company>_<Date>.txt`) and/or a cover letter formatted to match the applicant's reference letter (`Gaurav_CL-<Company>-<RoleToken>_<Date>.pdf` + `.txt`) |

Skill definitions live in `.claude/skills/`. The job-scraper skill uses `mcp__ScraplingServer__get` first, escalating to `mcp__ScraplingServer__fetch` (Playwright, `wait:2000`), `mcp__ScraplingServer__stealthy_fetch`, and finally Playwright MCP directly for sites the first three attempts can't render.

Each `SKILL.md` carries a `metadata.version` (semver) in its frontmatter and a changelog table under its title — bump the version and add a changelog row whenever a skill's behavior changes, not just wording.

## Conversion pipeline

Saving any `*_CV_*.md` or `*_CV_*.html` file triggers the PostToolUse hook automatically (the older `*_Resume_*` token from before 2026-09-08 is still recognized for backward compatibility, but `/resume-generator` now always saves with the `_CV_` token):

```
*.md   →  scripts/build_resume.py    →  *.docx  →  docx2pdf (Word COM/AppleScript)  →  *.pdf
*.html →  scripts/measure_resume.py  →  *.pdf  (Playwright, fully cross-platform)
```

- **`scripts/build_resume.py`** — python-docx template approach: opens `resume/Gaurav_Resume_1_2025-11-16.docx` as a style template, clears the body XML (keeping `sectPr`), then rebuilds content by classifying each markdown line and applying the matching Word style (`Title`, `Heading 1/2/3`, `List Paragraph`, `Normal`). Strips trailing `\` (pandoc hard-break marker) before processing.
- **`scripts/convert_resume.py`** — PostToolUse hook script (cross-platform: Windows/macOS/Linux, invoked via `uv run`). Reads tool event JSON from stdin, extracts `file_path`, skips non-resume files, and dispatches to `measure_resume.py` (for `.html`) or `build_resume.py` + `docx2pdf` (for `.md`). The `.md` → `.docx` → PDF path still requires Microsoft Word (COM on Windows, AppleScript on macOS) for the final PDF step — no Word means the `.docx` is produced but PDF conversion is skipped with a message; the `.html` path has no such dependency.
- **`scripts/log_resume.py`** — appends one row (date, company, role, JD URL, fill %, pages, iterations, filename) to `output/resume_log.csv`. Called automatically from `convert_resume.py` only on the `.html` path, after consuming and deleting the `_iterations.json` sidecar that `/resume-generator` writes before its final save. The legacy `.md` path does not log.
- The PostToolUse hook matcher is scoped to the **`Write`** tool only (see `.claude/settings.json`) — saving a resume via `cp`, `mv`, or any Bash command will not trigger conversion or logging; always use the Write tool for the final `*_CV_*` save.
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

Key packages: `python-docx`, `docx2pdf`, `pypdf` (PDF page-counting in `measure_resume.py`), `scrapling[ai]` (from GitHub HEAD — PyPI version lacks MCP support). The `ai` extra pulls in `mcp`, `click`, `markdownify`, and the `fetchers` extra (Playwright/Patchright). After `uv sync`, run `uv run scrapling install` once to download the Playwright/Patchright browser binaries — required for `fetch`/`stealthy_fetch`.

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
| Tailored CV | `<LastName>_CV_<Company>_<RoleToken>_<Date>.html` (+ `.pdf`; `_1p5_`/`_2p_` inserted before the date for non-default page counts). `<RoleToken>` is a compact tag from the JD title — a recognized role acronym where one exists (e.g. `TPM`, `STE`), otherwise each significant word truncated to ~3 letters (e.g. `ADASTesEng`) — always present, so two roles at the same company on the same day never collide on filename or blow past reasonable filename length | `output/<Company_Name>/` |
| Fit report (batch job-scraper mode) | `fit-report.md` | `output/<Company_Name>/` |
| Outreach email | `<LastName>_Email_<Company>_<YYYY-MM-DD>.txt` | `output/<Company_Name>/` |
| Cover letter | `Gaurav_CL-<Company>-<RoleToken>_<YYYY-MM-DD>.pdf` (+ `.html` build artifact, + `.txt` plain-text copy). `<RoleToken>` reuses the same token as that role's tailored CV filename | `output/<Company_Name>/` |
| Resume generation log | `resume_log.csv` (one row per `.html`→PDF conversion) | `output/` |

`<Company_Name>` is the company name with spaces replaced by underscores and special characters stripped (e.g., `output/Apple/`, `output/Woven_By_Toyota/`). The JD file also includes a `Job URL:` field in its header so the source link is preserved alongside the extracted content. Skills always pick the file with the most recent date in the name.

## MCP server

ScraplingServer is configured in `.mcp.json` (project scope) via `uv run scrapling mcp`. If it shows as disconnected, run `uv sync` (rebuilds `.venv`) and `uv run scrapling install` (installs Playwright/Patchright browser binaries). MCP tool schemas are deferred — use `ToolSearch` with `select:mcp__ScraplingServer__get` (etc.) before calling them.

Playwright MCP (`mcp__playwright__*`) is registered separately as a **local, user-scoped** fallback (`claude mcp add playwright -- npx -y @playwright/mcp@latest`) — it lives outside `.mcp.json`, so it is not shared via git and must be re-added on a new machine. `/job-scraper` only escalates to it after all three ScraplingServer attempts fail, typically for sites that render the job description client-side (e.g. Workday). Its tool schemas are deferred the same way — load with `ToolSearch` before calling.
