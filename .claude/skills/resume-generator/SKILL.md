---
name: resume-generator
description: Generate a tailored US Letter resume (1, 1.5, or 2 pages) in markdown format from a provided main resume file and a job description or context. Use this skill whenever asked to create a resume, write a CV, tailor a resume to a job, customize for a company or role, produce a resume from a job description, or prepare a job application. Triggers on phrases like "generate resume for [company]", "create resume", "tailor my resume", "write a 2-page resume for [JD]", or any request that includes a job description and asks for a resume. Always invoke this skill — never create a resume without it.
model: claude-haiku-4-5-20251001
---

# Resume Generator

Generates a tailored, ATS-compatible US Letter resume in markdown format from a source resume file. A post-tool hook automatically converts the saved `.md` to `.docx` and `.pdf` — no conversion work needed from you.

**Default page size: 1 page.** Use 1.5 or 2 pages only when the user explicitly requests it.

---

## Step 1 — Gather Inputs

### Applicant contact info
Read from `CLAUDE.local.md` (already loaded in context — **do not parse from the resume file**). Extract: Name, Email, Phone, LinkedIn, GitHub. If `CLAUDE.local.md` is absent or has no contact section, fall back to reading the top 3 lines of the main resume file.

### Main resume file
Use the Glob tool to find the latest main resume in `resume/main_resume_*.md` within this project. Pick the file with the most recent date in its name. If no file matches, ask the user: _"Please provide the path to your main resume file."_

### Review evidence file (IEEE/SAE/committee contexts only)
If the context is IEEE, SAE, a journal, editorial board, program committee, or technical committee, use Glob to find `resume/Review_Evidence_*.md`. Pick the most recent match. If none exists, ask the user before proceeding.

### Job description or context (required)
Any combination of: JD text, company name, role title, responsibilities, required skills, education requirements, or free-form notes. This must be provided — if absent, ask for it.

### Output directory
Default: `output/<Company_Name>/` where `<Company_Name>` is derived from the JD or context (spaces → underscores, special characters stripped). If the JD file is already inside an `output/<Company_Name>/` folder, use that same folder. Override only if the user specifies a different location.

### Page size detection
- No mention → **1 page** (default)
- "1.5 page" / "one and a half page" / "page and a half" → **1.5 pages**
- "2 page" / "two page" / "full two pages" → **2 pages**

---

## Step 2 — Read and Parse the Source Resume

Read the main resume file. Extract:
- **All roles**: title, company, location, date range, bullet points
- **Education**: degrees, institutions, dates, GPA (if present)
- **Skills / tools / certifications**: any listed
- **Projects / other sections**: anything present in the source
- Skip personal details (name, email, phone, LinkedIn, GitHub) — those come from `CLAUDE.local.md` per Step 1.

Identify the **past-6-years cutoff date** (today minus 6 years). Classify each role as recent or older accordingly.

---

## Step 3 — Extract Top 10 Keywords

Identify the 10 most important keywords and required skills from the JD or context. List them explicitly before proceeding. Look for:
- Technologies and tools specific to the domain
- Methodologies, standards, and certifications mentioned
- Domain-specific terminology used in the JD
- Seniority signals (e.g., "lead," "manage," "architect," "hands-on")

---

## Step 4 — Map Keywords to the Person's Experience

For each keyword, identify matching experience in the source resume. Be honest about gaps — never fill them with fabricated content. Note partial matches and use accurate language only.

---

## Step 5 — Core Rules for Bullet Points

Apply these universally across all page sizes.

### Writing formula
**Action verb → Accomplishment/action taken → Quantifiable result or scope**

- Start every bullet with a strong action verb: *Developed, Led, Designed, Implemented, Resolved, Directed, Validated, Reduced, Increased, Deployed, Coordinated, Spearheaded, Established, Managed, Delivered*
- State what was done and what it achieved — not what the role required
- Use metrics and numbers wherever the source resume provides them
- If no metric is available, use scope or scale (e.g., "across 5 product lines," "for a cross-functional team of 12")

