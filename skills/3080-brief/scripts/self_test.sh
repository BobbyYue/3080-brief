#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 "$SCRIPT_DIR/check_dependencies.py" --mode core
python3 "$SCRIPT_DIR/validate_skill.py" "$SKILL_DIR"
python3 "$SCRIPT_DIR/check_context_budget.py" "$SKILL_DIR"
python3 "$SCRIPT_DIR/run_evals.py"

CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}"
OFFICIAL_VALIDATOR="$CODEX_ROOT/skills/.system/skill-creator/scripts/quick_validate.py"
if [[ -f "$OFFICIAL_VALIDATOR" ]] && python3 -c 'import yaml' >/dev/null 2>&1; then
  python3 "$OFFICIAL_VALIDATOR" "$SKILL_DIR"
elif [[ ! -f "$OFFICIAL_VALIDATOR" ]]; then
  echo "[SKIP] optional official quick_validate.py is not installed; local standard-library validation passed"
else
  echo "[SKIP] optional official quick_validate.py requires PyYAML; local standard-library validation passed"
fi
