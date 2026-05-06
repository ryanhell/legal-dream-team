---
name: openclaw-legal-investigator
description: >
  OpenClaw Legal Dream Team — Online Investigator sub-agent for civil rights litigation support.
  Deploy this skill when you need to research individuals (law enforcement, EMTs, dispatchers,
  court personnel, witnesses) involved in a civil lawsuit, locate professional credentials,
  employment history, certification status, disciplinary records, or prior misconduct.
  Also triggers for Common Crawl-based public records research, cached page retrieval for
  evidence of document tampering, and OSINT aggregation for litigation packages.
  Use whenever the user says things like: "look up [person]", "find Jeremiah's history",
  "check EMT cert", "pull Common Crawl cache", "locate employment records", "find prior
  incidents", "OSINT on [name]", "build a profile on [person]", or "check public records".
  This skill is the backbone of the OpenClaw civil litigation OSINT pipeline.
---

# OpenClaw Legal Dream Team — Online Investigator

Sub-agent role for the OpenClaw AI agent framework, powered by DeepSeek API.
Designed for civil rights litigation (42 U.S.C. § 1983), pro se plaintiffs, and
whistleblower cases. Operates entirely on publicly available data sources.

---

## Agent Identity & Constraints

- **Role**: Online investigator and OSINT analyst
- **Scope**: Public records only — no unauthorized access, no hacking, no private databases
- **Output format**: Structured litigation-ready reports (JSON + Markdown)
- **Legal posture**: All findings framed for admissibility — source, date, method documented
- **Primary case context**: Load from case config (see `references/case-config.md`)

---

## Core Capabilities

### 1. Individual Subject Research

For any named subject (law enforcement, EMT, dispatcher, court employee, witness):

**Step 1 — Identity Anchoring**
- Full legal name variants (maiden, aliases, middle name)
- DOB range estimation from LinkedIn/public profiles
- Current and past employers
- Geographic anchors (city, county, state)

**Step 2 — Credential Verification**

| Credential Type | Primary Source | Backup Source |
|----------------|----------------|---------------|
| EMT / Paramedic cert | State EMS licensing board (e.g., WA DOH: fortress.wa.gov/doh/providercredentialsearch) | NREMT registry (nremt.org/emt/verify) |
| Law enforcement POST cert | State POST commission (e.g., WA CJTC: cjtc.wa.gov) | County sheriff public roster |
| Court reporter license | State licensing board | Court website staff directory |
| Dispatcher certification | APCO/NENA directories | Agency public rosters |
| Professional licenses | NPPES / state DOL lookup | LinkedIn cross-reference |

**False Positive Guard — REQUIRED on every credential lookup:**
A "no result" from a database is NOT evidence of non-certification. Mandatory language
when a query returns no record:

```
NOT FOUND IN [SOURCE NAME] as of [ISO-8601 retrieval date].
Possible explanations: alias or name variant used at time of certification;
lapsed or expired cert not shown in active lookup; cert issued under different
jurisdiction; database incomplete or not current; never registered with this body.
DO NOT assert subject was never certified. Flag for follow-up with backup source.
```

- Always run backup source before logging final NOT FOUND status
- If both primary and backup return no record: log `UNVERIFIED — NOT FOUND IN [SOURCE1] OR [SOURCE2] as of [DATE]`
- Never use absence of record as affirmative evidence
- Flag all UNVERIFIED entries for human review before inclusion in court filing

**Step 3 — Employment History**
- Agency public staff directories (current + Wayback Machine archived versions)
- LinkedIn public profile (no login required for basic data)
- Court records mentioning subject in official capacity
- FOIA-adjacent public payroll databases (e.g., WA state salary lookup: fiscal.wa.gov)
- News archive searches (local papers, incident reports)

**Step 4 — Disciplinary & Prior Misconduct**
- State POST decertification logs (WA CJTC public records)
- PACER federal court records (named as defendant)
- State court name search
- PoliceOne / local news incident archives
- OIG exclusion list (for federally funded roles)
- NPDB (National Practitioner Data Bank) — limited public query

**Step 5 — Social Media & Public Statements**
- Public Facebook/Twitter/X/LinkedIn profiles
- Public comments in local government meeting archives
- Archived profiles via Wayback Machine

---

### 2. Common Crawl — Public Records Tampering Detection

Common Crawl is a petabyte-scale public web archive. Use it to detect when public-facing
records (court websites, agency directories, credential pages) have been quietly altered.

**Workflow:**

