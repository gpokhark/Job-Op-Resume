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
- **Personal details**: name, email, phone, LinkedIn, GitHub (or equivalent links)
- **All roles**: title, company, location, date range, bullet points
- **Education**: degrees, institutions, dates, GPA (if present)
- **Skills / tools / certifications**: any listed
- **Projects / other sections**: anything present in the source

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

Use more bullets to fill the page — do not leave large blank areas. Aim for the upper end of each range when the role has relevant accomplishments.

| Role recency | 1 page | 1.5 pages | 2 pages |
|---|---|---|---|
| Recent (past 6 years) | 3–6 bullets | 4–6 bullets | 4–6 bullets |
| Older roles (pre-cutoff) | Omit or list with no bullets | 2–4 bullets | 2–4 bullets |

### Role inclusion rules

| Role age | 1 page | 1.5 pages | 2 pages |
|---|---|---|---|
| Past 6 years | Always include | Always include | Always include |
| 6–10 years old | Include only if directly relevant; bullets optional | Include if relevant, 2–3 bullets | Include, 2–4 bullets |
| 10+ years old | Omit unless uniquely relevant | Include only if relevant, no bullets required | Include if relevant, 1–2 bullets |

### Content rules per page size

**1 page:**
- Summary: 3–4 bullets
- Target ~500–650 words total
- Education: Degrees only (no short courses, online certifications, or nanodegrees)
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

## Step 7 — Draft the Resume

**Output the full resume as text in your response. Do NOT call the Write tool yet — saving happens only after Step 8 review passes.**

Use this exact formatting structure:

```
# **[FULL NAME IN CAPS]**

[email] | [phone] | [LinkedIn URL] | [GitHub or Portfolio URL]

# **SUMMARY**

* [Most relevant credential for this role]
* [Key technical skill matching top JD keyword]
* [Accomplishment or domain expertise relevant to role]

# **PROFESSIONAL EXPERIENCE**

## **[Job Title]	[Start Month Year] – [End Month Year or Present]**

### *[Company Name], [State/Region], [Country]*

* [Most JD-relevant accomplishment — action verb + result]
* [Second bullet]
* [Third bullet]

## **[Older Job Title]	[Start Month Year] – [End Month Year]**

### *[Company Name], [State/Region], [Country]*

# **EDUCATION**

**[Degree]**, *[University, State, Country]*	[Month Year] [(GPA – X.XX/X.XX if present)]\
**[Degree]**, *[University, Country]*	[Month Year] [(GPA – X.XX/X.XX if present)]
```

Formatting notes:
- Tab character (not spaces) between job title and date range on `##` heading lines
- Bold all section and role headings with `**`
- Italicize company/institution lines with `*`
- Use `*` bullet points (not `-`) for ATS compatibility
- List roles in reverse chronological order (most recent first)

---

## Step 8 — Inline Review Loop (run before saving)

Review the draft you just produced entirely within your current context. Do not spawn a subagent — all information is already available.

### A. Count words

Count the content words in the draft (exclude markdown symbols: `#`, `*`, `**`, URLs, pipe `|` separators). Compare to the target for the selected page size:

| Page size | Word count target | Minimum to pass |
|---|---|---|
| 1 page | 500–650 words | 500 |
| 1.5 pages | 750–950 words | 750 |
| 2 pages | 1000–1300 words | 1000 |

State the count explicitly: _"Word count: ~540 — PASS"_ or _"Word count: ~390 — FAIL (need ~110 more words)"_.

### B. Check quality — mark each item PASS or FAIL

- [ ] Word count within target range for selected page size
- [ ] Top 10 JD keywords addressed where person has real matching experience
- [ ] No fabricated skills, tools, certifications, metrics, or experience
- [ ] No generic filler or passive language ("responsible for," "assisted with," "worked on," "helped")
- [ ] Every bullet starts with a strong action verb
- [ ] Bullets are accomplishments/results — not task descriptions or duty lists
- [ ] Recent roles (past 6 years) are at the **upper end** of the bullet count range
- [ ] No role heading appears with zero bullets beneath it
- [ ] JD terminology mirrored verbatim in relevant bullets
- [ ] Education section matches page size rules (1-page: degrees only, no nanodegrees/online certs)
- [ ] Filename will include correct page size suffix (omit for 1-page default)

### C. Fix failing items (one iteration only)

If any item is FAIL:
1. List each issue precisely: _"Ford bullets 2 & 3 start with passive 'was responsible for'"_, _"word count 390 — add ~110 words to Valeo role"_
2. Rewrite **only the failing sections** inline — do not regenerate the entire resume
3. Re-state the updated word count and confirm each fixed item now passes

**Maximum one fix pass.** If a second issue remains after fixing, proceed to Step 9 and note the remaining issue to the user.

### D. Confirm review outcome

State one of:
- _"Review passed — proceeding to save."_
- _"Review passed after one fix — proceeding to save."_
- _"One issue remains after fix pass: [brief note]. Saving best-effort version."_

---

## Step 9 — Save the File

Determine the person's last name from the resume header.

Save to:
```
output/[Company_Name]/[LastName]_Resume_[Company]_[PageSuffix][YYYY-MM-DD].md
```

Where:
- `output/[Company_Name]/` = company name with spaces replaced by underscores, special characters stripped (e.g., `output/Apple/`, `output/Woven_By_Toyota/`). If the JD file is already in an `output/<Company_Name>/` folder, use that same folder path.
- `[LastName]` = person's last name extracted from the resume header
- `[Company]` = company name from the JD (shorten if long) or a short context descriptor (e.g., `ADAS_Engineer`, `IEEE_Committee`)
- `[PageSuffix]` = omit for 1-page; `_1p5_` for 1.5-page; `_2p_` for 2-page

**Example filenames:**
- 1 page: `output/Google/Smith_Resume_Google_2026-05-10.md`
- 1.5 page: `output/Google/Smith_Resume_Google_1p5_2026-05-10.md`
- 2 page: `output/Google/Smith_Resume_Google_2p_2026-05-10.md`

The post-tool hook runs automatically after the Write tool saves the file — it converts `.md` to `.docx` and `.pdf` in the same directory.

---

## Hard Rules (Non-Negotiable)

1. **No fabrication**: Never add skills, tools, certifications, metrics, or experience not present in the source resume.
2. **No filler or passive language**: Avoid "results-driven," "responsible for," "assisted with," and all similar generic or passive phrases.
3. **Always tailored**: Every resume must be tied to the specific role or context provided. Never produce a one-size-fits-all resume.
4. **Role-bullet contract**: A role either has bullets or is not listed. A heading with zero bullets is never acceptable.
5. **Recency priority**: Roles from the past 6 years always appear first and receive more bullets than older roles.
6. **Accomplishments over duties**: Every bullet describes an outcome or achievement — not a responsibility or a task.
7. **Page size is explicit only**: Never use 1.5 or 2-page format unless the user explicitly requests it.
