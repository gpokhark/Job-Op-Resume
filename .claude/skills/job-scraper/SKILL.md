---
name: job-scraper
description: Scrape a job listing URL and extract structured job data — title, location, posted date, job ID, description, responsibilities, and qualifications. Saves a JD text file ready to pass to /resume-generator. Use whenever the user gives a job URL and wants a resume generated or job data extracted.
model: claude-haiku-4-5-20251001
---

# Job Scraper

Fetches a job listing URL using the ScraplingServer MCP and extracts structured job information into a text file.

---

## Step 1 — Read the URL from Arguments

The job URL is provided in the skill arguments. If no URL is present, ask: _"Please provide the job listing URL."_

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

---

## Step 3 — Extract Job Fields

From the fetched markdown content, extract all of the following fields. If a field is not found, write `Not specified`.

| Field | What to look for |
|---|---|
| **Job Title** | The role name at the top of the listing |
| **Company** | The hiring company name |
| **Location** | City, state, country — or "Remote" |
| **Posted Date** | When the job was posted |
| **Job ID / Role Number** | Any reference ID, requisition number, or role number |
| **Job Description** | The overview paragraph describing the role and team |
| **Roles & Responsibilities** | Bulleted duties, what you will do, day-to-day work |
| **Minimum Qualifications** | Required skills, education, years of experience |
| **Preferred Qualifications** | Nice-to-have skills, preferred experience |
| **Salary / Pay Range** | Compensation if listed |

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

## Error Handling

- If all three fetch attempts return empty or error responses, report: _"Could not fetch the job page. The site may require login or block automated access. Try copying the JD text manually into a .txt file and use `/resume-generator for JD in @yourfile.txt`."_
- If some fields are missing, include what was found and mark missing fields as `Not specified` — do not invent content.

---

## Hard Rules

1. **Never fabricate**: only extract what is present in the fetched content.
2. **Use `get` first** — it is faster and cheaper. Only escalate to `fetch` or `stealthy_fetch` if the content is blocked or empty.
3. **Save to project root** — the file must be accessible to `/resume-generator`.
4. **Plain text output** — no markdown formatting inside the saved .txt file except for the structure shown in Step 5.
