#!/usr/bin/env python3
"""Validate the single-owner capability ledger and default runtime context budget."""

import argparse
import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
CONTRACT_PATH = SKILL_DIR / "evals" / "capability_contract.json"


def validate(skill_dir):
    skill_dir = Path(skill_dir).resolve()
    contract_path = skill_dir / "evals" / "capability_contract.json"
    errors = []
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"capability contract unavailable: {exc}"], None

    budget = contract.get("context_budget", {})
    if budget.get("default_runtime_files") != ["SKILL.md"]:
        errors.append("default_runtime_files must contain only SKILL.md")
    skill_path = skill_dir / "SKILL.md"
    try:
        skill_text = skill_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"SKILL.md unavailable: {exc}"], contract
    skill_bytes = len(skill_text.encode("utf-8"))
    skill_lines = len(skill_text.splitlines())
    if skill_bytes > budget.get("max_skill_bytes", 0):
        errors.append(f"SKILL.md is {skill_bytes} bytes; budget is {budget.get('max_skill_bytes')}")
    if skill_lines > budget.get("max_skill_lines", 0):
        errors.append(f"SKILL.md is {skill_lines} lines; budget is {budget.get('max_skill_lines')}")

    for relative in budget.get("retired_default_files", []):
        if (skill_dir / relative).exists():
            errors.append(f"retired default runtime file still exists: {relative}")
        if relative in skill_text:
            errors.append(f"SKILL.md still references retired default runtime file: {relative}")
    for phrase in budget.get("forbidden_default_phrases", []):
        if phrase in skill_text:
            errors.append(f"SKILL.md contains forbidden default-load phrase: {phrase}")

    required = contract.get("required_capability_ids", [])
    capabilities = contract.get("capabilities", [])
    ids = [item.get("id") for item in capabilities]
    if len(ids) != len(set(ids)):
        errors.append("capability IDs must be unique")
    if set(ids) != set(required):
        errors.append(f"capability IDs differ from required set: expected {sorted(required)}, got {sorted(ids)}")
    for item in capabilities:
        capability_id = item.get("id", "<missing>")
        owner = item.get("owner")
        if not isinstance(owner, dict) or set(owner) != {"file", "marker"}:
            errors.append(f"{capability_id}: owner must contain exactly file and marker")
            continue
        owner_path = skill_dir / owner["file"]
        if not owner_path.is_file():
            errors.append(f"{capability_id}: owner file is missing: {owner['file']}")
        elif owner["marker"] not in owner_path.read_text(encoding="utf-8"):
            errors.append(f"{capability_id}: owner marker is missing from {owner['file']}")
        enforcement = item.get("enforced_by")
        if not isinstance(enforcement, list) or not enforcement:
            errors.append(f"{capability_id}: enforced_by must be a non-empty list")
        else:
            for relative in enforcement:
                if not (skill_dir / relative).exists():
                    errors.append(f"{capability_id}: enforcement artifact is missing: {relative}")

    result = {
        "status": "FAIL" if errors else "PASS",
        "skill_bytes": skill_bytes,
        "skill_lines": skill_lines,
        "max_skill_bytes": budget.get("max_skill_bytes"),
        "max_skill_lines": budget.get("max_skill_lines"),
        "default_runtime_files": budget.get("default_runtime_files"),
        "capability_count": len(capabilities),
    }
    return errors, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_directory", nargs="?", type=Path, default=SKILL_DIR)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors, result = validate(args.skill_directory)
    if result is None:
        result = {"status": "FAIL"}
    result["errors"] = errors
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("FAIL")
        for error in errors:
            print(f"ERROR {error}")
    else:
        print(
            f"CONTEXT PASS: {result['skill_bytes']} bytes, {result['skill_lines']} lines, "
            f"{result['capability_count']} capabilities, default={','.join(result['default_runtime_files'])}"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
