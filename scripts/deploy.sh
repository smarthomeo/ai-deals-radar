#!/usr/bin/env bash
# Deploy: export deals from DB, commit, push to GitHub Pages.
# Run after each pipeline cycle.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PIPELINE_DIR="/root/ai-deals-pipeline"

cd "$REPO_DIR"

# 1. Export deals from SQLite to JSON
python3 "$SCRIPT_DIR/export_deals.py"

# 2. Commit and push (only if deals.json changed)
if git diff --quiet deals.json 2>/dev/null && git diff --cached --quiet deals.json 2>/dev/null; then
    echo "No changes to deals.json, skipping push."
    exit 0
fi

git add deals.json
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")
TOTAL=$(python3 -c "import json; print(json.load(open('deals.json'))['total'])")
git commit -m "Update deals: ${TOTAL} active (${TIMESTAMP})" --allow-empty
git push origin main

echo "Deployed ${TOTAL} deals at ${TIMESTAMP}"
