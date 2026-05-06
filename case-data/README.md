# OpenClaw Legal Dream Team
## Sub-Agent Architecture — Master Reference

---

## Agent Roster

| # | Agent | SOUL.md | Primary Output |
|---|-------|---------|---------------|
| 1 | OSINT / Public Records Investigator | `osint-agent/SOUL.md` | Subject profiles, tamper evidence reports |
| 2 | Evidence Forensics Agent | `forensics-agent/SOUL.md` | Forensic analysis reports, chain-of-custody manifests |
| 3 | Timeline Reconstruction Agent | `timeline-agent/SOUL.md` | Master timeline, gap report, conflict report |
| 4 | Statute & Caselaw Researcher | `statute-agent/SOUL.md` | Element checklists, controlling authority lists |
| 5 | Document Architect | `document-architect/SOUL.md` | CM/ECF-ready complaint, habeas petition, exhibit index |

---

## Data Flow

```
OSINT Agent ──────────────────────────────────────────┐
  (subject profiles, employment, credentials,          │
   tamper evidence reports)                            ↓
                                              TIMELINE AGENT
FORENSICS Agent ───────────────────────────→  (master timeline,
  (video timestamps, anomaly report,            gap analysis,
   chain-of-custody manifest)                  conflict report)
                                                        │
STATUTE Agent ────────────────────────────────────────┐ │
  (element checklists, controlling cases,              ↓ ↓
   QI status)                                  DOCUMENT ARCHITECT
                                               (formatted complaint,
                                                habeas petition,
                                                exhibit index,
                                                CM/ECF checklist)
```

---

## Global Case Config (inject into every agent)

```json
{
  "case_id": "Chelan County Superior Court 24-1-00253-04",
  "incident_date": "2024-07-04",
  "incident_location": "Chelan County, Washington",
  "incident_timezone": "America/Los_Angeles",
  "federal_venue": "EDWA — Spokane Division",
  "plaintiff": "Ryan [LAST NAME]",
  "primary_statutes": ["42 U.S.C. § 1983", "28 U.S.C. § 2241"],
  "subject_list": ["Jeremiah Johnson", "Jason Wargin", "Dan Ozment",
                   "Sean Esworthy", "Brian Chase", "Charissa Williams",
                   "Judge Robert E. Jordan"],
  "key_evidence": {
    "dashcam_video": true,
    "cad_logs": "PENDING FOIA",
    "dispatch_audio": "PENDING FOIA"
  }
}
```

---

## Refusal Hierarchy (all agents)

All agents share these baseline refusal rules:
1. **No fabrication** — if data cannot be verified from source, it is flagged UNVERIFIED
2. **No legal advice** — agents produce structured data, not legal conclusions
3. **No file alteration** — Forensics Agent reads only; never modifies evidence files
4. **No authenticated systems** — OSINT Agent touches public records only
5. **Hard stop on critical errors** — hash mismatch, missing required sections, tamper detected → flag and halt, await user decision

---

## References Directory (build these out)

```
references/
├── case-config.json          — Global case constants
├── defendant-roster.json     — Full legal names, titles, agencies
├── timeline-anchors.json     — Known verified event timestamps
├── forensic-baseline.json    — Prior FFmpeg anomaly findings
├── foia-templates.md         — CAD log, personnel file FOIA templates
└── wa-licensing-sources.md   — WA state credential lookup URLs
```

---

*Built for OpenClaw AI Agent Framework + DeepSeek API*
*Case: Chelan County Superior Court 24-1-00253-04*
