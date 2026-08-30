---
name: job-scraper
description: Scrape a job listing URL and extract structured job data — title, location, posted date, job ID, description, responsibilities, and qualifications. Saves a JD text file ready to pass to /resume-generator. Use whenever the user gives a job URL and wants a resume generated or job data extracted. When given multiple job listing URLs at once, scrapes each in a parallel subagent, scores fit against the applicant's resume, and reports a consolidated ranking table.
model: claude-haiku-4-5-20251001
metadata:
  version: 1.4.0
---

# Job Scraper

**Version:** 1.4.0 · Last updated 2026-08-29

| Version | Date | Change |
|---|---|---|
| 1.4.0 | 2026-08-29 | Reversed the Phenom People "not usable" conclusion — found a working technique via the site's search-results page (`phApp.ddo.eagerLoadRefineSearch.data.jobs[].postedDate`, keyed by job-ID search), distinct from and far more reliable than the confirmed-garbage detail-page JSON-LD `datePosted`. Verified stable and self-consistent across 4 jobs (11824, 11221, 12292, 11896), including two closed listings still present in the search index. Rewrote the `posted-date-workarounds.md` Phenom entry to promote this as the primary technique and clearly separate it from the known-bad detail-page field. |
| 1.3.8 | 2026-08-29 | Added a fourth confirmed data point to the Phenom People "not usable" finding — Honda job 11221 (also closed) returned the same anomalous `datePosted: 2026-08-30` as the job 11824 re-check, suggesting all Honda/Phenom pages return one shared stamped value per day regardless of which job is requested. Pattern now settled across four checks; no further verification needed. |
| 1.3.7 | 2026-08-29 | Re-verified the three "provisionally reliable" `posted-date-workarounds.md` entries (Astemo, Clinch/Waymo, Liferay/Honda RI) with independent second fetches — all three values came back byte-for-byte identical, upgrading each from "one job checked" to reliable, no re-verification needed before use. Also noted: a truncated `<head>`-only response on the Clinch/Waymo platform is a transient rendering timeout, not evidence of missing data — retry with a longer `wait` before concluding. |
| 1.3.6 | 2026-08-29 | Upgraded the Phenom People entry in `posted-date-workarounds.md` from "unreliable, usable with caveat" to "not usable at all" — re-checked Honda job 11824 after it closed and `datePosted` had advanced to a future date (`2026-08-30`, one day ahead of the actual check date) on a listing with no live content left. `datePosted` on this platform should no longer be reported to users under any caveat. |
| 1.3.5 | 2026-08-29 | Expanded the Google Careers negative-result entry in `posted-date-workarounds.md` with three more ruled-out methods (HTTP `Last-Modified` header, Wayback Machine snapshot lookup, live network-traffic capture via Playwright) — five methods total, all confirmed dead ends, so a future scrape doesn't retry any of them. |
| 1.3.4 | 2026-08-29 | Added a `posted-date-workarounds.md` entry recording Google Careers (google.com/about/careers) as a confirmed negative — no JSON-LD, no data blob, no date text anywhere on the page after an exhaustive check — so a future scrape skips re-searching and goes straight to "Not specified". |
| 1.3.3 | 2026-08-29 | Added a `posted-date-workarounds.md` entry for the Liferay DDM portal at usa.honda-ri.com — no JSON-LD here; the date lives in an inline `JobOfferData.publicationDate` JS object (human-readable, not ISO) that the page itself uses to populate the applicant confirmation email, making it stronger evidence than SEO-metadata sources. |
| 1.3.2 | 2026-08-29 | Added a `posted-date-workarounds.md` entry for the Clinch ATS platform (careers.withwaymo.com and similar `*.clinchtalent.com` sites) — plain `get` hits an AWS WAF JS challenge page, so the JSON-LD `datePosted` lookup requires `fetch` with `extraction_type: "html"` instead. Verified as a real past date (not a freshness reset) against `validThrough`. |
| 1.3.1 | 2026-08-29 | Added a `posted-date-workarounds.md` entry for the Astemo careers CMS (`<script id="js-job-posting" type="application/ld+json">` — note the `id` attribute breaks a regex anchored to `<script type=...>` with nothing in between). `datePosted` there checked out as a real past date, not a per-crawl freshness reset like the Phenom/Honda case. |
| 1.3.0 | 2026-08-29 | Added a Posted Date fallback: when the field isn't visible in rendered content, consult `references/posted-date-workarounds.md` for a per-platform technique (e.g. Phenom sites' JSON-LD `datePosted`) before giving up and writing "Not specified". |
| 1.2.0 | 2026-08-13 | Added Batch Fit-Scoring Mode: multiple job URLs run as parallel subagents, each scoring fit against the resume and writing a `fit-report.md`, consolidated into one ranking table. |
| 1.1.0 | 2026-08-13 | Added Playwright MCP fallback (Attempt 4) for JS-heavy or bot-protected listings ScraplingServer's three attempts can't fetch. |
| 1.0.0 | 2026-05-10 | Initial working skill: ScraplingServer 3-attempt fetch chain, structured field extraction, JD `.txt` output. |

