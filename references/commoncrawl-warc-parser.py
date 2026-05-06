#!/usr/bin/env python3
"""
commoncrawl-warc-parser.py
OpenClaw Legal Dream Team — OSINT Agent
Common Crawl WARC fetch, diff, SHA-256 tamper detection pipeline.

DISCLAIMER: I AM NOT A LAWYER. This tool is for document preservation and
tamper detection only. It does not provide legal advice, legal representation,
or case evaluation. The author is a pro se litigant, not an attorney.

Usage:
  python commoncrawl-warc-parser.py --url <TARGET_URL> [options]

Options:
  --url           Target URL to investigate (required)
  --out-dir       Output directory (default: /case-data/research/tamper-evidence/)
  --crawls        Number of most recent crawls to check (default: 10)
  --diff          Run unified diff between all snapshot pairs (default: True)
  --custody-log   Path to chain-of-custody log (default: /case-data/research/chain-of-custody.log)
  --wayback       Also pull Wayback Machine snapshots in parallel
  --verbose       Print progress to stdout
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import difflib
import datetime
import requests
from pathlib import Path
from urllib.parse import quote_plus

# ── Constants ─────────────────────────────────────────────────────────────────

CDX_COLLINFO   = "https://index.commoncrawl.org/collinfo.json"
CDX_API        = "https://index.commoncrawl.org/{crawl}-index?url={url}&output=json"
WARC_BASE      = "https://data.commoncrawl.org/"
WAYBACK_CDX    = "https://web.archive.org/cdx/search/cdx?url={url}&output=json&fl=timestamp,statuscode,digest,filename"
WAYBACK_FETCH  = "https://web.archive.org/web/{timestamp}/{url}"

AGENT_ID       = "OSINT-AGENT"
BACKOFF        = [2, 8, 30, 120]   # seconds per retry on 429
MAX_RPS        = 1.0               # max requests/sec to CDX
MAX_WARC_CONC  = 3                 # max concurrent WARC fetches

DEFAULT_OUT    = "/case-data/research/tamper-evidence"
DEFAULT_LOG    = "/case-data/research/chain-of-custody.log"

# ── Helpers ────────────────────────────────────────────────────────────────────

def ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def slug(url: str) -> str:
    """URL → filesystem-safe slug."""
    return re.sub(r"[^\w\-]", "_", url)[:80]

def log_custody(log_path: str, source_url: str, filename: str,
                file_hash: str, action: str):
    """Append one entry to the chain-of-custody log."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    entry = f"{ts()} | {AGENT_ID} | {source_url} | {filename} | {file_hash} | {action}\n"
    with open(log_path, "a") as f:
        f.write(entry)

def get_with_backoff(url: str, stream: bool = False,
                     headers: dict = None, verbose: bool = False):
    """GET with exponential backoff on 429. Returns Response or None."""
    for i, wait in enumerate(BACKOFF):
        try:
            r = requests.get(url, headers=headers or {}, stream=stream, timeout=30)
            if r.status_code == 429:
                if i == len(BACKOFF) - 1:
                    print(f"  [RATE_LIMITED] 4 retries exhausted: {url}", file=sys.stderr)
                    return None
                if verbose:
                    print(f"  [429] Backing off {wait}s (attempt {i+1})...")
                time.sleep(wait)
                continue
            return r
        except requests.RequestException as e:
            print(f"  [ERROR] Request failed: {e}", file=sys.stderr)
            if i == len(BACKOFF) - 1:
                return None
            time.sleep(wait)
    return None

# ── Common Crawl ───────────────────────────────────────────────────────────────

def get_crawl_list(n: int, verbose: bool) -> list[str]:
    """Return the N most recent crawl IDs (e.g. CC-MAIN-2024-10)."""
    if verbose:
        print(f"[+] Fetching crawl index list...")
    r = get_with_backoff(CDX_COLLINFO, verbose=verbose)
    if not r or r.status_code != 200:
        print("[ERROR] Could not fetch crawl list.", file=sys.stderr)
        return []
    crawls = [c["id"] for c in r.json()]
    return crawls[:n]