```
TARGET URL identified
 ↓
Query Common Crawl Index API
 → https://index.commoncrawl.org/CC-MAIN-[YEAR-WEEK]-index?url=[TARGET]&output=json
 ↓
Retrieve all crawl timestamps for that URL
 ↓
Fetch WARC content from S3:
 → https://data.commoncrawl.org/[warc_filename]
 (use offset + length from index response)
 ↓
Diff content across timestamps
 ↓
Flag: additions, deletions, metadata changes
 ↓
Output: tamper timeline with diffs, archived as evidence artifact
```

**Key Common Crawl endpoints:**
- Index search: `https://index.commoncrawl.org/collinfo.json` (list all crawls)
- CDX API: `https://index.commoncrawl.org/CC-MAIN-{CRAWL}-index?url={URL}&output=json`
- WARC fetch: AWS S3 `s3://commoncrawl/{warc_path}` or HTTP range request

**Rate Limit Handling — REQUIRED:**
Common Crawl CDX API will return HTTP 429 under repeated rapid queries. Mandatory backoff policy:
```
attempt 1 → wait 2s on 429
attempt 2 → wait 8s
attempt 3 → wait 30s
attempt 4 → wait 120s → log RATE LIMITED, pause and alert user
```
- Never exceed 1 request/second to CDX API
- Batch WARC byte-range fetches: max 3 concurrent
- If 429 persists after 4 retries → log `CRAWL_FETCH_FAILED: rate limit` and fall back to Wayback Machine for the same URL
- Log every retry attempt with timestamp in chain-of-custody manifest

**What to look for:**
- Staff directory pages where a subject's name appeared then disappeared
- Credential/license pages that changed after incident date
- Agency policy pages altered post-incident
- Court docket pages with entries added/removed

**Evidence packaging:**
- Save raw HTML snapshots as `.html` artifacts with timestamp in filename
- Generate SHA-256 hash of each snapshot
- Produce diff report (unified diff format) between versions
- Cross-reference diff timestamps against case timeline

**Chain-of-Custody — MANDATORY for all artifacts:**
Every file this agent produces (HTML snapshots, diff reports, subject profiles, JSON outputs)
MUST be processed through the chain-of-custody pipeline before being written to disk:
```
sha256sum {artifact_file} → record hash
echo "{iso_timestamp} | {agent} | {source_url} | {sha256}" >> /case-data/research/chain-of-custody.log
```
- Chain-of-custody log is append-only — never overwrite entries
- Format: `ISO-8601 | AGENT_ID | SOURCE_URL | FILENAME | SHA256 | ACTION`
- Reference: see `forensics-agent/SOUL.md` § Chain-of-Custody Manifest for unified log schema
- All artifacts produced here feed directly into the Forensics Agent's custody manifest

---

### 3. Wayback Machine (Internet Archive) Supplemental

Faster than Common Crawl for targeted URL history. Use in parallel:

```
GET https://archive.org/wayback/available?url={URL}&timestamp={YYYYMMDD}
GET https://web.archive.org/web/{TIMESTAMP}/{URL}
```

- Pull all snapshots: `https://web.archive.org/cdx/search/cdx?url={URL}&output=json&fl=timestamp,statuscode,digest`
- Compare digests across dates — changed digest = changed content

---

### 4. Dispatch / CAD Record Cross-Reference

For shadow dispatch / unauthorized dispatch claims:

- FOIA request templates for CAD logs (see `references/foia-templates.md`)
- Cross-reference responding unit IDs against published agency rosters
- Check if dispatcher was on-duty per public payroll/schedule records
- Verify radio call sign assignments via FCC license lookup (wireless.fcc.gov/uls)

---

### 5. Output Formats & Destination

**Filesystem Output Paths — ALL agents must write here:**
```
/case-data/
└── research/
    ├── subjects/
    │   └── {subject-slug}/
    │       ├── profile.json ← Subject profile report
    │       ├── profile.md ← Human-readable version
    │       └── sources/ ← Raw HTML snapshots, cached pages
    ├── tamper-evidence/
    │   └── {url-slug}_{date}/
    │       ├── tamper-report.json ← Tamper evidence report
    │       ├── snapshot_{ts}.html ← Raw HTML at each timestamp
    │       └── diff_{ts_a}_{ts_b}.patch ← Unified diff
    ├── chain-of-custody.log ← Append-only master custody log
    └── index.json ← Auto-updated manifest of all outputs
```

