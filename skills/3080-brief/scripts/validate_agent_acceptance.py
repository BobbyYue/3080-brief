#!/usr/bin/env python3
"""Validate real-agent acceptance receipts before claiming host support."""

import argparse
import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = SKILL_DIR / "evals" / "agent_acceptance.json"


def load_json(path, label, errors):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} is unavailable or invalid JSON: {exc}")
        return {}


def resolve_receipt(result_path, value):
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = Path(result_path).resolve().parent / candidate
    return candidate.resolve()


def validate(contract, result, result_path):
    errors = []
    for field in ("host", "agent_version", "model", "executed_at"):
        if not isinstance(result.get(field), str) or not result[field].strip():
            errors.append(f"result.{field} must be a non-empty string")
    expected_cases = {case["id"]: case for case in contract.get("required_cases", [])}
    cases = result.get("cases")
    if not isinstance(cases, list):
        return errors + ["result.cases must be an array"]
    actual_ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(actual_ids) != len(set(actual_ids)):
        errors.append("acceptance case IDs must be unique")
    if set(actual_ids) != set(expected_cases):
        errors.append(f"acceptance cases differ: expected {sorted(expected_cases)}, got {sorted(actual_ids)}")

    required_profile = contract.get("required_profile", "standard")
    required_checks = contract.get("required_delivery_checks", [])
    seen_run_ids = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("every acceptance case must be an object")
            continue
        case_id = case.get("id", "<missing>")
        expected = expected_cases.get(case_id, {})
        if case.get("status") != "PASS":
            errors.append(f"{case_id}: real-agent run did not PASS ({case.get('status', '<missing>')})")
            continue
        if not case.get("delivery_receipt"):
            errors.append(f"{case_id}: delivery_receipt path is missing")
            continue
        receipt_path = resolve_receipt(result_path, case["delivery_receipt"])
        receipt_errors = []
        receipt = load_json(receipt_path, f"{case_id} delivery receipt", receipt_errors)
        errors.extend(receipt_errors)
        if receipt_errors:
            continue
        if receipt.get("verdict") != "PASS":
            errors.append(f"{case_id}: delivery receipt is not PASS")
        run_id = receipt.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            errors.append(f"{case_id}: delivery receipt run_id is missing")
        elif run_id in seen_run_ids:
            errors.append(f"{case_id}: delivery receipt reuses another acceptance run_id")
        else:
            seen_run_ids.add(run_id)
        if receipt.get("profile") != required_profile:
            errors.append(f"{case_id}: expected profile {required_profile}, got {receipt.get('profile')}")
        if receipt.get("output_type") != expected.get("output_type"):
            errors.append(f"{case_id}: expected output type {expected.get('output_type')}, got {receipt.get('output_type')}")
        checks = receipt.get("checks", {})
        for check in required_checks:
            if checks.get(check) != "PASS":
                errors.append(f"{case_id}: required delivery check did not PASS: {check}")
        if expected.get("output_type") == "feishu" and checks.get("native_editable_whiteboard") != "PASS":
            errors.append(f"{case_id}: native editable Feishu whiteboard did not PASS")
        if not receipt.get("generated_output"):
            errors.append(f"{case_id}: generated output reference is missing")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    load_errors = []
    contract = load_json(args.contract, "acceptance contract", load_errors)
    result = load_json(args.result, "acceptance result", load_errors)
    errors = load_errors + (validate(contract, result, args.result) if not load_errors else [])
    report = {"status": "NOT_CERTIFIED" if errors else "CERTIFIED", "errors": errors}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif errors:
        print("NOT CERTIFIED")
        for error in errors:
            print(f"ERROR {error}")
    else:
        print("HOST ACCEPTANCE CERTIFIED")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