def query_cdx(crawl_id: str, url: str, verbose: bool) -> list[dict]:
    """Query a single crawl's CDX index for a URL. Returns list of records."""
    api_url = CDX_API.format(crawl=crawl_id, url=quote_plus(url))
    time.sleep(1.0 / MAX_RPS)
    if verbose:
        print(f"  [CDX] {crawl_id} → querying...")
    r = get_with_backoff(api_url, verbose=verbose)
    if not r or r.status_code == 404:
        return []
    if r.status_code != 200:
        return []
    records = []
    for line in r.text.strip().splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records

def fetch_warc_content(record: dict, verbose: bool) -> bytes | None:
    """Fetch raw HTML content from a WARC record using byte-range request."""
    warc_path   = record.get("filename", "")
    offset      = int(record.get("offset", 0))
    length      = int(record.get("length", 0))
    if not warc_path or not length:
        return None
    warc_url    = WARC_BASE + warc_path
    byte_range  = f"bytes={offset}-{offset + length - 1}"
    if verbose:
        print(f"    [WARC] Fetching {warc_url} range={byte_range}")
    r = get_with_backoff(warc_url, headers={"Range": byte_range}, verbose=verbose)
    if not r or r.status_code not in (200, 206):
        return None
    # WARC format: headers block + blank line + HTTP response + blank line + HTML
    raw = r.content
    # Extract HTTP response body from WARC envelope
    try:
        # Find double CRLF after WARC headers (end of WARC header block)
        warc_end = raw.index(b"\r\n\r\n") + 4
        http_block = raw[warc_end:]
        # Find double CRLF after HTTP headers (start of body)
        http_end = http_block.index(b"\r\n\r\n") + 4
        body = http_block[http_end:]
        return body
    except (ValueError, IndexError):
        # Fallback: return raw if WARC parsing fails
        return raw

# ── Wayback Machine ────────────────────────────────────────────────────────────

def query_wayback(url: str, verbose: bool) -> list[dict]:
    """Pull all Wayback CDX entries for a URL."""
    api_url = WAYBACK_CDX.format(url=quote_plus(url))
    if verbose:
        print(f"[+] Querying Wayback CDX for {url}...")
    r = get_with_backoff(api_url, verbose=verbose)
    if not r or r.status_code != 200:
        return []
    rows = r.json()
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    records = []
    for row in rows[1:]:
        rec = dict(zip(headers, row))
        if rec.get("statuscode") == "200":
            records.append(rec)
    return records

def fetch_wayback_snapshot(timestamp: str, url: str, verbose: bool) -> bytes | None:
    """Fetch a Wayback snapshot's raw HTML."""
    fetch_url = WAYBACK_FETCH.format(timestamp=timestamp, url=url)
    if verbose:
        print(f"  [WB] Fetching {timestamp}...")
    r = get_with_backoff(fetch_url, verbose=verbose)
    if not r or r.status_code != 200:
        return None
    return r.content

# ── Snapshot management ────────────────────────────────────────────────────────

def save_snapshot(content: bytes, out_dir: Path, timestamp: str,
                  source: str, url: str, custody_log: str) -> dict:
    """Save HTML snapshot, hash it, log custody. Returns snapshot metadata."""
    filename = f"snapshot_{source}_{timestamp}.html"
    filepath = out_dir / filename
    filepath.write_bytes(content)
    h = sha256(content)
    log_custody(custody_log, url, str(filepath), h, f"SNAPSHOT_SAVED source={source}")
    return {
        "source": source,
        "timestamp": timestamp,
        "filename": filename,
        "filepath": str(filepath),
        "sha256": h,
        "size_bytes": len(content),
    }

# ── Diff engine ────────────────────────────────────────────────────────────────

