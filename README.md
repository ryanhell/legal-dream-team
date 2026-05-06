# OpenClaw Legal Dream Team

**Open-source toolkit for pro se litigants filing civil rights lawsuits in federal court.**

> ⚠️ **DISCLAIMER:** This app, its developers, and all members are positively not lawyers and no advice is implied nor should it be inferred from humans or machine ("code"). This app could be helpful for conducting analysis or investigations within the allowances of local law and provisional requirements relating to investigators, Private Investigator's, and or stalking should this app be misused or abused beyond its intended purpose. The best thing to do is consult your local pro bono lawyer of the day consultation service or some similar access to a professional legal expert. This app is intended for lawful use only, as a fair mechanism to enable indigent or pro-se defendants (or, pro se plaintiffs!) the same calibre of tooling as their opponents in the court room, while complying with US, State, and municipal laws. If this app violates your local laws or court laws, delete it. If it presents a serious problem requiring take down and or modification; please contact the creator Ryan Michael Hell on GitHub IM.

This repository contains everything you need to investigate your case, organize evidence, research the law, and format court-ready filings — all with chain-of-custody proof that your evidence hasn't been tampered with.

> ⚠️ **LEGAL DISCLAIMER : I AM NOT A LAWYER.**
> 
The developers, contributors, and maintainers of this repository are not attorneys and are not licensed to practice law in any jurisdiction. Nothing in this repository — including but not limited to code, documentation, agent outputs, skill files, or any generated content — constitutes legal advice, legal counsel, or an attorney-client relationship. No such advice should be inferred from any human-authored or machine-generated content herein.
This tooling is designed solely to assist lawful research, open-source investigation, and document organization for individuals acting within the bounds of applicable federal, state, and local law. Intended users include pro se defendants, pro se plaintiffs, and indigent individuals seeking equitable access to investigative and organizational tooling comparable to that available to represented parties.
This tool is for lawful use only. Users are solely responsible for ensuring their use complies with all applicable laws, including but not limited to laws governing private investigation licensing, electronic surveillance, stalking, harassment, and data privacy in their jurisdiction. Misuse of this tooling for harassment, unlawful surveillance, or any purpose beyond its stated intent is expressly prohibited and is the sole legal responsibility of the user.
If you are facing legal proceedings, consult a licensed attorney. If cost is a barrier, contact your local bar association's lawyer referral service, a legal aid organization, or a law school clinic in your area.
If this repository conflicts with your local laws or applicable court rules, you are advised to discontinue use and delete it. For takedown requests, serious legal concerns, or required modifications, contact the repository maintainer directly via GitHub: @ryanhell.
This disclaimer does not create any warranty, express or implied, regarding the accuracy, completeness, or fitness for purpose of any content in this repository.
>
> 🚀 **New here? Start with [`USER_GUIDE.md`](USER_GUIDE.md)** for a complete walkthrough from zero to filing.
> 🛠️ **Already setup?** Jump to [Quick Start](#quick-start) below.
>
> **If you don't know what "skills" or "agents" are — don't worry.** The guide explains everything in plain language.

### What this does (plain English)

- **Finds public records** about people involved in your case — their jobs, licenses, certifications, disciplinary history, court cases
- **Detects tampered documents** by comparing old and new versions of public web pages (using Common Crawl and the Wayback Machine)
- **Builds a timeline** of everything that happened, flags gaps and contradictions in the official story
- **Organizes the law** — statutes, caselaw, element checklists for constitutional claims
- **Formats your court filing** so it meets federal district court rules — captions, exhibits, service certificates, page limits, all ready to upload to CM/ECF
- **Proves your evidence wasn't altered** — every file gets a SHA-256 hash logged in an append-only custody chain

### Who this is for

Pro se litigants in federal district court who:
- Cannot afford an attorney
- Have a civil rights case (42 U.S.C. § 1983)
- Need to organize large volumes of evidence
- Want court-admissible documentation of digital evidence integrity
- Are filing in the Eastern District of Washington (Spokane) — though the pattern works for any district

---

## Quick Start

```bash
git clone https://github.com/ryanhell/legal-dream-team.git
cd legal-dream-team
bash setup.sh
pip install -r requirements.txt
python references/commoncrawl-warc-parser.py --url "chelanwa.gov/sheriff/staff/" --verbose
```

---

## The Five Agents

| # | Agent | Skill File | What It Does |
|---|-------|-----------|--------------|
| 1 | **OSINT / Public Records Investigator** | `skills/openclaw-legal-investigator/SKILL.md` | Public records lookups, credential verification (EMT, POST, dispatcher), Common Crawl tamper detection, multi-jurisdictional bad actor profiling |
| 2 | **Evidence Forensics Agent** | `skills/openclaw-legal-forensics-agent/SKILL.md` | Video/audio metadata extraction, encoding continuity analysis, AI manipulation detection, chain-of-custody manifests |
| 3 | **Timeline Reconstruction** | `skills/openclaw-legal-timeline-reconstruction/SKILL.md` | Cross-source chronological reconstruction, gap analysis, conflict detection, shadow dispatch flagging |
| 4 | **Statute & Caselaw Researcher** | `skills/openclaw-legal-statute-researcher/SKILL.md` | Statute text retrieval, element checklists, controlling 9th Circuit / Supreme Court precedent, qualified immunity status |
| 5 | **Document Architect** | `skills/openclaw-legal-document-architect/SKILL.md` | EDWA CM/ECF-ready formatting, caption templates, exhibit system, certificate of service, pre-filing checklist |

---

## Directory Structure

```
legal-dream-team/
├── .gitignore                          # Python / OS / media artifacts
├── requirements.txt                    # Python deps (requests)
├── setup.sh                            # One-command installer
├── USER_GUIDE.md                       # Full setup + workflow guide
├── skills/
│   └── {agent-name}/SKILL.md           # Agent definitions
├── references/
│   ├── case-config.json                # Global case constants
│   ├── defendant-roster.json           # Named defendants & claims
│   ├── foia-templates.md               # 5 pre-drafted WA public records requests
│   ├── commoncrawl-warc-parser.py      # Tamper detection tool
│   └── state-licensing-router.md       # 50-state licensing board URLs
├── research/
│   ├── subjects/                       # OSINT investigator output
│   ├── tamper-evidence/                # WARC parser output
│   └── chain-of-custody.log            # Append-only artifact log
├── forensics/video/                    # Forensics agent output
├── timeline/references/                # Event timestamps & anchors
├── statutes/                           # Statute researcher output
└── filings/
    ├── drafts/                         # Working copies
    └── exhibits/                       # Formatted PDFs
```

---

## Workflow

```
CASE DEFINITION
  ↓
OSINT INVESTIGATION → Subject profiles, credential verification, tamper detection
  ↓
EVIDENCE FORENSICS → Hash + timestamp all exhibits, chain-of-custody
  ↓
TIMELINE RECONSTRUCTION → Master timeline, gap analysis, conflict detection
  ↓
STATUTE RESEARCH → Element checklists, controlling authority, QI status
  ↓
YOU WRITE THE LEGAL ARGUMENTS  ← this step is yours (not the AI)
  ↓
DOCUMENT ARCHITECT → EDWA formatting, captions, exhibits, COS, CM/ECF checklist
  ↓
FILE AT waed.uscourts.gov
```

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

## Chain-of-Custody

Every artifact produced by this pipeline gets:
1. **SHA-256 hashed** before writing to disk
2. **Logged** to `research/chain-of-custody.log` with timestamp, agent ID, source URL, and hash
3. **Cross-referenced** between agents — OSINT feeds Timeline, Forensics feeds Document Architect

When you produce a court affidavit of digital integrity, the custody log proves nothing was altered. Judges can verify: hash this file, compare to the log, confirm match.

**The log is append-only.** Never overwrite entries.

---

## Public Records — FOIA Templates

Five pre-drafted Washington Public Records Act (RCW 42.56) request templates in `references/foia-templates.md`:

| Template | Target |
|----------|--------|
| 1 | CAD logs & dispatch audio |
| 2 | Personnel records (employee/contractor) |
| 3 | Business entity records (B&T Towing) |
| 4 | Body-worn camera / dashcam video |
| 5 | Agency organizational records (Rivercom 911) |

---

## Credential Lookups — 50-State Router

`references/state-licensing-router.md` — EMS, POST, and private security licensing boards for all 50 states. Two-state quick reference included, plus IADLEST National Decertification Index for law enforcement decertification across jurisdictions.

---

## Ethical Boundaries

These tools are for **document organization, evidence management, and procedural formatting only.**

- ✅ Public records research
- ✅ Evidence hashing and chain-of-custody
- ✅ Statute retrieval and element checklists
- ✅ EDWA document formatting
- ❌ No agent drafts legal arguments
- ❌ No agent evaluates case strength
- ❌ No agent accesses private databases
- ❌ No agent provides legal advice

---

## Requirements

- **Python 3** + `requests` (pip install)
- **Internet** for public records lookups, Common Crawl, Wayback Machine
- **ffmpeg + exiftool** (optional — for Forensics Agent when built)
- **No API keys needed** for any agent — all sources are public

---

## Customization

Edit these files for your own case:
- `references/case-config.json` — case number, parties, evidence inventory
- `references/defendant-roster.json` — defendant names, roles, OSINT priorities
- `timeline/references/timeline-anchors.json` — known event timestamps

---

## License & Attribution

Open source under MIT. Built for the OpenClaw AI Agent Framework.
Case reference: Chelan County Superior Court 24-1-00253-04.

---

## Links

- **Repo:** `github.com/ryanhell/legal-dream-team` — clone, fork, share freely
- **License:** MIT — use it, modify it, build on it
- **OpenClaw:** `docs.openclaw.ai` | `github.com/openclaw/openclaw`
- **EDWA Local Rules:** `waed.uscourts.gov`
- **WA Public Records Act:** `RCW 42.56`
- **Common Crawl:** `index.commoncrawl.org`
- **Wayback Machine:** `web.archive.org`
- **WA DOH Credential Lookup:** `fortress.wa.gov/doh/providercredentialsearch`
- **WA CJTC (POST):** `cjtc.wa.gov`
- **IADLEST NDI:** `iadlest.org/NDI`
