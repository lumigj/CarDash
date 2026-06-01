#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BRANCH="main"

cd "$REPO_DIR"

for _ in {1..24}; do
    if git fetch origin "$BRANCH" && git reset --hard "origin/$BRANCH"; then
        break
    fi

    sleep 5
done

exec "$REPO_DIR/.venv/bin/python" "$REPO_DIR/scripts/obd_interface.py"