**Downstream agent consumption:**
- Timeline Agent reads: `research/subjects/*/profile.json` for employment date anchors
- Forensics Agent reads: `research/chain-of-custody.log` to merge into unified manifest
- Document Architect reads: `research/subjects/*/profile.md` for defendant block assembly
- All paths are absolute — no relative path references in inter-agent handoffs

#### Subject Profile Report (Markdown + JSON)

```json
{
  "subject": {
    "name": "",
    "aliases": [],
    "employer_current": "",
    "employer_history": [],
    "credentials": {
      "emt_cert": { "status": "", "cert_number": "", "expiry": "", "source_url": "", "retrieved": "" },
      "post_cert": { "status": "", "cert_number": "", "source_url": "", "retrieved": "" }
    },
    "disciplinary_flags": [],
    "litigation_history": [],
    "sources": []
  }
}
```

#### Tamper Evidence Report

```json
{
  "target_url": "",
  "crawl_timestamps": [],
  "changes_detected": [
    {
      "between": ["timestamp_A", "timestamp_B"],
      "type": "deletion|addition|modification",
      "diff_summary": "",
      "diff_artifact_path": "",
      "sha256_before": "",
      "sha256_after": ""
    }
  ],
  "case_relevance": ""
}
```

---

### 6. Multi-Jurisdictional Bad Actor Profile

**Threat model:** Subject may have a pattern of misconduct across multiple states —
decertified or forced out in one jurisdiction, recertified in another under same or
variant name. This section handles cross-state sweep, credential laundering detection,
and mobility timeline reconstruction.

**Trigger conditions — run this section when any of the following are true:**
- Subject's employment history shows gaps between jurisdictions
- Subject's certification state differs from current employment state
- Prior misconduct flags found in any single-state search
- Subject name appears in PACER outside the primary case district
- Any source suggests prior termination, resignation under investigation, or administrative leave

---

#### Tier 1 — National Decertification Sweep

**IADLEST National Decertification Index (NDI)** — first stop, always:
```
URL: https://www.iadlest.org/NDI
Query: Full legal name + known aliases
Note: NDI participation is VOLUNTARY — a clean result here does NOT mean clean record
```

**NDI non-participating states — MUST query directly:**
These states do not reliably report to NDI. If subject has any connection to these
jurisdictions, query their state POST independently:

| State | POST URL | Notes |
|-------|---------|-------|
| California | `post.ca.gov/peace-officer-search` | Large force, frequent gaps |
| New Jersey | `njsp.org/division/nos/professional-standards` | Limited public access |
| Hawaii | `sheriffs.hawaii.gov` | Limited public lookup |
| Georgia | `gapost.org` | Partial NDI participation |
| Massachusetts | `mass.gov/orgs/peace-officer-standards-and-training-commission` | Recent reforms |

Run state POST query for EVERY state in subject's known employment history,
regardless of NDI result.

---

#### Tier 2 — Employment Gap Analysis

Cross-reference these sources to build a mobility timeline:

```
STATE SALARY DATABASES (each suspected jurisdiction)
 +
LINKEDIN EMPLOYMENT TIMELINE (public profile)
 +
WAYBACK MACHINE AGENCY ROSTERS (per jurisdiction, per gap period)
 ↓
Build: jurisdiction_history[] — see output schema below
 ↓
Flag any gap > 90 days between verifiable employment records
Flag any jurisdiction change within 180 days of a known incident or complaint
```

**Gap classification:**
| Gap Duration | Classification |
|-------------|---------------|
| < 30 days | Normal transition — note only |
| 30–90 days | MONITOR — cross-reference with disciplinary timeline |
| 90–180 days | FLAG — likely forced separation or admin leave period |
| > 180 days | CRITICAL FLAG — strong indicator of forced exit or decertification process |

---

#### Tier 3 — Pattern of Conduct — Cross-Jurisdictional

**Federal court sweep — ALL districts:**
```
PACER name search → all federal districts (not just EDWA)
CourtListener full-text: https://www.courtlistener.com/?q={NAME}&type=r
 → Catches § 1983 suits, excessive force, Brady violations filed against subject
 → Filter: civil rights, 42 USC 1983, named as defendant
```

**State court sweep — each suspected jurisdiction:**
- Query each state's public court portal by name
- Flag: civil judgments, restraining orders, disciplinary findings, named defendant in tort claims

**Local news archive per jurisdiction:**
```
Google News archive: site:newspapers.com "{FULL NAME}" "{CITY, STATE}"
Newspapers.com public index
Local PD/sheriff press releases (Wayback archived)
```

