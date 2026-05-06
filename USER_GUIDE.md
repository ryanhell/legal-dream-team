# OpenClaw Legal Dream Team — User Guide

> ⚠️ **DISCLAIMER: I AM NOT A LAWYER.** This is a document organization and evidence management toolkit. Nothing in this repository constitutes legal advice, legal representation, or a substitute for the advice of a licensed attorney. The author is a pro se litigant, not an attorney. Use at your own risk.

A five-agent pipeline for pro se civil rights litigation: OSINT investigation, evidence forensics, timeline reconstruction, statute research, and document formatting. Designed for federal district court (EDWA), built for self-represented litigants.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/ryanhell/legal-dream-team.git
cd legal-dream-team

# 2. Setup
bash setup.sh

# 3. Run your first OSINT target
pip install -r requirements.txt
python references/commoncrawl-warc-parser.py --url "chelanwa.gov/sheriff/staff/" --verbose
```

---

## What's In The Box

| Agent | Skill File | What It Does |
|-------|-----------|--------------|
| 1 — OSINT Investigator | `skills/openclaw-legal-investigator/SKILL.md` | Public records lookups, credential verification (EMT, POST, dispatcher), Common Crawl tamper detection, multi-jurisdictional bad actor profiling |
| 2 — Evidence Forensics | *(your FFmpeg/exiftool pipelines)* | Video frame analysis, audio metadata extraction, tamper detection, chain-of-custody manifests |
| 3 — Timeline Reconstruction | `skills/openclaw-legal-timeline-reconstruction/SKILL.md` | Cross-source chronological reconstruction, gap analysis, conflict detection, shadow dispatch flagging |
| 4 — Statute & Caselaw Researcher | `skills/openclaw-legal-statute-researcher/SKILL.md` | Statute text retrieval, element checklists, controlling 9th Circuit / Supreme Court precedent, qualified immunity status |
| 5 — Document Architect | `skills/openclaw-legal-document-architect/SKILL.md` | EDWA CM/ECF-ready complaint formatting, caption templates, exhibit system, certificate of service, pre-filing checklist |

---

## Directory Structure

```
legal-dream-team/
├── .gitignore
├── requirements.txt          # Python dependencies (just: requests)
├── setup.sh                  # One-command installer
├── case-data/READEME.md      # Architecture & data flow
├── skills/
│   └── {agent-name}/SKILL.md # Agent definitions
├── references/
│   ├── case-config.json       # Global case constants
│   ├── defendant-roster.json  # Named defendants & claims
│   ├── foia-templates.md      # Pre-drafted public records requests
│   ├── commoncrawl-warc-parser.py  # Tamper detection tool
│   └── state-licensing-router.md   # 50-state licensing board URLs
├── research/
│   ├── subjects/              # OSINT investigator output
│   ├── tamper-evidence/       # WARC parser output
│   ├── chain-of-custody.log   # All artifacts logged here
├── forensics/video/           # Forensics agent output
├── timeline/references/       # Timeline anchors
├── statutes/                  # Statute researcher output
└── filings/
    ├── drafts/                # Working copies
    └── exhibits/              # Formatted PDFs
```

---

## Workflow

### Step 1 — Define Your Case

Edit `references/case-config.json`:
- Set your case number (state criminal and federal civil)
- Update incident date and timezone
- List known parties, evidence, and subjects

Edit `references/defendant-roster.json`:
- Add each defendant and their role
- Mark OSINT priority (critical / high / medium / monitor)
- List applicable claims per defendant

### Step 2 — OSINT Investigation

Run the OSINT Agent to build subject profiles:

```
Targets to investigate (priority order):
1. Primary defendants — credential verification, employment history, court records
2. Agency pages — WayBack Machine and Common Crawl for tamper detection
3. Business entities — Secretary of State records for dissolved companies
4. Court records — PACER all-district name search
```

```bash
# Check agency pages for tampered records
python references/commoncrawl-warc-parser.py --url "chelanwa.gov/sheriff/staff/" --wayback --verbose