Fetches a job listing URL using the ScraplingServer MCP and extracts structured job information into a text file.

---

## Step 1 — Read the URL(s) from Arguments

The job URL is provided in the skill arguments. If no URL is present, ask: _"Please provide the job listing URL."_

**If more than one job listing URL is present** (multiple links pasted, one per line, or the user says something like "these N job postings"), do **not** run Steps 2–6 directly in this conversation. Switch to **Batch Fit-Scoring Mode** below instead — it handles fetching, scoring, and reporting for every URL via parallel subagents. Steps 2–6 below still apply, but as the per-URL instructions given to each subagent, not as something this top-level flow executes itself.

---

## Step 2 — Fetch the Job Page

Use the ScraplingServer MCP tools to fetch the page. Try in order until you get meaningful content:

### Attempt 1: `mcp__ScraplingServer__get`
Call with:
- `url`: the job URL
- `extraction_type`: `"markdown"`
- `main_content_only`: `true`

**Check the result**: if it contains recognizable job content (title, qualifications, or description text), proceed to Step 3.

### Attempt 2: `mcp__ScraplingServer__fetch` (if Attempt 1 was empty or blocked)
Call with:
- `url`: the job URL
- `extraction_type`: `"markdown"`
- `main_content_only`: `true`
- `wait`: `2000` (2 seconds for JS to load)

### Attempt 3: `mcp__ScraplingServer__stealthy_fetch` (if Attempt 2 was also blocked)
Same parameters as Attempt 2. Use this for sites with aggressive bot detection (LinkedIn, Greenhouse, etc.)

