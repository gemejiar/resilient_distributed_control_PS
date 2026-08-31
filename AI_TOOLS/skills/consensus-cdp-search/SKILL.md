---
name: consensus-cdp-search
description: Use this skill when the user wants to search papers or download PDFs from consensus.app using the exact workflow that worked in this workspace: debug Chrome or Edge on port 9222, logged-in Consensus session, CDP control from PowerShell, explicit click on the blue search button, result capture, and download logging. Trigger on: Consensus, consensus.app, blue arrow search button, search papers in Consensus, logged-in browser search, CDP browser automation, download PDF from Consensus, or when browser automation must reuse the authenticated local session instead of Playwright.
---

# Consensus CDP Search

Use this skill for `consensus.app` work that must actually run in the local authenticated browser session.

This skill exists because the stable path in this workspace was **not** Playwright. The reliable path was:

1. Start Chrome or Edge with remote debugging on `http://127.0.0.1:9222`
2. Reuse the local browser profile under `.browser_automation/chrome-profile`
3. Make sure the user is logged into `Consensus`
4. Control the page through CDP from PowerShell
5. Put the query into `textarea[name="newMessage"]`
6. Click the blue submit button `button[data-testid="search-button"]`
7. Capture the result thread and visible paper cards
8. Attempt `PDF` or `Full text` download and log success or failure

Do **not** default to Playwright here unless the environment was repaired and verified in the current session.

## When To Use

Use this skill when the user wants any of the following:

- run literature searches on `https://consensus.app/`
- reuse a logged-in browser session
- click the blue search button on the right of the query box
- collect result cards, titles, DOIs, venues, years, or Q1 hints from Consensus
- open `PDF` or `Full text` links from Consensus results
- maintain a ledger of what downloaded and what failed

Do not use this skill for generic OpenAlex or Crossref API search unless the user explicitly moved away from `Consensus`.

## Preconditions

Before searching:

1. Use the existing browser automation root in this repo:
   - `.browser_automation/start_debug_chrome.ps1`
   - `.browser_automation/consensus_cdp_search.ps1`
   - `.browser_automation/consensus_cdp_capture_url.ps1`
2. Assume the browser must be launched with remote debugging on port `9222`.
3. Assume the user may need to log in manually once per browser profile.
4. Assume `Consensus` search is more reliable when the actual blue submit button is clicked than when synthetic deep links or `Quick` routes are forced.
5. Assume shell downloads may fail inside the sandbox. If that happens, retry with escalation or use a browser-session-based path.

## Known Good Local Entry Points

### Start the debug browser

Use:

```powershell
powershell -ExecutionPolicy Bypass -File .browser_automation\start_debug_chrome.ps1
```

What this does:

- finds Chrome or Edge in default Windows paths
- launches it with `--remote-debugging-port=9222`
- uses `.browser_automation\chrome-profile` as the persistent profile

### Verify the CDP endpoint

Minimal check:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:9222/json/version
```

If this fails, do not continue with `Consensus` automation yet.

## Exact Working Search Workflow (Validated in Session 1-GA.1)

### The Proven 3-Step Method

**Context:** User conducts manual search in Consensus browser, then automation extracts and processes papers.

### Step 1. Capture the search results page using CDP

Once the user has manually run a search in Consensus (e.g., query R1 in the browser), capture the results page with:

```powershell
& powershell -NoProfile -ExecutionPolicy Bypass -File ".browser_automation/consensus_cdp_capture_url.ps1" `
    -Url "https://consensus.app/search/inverter-dominated-power-systems-control/ja4a9lAeRrS08p1iFEJHbw/" `
    -OutFile "Paper_refs/2026Q2_DDC/raw/results_page.json" `
    -WaitSeconds 12
```

**Output:** JSON file with `anchors_top` array containing all visible paper URLs.

**Key:** The `-WaitSeconds` parameter gives the page time to fully load all papers in the thread. 12 seconds is safe for most queries.

### Step 2. Extract unique paper URLs from results JSON

Parse the captured results JSON and filter anchors where `href` contains `/papers/`:

```powershell
$json = Get-Content "results_page.json" -Raw | ConvertFrom-Json
$paperUrls = @($json.anchors_top) |
    Where-Object { $_.href -match '/papers/' } |
    Select-Object -ExpandProperty href -Unique |
    Select-Object -First 20
```

**Expected outcome:** 15–20 unique paper URLs per query.

### Step 3. Capture each individual paper page and extract metadata

For each paper URL, capture its detail page:

```powershell
& powershell -NoProfile -ExecutionPolicy Bypass -File ".browser_automation/consensus_cdp_capture_url.ps1" `
    -Url $paperUrl `
    -OutFile "paper_${rank}.json" `
    -WaitSeconds 8
```

**From the captured JSON, extract:**
- `title` (remove " - Consensus" suffix)
- `year` via regex `Published\s+(\d{4})` in `text_excerpt`
- `doi` from anchor with `href` matching `^https://doi\.org/`
- `venue` (first non-empty line after "Published YYYY" that is not a label)
- `q1_flag` by checking if text contains lines `^Q1$`, `^Q2$`, etc.
- `pdf_link_url` from anchor where `text` is "PDF" or "Full text"

**Validation rule:** All metadata must be extracted from the JSON; **never** guess or synthesize.

### Step 4. Download PDF if available, validate by header

If `pdf_link_url` is present and non-empty:

```powershell
$curlOut = & curl.exe --silent --show-error -L --max-time 40 --output $pdfPath $pdfUrl 2>&1
```

**Then validate:**
```powershell
$bytes = [System.IO.File]::ReadAllBytes($pdfPath)
$head = [System.Text.Encoding]::ASCII.GetString($bytes[0..4])
if ($head -eq "%PDF-") { $status = "downloaded" }
else { $status = "invalid_non_pdf"; Remove-Item $pdfPath }
```

### Step 5. Log results to CSVs

**`reviews_consensus_hits_1GA1.csv`** — one row per paper:
- `query_id`, `query_text`, `title`, `doi`, `year`, `venue`, `q1_flag`, `pdf_affordance`, `keep_decision`, etc.

**`reviews_pdf_attempts_1GA1.csv`** — one row per PDF attempt:
- `query_id`, `title`, `pdf_link_url`, `attempt_status` (downloaded|invalid_non_pdf|network_failed|no_pdf_button), `downloaded_file`, `attempt_date`, `notes`

### Lessons Learned (1-GA.1)

1. **User manual search + automation extraction is faster and more reliable** than forcing query submission via CDP.
   - The user navigates Consensus in the browser UI naturally.
   - Automation captures the results page as it appears (with all interactive elements loaded).
   - No retry loops needed for button clicks or form submission.

2. **JSON capture with `consensus_cdp_capture_url.ps1` is robust:**
   - Handles dynamic content loading.
   - Provides `anchors_top` array with all links (papers, DOI, PDF, related work, etc.).
   - No Playwright/Selenium fragility.

3. **Metadata extraction from `text_excerpt` is reliable:**
   - Published year regex works consistently.
   - Q1/Q2/Q3/Q4 appear as standalone lines in the extracted text.
   - Venue is the first non-label line after "Published YYYY".

4. **PDF downloads must validate by header:**
   - Some URLs return HTML or error pages with `.pdf` extension.
   - Only `%PDF-` header confirms a valid PDF.

5. **Curl is reliable for downloads:**
   - `--max-time 40` prevents hangs on paywalled or slow URLs.
   - `-L` follows redirects (critical for DOI links).
   - Exit code 0 + file exists does not guarantee valid PDF; always check header.

## Existing Scripts To Reuse

### `.browser_automation/consensus_cdp_search.ps1`

Use this when you want to:

- open a new tab to `Consensus`
- submit a query
- capture the resulting page text, URL, and top anchors

Important note:

- the current script uses `Enter` dispatch after `Input.insertText`
- in this workspace, the most reliable live flow was the explicit blue-button click after login

Therefore:

- reuse the script if it still works in the current session
- if not, patch it to click `button[data-testid="search-button"]` instead of relying only on `Enter`
- do not create a second independent automation path unless necessary