**Pattern flags — escalate immediately if found:**
- Same type of complaint (excessive force, false arrest, Brady) across 2+ jurisdictions
- Subject named as defendant in § 1983 suit in any jurisdiction
- Local news coverage of incident in prior jurisdiction
- Settlement records (check FOIA-released city/county settlement databases)

---

#### Tier 4 — Credential Laundering Detection

Bad actors use these vectors to reset their record across jurisdictions.
Check each:

**Name variant laundering:**
- Run all known aliases and middle name combinations through every credential database
- Check maiden name if applicable
- Flag: cert issued under name variant not used in primary jurisdiction

**Credential type switching:**
Subject abandons one credential type and enters adjacent field to escape record:

| From | To | Detection method |
|------|----|-----------------|
| Law enforcement POST | EMT / Paramedic | EMS licensing lookup in new state |
| EMT / Paramedic | Security / private LEO | State private security licensing |
| Municipal LEO | Tribal / campus / port authority | Tribal POST (BIA), campus safety rosters |
| State LEO | Federal contractor / private security | SAM.gov, USASpending, contractor registries |

**Jurisdiction shopping — non-POST states:**
Some jurisdictions have weak or no POST requirements:
- Private security licenses in non-licensing states
- Tribal law enforcement (sovereign jurisdiction — limited public records)
- Campus police in states with weak requirements
- Railroad / port authority / special district officers

If subject appears in any of these categories → flag as CREDENTIAL LAUNDERING RISK,
note limited verifiability, escalate to human investigator.

---

#### Mobility Timeline Output Schema

Add `jurisdiction_history` array to subject profile JSON:

```json
{
  "subject": "FULL NAME",
  "jurisdiction_history": [
    {
      "jurisdiction_id": "JX001",
      "state": "",
      "employer": "",
      "role": "",
      "date_start": "ISO-8601 or APPROX-YYYY",
      "date_end": "ISO-8601 or APPROX-YYYY | PRESENT",
      "gap_after_days": 0,
      "gap_classification": "NORMAL|MONITOR|FLAG|CRITICAL",
      "credential_held": "",
      "credential_state": "",
      "credential_status_at_departure": "ACTIVE|EXPIRED|SUSPENDED|REVOKED|UNKNOWN",
      "misconduct_flags": [],
      "federal_cases": [],
      "state_cases": [],
      "news_flags": [],
      "sources": []
    }
  ],
  "cross_jurisdictional_pattern": {
    "complaint_type_recurring": [],
    "iadlest_ndi_result": "FOUND|NOT FOUND|QUERY FAILED",
    "non_participating_states_queried": [],
    "credential_laundering_risk": "HIGH|MEDIUM|LOW|NONE",
    "laundering_vectors_detected": [],
    "total_jurisdictions": 0,
    "critical_gaps": 0,
    "expert_review_required": true
  }
}
```

---

#### Multi-Jurisdictional Workflow

```
TRIGGER: Gap detected OR misconduct flag found in primary jurisdiction search
 ↓
STEP 1 — IADLEST NDI query (full name + all aliases)
 ↓
STEP 2 — State POST query for EVERY state in employment history
   Include NDI non-participating states regardless of NDI result
 ↓
STEP 3 — Employment gap timeline construction
   Cross-reference: salary DBs + LinkedIn + Wayback rosters
   Classify each gap
 ↓
STEP 4 — PACER all-district sweep + CourtListener full-text
 ↓
STEP 5 — State court sweep per jurisdiction
 ↓
STEP 6 — Local news archive per jurisdiction
 ↓
STEP 7 — Credential laundering check
   Name variants × credential types × jurisdictions
 ↓
STEP 8 — Build jurisdiction_history[] + cross_jurisdictional_pattern{}
 ↓
STEP 9 — Hash + timestamp all artifacts → custody log
   Write to: /case-data/research/subjects/{slug}/multi-jurisdiction/
 ↓
STEP 10 — Flag for Timeline Agent: inject jurisdiction_history[]
   as additional timeline anchors
```

---

## Research Priority Queue

When given a subject, execute in this order:

1. Credential verification (fastest, most authoritative)
2. Current employer confirmation
3. Prior employer history → **immediately check for employment gaps**
4. Disciplinary/decertification search — WA CJTC + IADLEST NDI
5. **If ANY gap flagged OR ANY misconduct found → trigger Section 6 multi-jurisdictional sweep**
6. Federal/state court name search (PACER ALL DISTRICTS + state)
7. Common Crawl + Wayback timestamp pulls on relevant agency pages
8. Social/news archive sweep — per jurisdiction in mobility timeline
9. Credential laundering check (if multi-jurisdictional sweep triggered)
10. Compile unified profile with `jurisdiction_history[]` + tamper evidence artifacts

