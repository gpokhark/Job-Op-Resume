# Posted Date Workarounds

Per-platform/per-company techniques for extracting a job's Posted Date when it is not
present in the visible, rendered page content. Consulted only as a fallback — see
`SKILL.md` Step 3 for when to load this file.

Do not load this file for every scrape. Only read it (and only the one matching
section, not the whole file) after the normal fetch chain (Step 2) has returned
content and the Posted Date is still not visible on the page.

Format per entry: URL/domain pattern to match, the technique, and a caveat on how
much to trust the result.

---

## Phenom People platform (e.g. careers.honda.com, and other `*.phenompeople.com`-backed
## career sites — recognizable by `cdn.phenompeople.com` asset URLs in the page)

**Technique (use this one — search/listing page, not the detail page):** The
job's *detail* page carries a schema.org JSON-LD `datePosted` field that is
confirmed garbage (see "Known-bad" below) — do not use it. Instead, fetch the
site's **search-results page**, keyed by the job ID as the search keyword, e.g.:
```
https://careers.honda.com/us/en/search-results?keywords=<jobId>
```
with `mcp__ScraplingServer__get`, `extraction_type: "html"`, `main_content_only:
false`. The page embeds a large `phApp.ddo = {...}` JS object (not JSON-LD —
plain `var phApp.ddo = ` followed by a JSON literal) containing the search
index's own job records at
`phApp.ddo.eagerLoadRefineSearch.data.jobs[]`, each with a stable `jobId`,
`postedDate` (ISO datetime, e.g. `"2026-08-19T00:00:00.000+0000"`), and a
`dateCreated` field a few minutes/hours later the same day — useful as a
same-day internal-consistency check. Searching by job ID as the keyword
reliably returns just that one job in the array (avoid keyword text searches,
which can return many jobs and require finding the matching `jobId`).
Extraction requires balanced-brace parsing (a naive regex breaks — the object
contains nested braces and escaped quotes in `description`/`descriptionTeaser`
fields):
```python
import json

marker = 'phApp.ddo = '
start = html.find(marker) + len(marker)
depth = 0
in_str = False
esc = False
i = start
while i < len(html):
    c = html[i]
    if in_str:
        if esc:
            esc = False
        elif c == '\\':
            esc = True
        elif c == '"':
            in_str = False
    else:
        if c == '"':
            in_str = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                i += 1
                break
    i += 1
obj = json.loads(html[start:i])
jobs = obj['eagerLoadRefineSearch']['data']['jobs']
print(jobs[0]['postedDate'] if jobs else 'NOT_FOUND')
```
This works even for jobs whose detail page shows "no longer accepting
applications" — closed listings stayed in the search index and returned
correct data (verified on jobs 11824 and 11221, both closed).

**Verified stable, cross-checked across 4 jobs (2026-08-29), all self-consistent
(`postedDate` and `dateCreated` land on/near the same date, none show "today" or
a future date):**
| jobId | title | postedDate |
|---|---|---|
| 11824 | Principal ADAS Development Engineer (closed) | 2026-07-16 |
| 11221 | Senior ADAS Test Engineer II (closed) | 2026-08-19 |
| 12292 | (ADAS role) | 2026-08-14 |
| 11896 | (ADAS role) | 2026-07-20 |

**How to report it:** Plain confirmed date, truncated to `YYYY-MM-DD`:
```
Posted: 2026-08-19
```

**Fallback if a job doesn't appear in search-results:** try a couple of
different keyword variants (job ID is most reliable; a distinctive phrase from
the title is a second option) before concluding it's been fully de-indexed and
falling back to `Posted: Not specified`.

---

### Known-bad: the detail-page JSON-LD `datePosted` (do NOT use this field)

The job's own detail page (`careers.honda.com/us/en/job/<id>/<slug>`) also
carries a separate schema.org `JobPosting` JSON-LD block with its own
`datePosted` field — this is a **different, unrelated field** from the
search-page `postedDate` above, and it is confirmed unusable. Do not extract
or offer it under any circumstances, caveat included.

Confirmed across four checks (2026-08-29): jobs 11824 and 12292 (both
pre-existing, non-new listings) returned `datePosted` equal to the *current
check date*; a later re-check of job 11824 (by then closed, no live content on
the page) and a check of job 11221 (also closed) both returned `datePosted:
2026-08-30` — *tomorrow* relative to the actual check date, and identical
across two different, unrelated jobs. A closed listing cannot have a real
future posting date, and two different jobs cannot share one. This field is
not tracking any real job lifecycle — it just stamps something close to "now"
(probably server-local time in a different zone, explaining the one-day drift)
on every fetch, shared across all jobs that day, regardless of the job's actual
age or status.

