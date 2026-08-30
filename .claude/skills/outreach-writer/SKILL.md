---
name: outreach-writer
description: Write a short Dale Carnegie–style outreach email to a hiring manager or recruiter, and/or a tailored cover letter, based on the applicant's tailored resume and a job description. Use whenever asked to "write an email to the hiring manager/recruiter", "draft an outreach email", "write a cover letter", "generate a cover letter for [company]", or any request to reach out about a job application. Triggers on phrases combining an email or cover letter with a company, role, or job description. Always invoke this skill — never hand-write outreach copy without it.
metadata:
  version: 1.0.0
---

# Outreach Writer

**Version:** 1.0.0 · Last updated 2026-07-30

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-07-30 | Initial skill: outreach email (Dale Carnegie style, .txt) and cover letter (matched to reference PDF format, rendered via HTML → PDF). |

Generates two possible deliverables from the same inputs — an applicant's tailored resume and a job description:

1. **Outreach email** — a short, Dale Carnegie–style email to a hiring manager or recruiter (200–250 words, 3 points). **Output: plain text (`.txt`)** — no markdown formatting, to avoid rendering artifacts when pasted into an email client.
2. **Cover letter** — a formal cover letter tied to the resume and JD (~5 bullet points, ~220 words), formatted to match `resume/GAURAV-POKHARKAR-Cover-Letter-20240712.pdf` (the applicant's reference example). **Output: PDF (`.pdf`)** — the HTML used to render it is kept alongside as a build artifact, but the PDF is the deliverable.

Generate whichever the user asked for. If the request is ambiguous ("write something to send with my application"), ask which one(s) they want.

---

## Step 1 — Determine What to Generate

- "email", "outreach email", "message to the hiring manager/recruiter" → **Email only**
- "cover letter" → **Cover letter only**
- "both", "email and cover letter", or genuinely ambiguous phrasing → ask the user via a clarifying question before proceeding

---

## Step 2 — Gather Inputs

### Applicant contact info and name
Read from `CLAUDE.local.md` if present (Name, Email, Phone, LinkedIn, GitHub). If absent, fall back to the top 3 lines of the main resume file (`resume/main_resume_*.md`, most recent date).

### Tailored resume for this role (preferred source)
Use Glob to find `output/<Company_Name>/*_Resume_*.{html,md}` — the most recently dated tailored resume for this company. This is the primary source of points and keywords, since it is already JD-tailored.

If no tailored resume exists yet for this company, fall back to `resume/main_resume_*.md` (most recent date) and note to the user that a tailored resume doesn't exist yet — offer to run `/resume-generator` first, but proceed with the main resume if the user wants to continue anyway.

### Job description
Use Glob to find `output/<Company_Name>/JD_*.txt` (most recent date). If none exists and the user hasn't pasted JD text inline, ask for it — this is required.

### Recipient details
- **Hiring manager or recruiter name**: check the JD text and conversation context first. If genuinely unknown, ask the user once. If they don't know it either, use "Dear Hiring Team," (email) or "Dear Hiring Manager," (cover letter) — never invent a name.
- **Company name and role title**: from the JD file header/filename.

### Output directory
`output/<Company_Name>/` — same folder as the JD and tailored resume for this company.

---

## Step 3 — Extract Shared Value Points

Compare the tailored resume against the JD and identify 4–6 candidate points where the applicant's real, documented experience directly matches a JD requirement or priority. Rank them by relevance. These candidate points feed both the email (pick top 3) and the cover letter (pick top 5).

Never use a point that isn't backed by content actually present in the resume — no fabrication, no inflated claims.

---

## Step 4 — Dale Carnegie Writing Principles (apply to both documents)

These principles, from *How to Win Friends and Influence People*, govern tone and structure for both the email and the cover letter:

1. **Talk in terms of the other person's interests.** Frame every point as a benefit to their team or organization, not as a personal accomplishment in isolation. "This means your team gets X" beats "I did X."
2. **Don't open with "I."** Lead with something about their company, team, or need — not with "I am writing to apply" or "I am a [job title] with N years of experience."
3. **Make the other person feel important.** Reference something specific and genuine about the role, team, or company mission drawn from the JD — not generic flattery.
4. **Arouse an eager want.** Close with a forward-looking, low-pressure next step (e.g., "I'd welcome the chance to talk about how I can help your team hit X") rather than a demanding ask.
5. **Be short, sincere, and specific.** No generic filler: never use "results-driven," "dynamic," "passionate," "proven track record," "team player," "hardworking," "synergy," or similar stock phrases.
6. **Every claim must be true and drawn from the resume/JD.** Sincerity is a Carnegie principle in itself — an exaggerated or generic letter reads as insincere and undermines the whole approach.

---

## Step 5A — Draft the Email (if requested)

**Target: 200–250 words, 3 points.**

Structure (prose paragraphs, in the spirit of Carnegie's own example — not necessarily bulleted):

```
Subject: [Role Title] (Role/Job ID: [ID, if known]) – [Applicant Full Name]

Dear [Hiring Manager Name / Hiring Team],

[Opening: 1–2 sentences that name the specific role title and Job ID/Role Number (if known), connect it to something specific about their team's focus, and state plainly that the applicant is confident they can bring value to that role — not "I am applying for..." or a bare title drop with no value claim]

[Point 1: 1–2 sentences — a documented skill/achievement mapped to a top JD need, phrased as value to them, with enough concrete detail (tools, scope, outcome) to substantiate it]

[Point 2: 1–2 sentences — same pattern, different JD need]

[Point 3: 1–2 sentences — same pattern, different JD need]

[Closing: 1–2 sentences, forward-looking, low-pressure call to action]

Sincerely,
[Applicant Full Name]
[Phone] | [Email] | [LinkedIn]
```

**Opening line requirements (non-negotiable):**
- Must name the exact role title from the JD.
- Must include the Job ID/Role Number if the JD provides one (check the JD file's "Role Number:" / "Job ID:" / "Job Code:" field).
- Must explicitly state the applicant's confidence in bringing value to that specific role — not just imply it through the points that follow.

**Avoid invented-sounding specificity.** Never construct a number or label that doesn't exist in the source resume (e.g., turning "led calibration delivery across software, bench, vehicle test, systems, and CAD teams" into "six-team ADAS programs" — that number was never stated as a team count in the resume and reads as a fabricated metric). If a bullet lists several team names, refer to them as "cross-functional teams" or name 2–3 of the most relevant ones — do not compress them into an invented headcount or program-size figure.

**Don't stretch a skill's timeframe to the applicant's total years of experience.** A skill or achievement drawn from one specific role must not be framed as if practiced across the applicant's entire career span (e.g., "Over 9+ years, I have forecasted engineering hours and budget allocation..." when that forecasting work only happened during a ~2-year role at one company — the applicant's total automotive experience is 9+ years, but individual skills belong to whichever specific role(s) they actually appear in). When citing a resume-backed skill, either attribute it to the specific company/role it came from (e.g., "At [Company], I...") or state it without a timeframe at all — never default to the applicant's total-years figure unless the skill genuinely spans that long per the resume.

Draft the body text first (excluding the Sincerely/signature block) and count words with a quick word count. Adjust once if outside the 200–250 range — expand a point with concrete detail (tool, scope, outcome) if under 200, or trim the least JD-relevant clause if over 250. Do not pad with filler to hit the count.

### Save
`output/<Company_Name>/<LastName>_Email_<Company>_<YYYY-MM-DD>.txt`

Plain text file, exactly the structure above with placeholders filled in. No markdown formatting, no HTML — this is meant to be copy-pasted directly into an email client.

---

## Step 5B — Draft the Cover Letter (if requested)

**Format reference:** `resume/GAURAV-POKHARKAR-Cover-Letter-20240712.pdf` — the applicant's own prior cover letter. Match its structure exactly: header block, right-aligned date, 3-line recipient block, one-paragraph opening naming the role and job ID, a transition sentence, 5 bold-labeled bullets, a two-paragraph closing, and a bare sign-off (name only, no repeated contact block).

**Target: ~220 words (200–260 acceptable) across the opening + bullets + closing, exactly 5 bullet points, each with a bolded category label.**

Structure:

```
[Applicant Full Name]
[Phone] | [Email] | [LinkedIn] | [GitHub]

[Today's date, right-aligned, e.g. Month Day, Year]

[Hiring Manager Name, or "Hiring Manager" if unknown]
[Company Name]
[Location — city/state or country, from the JD, if available]

Dear [Hiring Manager Name / "Hiring Manager"],

[Opening paragraph, one paragraph, 3–4 sentences: "I am writing to express my interest in the [Role Title] position ([Job ID/Role Number, if known]) at [Company]. With over [N years from resume] years of hands-on experience in [domain], I am confident in my ability to contribute effectively to your team. My background in [2–3 areas drawn from the resume] aligns well with the qualifications and responsibilities outlined for this role."]

My professional experience and technical expertise make me a strong candidate for this position:

• **[Category Label 1]:** [1–2 sentences — resume-backed skill/achievement mapped to a JD requirement]
• **[Category Label 2]:** [1–2 sentences — resume-backed skill/achievement mapped to a JD requirement]
• **[Category Label 3]:** [1–2 sentences — resume-backed skill/achievement mapped to a JD requirement]
• **[Category Label 4]:** [1–2 sentences — resume-backed skill/achievement mapped to a JD requirement]
• **[Category Label 5]:** [1–2 sentences — resume-backed skill/achievement mapped to a JD requirement]

[Closing paragraph 1, 1–2 sentences: enthusiasm about contributing to something specific from the JD/company mission — "I am excited about the opportunity to bring my skills and experience to [Company], contributing to [specific JD/company goal]."]

[Closing paragraph 2, 1–2 sentences: "Thank you for considering my application. I look forward to the possibility of discussing how my background, skills, and experience align with [Company]'s goals."]

Sincerely,
[Applicant Full Name]
```

The 5 category labels should be short JD-derived phrases (e.g. "Extensive ADAS Experience," "Project Management Skills") — pick labels that name the JD requirement each bullet answers, not generic headers.

Draft this plain-text body first and count words across the opening paragraph + transition sentence + 5 bullets + 2 closing paragraphs (excluding the header block, date, recipient block, and signature). Adjust once if outside 200–260 words.

### Render as HTML and save

Wrap the drafted content in this template (do not alter the CSS — matches the resume pipeline's page assumptions):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    line-height: 1.35;
    color: #000;
    width: 7.5in;
  }
  .sender-name { font-size: 16pt; font-weight: bold; text-align: center; margin-bottom: 2pt; }
  .sender-contact { font-size: 10pt; text-align: center; margin-bottom: 18pt; }
  .date { text-align: right; margin-bottom: 14pt; }
  .recipient { margin-bottom: 14pt; }
  p { margin-bottom: 10pt; text-align: justify; }
  ul { margin-left: 18pt; margin-bottom: 10pt; }
  li { margin-bottom: 6pt; }
  .signoff { margin-top: 10pt; }
</style>
</head>
<body>

<div class="sender-name">[APPLICANT FULL NAME IN CAPS]</div>
<div class="sender-contact">[Email] | [Phone] | [LinkedIn URL] | [GitHub URL]</div>

<div class="date">[Month Day, Year]</div>

<div class="recipient">
  [Hiring Manager Name / Hiring Manager]<br>
  [Company Name]<br>
  [Location]
</div>

<p>Dear [Hiring Manager Name / Hiring Manager],</p>

<p>[Opening paragraph]</p>

<p>My professional experience and technical expertise make me a strong candidate for this position:</p>

<ul>
  <li><strong>[Category Label 1]:</strong> [Bullet 1 text]</li>
  <li><strong>[Category Label 2]:</strong> [Bullet 2 text]</li>
  <li><strong>[Category Label 3]:</strong> [Bullet 3 text]</li>
  <li><strong>[Category Label 4]:</strong> [Bullet 4 text]</li>
  <li><strong>[Category Label 5]:</strong> [Bullet 5 text]</li>
</ul>

<p>[Closing paragraph 1]</p>

<p>[Closing paragraph 2]</p>

<p class="signoff">Sincerely,<br>[Applicant Full Name]</p>

</body>
</html>
```

### Filename

Save the HTML and PDF to:

```
output/<Company_Name>/Gaurav_Cover-<Company>-<Title>.html
output/<Company_Name>/Gaurav_Cover-<Company>-<Title>.pdf
```

Where `<Company>` and `<Title>` follow the same sanitization as JD filenames (spaces → underscores, special characters stripped, title shortened to its first 3–4 words) — reuse the exact shortened `<Company>`/`<Title>` tokens already used in that company's JD filename for consistency. No date component. Example: `output/Honda/Gaurav_Cover-Honda-Principal_ADAS_Development.pdf`.

Generate the PDF directly (the PostToolUse hook for resumes does not cover this filename pattern, so convert explicitly):

```bash
uv run python scripts/measure_resume.py output/<Company_Name>/Gaurav_Cover-<Company>-<Title>.html --save-pdf output/<Company_Name>/Gaurav_Cover-<Company>-<Title>.pdf
```

At ~220 words this will almost always report `"underflow"` (well under a full page) — that is expected and correct; do **not** pad content to raise the fill percentage. Only act if the script reports `"overflow"` (more than 1 page): trim the least JD-relevant bullet, or shorten the two closing paragraphs.

---

## Step 6 — Report Back

After saving, report what was generated and where, e.g.:

```
Email saved: output/Honda/Pokharkar_Email_Honda_2026-07-18.txt (98 words)
Cover letter saved: output/Honda/Gaurav_Cover-Honda-Principal_ADAS_Development.pdf (231 words)
```

---

## Hard Rules (Non-Negotiable)

1. **No fabrication**: every point, skill, or achievement referenced must exist in the tailored resume or main resume. Never invent metrics, availability dates, locations, or relationships not stated by the user.
2. **No invented recipient names**: if the hiring manager/recruiter name is unknown and the user can't supply it, use a generic salutation ("Dear Hiring Team," for the email, "Dear Hiring Manager," for the cover letter) — never guess a name.
3. **Word counts are targets, not suggestions**: email 200–250 words, cover letter ~220 words (200–260). One adjustment pass max; report the final count either way.
4. **Dale Carnegie tone in the email**: benefit-to-them framing, no opening with "I," no generic filler adjectives, sincere and specific, low-pressure close. The cover letter follows the reference example's more traditional opening ("I am writing to express my interest...") but keeps every other Carnegie principle — specific, sincere, benefit-framed bullets, no filler adjectives.
5. **Always tied to a real JD**: never generate generic, un-tailored outreach copy — a job description (file or pasted text) is required input.
6. **Cover letter bullet count is exactly 5**, each with a bolded category label — not 4, not 6.
7. **Email point count is exactly 3.**
8. **File formats are fixed**: email is always plain `.txt`; cover letter is always rendered to `.pdf` (via the HTML intermediate) — never skip the PDF conversion step.
