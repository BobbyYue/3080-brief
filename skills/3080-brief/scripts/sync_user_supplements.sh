#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
export LANG=C

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DOC="$SKILL_DIR/docs/user-supplements-template.md"
SKILL_FILE="$SKILL_DIR/SKILL.md"
RULES_FILE="$SKILL_DIR/references/user-supplements-rules.md"
STATE_DIR="$SKILL_DIR/.sync-state"
HASH_FILE="$STATE_DIR/user-supplements.sha256"
MANIFEST_HASH="$STATE_DIR/skill-manifest.sha256"
LOCK_DIR="$STATE_DIR/sync.lock"

SOURCE_START="<!-- SYNC_TO_SKILL_START -->"
SOURCE_END="<!-- SYNC_TO_SKILL_END -->"
TARGET_START="<!-- USER_SUPPLEMENTS_START -->"
TARGET_END="<!-- USER_SUPPLEMENTS_END -->"

mkdir -p "$STATE_DIR"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  if [[ -d "$LOCK_DIR" ]]; then
    echo "sync already running"
    exit 0
  fi
  echo "sync failed: cannot create lock directory $LOCK_DIR; check write permissions" >&2
  exit 1
fi

SOURCE_PAYLOAD="$(mktemp)"
OLD_RULES="$(mktemp)"

cleanup() {
  rm -f "$SOURCE_PAYLOAD" "$OLD_RULES"
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

extract_between() {
  local start="$1" end="$2" file="$3"
  awk -v start="$start" -v end="$end" '
    $0 == start { found_start = 1; capture = 1; next }
    $0 == end { found_end = 1; capture = 0; exit }
    capture { print }
    END { if (!found_start || !found_end) exit 2 }
  ' "$file"
}

validate_sources() {
  [[ -f "$SOURCE_DOC" ]] || { echo "source supplement doc not found: $SOURCE_DOC" >&2; return 1; }
  [[ -f "$SKILL_FILE" ]] || { echo "skill file not found: $SKILL_FILE" >&2; return 1; }
  extract_between "$SOURCE_START" "$SOURCE_END" "$SOURCE_DOC" > "$SOURCE_PAYLOAD"
  extract_between "$TARGET_START" "$TARGET_END" "$SKILL_FILE" > /dev/null
  grep -q '^## User Supplements and Limits$' "$SOURCE_PAYLOAD"
  grep -q '^### Evidence, Risk, And Review$' "$SOURCE_PAYLOAD"
}

skill_manifest_hash() {
  (
    cd "$SKILL_DIR"
    find . -type f \
      ! -path './.sync-state/*' \
      ! -path './logs/*' \
      ! -name '.DS_Store' \
      ! -name '*.pyc' \
      | sort \
      | while IFS= read -r file; do shasum -a 256 "$file"; done \
      | shasum -a 256 \
      | awk '{print $1}'
  )
}

validate_sources
SOURCE_HASH="$(shasum -a 256 "$SOURCE_PAYLOAD" | awk '{print $1}')"
RULES_CHANGED=1
if [[ -f "$RULES_FILE" ]] && cmp -s "$SOURCE_PAYLOAD" "$RULES_FILE"; then
  RULES_CHANGED=0
else
  [[ -f "$RULES_FILE" ]] && cp "$RULES_FILE" "$OLD_RULES" || : > "$OLD_RULES"
  cp "$SOURCE_PAYLOAD" "$RULES_FILE"
fi

if ! bash "$SCRIPT_DIR/self_test.sh"; then
  if [[ "$RULES_CHANGED" -eq 1 ]]; then
    if [[ -s "$OLD_RULES" ]]; then cp "$OLD_RULES" "$RULES_FILE"; else rm -f "$RULES_FILE"; fi
  fi
  echo "sync aborted: self-test failed; canonical skill was not published" >&2
  exit 1
fi

printf '%s\n' "$SOURCE_HASH" > "$HASH_FILE"
skill_manifest_hash > "$MANIFEST_HASH"

if [[ "$RULES_CHANGED" -eq 1 ]]; then
  echo "updated canonical runtime rules at $RULES_FILE from $SOURCE_DOC"
else
  echo "no supplement changes; canonical skill validated"
fi
