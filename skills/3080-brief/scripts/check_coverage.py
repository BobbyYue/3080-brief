#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compact(value):
    return re.sub(r"\s+", "", str(value)).casefold()


def visible_block_text(block):
    values = [block.get("title", ""), block.get("note", ""), block.get("threshold_label", ""), block.get("value_label", "")]
    values.extend(block.get("rows") or [])
    values.extend(block.get("columns") or [])
    for item in (block.get("items") or []) + (block.get("cells") or []):
        for field in ("label", "display", "value", "row", "column"):
            if item.get(field) not in (None, ""):
                values.append(item[field])
    for field in ("minimum", "maximum", "threshold", "value"):
        if block.get(field) not in (None, ""):
            values.append(block[field])
    return compact(" ".join(str(value) for value in values if value not in (None, "")))


def main():
    parser = argparse.ArgumentParser(description="Calculate value-weighted 3080 whiteboard coverage.")
    parser.add_argument("ledger", help="claim_ledger.json")
    parser.add_argument("--visual-spec", required=True, help="Approved visual_spec.json")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "3080-brief.json"))
    parser.add_argument("--json", action="store_true", help="Return machine-readable output")
    args = parser.parse_args()

    ledger = load_json(args.ledger)
    spec = load_json(args.visual_spec)
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
    visual_blocks = {block.get("id"): block for block in spec.get("blocks", []) if block.get("id")}

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
        if status in {"covered", "partial"}:
            block_id = claim.get("board_block")
            block = visual_blocks.get(block_id)
            if not block:
                errors.append(f"{claim_id}: board block {block_id or '<missing>'} is absent from visual spec")
            else:
                block_claims = set(block.get("claim_ids") or [])
                if claim_id not in block_claims:
                    errors.append(f"{claim_id}: board block {block_id} does not map this claim")
                required_tokens = claim.get("visual_required_tokens") or []
                if priority in {"P0", "P1"} and not required_tokens:
                    errors.append(f"{claim_id}: covered/partial P0/P1 claim lacks visual_required_tokens")
                visible_text = visible_block_text(block)
                missing_tokens = [token for token in required_tokens if compact(token) not in visible_text]
                if missing_tokens:
                    errors.append(f"{claim_id}: board block {block_id} omits visible token(s): {', '.join(missing_tokens)}")
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
    declared_percent = spec.get("coverage_percent")
    if declared_percent is not None and float(declared_percent) != percent:
        errors.append(f"visual spec declares coverage_percent={declared_percent}, but ledger computes {percent}")
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