### `.browser_automation/consensus_cdp_capture_url.ps1`

Use this when you already have a result URL or a paper page URL and want to capture:

- title
- final URL
- page text excerpt
- top anchors
- top buttons

This is useful for paper-detail pages and for extracting visible `PDF` or `Full text` links.

## Search Strategy Inside Consensus

Use the query plan already defined by the project when available.

For this workspace, the operational rule was:

- about `70%` of the first-pass hits should come from `2023-2026`
- the remaining `30%` can backfill `2018-2022` or older seminal baselines

Filter priorities:

1. retain `Q1` journals for the main corpus whenever possible
2. keep strong non-Q1 or unknown items only when they are clearly seminal, review-like, bridge papers, or necessary support evidence
3. do not keep papers only because they appear in Consensus

After each search result page:

1. capture candidate titles
2. capture DOI if visible
3. capture venue and year
4. flag whether the page shows `Q1`, `UNKNOWN`, `PDF`, or `Full text`
5. record the item into a hits ledger

## Recommended Logging Artifacts

If the project already has specific CSVs, use those. In this workspace, the useful examples were:

- `Paper_refs/2026Q2_DDC/consensus_screening_log.csv`
- `Paper_refs/2026Q2_DDC/reviews_consensus_hits_1GA1.csv`
- `Paper_refs/2026Q2_DDC/reviews_pdf_attempts_1GA1.csv`

If the target project does not already define a ledger, create two CSVs:

### `consensus_hits.csv`

Recommended columns:

- `query_id`
- `query_text`
- `captured_at`
- `consensus_thread_url`
- `paper_title`
- `doi`
- `venue`
- `year`
- `q1_hint`
- `pdf_affordance`
- `full_text_affordance`
- `decision`
- `decision_note`

### `consensus_pdf_attempts.csv`

Recommended columns:

- `paper_title`
- `doi`
- `consensus_paper_url`
- `download_source`
- `attempted_at`
- `status`
- `saved_path`
- `content_type`
- `validation`
- `failure_reason`

Use explicit `status` values such as:

- `downloaded`
- `opened_only`
- `blocked`
- `network_failed`
- `paywalled`
- `no_pdf_button`

## Download Workflow

### Goal

The goal is not only to find papers. The goal is to leave a traceable record of:

- what was visible in Consensus
- what could be opened
- what could be downloaded
- what failed and why

### Preferred order

1. Open the paper card or paper-detail page in Consensus
2. Check if a visible `PDF` or `Full text` affordance exists
3. Capture the paper page before downloading
4. Attempt the download
5. Validate the saved file
6. Update the ledger

### Validation rule for saved PDFs

Do not trust the `.pdf` extension alone.

Check at least one of:

- response `Content-Type` is `application/pdf`
- file header starts with `%PDF-`

If neither is true, log the attempt as failed or invalid.

## Failure Modes And Fixes

### Failure 1. Query text appears, button enables, but the page stays on home

Interpretation:

- the search submission did not complete successfully
- session state may be stale
- the browser may not actually be on the logged-in profile

Fix:

1. verify login in the debug browser window
2. verify port `9222` is still alive
3. prefer explicit click on the submit button
4. retry once before changing the query

### Failure 2. Search thread opens, but a deeper route lands on sign-up

Interpretation:

- the thread page exists, but a secondary route is gated or unstable

Fix:

1. stay on the first successful thread page
2. extract visible results from there
3. avoid forcing `Quick` or other deeper routes unless necessary

### Failure 3. Some queries bounce to home, others work

Interpretation:

- not every query string is equally stable in the UI

Fix:

1. shorten the query
2. split long Boolean-like phrasing into smaller semantic chunks
3. keep the main nouns and the method phrase
4. rerun through the same button-click path

### Failure 4. Playwright is installed but broken

Interpretation:

- the local venv or native wheel stack is inconsistent

Fix:

1. do not spend time repairing Playwright unless the user asked for that
2. continue with PowerShell + raw CDP

### Failure 5. The download link exists, but shell download fails

Interpretation:

- sandbox or network restrictions blocked the transfer

