#!/usr/bin/env python3
"""Validate a visual-only replay against the rendered image and hidden claim map."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load_json(path, label):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{label} unavailable: {exc}")


def validate(report, preview, ledger, visual_spec):
    errors = []
    digest = hashlib.sha256(Path(preview).read_bytes()).hexdigest()
    if report.get("reader_role") != "visual_blind":
        errors.append("reader_role must be visual_blind")
    if report.get("visual_artifact_id") != digest:
        errors.append("visual_artifact_id does not match the rendered preview")
    if not isinstance(report.get("review_round"), int) or report.get("review_round", 0) < 1:
        errors.append("review_round must be a positive integer")

    replay = report.get("replay") or {}
    for key in ("main_judgment", "next_action_or_boundary", "reading_path"):
        if not isinstance(replay.get(key), str) or not replay[key].strip():
            errors.append(f"replay.{key} must be non-empty")
    if not isinstance(replay.get("supporting_evidence"), list) or not any(str(item).strip() for item in replay.get("supporting_evidence", [])):
        errors.append("replay.supporting_evidence must contain visible evidence")
    if not isinstance(replay.get("unresolved_confusion"), list):
        errors.append("replay.unresolved_confusion must be an array")

    evaluation = report.get("evaluation") or {}
    verdict = evaluation.get("verdict")
    if verdict not in {"PASS", "FAIL"}:
        errors.append("evaluation.verdict must be PASS or FAIL")
    claims = {claim.get("id"): claim for claim in ledger.get("claims", []) if claim.get("id")}
    blocks = visual_spec.get("blocks") or []
    visual_claim_ids = {claim_id for block in blocks for claim_id in block.get("claim_ids", [])}
    anchor = next((block for block in blocks if block.get("visual_role") == "anchor"), blocks[0] if blocks else {})
    anchor_claim_ids = set(anchor.get("claim_ids", []))
    anchor_p0 = {claim_id for claim_id in anchor_claim_ids if claims.get(claim_id, {}).get("priority") == "P0"}
    visual_p0 = {claim_id for claim_id in visual_claim_ids if claims.get(claim_id, {}).get("priority") == "P0"}
    expected_action_boundary = {
        claim_id for claim_id in visual_claim_ids
        if claims.get(claim_id, {}).get("kind") in {"action", "boundary"}
    }

    id_fields = ("main_judgment_claim_ids", "evidence_claim_ids", "action_or_boundary_claim_ids")
    for field in id_fields:
        values = evaluation.get(field)
        if not isinstance(values, list):
            errors.append(f"evaluation.{field} must be an array")
            continue
        unknown = set(values) - visual_claim_ids
        if unknown:
            errors.append(f"evaluation.{field} contains claims not mapped to the visual: {sorted(unknown)}")

    if verdict == "PASS":
        main_ids = set(evaluation.get("main_judgment_claim_ids") or [])
        evidence_ids = set(evaluation.get("evidence_claim_ids") or [])
        action_ids = set(evaluation.get("action_or_boundary_claim_ids") or [])
        required_main = anchor_p0 or visual_p0
        if required_main and not main_ids.intersection(required_main):
            errors.append("PASS requires a mapped P0 main judgment carried by the anchor when available")
        if not evidence_ids:
            errors.append("PASS requires at least one mapped evidence claim")
        if expected_action_boundary and not action_ids.intersection(expected_action_boundary):
            errors.append("PASS requires the visible mapped action or decision-changing boundary")
        if evaluation.get("reading_path_clear") is not True:
            errors.append("PASS requires a clear replayed reading path")
        if evaluation.get("unresolved_confusion_blocks_decision") is not False:
            errors.append("PASS requires unresolved confusion to be non-blocking for the intended decision")
        if evaluation.get("blocking_issues"):
            errors.append("PASS cannot retain blocking issues")
    elif verdict == "FAIL" and not evaluation.get("blocking_issues"):
        errors.append("FAIL requires at least one blocking issue")

    if not isinstance(evaluation.get("unresolved_confusion_blocks_decision"), bool):
        errors.append("evaluation.unresolved_confusion_blocks_decision must be boolean")
    if not isinstance(evaluation.get("required_fixes"), list):
        errors.append("evaluation.required_fixes must be an array")
    status = "FAIL" if errors or verdict == "FAIL" else "PASS"
    return status, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--visual-preview", required=True, type=Path)
    parser.add_argument("--claim-ledger", required=True, type=Path)
    parser.add_argument("--visual-spec", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    for path, label in ((args.visual_preview, "visual preview"), (args.report, "visual replay")):
        if not path.is_file():
            raise SystemExit(f"{label} is missing: {path}")
    report = load_json(args.report, "visual replay")
    ledger = load_json(args.claim_ledger, "claim ledger")
    visual_spec = load_json(args.visual_spec, "visual spec")
    status, errors = validate(report, args.visual_preview, ledger, visual_spec)
    result = {"status": status, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(status)
        for error in errors:
            print(f"ERROR {error}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