### Pitfalls to avoid
- **No passive language**: Never write "responsible for," "assisted with," "helped," "was involved in," or "worked on"
- **No paragraphs**: Bullets only — one concise line per bullet
- **No task lists**: Only accomplishments and outcomes; not every daily duty
- **No generic filler**: Never use "results-driven," "dynamic," "passionate," "proven track record," "team player," "strong communicator"

### Tailoring
- Include JD keywords naturally in bullet text where the person's real experience supports it
- Mirror the exact terminology from the JD (e.g., if JD says "functional safety," use that — not "safety standards")
- Reorder bullets within each role so the most JD-relevant accomplishment appears first

---

## Step 6 — Select Content by Page Size

### Bullet count targets

> **CSS capacity (measured):** Each 25-word bullet renders to ~50px in Chromium. A 3-role resume at 4+4+3=11 bullets fills ~930px (97%); at 5+5+4=14 bullets it hits ~1100px (overflow). **Always start the 1-page draft at 4 bullets per recent role and 3 for the oldest included role.** Expand only after measuring `"underflow"`. Never start with 5+ and trim — that wastes one full measurement cycle.

Section headings and their spacing consume significant vertical space that word count does not capture. The table below shows outer limits, not starting targets.

| Role recency | 1 page | 1.5 pages | 2 pages |
|---|---|---|---|
| Recent (past 6 years) | **4 bullets to start; 5–6 only after underflow** | 4–6 bullets | 4–6 bullets |
| Older roles (pre-cutoff) | Omit or list with no bullets | 2–4 bullets | 2–4 bullets |

### Role inclusion rules

| Role age | 1 page | 1.5 pages | 2 pages |
|---|---|---|---|
| Past 6 years | Always include | Always include | Always include |
| 6–10 years old | Include only if directly relevant; bullets optional | Include if relevant, 2–3 bullets | Include, 2–4 bullets |
| 10+ years old | Omit unless uniquely relevant | Include only if relevant, no bullets required | Include if relevant, 1–2 bullets |

### Content rules per page size

**1 page:**
- Summary: **4 bullets** (fixed — not a range)
- Recent roles: **4 bullets each to start** — add a 5th only if measurement returns `"underflow"`
- **Each bullet must average 20–28 words** — short bullets (under 15 words) are the primary cause of white space; elaborate them with scope, method, or outcome rather than adding more bullets
- Target ~560–660 words total for a 3-recent-role resume
- Education: Degrees only (no short courses, online certifications, or nanodegrees)
- **Technical Skills block (2 lines max):** after Education, add a compact inline block of the most JD-relevant tools and technologies from the source resume. Use a simple format: `**Category:** Tool1, Tool2, Tool3`. Maximum 2 lines. Include only tools genuinely present in the source resume and relevant to the JD — this is ATS-critical and fills the bottom naturally without padding.
- Drop older roles freely to stay within limit
- No Projects section

**1.5 pages:**
- Summary: 4–5 bullets
- Target ~750–950 words total
- Education: Degrees + online certifications/nanodegrees only if directly relevant to the role
- Include older roles with bullets if relevant
- Projects section: optional, 2–3 relevant projects if space allows

**2 pages:**
- Summary: 4–5 bullets
- Target ~1000–1300 words total
- Education: Degrees + relevant certifications/courses
- Include all relevant roles with full bullets
- Projects section: 3–5 relevant projects
- Extracurricular/competition experience (e.g., FSAE) if relevant to the role

---

## Step 7 — Draft the Resume as HTML

**Write the full resume as a self-contained HTML file. Do NOT call the Write tool yet — saving happens only after Step 8 measurement passes.**

