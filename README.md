# Job-Op-Resume

A Claude Code workflow that scrapes job listings and generates tailored, ATS-compatible resumes as `.md` → `.docx` → `.pdf` — driven entirely by two slash commands.

## Prerequisites

- [Claude Code](https://claude.ai/code) (CLI or IDE extension)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- Microsoft Word (required for PDF conversion via `docx2pdf`)

## Setup

```powershell
uv sync
```

This installs all dependencies into `.venv`, including `python-docx`, `docx2pdf`, and `scrapling` (GitHub HEAD — for MCP support).

## Workflow

### Step 1 — Scrape a job listing

```
/job-scraper <job-url>
```

Fetches the job page (escalating from plain HTTP → Playwright → stealth Playwright for JS-heavy sites), extracts structured fields, and saves a `.txt` file:

```
output/<Company_Name>/JD_<Company>_<Title>_<YYYY-MM-DD>.txt
```

The file includes: Job Title, Location, Posted Date, Job ID, Job URL, full description, responsibilities, and qualifications.

### Step 2 — Generate the resume

```
/resume-generator for JD in @output/<Company_Name>/JD_<Company>_<Title>.txt
```

Reads `resume/main_resume_*.md` (most recent date), tailors a 1-page resume to the JD, and saves it. The post-save hook converts automatically:

```
output/<Company_Name>/<LastName>_Resume_<Company>_<Date>.md
                                                          └─→ .docx  (python-docx)
                                                          └─→ .pdf   (docx2pdf via Word)
```

Add `1.5 page` or `2 page` to the command to change page count.

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
    *_Resume_*.md / .docx / .pdf

scripts/
  build_resume.py                ← md → docx (python-docx, template-based)
  convert_resume.ps1             ← PostToolUse hook: md → docx → pdf

.claude/
  skills/job-scraper/SKILL.md
  skills/resume-generator/SKILL.md
  settings.json                  ← hook config
.mcp.json                        ← ScraplingServer MCP (project-scoped)
```

> `output/` is git-ignored — generated resumes stay local.

## Manual conversion

If you edit a resume `.md` outside Claude Code and need to regenerate the output files:

```powershell
uv run python scripts/build_resume.py resume\<file>.md output\<Company>\<file>.docx
uv run python -c "from docx2pdf import convert; convert(r'output\<Company>\<file>.docx', r'output\<Company>\<file>.pdf')"
```