If you land on this field while investigating a Phenom-backed site, skip it
entirely and use the search-results technique above instead.

---

## Astemo careers CMS (careers.astemo.com — recognizable by `<script id="js-job-posting"
## type="application/ld+json">`; may be shared by other career sites on the same CMS vendor)

**Technique:** Re-fetch the job URL with `mcp__ScraplingServer__get` using
`extraction_type: "html"` and `main_content_only: false` (the JSON-LD block lives
outside the main-content region). Unlike the Phenom entry above, the `<script>` tag
here carries an `id="js-job-posting"` attribute before `type=`, so a regex anchored
to `<script type="application/ld+json">` with nothing in between will miss it —
match on `type="application/ld+json"` anywhere in the tag instead. It contains a
schema.org `JobPosting` object with `datePosted` (ISO date, e.g. `"2026-05-29"`),
plus `title`, `hiringOrganization`, `jobLocation`, `employmentType`.

```bash
python3 -c "
import json, re, sys
html = json.load(open(sys.argv[1]))['content'][0]
m = re.search(r'<script[^>]*type=\"application/ld\+json\"[^>]*>(.*?)</script>', html, re.DOTALL)
print(json.loads(m.group(1)).get('datePosted', 'NOT_FOUND'))
" <path-to-tool-result-file>
```