Use this exact HTML template. Fill in the bracketed placeholders with the tailored resume content. Do not change the CSS — only fill in the content sections.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10.5pt;
    line-height: 1.2;
    color: #000;
    width: 7.5in;
  }
  .name {
    font-size: 17pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 2pt;
  }
  .contact {
    text-align: center;
    font-size: 9.5pt;
    margin-bottom: 5pt;
  }
  .section {
    font-size: 10.5pt;
    font-weight: bold;
    text-transform: uppercase;
    border-bottom: 1pt solid #000;
    margin-top: 5pt;
    margin-bottom: 2pt;
    letter-spacing: 0.4pt;
  }
  .role-line {
    display: flex;
    justify-content: space-between;
    font-weight: bold;
    font-size: 10.5pt;
    margin-top: 2pt;
    margin-bottom: 1pt;
  }
  .company-line {
    font-style: italic;
    font-size: 10pt;
    margin-bottom: 1pt;
  }
  ul {
    margin-left: 13pt;
    margin-bottom: 0;
  }
  li {
    margin-bottom: 1.5pt;
    font-size: 10.5pt;
    text-align: justify;
  }
  .edu-line {
    display: flex;
    justify-content: space-between;
    margin-bottom: 1.5pt;
  }
  .skills-line {
    font-size: 10pt;
    margin-bottom: 1.5pt;
  }
</style>
</head>
<body>

<div class="name">[FULL NAME IN CAPS]</div>
<div class="contact">[email] | [phone] | [LinkedIn URL] | [GitHub URL]</div>

<div class="section">Summary</div>
<ul>
  <li>[Summary bullet 1 — most relevant credential]</li>
  <li>[Summary bullet 2 — key technical skill matching top JD keyword]</li>
  <li>[Summary bullet 3 — accomplishment or domain expertise]</li>
  <li>[Summary bullet 4 — differentiator relevant to this role]</li>
</ul>

<div class="section">Professional Experience</div>

<div class="role-line"><span>[Job Title]</span><span>[Start Month Year] – [End Month Year or Present]</span></div>
<div class="company-line">[Company Name], [State], [Country]</div>
<ul>
  <li>[Most JD-relevant bullet — action verb + outcome]</li>
  <li>[Bullet 2]</li>
  <li>[Bullet 3]</li>
  <li>[Bullet 4]</li>
  <li>[Bullet 5]</li>
</ul>

<div class="role-line"><span>[Job Title]</span><span>[Start Month Year] – [End Month Year]</span></div>
<div class="company-line">[Company Name], [State], [Country]</div>
<ul>
  <li>[Bullet 1]</li>
  <li>[Bullet 2]</li>
  <li>[Bullet 3]</li>
  <li>[Bullet 4]</li>
  <li>[Bullet 5]</li>
</ul>

<div class="section">Education</div>
<div class="edu-line">
  <span><strong>[Degree]</strong>, <em>[University, State, Country]</em></span>
  <span>[Month Year] (GPA – X.XX/X.XX)</span>
</div>
<div class="edu-line">
  <span><strong>[Degree]</strong>, <em>[University, Country]</em></span>
  <span>[Month Year] (GPA – X.XX/X.XX)</span>
</div>

<div class="section">Technical Skills</div>
<div class="skills-line"><strong>[Category]:</strong> [Tool1], [Tool2], [Tool3], [Tool4]</div>
<div class="skills-line"><strong>[Category]:</strong> [Tool1], [Tool2], [Tool3], [Tool4]</div>

