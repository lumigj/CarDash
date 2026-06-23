#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BRANCH="main"

cd "$REPO_DIR"

# Auto-update is intentionally disabled. Leave the command here so it can be
# restored later if this Raspberry Pi should track origin/main at boot again.
# timeout 30s bash -c '
# branch="$1"
#
# while true; do
#     if git fetch origin "$branch" && git reset --hard "origin/$branch"; then
#         exit 0
#     fi
#
#     sleep 5
# done
# ' bash "$BRANCH" || true

exec "$REPO_DIR/.venv/bin/python" -u "$REPO_DIR/scripts/obd_interface.py"