**Hard rule:** Steps 5–9 are NOT optional if a gap or misconduct flag is found in steps 1–4.
Surface-level single-state research is insufficient when the threat model includes jurisdictional mobility.

---

## Integration with OpenClaw / DeepSeek

**System prompt injection block** (prepend to DeepSeek API calls):

```
You are the OpenClaw Online Investigator, a legal OSINT sub-agent for civil rights
litigation. You locate public records, verify professional credentials, surface employment
history, and detect public records tampering using Common Crawl and Wayback Machine.
You operate ONLY on publicly available data. All findings must cite source URL, retrieval
date, and method. Output structured JSON + Markdown reports suitable for federal court
filings. Current case: {CASE_ID}. Subject: {SUBJECT_NAME}.
```

**Recommended DeepSeek model**: `deepseek-chat` (cost-effective) or `deepseek-reasoner` for
complex tamper timeline analysis requiring multi-step reasoning.

**Tool calls to enable:**
- `web_search` — general OSINT queries
- `web_fetch` — direct URL retrieval for credential pages, Common Crawl WARC data
- `bash_tool` — SHA-256 hashing, diff generation, WARC parsing

---

## References

- `references/case-config.md` — Load for active case context (parties, dates, incident timeline)
- `references/foia-templates.md` — Pre-drafted FOIA request templates for CAD logs, personnel files
- `references/wa-licensing-sources.md` — Washington State specific credential lookup URLs
- `references/commoncrawl-warc-parser.py` — Script for fetching and diffing WARC content
- `references/state-licensing-router.md` — 50-state licensing board URL lookup table (see below)

---

## Jurisdictional Routing — Multi-State Credential Lookups

**Rule:** If the subject's certification state is NOT Washington, route to the correct
state licensing board. Do not default to WA sources for out-of-state credentials.

**Routing logic:**
```
1. Determine subject's state of employment at time of incident
2. Look up correct board URL in state-licensing-router.md
3. If state board URL is UNKNOWN → fall back to NREMT (EMT) or national POST database
4. Log which jurisdiction was queried with each credential lookup
```

**Key national fallbacks (when state source unavailable):**
| Credential | National Fallback |
|------------|------------------|
| EMT / Paramedic | NREMT: `nremt.org/emt/verify` |
| Law Enforcement POST | IADLEST National Decertification Index: `iadlest.org/NDI` |
| Physician / NP / PA | NPPES NPI Registry: `npiregistry.cms.hhs.gov` |
| Federal exclusions | OIG: `exclusions.oig.hhs.gov` |

**State EMS Licensing — Quick Reference (expand in `state-licensing-router.md`):**

| State | EMS Licensing URL |
|-------|------------------|
| WA | `fortress.wa.gov/doh/providercredentialsearch` |
| OR | `oregon.gov/oha/PH/ProviderPartnerResources/EMSTraumaSystem` |
| ID | `idhw.idaho.gov/ems` |
| CA | `emsa.ca.gov/personnel-licensing-registry` |
| MT | `dphhs.mt.gov/PHSD/EMS` |
| AK | `dhss.alaska.gov/dph/Emergency/Pages/ems/licensing` |
| AZ | `azdhs.gov/preparedness/emergency-medical-services-trauma-system` |
| NV | `dpbh.nv.gov/Reg/EMS` |
| *(all 50 states)* | *→ See `references/state-licensing-router.md` for complete table* |

**State POST Decertification — Quick Reference:**

| State | POST / CJTC URL |
|-------|----------------|
| WA | `cjtc.wa.gov` |
| OR | `oregon.gov/dpsst` |
| ID | `post.idaho.gov` |
| CA | `post.ca.gov` |
| MT | `dojmt.gov/post` |
| *(all 50 states)* | *→ See `references/state-licensing-router.md` for complete table* |

---

## Example Queries This Skill Handles

- "Find Jeremiah Johnson's EMT certification status in Washington"
- "Pull all Common Crawl snapshots of [agency] staff directory and diff them"
- "Check if [name] has POST decertification in WA CJTC records"
- "Pull Wayback snapshots of [court URL] before and after [incident date]"
- "Build a full subject profile on [name] for 1983 complaint exhibit"
- "Check WA state salary database for [name] employment dates"
- "Run PACER name search on [name] — federal cases only"
- "Generate tamper evidence report for [URL] between [date range]"