### Attempt 4: Playwright MCP (if Attempt 3 was also blocked or empty)
General-purpose fallback for any job listing page where all three ScraplingServer attempts return empty, placeholder, or clearly incomplete content — e.g. sites that render the job description client-side after several XHR calls (Workday's `myworkdayjobs.com` is one common example, but this applies to any such site).

The Playwright MCP server is registered locally for this project (`claude mcp add playwright -- npx -y @playwright/mcp@latest`) — it is **not** in the project's `.mcp.json`, so it is scoped to this machine, not committed/shared. Its tool schemas are deferred like ScraplingServer's; load them first:
```
ToolSearch("select:mcp__playwright__browser_navigate,mcp__playwright__browser_snapshot,mcp__playwright__browser_wait_for")
```

Steps:
1. `mcp__playwright__browser_navigate` to the job URL.
2. `mcp__playwright__browser_wait_for` (or a short pause) for the job description content to render — client-rendered career sites typically populate within a few seconds of navigation.
3. `mcp__playwright__browser_snapshot` to get the page's accessibility-tree text, which includes the fully-rendered job description, qualifications, and metadata even when they were injected by JS after load.
4. Extract fields from the snapshot text the same way as Step 3 below.
5. Close the page/tab when done if the tool set exposes a close action, so the browser doesn't stay open across scrapes.

If Attempt 4 also returns empty or clearly incomplete content, fall through to the standard error handling below.

---

## Step 3 — Extract Job Fields

From the fetched markdown content, extract all of the following fields. If a field is not found, write `Not specified`.

| Field | What to look for |
|---|---|
| **Job Title** | The role name at the top of the listing |
| **Company** | The hiring company name |
| **Location** | City, state, country — or "Remote" |
| **Posted Date** | When the job was posted. If not visible anywhere in the fetched content, see the fallback below before writing "Not specified". |
| **Job ID / Role Number** | Any reference ID, requisition number, or role number |
| **Job Description** | The overview paragraph describing the role and team |
| **Roles & Responsibilities** | Bulleted duties, what you will do, day-to-day work |
| **Minimum Qualifications** | Required skills, education, years of experience |
| **Preferred Qualifications** | Nice-to-have skills, preferred experience |
| **Salary / Pay Range** | Compensation if listed |

### Posted Date fallback

If Posted Date is not visible anywhere in the content returned by Step 2 (this is common — many career sites never render a posted date on the page itself), **do not immediately write "Not specified".** Instead:

1. Read `references/posted-date-workarounds.md` (in this skill's directory) and check whether the current URL's domain/platform matches an existing entry.
2. If it matches, follow that entry's technique exactly, including its caveat — if the entry says the value is unreliable, carry that caveat into the JD file's `Posted:` line verbatim (e.g. `Posted: 2026-08-29 (per site metadata — may reflect last crawl/refresh, not original post date)`), never present it as a bare confirmed date.
3. If no entry matches this platform, only then write "Not specified" for this run — do not spend extra fetch attempts hunting for a date. Optionally note the new platform back to the user so a new entry can be added to the reference file for next time.

This keeps the per-scrape cost near zero: the reference file is read only on this fallback path (never on every scrape), and only long enough to find the one matching entry.

---

## Step 4 — Determine Output Path

Build the output directory and filename from extracted data:
```
output/<Company_Name>/JD_<Company>_<JobTitle>_<YYYY-MM-DD>.txt
```

Rules:
- `<Company_Name>` folder: company name with spaces replaced by underscores, special characters stripped (e.g., `Apple`, `Woven_By_Toyota`)
- Filename: replace spaces with underscores, strip special characters, shorten long titles to the first 4 words
- Use today's date (`currentDate` from context) for `<YYYY-MM-DD>`
- Example: `output/Apple/JD_Apple_Sensing_Systems_Engineer_2026-05-10.txt`

Save to `D:\github\Job-Op-Resume\output\<Company_Name>\`. The Write tool creates parent directories automatically.

---

## Step 5 — Write the Output File

Write a plain text file in this exact format:

```
<Job Title>
<Location>
<Department or Team if available>

Submit Resume

Summary
Posted: <Posted Date>
Role Number: <Job ID>
Job URL: <the original job listing URL>

<Full job description paragraph>

Description
<Role description paragraphs>

Minimum Qualifications
<Bullet each requirement>

Preferred Qualifications
<Bullet each preferred skill>

Pay & Benefits
<Salary range if present, otherwise omit this section>
```

This format mirrors what `/resume-generator` expects as a JD input file.

---

## Step 6 — Report Back

After saving, output:

```
Job scraped: <Job Title> at <Company>
Saved to: output/<Company_Name>/<filename>

To generate a resume, run:
  /resume-generator for JD in @output/<Company_Name>/<filename>
```

---

## Batch Fit-Scoring Mode (2+ job posting URLs)

Triggered whenever the arguments contain multiple job listing URLs. Each URL gets its own isolated subagent that scrapes the JD, scores it against the applicant's resume, and writes a fit report — then this top-level flow consolidates the results into one ranking.

### A. Resolve the CV baseline once

Glob `resume/main_resume_*.md` and pick the most recent date. This is the fit-scoring reference for **every** subagent — always the latest-dated main resume file, never a literal `cv.md` (it doesn't exist in this repo) and never a per-URL guess. Resolve this once, up front, and pass the resolved absolute path to each subagent so they don't each re-glob it.

### B. Launch one subagent per URL, in parallel

Use the Agent tool with `subagent_type: "general-purpose"` (not `fork` — each subagent needs no prior conversation context, just the instructions below). Launch all of them in a single message with multiple Agent tool calls so they run concurrently, not sequentially.

Each subagent's prompt must be self-contained and include:
- The exact job URL to scrape.
- The full fetch chain from Step 2 above (get → fetch → stealthy_fetch → Playwright MCP), the field list and Posted Date fallback from Step 3 (including the path to `references/posted-date-workarounds.md`, resolved relative to the job-scraper skill directory), and the output path/format from Steps 4–5 — i.e., produce the same `output/<Company>/JD_<Company>_<Title>_<Date>.txt` file a single-URL run would.
- The resolved absolute path to the latest main resume file from part A, with instructions to read it in full.
- Fit-scoring instructions (part C below).
- Instructions to report back a short structured result: company, role title, JD file path, fit score, fit-report path, and scrape status (OK or Failed + reason) — this is what gets read back to build the consolidated table.

### C. Fit-scoring instructions (given to each subagent)

Compare the scraped JD's minimum and preferred qualifications against the resume's actual, documented experience — the same honesty standard as `/resume-generator`: no inflating fit, no treating a tangential skill as a direct match. Produce:
- **Fit Score**: 0–100, where the score reflects how much of the JD's core requirements are backed by real resume experience (minimum qualifications weighted heavier than preferred).
- **Matches**: 3–5 bullets, each naming a specific JD requirement and the specific resume evidence that satisfies it.
- **Gaps**: bullets naming JD requirements the resume does not support — do not omit real gaps to make the score look better.
- **Recommendation**: one line — "Strong fit", "Partial fit", or "Weak fit" — with a short reason.

Write this to `output/<Company>/fit-report.md`:

```markdown
# Fit Report: <Job Title> at <Company>

**Job URL:** <url>
**Fit Score:** <0-100>/100
**Recommendation:** <Strong fit / Partial fit / Weak fit> — <one-line reason>

## Matches
- <JD requirement> — <resume evidence>
- ...

## Gaps
- <JD requirement not backed by resume experience>
- ...
```

If the scrape itself fails (all four fetch attempts in Step 2 return empty/blocked), the subagent does **not** write a fit-report.md — it reports back scrape status `Failed` with the specific reason (e.g., "blocked after 4 attempts — likely requires login").

### D. Consolidate results

Once all subagents report back, do not block on any single failure — collect whatever came back from each. Build one consolidated ranking table sorted by fit score descending, with failed scrapes listed at the bottom (no score):

```markdown
| Rank | Company | Role | Fit Score | Fit Report | Status |
|---|---|---|---|---|---|
| 1 | Waymo | Structured Testing Vendor Engineering Lead | 82/100 | output/Waymo/fit-report.md | OK |
| — | SiteX | Senior Test Engineer | — | — | Failed: blocked after 4 fetch attempts |
```

Below the table, list each failure with its specific reason, and suggest the manual-paste fallback (`/resume-generator for JD in @yourfile.txt` after pasting the JD text manually) for those.

---

## Error Handling

- If all four fetch attempts (including the Playwright MCP fallback) return empty or error responses, report: _"Could not fetch the job page. The site may require login or block automated access. Try copying the JD text manually into a .txt file and use `/resume-generator for JD in @yourfile.txt`."_
- If some fields are missing, include what was found and mark missing fields as `Not specified` — do not invent content.

---

## Hard Rules

1. **Never fabricate**: only extract what is present in the fetched content. In Batch Fit-Scoring Mode, this also means never inflating a fit score or omitting a real gap.
2. **Use `get` first** — it is faster and cheaper. Only escalate to `fetch`, then `stealthy_fetch`, then Playwright MCP, in that order, if the content is blocked or empty.
3. **Save to project root** — the file must be accessible to `/resume-generator`.
4. **Plain text output** — no markdown formatting inside the saved .txt file except for the structure shown in Step 5. (Batch mode's `fit-report.md` is markdown by design — this rule applies to the JD `.txt` file only.)
5. **One failed scrape never blocks the batch** — in Batch Fit-Scoring Mode, collect whatever subagents return and report failures inline in the final table rather than stalling on a retry loop.
6. **CV baseline is always the latest-dated `resume/main_resume_*.md`** — never a literal `cv.md`, never re-resolved per subagent when running in batch mode (resolve once, pass the path to every subagent).