def run_diff(snap_a: dict, snap_b: dict, out_dir: Path,
             url: str, custody_log: str) -> dict | None:
    """Generate unified diff between two snapshots. Returns diff metadata."""
    content_a = Path(snap_a["filepath"]).read_text(errors="replace").splitlines(keepends=True)
    content_b = Path(snap_b["filepath"]).read_text(errors="replace").splitlines(keepends=True)
    diff_lines = list(difflib.unified_diff(
        content_a, content_b,
        fromfile=f"{snap_a['source']}_{snap_a['timestamp']}",
        tofile=f"{snap_b['source']}_{snap_b['timestamp']}",
        lineterm=""
    ))
    if not diff_lines:
        return None  # identical — no change

    # Classify change types
    added   = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    change_type = []
    if removed and added:
        change_type.append("modification")
    elif removed:
        change_type.append("deletion")
    elif added:
        change_type.append("addition")

    diff_text = "".join(diff_lines)
    ts_a = snap_a["timestamp"]
    ts_b = snap_b["timestamp"]
    diff_filename = f"diff_{snap_a['source']}_{ts_a}__{snap_b['source']}_{ts_b}.patch"
    diff_path = out_dir / diff_filename
    diff_path.write_text(diff_text, encoding="utf-8")
    h = sha256(diff_text.encode())
    log_custody(custody_log, url, str(diff_path), h, "DIFF_GENERATED")

    return {
        "between": [f"{snap_a['source']}:{ts_a}", f"{snap_b['source']}:{ts_b}"],
        "type": "|".join(change_type),
        "lines_added": added,
        "lines_removed": removed,
        "diff_filename": diff_filename,
        "diff_path": str(diff_path),
        "sha256": h,
        "sha256_before": snap_a["sha256"],
        "sha256_after": snap_b["sha256"],
    }

# ── Report builder ─────────────────────────────────────────────────────────────