</body>
</html>
```

Content rules inside the HTML:
- Each `<li>` bullet: 20–28 words, strong action verb first, accomplishment + outcome
- No passive language inside tags: no "responsible for," "assisted with"
- Recent roles: 4 `<li>` bullets each to start; add a 5th only after measuring `"underflow"`
- Technical Skills: exactly 2 `<div class="skills-line">` lines, JD-relevant tools only
- Do not alter any CSS values — spacing is calibrated for US Letter fill

---

## Step 8 — Measure Page Fill (Playwright feedback loop)

This step uses `scripts/measure_resume.py` to render the draft in headless Chromium and report actual page count and fill percentage. This replaces word-count guessing with real rendering feedback.

### A. Save the draft to a temp path

Save the HTML to `output/[Company_Name]/_draft.html` using the Write tool. This path does **not** match the `*_Resume_*` hook pattern, so no PDF conversion runs yet.

### B. Run the measurement script

Start an internal iteration counter at **1** before the first measurement. Increment it by 1 each time you run the script again (after an adjustment). Carry this count forward to Step 10.

```bash
uv run python scripts/measure_resume.py output/[Company_Name]/_draft.html
```

The script outputs JSON. Read the `status` and `guidance` fields:

| `status` | Meaning | Action |
|---|---|---|
| `"ok"` | 1 page, ≥88% full | Proceed to Step 9 — save final file |
| `"overflow"` | >1 page | Trim content — see guidance for line count to remove |
| `"underflow"` | 1 page, <88% full | Add content — see guidance for line count to add |

### C. Adjust if needed (one iteration max)

**Overflow:** Remove the least JD-relevant bullets from the oldest included role first. Shorten bullets that are over 28 words. Do not remove bullets from the most recent role.

**Underflow:** Expand existing bullets — add scope, method, or outcome detail. Add a bullet to the oldest included role if all roles are already at minimum. Do not fabricate content.

After adjusting, overwrite `_draft.html` and run the measurement script again.

**Maximum one adjustment iteration.** If status is still not `"ok"` after one fix, proceed to Step 9 anyway and note the remaining issue to the user.

### D. Quality check (run alongside measurement)

While the script runs, confirm:
- [ ] No fabricated skills, tools, certifications, or metrics
- [ ] No passive language ("responsible for," "assisted with," "worked on")
- [ ] Every `<li>` starts with a strong action verb
- [ ] JD terminology mirrored verbatim in relevant bullets
- [ ] Education: degrees only for 1-page (no nanodegrees/online certs)
- [ ] Technical Skills: ≤2 lines, all tools present in source resume

---

## Step 9 — Save the Final File

Once measurement status is `"ok"` (or after one iteration), save the final HTML to:

```
output/[Company_Name]/[LastName]_Resume_[Company]_[PageSuffix][YYYY-MM-DD].html
```

Where:
- `[Company_Name]` folder: spaces → underscores, special characters stripped
- `[LastName]`: from the resume name header
- `[Company]`: company name from JD (shorten if long)
- `[PageSuffix]`: omit for 1-page; `_1p5_` for 1.5-page; `_2p_` for 2-page

The PostToolUse hook detects `*_Resume_*.html`, runs `measure_resume.py --save-pdf`, and saves the PDF alongside the HTML automatically. No manual conversion needed.

**Example filenames:**
- 1 page: `output/Honda/Pokharkar_Resume_Honda_2026-05-10.html`
- 1.5 page: `output/Honda/Pokharkar_Resume_Honda_1p5_2026-05-10.html`

After saving, report the measurement result to the user:
_"Saved. PDF generated: 1 page, 94% full."_

---

## Step 10 — Write Iteration Sidecar

Before saving the final HTML in Step 9 (immediately before the Write tool call), write a small JSON file so the PostToolUse hook can log the iteration count without any extra Claude reasoning:

```
output/[Company_Name]/_iterations.json
```

Content (replace N with your iteration counter from Step 8):
```json
{"iterations": N}
```

Use the Write tool. The hook reads this file, appends the full row to `output/resume_log.csv`, then deletes `_iterations.json` automatically. You do not need to read or write the CSV yourself.

---

## Hard Rules (Non-Negotiable)

1. **No fabrication**: Never add skills, tools, certifications, metrics, or experience not present in the source resume.
2. **No filler or passive language**: Avoid "results-driven," "responsible for," "assisted with," and all similar generic or passive phrases.
3. **Always tailored**: Every resume must be tied to the specific role or context provided. Never produce a one-size-fits-all resume.
4. **Role-bullet contract**: A role either has bullets or is not listed. A heading with zero bullets is never acceptable.
5. **Recency priority**: Roles from the past 6 years always appear first and receive more bullets than older roles.
6. **Accomplishments over duties**: Every bullet describes an outcome or achievement — not a responsibility or a task.
7. **Page size is explicit only**: Never use 1.5 or 2-page format unless the user explicitly requests it.
