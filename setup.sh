#!/usr/bin/env bash
# setup.sh — OpenClaw Legal Dream Team
# Install Python dependencies and verify toolchain.
# Run from repo root: bash setup.sh

set -e

REQUIREMENTS="requirements.txt"
PYTHON="python3"

echo "=== OpenClaw Legal Dream Team — Setup ==="
echo ""

# Check Python
if ! command -v $PYTHON &>/dev/null; then
    echo "[ERROR] Python 3 not found. Install it first: brew install python3"
    exit 1
fi
echo "[OK] Python 3 found: $($PYTHON --version)"

# Check pip
if ! $PYTHON -m pip --version &>/dev/null; then
    echo "[ERROR] pip not available. Install: $PYTHON -m ensurepip"
    exit 1
fi
echo "[OK] pip available"

# Install dependencies
if [ -f "$REQUIREMENTS" ]; then
    echo "[+] Installing Python dependencies..."
    $PYTHON -m pip install -r "$REQUIREMENTS" --quiet
    echo "[OK] Dependencies installed"
else
    echo "[WARN] requirements.txt not found — skipping pip install"
fi

# Optional: check ffmpeg (for Forensics Agent)
if command -v ffmpeg &>/dev/null; then
    echo "[OK] ffmpeg found: $(ffmpeg -version 2>&1 | head -1)"
else
    echo "[WARN] ffmpeg not found — Forensics Agent requires it. Install: brew install ffmpeg"
fi

# Optional: check exiftool
if command -v exiftool &>/dev/null; then
    echo "[OK] exiftool found: $(exiftool -ver)"
else
    echo "[WARN] exiftool not found — Forensics Agent may need it. Install: brew install exiftool"
fi

# Verify WARC parser runs
if [ -f "references/commoncrawl-warc-parser.py" ]; then
    echo "[+] Verifying WARC parser..."
    $PYTHON references/commoncrawl-warc-parser.py --help &>/dev/null && \
        echo "[OK] WARC parser ready" || \
        echo "[WARN] WARC parser import check failed — check dependencies"
fi

echo ""
echo "=== Setup complete ==="
echo "Next:"
echo "  Read skills/openclaw-legal-investigator/SKILL.md"
echo "  python references/commoncrawl-warc-parser.py --url <target> --verbose"
