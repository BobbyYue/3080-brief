#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL="$(cd "$SCRIPT_DIR/.." && pwd)"
EXPECTED="${BRIEF3080_CANONICAL_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/3080-brief}"
FORBIDDEN=(
  "${CLAUDE_HOME:-$HOME/.claude}/skills/3080-brief"
  "${AGENTS_HOME:-$HOME/.agents}/skills/3080-brief"
)

[[ "$CANONICAL" == "$EXPECTED" ]] || {
  echo "canonical path mismatch: expected $EXPECTED, got $CANONICAL" >&2
  exit 1
}

for path in "${FORBIDDEN[@]}"; do
  if [[ -e "$path" ]]; then
    echo "duplicate 3080-brief skill found at forbidden path: $path" >&2
    exit 1
  fi
done
echo "single-source verification PASS: $CANONICAL"
