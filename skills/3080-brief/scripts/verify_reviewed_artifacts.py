#!/usr/bin/env python3
"""Low-level native review binding checks, not writing-lifecycle acceptance."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import reader_answer_gate
import editorial_gate
import body_completion


def digest(path):
    if not path:
        return None
    candidate = Path(path)
    return hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None


def build_parser():
    parser = argparse.ArgumentParser(description="Check native review bindings only; use deliver.py for lifecycle-checked delivery.")
    parser.add_argument("--review-result", required=True)
    parser.add_argument("--source-snapshot", default="")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--claim-ledger", required=True)
    parser.add_argument("--tldr", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--brief-json", required=True)
    parser.add_argument("--body-visible-text", default="")
    parser.add_argument("--draft", default="")
    parser.add_argument("--delivery-artifact", default="")
    parser.add_argument("--visual-spec", default="")
    parser.add_argument("--html-design-plan", default="")
    parser.add_argument("--validation-notes", default="")
    parser.add_argument("--whiteboard-preview", default="")
    parser.add_argument("--document-preview", default="")
    parser.add_argument("--full-page-preview", default="")
    parser.add_argument("--geometry-report", default="")
    parser.add_argument("--full-page-replay", default="")
    parser.add_argument("--source-outline", required=True)
    parser.add_argument("--source-excerpts", required=True)
    parser.add_argument("--readiness-receipt", required=True)
    return parser


def incomplete_review_errors(reviewed, bundle):
    """Check failed-review provenance without turning semantic failures into PASS."""
    errors = []
    try:
        receipt = reviewed["reader_value_receipt"]
        inputs = receipt["inputs"]
        if digest(inputs["path"]) != inputs["sha256"]:
            errors.append("editorial inputs changed after review")
        if json.loads(Path(inputs["path"]).read_text(encoding="utf-8")) != bundle:
            errors.append("editorial inputs do not match the current artifact inputs")
        if bundle.get("mode") == "fast-self-check":
            errors.append("self-check cannot impersonate independent review")
        roles = []
        for entry in receipt["reviews"]:
            if digest(entry["path"]) != entry["sha256"]:
                errors.append("original review changed after aggregation")
            original = json.loads(Path(entry["path"]).read_text(encoding="utf-8"))
            roles.append(original.get("reviewer_role"))
            if (original.get("artifact_set_id") != reviewed.get("artifact_set_id") or
                    original.get("review_round") != reviewed.get("review_round")):
                errors.append("original review belongs to another artifact set or round")
            if original.get("review_method", "independent") != "independent":
                errors.append("original review is not independent")
            if original.get("verdict") not in {"PASS", "FAIL"}:
                errors.append("original review is unfinished")
            checks = original.get("checks")
            if not isinstance(checks, list) or not checks or any(
                    not isinstance(check, dict) or check.get("result") not in {"PASS", "FAIL"} or
                    not isinstance(check.get("reason"), str) or not check["reason"].strip() for check in checks):
                errors.append("original review checks are unfinished")
            for name in ("blocking_issues", "unsupported_claims", "missing_coverage", "required_fixes"):
                if not isinstance(original.get(name), list):
                    errors.append("original review issue lists are missing")
        if sorted(roles) != sorted(editorial_gate.AXES):
            errors.append("incomplete review must retain exactly the three original roles")
        if not isinstance(reviewed.get("review_round"), int) or reviewed["review_round"] < 1:
            errors.append("review round is missing")
        if not any(reviewed.get(name) for name in ("blocking_issues", "integrity_issues", "failed_roles")):
            errors.append("incomplete review must retain unresolved issues")
    except (OSError, ValueError, KeyError, TypeError):
        errors.append("incomplete review evidence is missing or malformed")
    return errors


def verify(args, receipt=None, *, incomplete=False):

    review_bytes = Path(args.review_result).read_bytes()
    reviewed = json.loads(review_bytes)
    if reviewed.get("review_method") == "self-check":
        print("FAIL: Fast self-check is not independent review; use editorial_gate.py verify-fast and disclose omissions")
        return 1
    readiness = json.loads(Path(args.readiness_receipt).read_text(encoding="utf-8"))
    # Draft exit retains failed semantic judgments; never turn missing answers into PASS.
    body_record = body_completion.context(args.brief_json, source_snapshot=args.source_snapshot,
        claim_ledger=args.claim_ledger, source_outline=args.source_outline)
    if body_record != readiness.get("body_completion"):
        print("FAIL body completion: readiness binding is missing or stale")
        return 1
    answer_errors = reader_answer_gate.validate_readiness_binding(readiness, args.draft, args.source_snapshot, args.claim_ledger, args.visual_spec, args.whiteboard_preview)
    if answer_errors:
        print("FAIL opening comprehension: " + "; ".join(answer_errors))
        return 1
    hashes = {
        "delivery_artifact": digest(args.delivery_artifact),
        "source_snapshot": digest(args.source_snapshot),
        "inventory": digest(args.inventory),
        "claim_ledger": digest(args.claim_ledger),
        "tldr": digest(args.tldr),
        "body": digest(args.body),
        "brief_json": digest(args.brief_json),
        "body_visible_text": digest(args.body_visible_text),
        "draft": digest(args.draft),
        "visual_spec": digest(args.visual_spec),
        "html_design_plan": digest(args.html_design_plan),
        "validation_notes": digest(args.validation_notes),
        "whiteboard_preview": digest(args.whiteboard_preview),
        "document_preview": digest(args.document_preview),
        "full_page_preview": digest(args.full_page_preview),
        "geometry_report": digest(args.geometry_report),
        "full_page_replay": digest(args.full_page_replay),
        "source_outline": digest(args.source_outline),
        "source_excerpts": digest(args.source_excerpts),
        "readiness_receipt": digest(args.readiness_receipt),
    }
    hashes = {key: value for key, value in hashes.items() if value}
    artifact_set_id = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode("utf-8")).hexdigest()
    bundle = editorial_gate.inputs(args, artifact_set_id)
    editorial_errors = (incomplete_review_errors(reviewed, bundle) if incomplete else
                        editorial_gate.verify_receipt(reviewed, bundle))
    if editorial_errors:
        print("FAIL editorial review: " + "; ".join(editorial_errors))
        return 1
    expected = reviewed.get("artifact_set_id")
    if reviewed.get("verdict") != ("FAIL" if incomplete else "PASS"):
        print("FAIL review result does not match the requested mode")
        return 1
    if artifact_set_id != expected:
        print(f"FAIL artifact set changed after review: expected {expected}, got {artifact_set_id}")
        return 1
    if receipt is not None:
        receipt.update(status="review-incomplete-draft" if incomplete else "pass",
            verification_scope="native-review-bindings-only", artifact_sha256=hashes.get("delivery_artifact"),
            verified_inputs={str(Path(args.review_result).resolve()): hashlib.sha256(review_bytes).hexdigest(),
                             **{str(Path(getattr(args, name)).resolve()): value for name, value in hashes.items()}})
        if incomplete:
            receipt["issues"] = [issue for name in ("blocking_issues", "integrity_issues", "failed_roles")
                                 for issue in reviewed.get(name, [])]
    label = "INCOMPLETE_REVIEW_BINDINGS_ONLY" if incomplete else "PASS_REVIEW_BINDINGS_ONLY"
    print(f"{label} artifact_set_id={artifact_set_id}; writing lifecycle not checked; use deliver.py")
    return 0


def verify_incomplete(args, receipt=None):
    return verify(args, receipt, incomplete=True)


def main():
    return verify(build_parser().parse_args())


if __name__ == "__main__":
    sys.exit(main())
