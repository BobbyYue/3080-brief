"""Reuse the three 3080 reviewers for artifact-bound editorial acceptance."""
import json
import argparse
import hashlib
from pathlib import Path
import reader_value

AXES = {"reader": ("expression", "selection", "unit_roles"),
        "source": ("meaning",), "visual": ("presentation",)}


def inputs(args, binding):
    groups = {
        "text": [args.tldr, args.body, args.draft, args.visual_spec],
        "source": [args.source_snapshot, args.source_excerpts],
        "renders": [args.whiteboard_preview, args.document_preview, args.full_page_preview],
    }
    return {"version": 1, "artifact_binding": binding, **{
        group: [{"path": str(Path(p).resolve()), "sha256": reader_value.sha256(p)}
                for p in dict.fromkeys(paths) if p and Path(p).is_file()]
        for group, paths in groups.items()
    }}


def validate(review, bundle):
    errors = []
    role = review.get("reviewer_role")
    if role not in AXES:
        return ["unknown editorial reviewer role"]
    if review.get("verdict") != "PASS":
        errors.append(f"{role} review did not pass")
    checks = review.get("checks")
    if not isinstance(checks, list) or not checks or any(
            not isinstance(c, dict) or c.get("result") != "PASS" or not reader_value.substantive(c.get("reason"))
            for c in checks):
        errors.append(f"{role} required checks are absent, failed or unexplained")
    for field in ("blocking_issues", "unsupported_claims", "missing_coverage"):
        if review.get(field) != []:
            errors.append(f"{role} has unresolved or missing {field}")
    if bundle.get("version") != 1 or bundle.get("artifact_binding") != review.get("artifact_set_id"):
        errors.append("editorial inputs belong to another artifact set")
    content = {}
    try:
        for group in ("text", "source", "renders"):
            entries = bundle[group]
            if not isinstance(entries, list) or not entries:
                return errors + [f"missing editorial {group} inputs"]
            for entry in entries:
                if reader_value.sha256(entry["path"]) != entry["sha256"]:
                    errors.append(f"editorial {group} evidence changed: {entry['path']}")
            content[group] = entries
        text = "\n".join(reader_value.read_text(e["path"]) for e in content["text"])
        source = "\n".join(reader_value.read_text(e["path"]) for e in content["source"])
        errors.extend(reader_value.validate(review.get("reader_value"), AXES[role],
            bundle["artifact_binding"], text, source=source,
            renders=[e["path"] for e in content["renders"]]))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"invalid editorial evidence: {exc}")
    return errors


def verify_receipt(result, expected_bundle=None):
    receipt = result.get("reader_value_receipt")
    if not isinstance(receipt, dict):
        return ["missing mandatory editorial review receipt"]
    errors = []
    try:
        entry = receipt["inputs"]
        if reader_value.sha256(entry["path"]) != entry["sha256"]:
            errors.append("editorial inputs changed after review")
        bundle = json.loads(Path(entry["path"]).read_text(encoding="utf-8"))
        if expected_bundle is not None and bundle != expected_bundle:
            errors.append("editorial inputs do not match the actual delivered artifact inputs")
        if bundle["artifact_binding"] != result.get("artifact_set_id"):
            errors.append("editorial receipt belongs to another artifact set")
        roles = []
        for entry in receipt["reviews"]:
            if reader_value.sha256(entry["path"]) != entry["sha256"]:
                errors.append("editorial review changed after aggregation")
            review = json.loads(Path(entry["path"]).read_text(encoding="utf-8"))
            roles.append(review.get("reviewer_role"))
            errors.extend(validate(review, bundle))
        if sorted(roles) != sorted(AXES):
            errors.append("editorial receipt must contain all three roles")
    except (KeyError, OSError, ValueError, TypeError) as exc:
        errors.append(f"invalid editorial receipt: {exc}")
    return errors


def fast_inputs(args):
    groups = {group: [{"path": str(Path(p).resolve()), "sha256": reader_value.sha256(p)}
                      for p in dict.fromkeys(getattr(args, group))]
              for group in ("text", "source", "renders")}
    binding = hashlib.sha256(json.dumps(groups, sort_keys=True).encode()).hexdigest()
    return {"version": 1, "artifact_binding": binding, "mode": "fast-self-check", **groups}


def main():
    parser = argparse.ArgumentParser(description="Editorial checks for explicitly requested Fast mode; no independent-review claim.")
    parser.add_argument("action", choices=("prepare-fast", "verify-fast"))
    for name in ("text", "source", "renders"):
        parser.add_argument("--" + name, action="append", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    bundle = fast_inputs(args)
    if args.action == "prepare-fast":
        if not args.output:
            parser.error("prepare-fast requires --output directory")
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "reader-value-inputs.json").write_text(json.dumps(bundle, indent=2) + "\n")
        for role, axes in AXES.items():
            review = {"reviewer_role": role, "artifact_set_id": bundle["artifact_binding"],
                      "review_round": 1, "review_method": "self-check", "verdict": "FAIL",
                      "checks": [{"name": "reader value", "result": "FAIL", "reason": ""}],
                      "blocking_issues": [], "unsupported_claims": [], "missing_coverage": [], "required_fixes": [],
                      "reader_value": reader_value.template(axes, bundle["artifact_binding"])}
            (args.output / (role + ".json")).write_text(json.dumps(review, indent=2) + "\n")
        print("PENDING: complete the same-agent checks, then aggregate with --self-check")
        return 0
    if not args.result:
        parser.error("verify-fast requires --result")
    result = json.loads(args.result.read_text())
    errors = verify_receipt(result, bundle)
    if result.get("verdict") != "PASS" or result.get("review_method") != "self-check":
        errors.append("Fast verification requires a passing disclosed self-check result")
    if errors:
        print("FAIL: " + "; ".join(errors))
        return 1
    print("PASS_EDITORIAL_SELF_CHECK_ONLY: existing source, coverage and rendering gates still apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