def build_report(url: str, snapshots: list[dict],
                 changes: list[dict], out_dir: Path,
                 custody_log: str) -> dict:
    """Build and save tamper evidence report JSON."""
    report = {
        "target_url": url,
        "query_date": ts(),
        "agent": AGENT_ID,
        "snapshots_retrieved": len(snapshots),
        "snapshots": snapshots,
        "changes_detected": changes,
        "tamper_detected": len(changes) > 0,
        "case_relevance": "MANUAL REVIEW REQUIRED — diff content must be assessed by human"
    }
    report_path = out_dir / "tamper-report.json"
    report_json = json.dumps(report, indent=2)
    report_path.write_text(report_json)
    h = sha256(report_json.encode())
    log_custody(custody_log, url, str(report_path), h, "REPORT_GENERATED")

    # Human-readable summary
    md_lines = [
        f"# Tamper Evidence Report",
        f"**Target URL:** {url}",
        f"**Query Date:** {ts()}",
        f"**Snapshots Retrieved:** {len(snapshots)}",
        f"**Changes Detected:** {len(changes)}",
        f"**Tamper Flag:** {'⚠️  YES' if changes else '✅ NO CHANGES DETECTED'}",
        "",
        "## Snapshots",
    ]
    for s in snapshots:
        md_lines.append(f"- `{s['source']}` @ `{s['timestamp']}` — SHA-256: `{s['sha256'][:16]}...`")
    md_lines += ["", "## Changes"]
    if not changes:
        md_lines.append("No differences found between any snapshot pair.")
    for c in changes:
        md_lines += [
            f"### {c['between'][0]} → {c['between'][1]}",
            f"- Type: **{c['type']}**",
            f"- Lines added: {c['lines_added']} | Lines removed: {c['lines_removed']}",
            f"- Diff: `{c['diff_filename']}`",
            f"- SHA-256 before: `{c['sha256_before'][:32]}...`",
            f"- SHA-256 after:  `{c['sha256_after'][:32]}...`",
            "",
        ]
    md_path = out_dir / "tamper-report.md"
    md_path.write_text("\n".join(md_lines))
    h_md = sha256("\n".join(md_lines).encode())
    log_custody(custody_log, url, str(md_path), h_md, "REPORT_MD_GENERATED")

    return report

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OpenClaw WARC Parser — Tamper Detection")
    parser.add_argument("--url",         required=True,  help="Target URL to investigate")
    parser.add_argument("--out-dir",     default=DEFAULT_OUT)
    parser.add_argument("--crawls",      type=int, default=10, help="Number of CC crawls to check")
    parser.add_argument("--custody-log", default=DEFAULT_LOG)
    parser.add_argument("--wayback",     action="store_true", help="Also pull Wayback Machine")
    parser.add_argument("--no-diff",     action="store_true", help="Skip diff generation")
    parser.add_argument("--verbose",     action="store_true")
    args = parser.parse_args()

    url        = args.url
    verbose    = args.verbose
    do_diff    = not args.no_diff

    # Build output directory
    url_slug   = slug(url)
    date_str   = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir    = Path(args.out_dir) / f"{url_slug}__{date_str}"
    out_dir.mkdir(parents=True, exist_ok=True)
    custody_log = args.custody_log
    os.makedirs(os.path.dirname(custody_log), exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  OpenClaw WARC Parser")
    print(f"  Target : {url}")
    print(f"  Output : {out_dir}")
    print(f"{'='*60}\n")

    snapshots = []

    # ── Common Crawl ───────────────────────────────────────────────────────────
    crawl_ids = get_crawl_list(args.crawls, verbose)
    if not crawl_ids:
        print("[WARN] No crawl IDs retrieved — check network or fall back to Wayback only.")
    else:
        print(f"[+] Checking {len(crawl_ids)} Common Crawl indexes...")

    for crawl_id in crawl_ids:
        records = query_cdx(crawl_id, url, verbose)
        if not records:
            if verbose:
                print(f"  [NO DATA] {crawl_id}")
            continue
        print(f"  [FOUND] {crawl_id} — {len(records)} record(s)")
        for rec in records[:1]:  # take first (most relevant) per crawl
            content = fetch_warc_content(rec, verbose)
            if content:
                snap = save_snapshot(
                    content, out_dir,
                    timestamp=rec.get("timestamp", crawl_id),
                    source="CC",
                    url=url,
                    custody_log=custody_log
                )
                snapshots.append(snap)
                print(f"    [SAVED] {snap['filename']} — SHA-256: {snap['sha256'][:16]}...")
            else:
                print(f"    [WARN] WARC fetch failed for {crawl_id}")
        time.sleep(1.0 / MAX_RPS)

    # ── Wayback Machine ────────────────────────────────────────────────────────
    if args.wayback:
        print(f"\n[+] Querying Wayback Machine...")
        wb_records = query_wayback(url, verbose)
        print(f"  [FOUND] {len(wb_records)} Wayback snapshot(s)")

        # Sample evenly: take up to 5 snapshots spread across the archive
        if wb_records:
            step = max(1, len(wb_records) // 5)
            sampled = wb_records[::step][:5]
            for rec in sampled:
                wts = rec.get("timestamp", "")
                content = fetch_wayback_snapshot(wts, url, verbose)
                if content:
                    snap = save_snapshot(
                        content, out_dir,
                        timestamp=wts,
                        source="WB",
                        url=url,
                        custody_log=custody_log
                    )
                    snapshots.append(snap)
                    print(f"  [SAVED] {snap['filename']} — SHA-256: {snap['sha256'][:16]}...")
                time.sleep(1)

    # ── Diff all snapshot pairs ────────────────────────────────────────────────
    changes = []
    if do_diff and len(snapshots) >= 2:
        print(f"\n[+] Running diffs across {len(snapshots)} snapshots...")
        # Sort by timestamp before diffing
        snapshots_sorted = sorted(snapshots, key=lambda s: s["timestamp"])
        for i in range(len(snapshots_sorted) - 1):
            a = snapshots_sorted[i]
            b = snapshots_sorted[i + 1]
            diff = run_diff(a, b, out_dir, url, custody_log)
            if diff:
                changes.append(diff)
                print(f"  [CHANGE] {a['timestamp']} → {b['timestamp']} — {diff['type']} "
                      f"(+{diff['lines_added']} / -{diff['lines_removed']})")
            else:
                print(f"  [SAME]   {a['timestamp']} → {b['timestamp']} — no change")
    elif len(snapshots) < 2:
        print(f"\n[INFO] Only {len(snapshots)} snapshot(s) retrieved — diff requires 2+.")

    # ── Build report ───────────────────────────────────────────────────────────
    report = build_report(url, snapshots, changes, out_dir, custody_log)

    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"  Snapshots : {len(snapshots)}")
    print(f"  Changes   : {len(changes)}")
    print(f"  Tamper    : {'⚠️  YES — REVIEW DIFFS' if changes else 'NO CHANGES DETECTED'}")
    print(f"  Output    : {out_dir}")
    print(f"  Report    : {out_dir}/tamper-report.json")
    print(f"{'='*60}\n")

    if not snapshots:
        print("[WARN] NO CRAWL DATA FOUND for this URL in checked sources.")
        print("       Possible explanations: URL never crawled, blocked by robots.txt,")
        print("       or dynamic content not captured. Flag: NO CRAWL DATA FOUND.")

    return 0 if not changes else 1  # exit 1 if changes detected (useful for CI/scripting)

if __name__ == "__main__":
    sys.exit(main())