# Check court/credential pages
python references/commoncrawl-warc-parser.py --url "courts.wa.gov/case/24-1-00253-04" --wayback --verbose
```

OSINT Agent output goes in `research/subjects/{name}/`.

### Step 3 — Evidence Forensics & Chain-of-Custody

- Hash all evidence files with SHA-256
- Extract video metadata (timestamps, device IDs, GPS)
- Detect tampering or edits in video/audio
- Record every hash in `research/chain-of-custody.log`

Forensics Agent output goes in `forensics/video/{exhibit-letter}/`.

### Step 4 — Timeline Construction

- Ingest CAD logs, call records, video timestamps, police reports
- Normalize all timestamps to UTC
- Run gap analysis — look for periods with zero source coverage
- Detect conflicts between sources
- Multi-jurisdictional employment timeline (if applicable)

Timeline Agent output goes in `timeline/`.

### Step 5 — Statute & Caselaw Research

For each claim you're considering:

1. Read the relevant track in `skills/openclaw-legal-statute-researcher/SKILL.md`
2. Retrieve statute text and element checklist
3. Find controlling Supreme Court and 9th Circuit cases
4. Check qualified immunity status per element
5. Note circuit splits or unresolved questions

Statute Agent output goes in `statutes/track-{n}-{claim-name}.md`.

### Step 6 — Document Formatting

When ready to file:

1. Write your factual allegations and legal arguments (you do the writing)
2. Pull in:
   - OSINT Agent → verified defendant names and titles
   - Forensics Agent → forensic reports and custody manifests
   - Timeline Agent → master timeline and gap report
   - Statute Researcher → element checklists
3. Run through the Document Architect's EDWA formatting:
   - Correct caption for Spokane Division
   - Sequential paragraph numbering
   - Exhibit IDs and cross-references
   - Certificate of Service
4. Run the CM/ECF pre-filing checklist
5. Export to PDF/A
6. File at waed.uscourts.gov

Drafts go in `filings/drafts/`. Final exhibits in `filings/exhibits/`.

---

## Running the WARC Parser (Tamper Detection)

```bash
# Basic — check 10 most recent Common Crawl indexes
python references/commoncrawl-warc-parser.py --url "target-url.com/page" --verbose

# Deep — Common Crawl + Wayback Machine, 20 crawls
python references/commoncrawl-warc-parser.py --url "target-url.com/page" --crawls 20 --wayback --verbose

# Custom output + custody log path
python references/commoncrawl-warc-parser.py --url "target-url.com/page" \
  --out-dir /path/to/output \
  --custody-log /path/to/chain-of-custody.log \
  --wayback --verbose
```

Exit codes: `0` = no changes detected, `1` = tamper detected.

---

## What Each Skill Requires

### OSINT Investigator
- Python 3 + requests
- Internet access (Common Crawl, WayBack Machine, state databases)
- No API keys needed — all sources are public

### Timeline Reconstruction
- Source documents (CAD logs, call records, police reports)
- Python 3 (datetime parsing, JSON merging)
- No external API dependencies

### Statute & Caselaw Researcher
- Internet access (CourtListener, Cornell LII, Google Scholar)
- No API keys needed

### Document Architect
- Python 3 (PDF generation)
- A text editor for your draft
- Access to current EDWA Local Civil Rules (free: waed.uscourts.gov)

### Evidence Forensics *(when built)*
- ffmpeg (`brew install ffmpeg`)
- exiftool (`brew install exiftool`)
- Python 3

---

## Chain-of-Custody — Why It Matters

Every artifact this pipeline produces gets:

1. **SHA-256 hashed** before writing to disk
2. **Logged** to `research/chain-of-custody.log` with timestamp, agent ID, source URL, and hash
3. **Cross-referenced** between agents (OSINT → Timeline, Forensics → Document Architect)

When you produce an affidavit of digital integrity for court, the chain-of-custody log is your evidence that nothing was altered. A judge or opposing counsel can verify: hash this file, compare to the log entry, see if it matches.

**The log is append-only.** Never delete or modify entries.

---

## Ethical Use & Boundaries

These tools are for **document organization, evidence management, and procedural formatting only**. They are not a substitute for legal advice.

- **No agent drafts legal arguments** — that's your work
- **No agent evaluates case strength** — that requires a licensed attorney
- **No agent accesses private databases** — public records only
- **No agent provides advice** — structured data only

If you're unsure whether any output crosses this line, ask a licensed attorney before filing.

---

## Customizing For Your Case

1. **`references/case-config.json`** — Update case number, parties, evidence, subjects
2. **`references/defendant-roster.json`** — Add/remove defendants, set OSINT priority
3. **`timeline/references/timeline-anchors.json`** — Add your known event timestamps
4. **Agent skill files** — Tweak search scope, output paths, or tool allowances in each `SKILL.md`

---

## Getting Help

- This repo: `github.com/ryanhell/legal-dream-team`
- OpenClaw framework: `docs.openclaw.ai`
- EDWA local rules: `waed.uscourts.gov`
- WA Public Records Act: `RCW 42.56`
- Common Crawl: `index.commoncrawl.org`
- WayBack Machine: `web.archive.org`
- WA DOH credential lookup: `fortress.wa.gov/doh/providercredentialsearch`
- WA CJTC POST: `cjtc.wa.gov`
- IADLEST NDI: `iadlest.org/NDI`

---

*Not legal advice. Built for pro se litigants by a pro se litigant.*