Fix:

1. log the failed attempt first
2. retry with escalation if allowed
3. if the source depends on browser session state, use the authenticated browser path instead of a cold shell request

## Practical Success Criteria (Validated Session 1-GA.1)

Treat the run as successful only if all of the following are true:

1. the query produced a result thread or result page
2. at least one paper card was captured with title plus some metadata
3. the hit was written to a ledger
4. every PDF attempt was logged as success or failure
5. every downloaded file was validated as a real PDF

## Critical Lessons from Session 1-GA.1

### What Worked

1. **Quick Search URL approach:** `https://consensus.app/quick?q=QUERY` reliably returns papers in `/papers/` anchors
2. **CDP capture via `consensus_cdp_capture_url.ps1`:** Fast (8-15 sec), captures full page with anchors, no Playwright needed
3. **Metadata extraction from text_excerpt:** Year regex, Q1 detection, venue parsing all work reliably
4. **PDF header validation:** `%PDF-` check catches invalid downloads
5. **Manual filter application in UI + programmatic capture:** User applies Filter (Year, Q1) manually, script captures filtered page
6. **Deduplication by URL:** Group anchors by href, select unique → no duplicates in processing

### What Failed / Don't Do

1. ~~**Automate Filter panel via CDP:** Requires exact selectors; attempted JavaScript async/await parsing failed in PowerShell~~
   - **Workaround:** User applies Filter in UI (30 sec), script captures and processes (reliable)
2. ~~**Parallel CSV writes:** Multiple scripts writing to same CSV simultaneously caused data loss~~
   - **Fix:** Use separate CSV files per query, then merge; OR process queries sequentially
3. ~~**Query parameters for filters:** `?year_from=2023&year_to=2026&q1=true` not recognized by Consensus~~
   - **Reality:** Filters only work in UI; capture output, not input

### Recommended Workflow (Proven in 1-GA.1)

For queries R1-R8 (Consensus search reviews):

```
For each query:
  1. User: open Consensus, paste query, click search
  2. User: open Filter, set Year 2023-2026 + Q1, click Apply (30 sec)
  3. Claude: capture filtered page via CDP (15 sec)
  4. Claude: extract papers from /papers/ anchors (2 sec)
  5. Claude: process each paper (capture metadata, attempt PDF) (10 sec/paper)
  6. Claude: append to CSV (or use per-query CSV to avoid conflicts)
  
Total per query: ~3-5 minutes (user 30s + Claude 2-5m)
```

## Minimal Operator Notes

- Search without traceability is not enough.
- Download without validation is not enough.
- A bounced query is still useful evidence if the failure reason is logged.
- Reuse the same debug profile across the whole session; do not rotate profiles mid-run.
- **In this workspace, the biggest difference between failure and success is:**
  - Manual UI filtering (User responsible; CDP automation too fragile)
  - Fast CDP capture of results (no Playwright overhead)
  - Per-query or sequential CSV writes (avoid parallel write conflicts)
  - Proper PDF header validation (`%PDF-` check mandatory)

## Output Expectations

At the end of a run, report:

1. which query set was executed (R1-R4, R5-R8, Q1-Q4, etc.)
2. which browser profile or session was used (e.g., `.browser_automation/chrome-profile`)
3. which pages produced real Consensus threads (paper URLs captured)
4. how many hits were retained per query
5. how many PDF attempts succeeded (usually 0 due to network/paywall)
6. how many failed, and the top failure reasons (usually curl exit 23 = timeout, 60 = auth)

## Session 1-GA.1 Results

- **R1:** 19 papers captured (Koopman, system ID, PINN, DeePC scope)
- **R2:** 20 papers captured (DeePC + Koopman specific)
- **R3:** 0 papers (query too restrictive; backfill with manual search)
- **R4:** 20 papers captured (PINN grey-box focus)
- **Total candidate papers:** ~59 from R1-R4
- **Keep (Q1 + 2023-2026):** ~5-8 high-relevance papers
- **Support (backfill):** ~50+ secondary evidence papers
- **PDF downloads:** Mostly blocked (paywall/network); rely on DOI links for access

