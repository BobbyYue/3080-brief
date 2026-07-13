#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Calculate value-weighted 3080 whiteboard coverage.")
    parser.add_argument("ledger", help="claim_ledger.json")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "3080-brief.json"))
    parser.add_argument("--json", action="store_true", help="Return machine-readable output")
    args = parser.parse_args()

    ledger = load_json(args.ledger)
    config = load_json(args.config)
    coverage = config["coverage"]
    weights = coverage["weights"]
    partial_credit = float(coverage["partial_credit"])
    minimum = float(coverage["minimum_percent"])

    seen = set()
    total = 0.0
    covered = 0.0
    missing = []
    errors = []

    for claim in ledger.get("claims", []):
        claim_id = claim.get("id", "")
        if not claim_id or claim_id in seen:
            errors.append(f"duplicate or missing claim id: {claim_id or '<empty>'}")
            continue
        seen.add(claim_id)
        if claim.get("appendix", False):
            continue
        priority = claim.get("priority")
        if priority not in weights:
            errors.append(f"{claim_id}: invalid priority {priority!r}")
            continue
        status = claim.get("board_status")
        if status not in coverage["countable_statuses"]:
            errors.append(f"{claim_id}: invalid board_status {status!r}")
            continue
        weight = float(weights[priority])
        total += weight
        if status == "covered":
            covered += weight
        elif status == "partial":
            covered += weight * partial_credit
            missing.append({"id": claim_id, "priority": priority, "status": status})
        else:
            missing.append({"id": claim_id, "priority": priority, "status": status})
            if priority == "P0":
                errors.append(f"{claim_id}: P0 claim cannot be omitted from the one-picture summary")

    percent = round((covered / total * 100.0) if total else 0.0, 1)
    passed = not errors and total > 0 and percent >= minimum
    result = {
        "verdict": "PASS" if passed else "FAIL",
        "coverage_percent": percent,
        "minimum_percent": minimum,
        "covered_weight": covered,
        "total_weight": total,
        "missing_or_partial": missing,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['verdict']} coverage={percent}% minimum={minimum:g}%")
        for error in errors:
            print(f"ERROR {error}")
        for item in missing:
            print(f"GAP {item['id']} {item['priority']} {item['status']}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