**Caveat:** Verified against Astemo job J0050763 (scraped 2026-08-29): `datePosted`
came back as `2026-05-29` — roughly 3 months in the past, not the current date.
Unlike the Phenom/Honda case, this is evidence *against* a per-crawl regeneration
pattern (a freshness-reset field would show today's date).

**Re-verified same day (second fetch, 2026-08-29):** re-ran the technique
independently against the same job. `datePosted` came back byte-for-byte identical
(`2026-05-29`) on the second, unrelated fetch. A freshness-reset field would have
advanced or stayed pinned to "now" on the later fetch — it did neither. Confidence
upgraded from "provisionally reliable" to reliable; no longer needs re-verification
before use.

**How to report it:** Report as a plain confirmed date, no caveat suffix needed
unless a future check contradicts the pattern above:
```
Posted: 2026-05-29
```

---

## Clinch ATS platform (careers.withwaymo.com, and likely other `*.clinchtalent.com`-backed
## career sites — recognizable by `files.clinchtalent.com` asset URLs, and by an AWS WAF
## JS bot-challenge page (`*.token.awswaf.com/.../challenge.js`) blocking plain HTTP fetches)

**Technique:** `mcp__ScraplingServer__get` (plain HTTP, no JS execution) does not work
at all on this platform — it returns the raw AWS WAF challenge page, not the job page,
regardless of `extraction_type`. This is also why Attempt 1 of the normal fetch chain
fails on these URLs (empty/202 response) and Attempt 2 (`fetch`, which runs a real
headless browser and can pass the JS challenge) is required just to get the visible
job text. For the posted date specifically, re-run `mcp__ScraplingServer__fetch` (not
`get`) with `extraction_type: "html"`, `main_content_only: false`, and `wait: 2000`.
Search the returned HTML for a `<script type="application/ld+json">` block and parse
it as JSON — same schema.org `JobPosting` shape as the Phenom entry above, with
`datePosted` (ISO datetime, e.g. `"2026-05-05T16:00:54Z"`) and also a `validThrough`
field useful as a secondary sanity check (posted-to-expiry gap should be a normal
listing lifecycle, not e.g. negative or multi-year).

```bash
python3 -c "
import json, re, sys
html = json.load(open(sys.argv[1]))['content'][0]
m = re.search(r'<script[^>]*type=\"application/ld\+json\"[^>]*>(.*?)</script>', html, re.DOTALL)
print(json.loads(m.group(1)).get('datePosted', 'NOT_FOUND'))
" <path-to-tool-result-file>
```

**Caveat:** Verified against Waymo job 4805 / e0c6a49d85e932fa00ef19a36e07b8d1
(scraped 2026-08-29): `datePosted` came back as `2026-05-05T16:00:54Z` — roughly
3.5 months in the past — and `validThrough` was `2026-11-26T16:44:29Z`, a normal
~6-month posting lifecycle. Neither looks like a per-crawl freshness reset (unlike
the Phenom/Honda case).

**Re-verified same day (second fetch, 2026-08-29):** re-ran the technique
independently against the same job (first retry attempt actually returned a
truncated `<head>`-only page with no JSON-LD at all — a transient rendering
timeout, not a real signal; a longer `wait` fixed it). On the successful second
fetch, both `datePosted` (`2026-05-05T16:00:54Z`) and `validThrough`
(`2026-11-26T16:44:29Z`) came back byte-for-byte identical, down to the second.
Confidence upgraded from "provisionally reliable" to reliable; no longer needs
re-verification before use. Note for future scrapes: if a fetch on this platform
comes back suspiciously small or missing the `<body>` entirely, retry with a
longer `wait` before concluding the JSON-LD is absent.

**How to report it:** Report as a plain confirmed date (truncate the ISO datetime
to just the date portion to match this skill's `YYYY-MM-DD` convention), no caveat
suffix needed unless a future check contradicts the pattern above:
```
Posted: 2026-05-05
```

---

## Liferay DDM portal — Honda Research Institute USA (usa.honda-ri.com — recognizable by
## `/o/liferay-hri-theme/` asset paths and a `com_liferay_dynamic_data_mapping_form_web_portlet`
## instance on the job page; may generalize to other Liferay-DDM-backed career pages)

**Technique:** No JSON-LD block exists on this platform — do not bother searching
for `application/ld+json`. Instead, re-fetch the job URL with
`mcp__ScraplingServer__get` using `extraction_type: "html"` and
`main_content_only: false`, then search the raw HTML for a `JobOfferData` JS object
literal (inline in a `<script>` tag powering the application form). It has the shape:
```js
var JobOfferData = {
  id: "P25F15",
  name: "Flight Test Team Lead",
  publicationDate: "Jun 24, 2026 6:42:50 AM"
};
```
`publicationDate` is a human-readable datetime string (`"Mon D, YYYY H:MM:SS AM/PM"`),
not ISO — parse/reformat to this skill's `YYYY-MM-DD` convention before writing it.

```bash
python3 -c "
import json, re, sys
html = json.load(open(sys.argv[1]))['content'][0]
m = re.search(r'publicationDate:\s*\"([^\"]+)\"', html)
print(m.group(1) if m else 'NOT_FOUND')
" <path-to-tool-result-file>
```

**Caveat:** Verified against Honda RI USA job P25F15 (scraped 2026-08-29):
`publicationDate` came back as `Jun 24, 2026 6:42:50 AM` — about 2 months in the
past, not the current date. Stronger confidence than the JSON-LD cases above: this
field isn't SEO/Google-Jobs metadata at all — the same page uses it verbatim to
populate the "Published in" line of the applicant's confirmation email, so it reads
as the site's own authoritative record of the listing's publish date rather than a
freshness signal.

**Re-verified same day (second fetch, 2026-08-29):** re-ran the technique
independently against the same job. `publicationDate` came back byte-for-byte
identical (`Jun 24, 2026 6:42:50 AM`), matching down to the second. Confidence
upgraded from "one job checked" to reliable; no longer needs re-verification
before use.

**How to report it:** Report as a plain confirmed date, reformatted to
`YYYY-MM-DD`:
```
Posted: 2026-06-24
```

---

## Google Careers (google.com/about/careers, careers.google.com — confirmed NO
## working technique after five independent methods tried)

**Technique:** None found. This is a documented negative result, not a gap to
re-investigate on the next scrape — do not spend a fetch attempt checking again
unless Google visibly changes the page structure. Five independent methods were
tried against job 89596976735101638 (Research Scientist, Robotics, DeepMind,
scraped 2026-08-29), all dead ends:

1. **Visible rendered content** (normal Step 2 fetch chain) — no Posted/date field
   anywhere in the markdown output.
2. **Full raw HTML, JSON-LD search** — `mcp__ScraplingServer__get` with
   `extraction_type: "html"`, `main_content_only: false` (full ~1.1MB page). No
   `<script type="application/ld+json">` block anywhere on the page.
3. **Full raw HTML, broader data-blob search** — searched for Google's
   `AF_initDataCallback` JSON payload pattern (used elsewhere on Google properties
   to hydrate SSR'd apps with structured data) and for generic date patterns (ISO
   dates, month names, "N days ago", a "Posted" label) anywhere in the job-detail
   render region. The job content turns out to be server-rendered directly into
   DOM text nodes, not delivered as a separate structured data blob — nothing
   found.
4. **HTTP response headers** — `curl -I <job-url>`. No `Last-Modified` header;
   response is explicitly `Cache-Control: no-cache, no-store, max-age=0,
   must-revalidate`, i.e. dynamically regenerated on every request with no
   caching metadata to exploit.
5. **Wayback Machine** — `http://archive.org/wayback/available?url=<job-url>`
   returned `archived_snapshots: {}` — no snapshot exists for this exact job URL
   (the CDX API for a fuller history hit a 429 rate limit on retry, but the
   primary lookup was conclusive on its own).
6. **Live network traffic capture** — navigated with Playwright MCP and pulled
   `mcp__playwright__browser_network_requests` (non-static) for the full page
   load. Only analytics/telemetry beacons fire (Google Analytics, Google Tag
   Manager, an internal `browserinfo` logging call) — no XHR/fetch call ever
   requests a separate JSON payload with job metadata, confirming there's no
   hidden second data source client-side either.

**Caveat:** Google's careers site appears not to expose a posted date to the
client at all for individual job pages, through any channel checked — this isn't
a "hidden but present" case like the other entries in this file, it looks like a
genuine absence. A logged-in/internal API might carry it, but that's out of scope
for this skill.

**How to report it:** `Posted: Not specified` — no caveat suffix needed, this is a
confirmed absence rather than an unreliable value.

---

## Ashby job boards (jobs.ashbyhq.com — recognizable by the `jobs.ashbyhq.com/<org>/<job-id>`
## URL pattern; job id is a UUID)

**Technique:** The rendered page (both the plain `get` and JS-rendered `fetch`
attempts) never shows a posted date anywhere in visible content. Ashby exposes
a public, unauthenticated job-board API instead — no scraping or JS rendering
needed, so this is cheaper than the normal fetch chain once you know the org
slug (it's the first path segment after `jobs.ashbyhq.com/`):
```
https://api.ashbyhq.com/posting-api/job-board/<org-slug>?includeCompensation=true
```
This returns a JSON object with a `jobs[]` array covering every open listing
for that org. Find the entry whose `id` matches the UUID from the job URL, and
read its `publishedAt` field (ISO datetime, e.g.
`"2026-09-01T16:48:47.506+00:00"`) — truncate to `YYYY-MM-DD`. The same
response also carries the full `descriptionHtml`/`descriptionPlain`, `title`,
`department`, `location`, and `compensation` block, so it can serve as a
faster alternative to the page-scrape entirely if ScraplingServer is
unavailable — this was in fact how it got verified: ScraplingServer's MCP
connection dropped mid-scrape and a plain `curl` to this endpoint substituted
successfully.

```bash
curl -s "https://api.ashbyhq.com/posting-api/job-board/<org-slug>?includeCompensation=true" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for j in data.get('jobs', []):
    if j.get('id') == '<job-uuid-from-url>':
        print(j['publishedAt'])
        break
else:
    print('NOT_FOUND')
"
```

**Caveat:** Verified against OpenAI job 393b88d7-1fbc-466a-9108-a7c1bafeb8d8
(Systems Test Engineer, End-to-End Validation, scraped 2026-09-08):
`publishedAt` came back as `2026-09-01T16:48:47.506+00:00` — about a week in
the past, not the current date, and not a per-crawl freshness reset. Single
data point so far — no second fetch or second job cross-checked yet.

**How to report it:** Report as a plain confirmed date, truncated to
`YYYY-MM-DD`, no caveat suffix needed unless a future check contradicts the
pattern above:
```
Posted: 2026-09-01
```

**Fallback if the job doesn't appear in the `jobs[]` array:** the listing may
have been unpublished/closed and dropped from the public board API — fall
back to the normal rendered-content check and, failing that, `Posted: Not
specified`.

---

## (Add new entries below as new platforms are encountered)

Template for a new entry:
```
## <Platform name> (recognizable by: <distinguishing URL/asset pattern>)

**Technique:** <exact steps/tool calls>

**Caveat:** <how reliable this is, verified against which job(s)/date>

**How to report it:** <exact label format for the JD file, if any caveat applies>
```
