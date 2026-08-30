# Job-Op-Resume

A Claude Code workflow that scrapes job listings, generates a tailored ATS-compatible resume (`.html` → `.pdf`), and drafts outreach copy (email and/or cover letter) — driven entirely by three slash commands.

## Prerequisites

- [Claude Code](https://claude.ai/code) (CLI or IDE extension)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- Microsoft Word — only required for the `.md` → `.docx` → PDF path (`docx2pdf` drives Word via COM on Windows or AppleScript on macOS). The `.html` resume path renders PDFs with Playwright and needs no Word install.

## Setup

```bash
uv sync
```

This installs all dependencies into `.venv`, including `python-docx`, `docx2pdf`, and `scrapling` (GitHub HEAD — for MCP support).

## Workflow

### Step 1 — Scrape a job listing

```
/job-scraper <job-url>
```

Fetches the job page (escalating from plain HTTP → Playwright → stealth Playwright, then to a separate Playwright MCP browser session for sites that render content client-side, e.g. Workday), extracts structured fields, and saves a `.txt` file:

```
output/<Company_Name>/JD_<Company>_<Title>_<YYYY-MM-DD>.txt
```

The file includes: Job Title, Location, Posted Date, Job ID, Job URL, full description, responsibilities, and qualifications.

Pass multiple job URLs at once and it switches to **Batch Fit-Scoring Mode**: a separate subagent scrapes each listing and scores it against your most recent `main_resume_*.md`, writing `output/<Company_Name>/fit-report.md` for each, then reports a consolidated ranking table (failed scrapes are listed with a reason, not treated as blockers).

### Step 2 — Generate the resume

```
/resume-generator for JD in @output/<Company_Name>/JD_<Company>_<Title>.txt
```

Reads `resume/main_resume_*.md` (most recent date), tailors a resume to the JD, drafts it as HTML, and iterates against a Playwright-measured page-fill check before saving:

```
output/<Company_Name>/<LastName>_Resume_<Company>_<Date>.html
                                                           └─→ .pdf  (Playwright, no Word required)
```

A row is also appended to `output/resume_log.csv` (date, company, role, fill %, pages, iterations). Add `1.5 page` or `2 page` to the command to change page count (default is 1 page); `_1p5_`/`_2p_` is inserted into the filename for those.

### Step 3 — Draft outreach copy

```
/outreach-writer
```

Reads the tailored resume and JD for a company and writes, on request, a Dale Carnegie–style outreach email (`output/<Company_Name>/<LastName>_Email_<Company>_<Date>.txt`) and/or a cover letter matched to your reference letter's format (`output/<Company_Name>/Gaurav_Cover-<Company>-<Title>.pdf`).

## Source resume format

Place your master resume at `resume/main_resume_<YYYY-MM-DD>.md`. See `resume/main_resume_sample.md` for the expected structure. Key formatting rules:

- Name: `# **FIRSTNAME LASTNAME**`
- Contact: `email | phone | LinkedIn | GitHub` (pipe-separated, no `#`)
- Section headings: `# **SUMMARY**`, `# **PROFESSIONAL EXPERIENCE**`, etc.
- Role heading: `## **Job Title\tStart – End**` (tab between title and date)
- Company line: `### *Company, State, Country*`
- Bullets: `* text` (asterisk, not dash)
- Education entries: `**Degree**, *University*\tDate` (tab before date; use `\` at end of line to separate entries without extra spacing)

## Repository layout

```
resume/
  main_resume_<YYYY-MM-DD>.md    ← your master resume (edit this)
  main_resume_sample.md          ← anonymized example
  Gaurav_Resume_1_2025-11-16.docx ← Word style template (do not delete)

output/
  <Company_Name>/                ← created per job application
    JD_*.txt
    *_Resume_*.html / .pdf       ← primary path; .md / .docx still supported (legacy/manual)
    fit-report.md                ← only in job-scraper Batch Fit-Scoring Mode
    <LastName>_Email_*.txt
    Gaurav_Cover-*.html / .pdf
  resume_log.csv                 ← one row per .html → PDF conversion

scripts/
  build_resume.py                ← md → docx (python-docx, template-based)
  measure_resume.py              ← html → pdf via Playwright, reports page fill %
  convert_resume.py              ← PostToolUse hook (cross-platform, Write-tool only): dispatches md or html to the above
  log_resume.py                  ← appends a row to output/resume_log.csv (.html path only)

.claude/
  skills/job-scraper/SKILL.md
  skills/resume-generator/SKILL.md
  skills/outreach-writer/SKILL.md
  settings.json                  ← hook config
.mcp.json                        ← ScraplingServer MCP (project-scoped)
                                    Playwright MCP is registered separately, locally (`claude mcp add`) — not in this file
```

> `output/` is git-ignored — generated resumes stay local.

## Manual conversion

If you edit a resume outside Claude Code and need to regenerate the output files:

```bash
# .md resume
uv run python scripts/build_resume.py output/<Company>/<file>.md output/<Company>/<file>.docx
uv run python -c "from docx2pdf import convert; convert('output/<Company>/<file>.docx', 'output/<Company>/<file>.pdf')"

# .html resume
uv run python scripts/measure_resume.py output/<Company>/<file>.html --save-pdf output/<Company>/<file>.pdf
```

Cover letters use the same `.html` → `.pdf` command — the PostToolUse hook only watches `*_Resume_*` filenames, so `/outreach-writer` runs this conversion explicitly rather than relying on the hook.
