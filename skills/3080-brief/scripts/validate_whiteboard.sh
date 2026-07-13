#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: validate_whiteboard.sh <diagram.svg> [output_dir]" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
svg="$1"
out_dir="${2:-$(dirname "$svg")}"
base="$(basename "$svg" .svg)"
png="$out_dir/${base}.png"

mkdir -p "$out_dir"
python3 "$SCRIPT_DIR/validate_whiteboard_svg.py" "$svg"

set +e
whiteboard_cli="$(python3 "$SCRIPT_DIR/check_dependencies.py" --resolve whiteboard-cli)"
dependency_status=$?
set -e
if [[ "$dependency_status" -ne 0 ]]; then
  echo "BLOCKED: pinned whiteboard-cli is unavailable. Run check_dependencies.py --mode feishu --json and request user approval before installation." >&2
  exit "$dependency_status"
fi

"$whiteboard_cli" -i "$svg" -o "$png" -f svg
"$whiteboard_cli" -i "$svg" -f svg --check
echo "$png"
