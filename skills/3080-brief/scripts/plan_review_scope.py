#!/usr/bin/env python3
"""Plan and verify scoped 3080 revalidation from layer-level hashes."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
import reader_value
import editorial_gate
import body_completion


LAYERS = ("source", "content", "visual", "layout_desktop", "layout_mobile")
ROLES = ("reader", "source", "visual")


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_id(value):
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def parse_named_file(value, allowed_prefixes):
    try:
        left, raw_path = value.split("=", 1)
        prefix, key = left.split(":", 1)
    except ValueError as exc:
        raise SystemExit(f"Invalid entry {value!r}; expected layer:key=path") from exc
    if prefix not in allowed_prefixes or not key or not raw_path:
        raise SystemExit(f"Invalid entry {value!r}")
    path = Path(raw_path).resolve()
    if not path.is_file():
        raise SystemExit(f"Missing input file: {path}")
    return prefix, key, path


def command_snapshot(args):
    layers = {layer: {} for layer in LAYERS}
    for entry in args.input:
        layer, key, path = parse_named_file(entry, LAYERS)
        if key in layers[layer]:
            raise SystemExit(f"Duplicate input key: {layer}:{key}")
        layers[layer][key] = {"path": str(path), "sha256": sha256_file(path), "size": path.stat().st_size}
    missing = [layer for layer, values in layers.items() if not values]
    if missing:
        raise SystemExit("Every review layer needs at least one input: " + ", ".join(missing))

    reviews = {}
    for entry in args.review:
        try:
            role, raw_path = entry.split("=", 1)
        except ValueError as exc:
            raise SystemExit(f"Invalid review {entry!r}; expected role=path") from exc
        if role not in ROLES or role in reviews:
            raise SystemExit(f"Invalid or duplicate review role: {role}")
        path = Path(raw_path).resolve()
        data = load_json(path)
        if data.get("reviewer_role") != role or data.get("verdict") not in {"PASS", "FAIL"}:
            raise SystemExit(f"Review file does not match role {role}: {path}")
        reviews[role] = {
            "path": str(path),
            "verdict": data["verdict"],
            "artifact_set_id": data.get("artifact_set_id", ""),
            "sha256": sha256_file(path),
        }

    manifest = {"schema_version": 1, "layers": layers, "reviews": reviews}
    if getattr(args, "brief_json", ""):
        manifest["body_completion"] = body_completion.context(args.brief_json)
    if getattr(args, "delivery_artifact", ""):
        if "body_completion" not in manifest:
            raise SystemExit("Scoped delivery snapshot requires --brief-json")
        artifact = Path(args.delivery_artifact).resolve()
        manifest["delivery_artifact"] = {"path": str(artifact), "sha256": sha256_file(artifact)}
        if getattr(args, "body_visible_text", ""):
            manifest["body_visible_text"] = body_completion.visible_ref(args.body_visible_text, artifact)
        try:
            manifest["delivery_artifact"]["content_sha256"] = sha256_bytes(reader_value.normalize(reader_value.read_text(artifact)).encode())
        except (ValueError, UnicodeError, OSError):
            manifest["delivery_artifact"]["content_sha256"] = None
        errors = validate_delivery_layer(manifest["delivery_artifact"], layers)
        if errors:
            raise SystemExit("; ".join(errors))
    manifest["manifest_id"] = stable_id(manifest)
    write_json(args.output, manifest)
    print(f"PASS snapshot manifest_id={manifest['manifest_id']}")


def changed_layers(before, after):
    def values(manifest, layer):
        return {key: {k: v for k, v in entry.items() if k != "path"}
                for key, entry in manifest["layers"].get(layer, {}).items()}
    return [layer for layer in LAYERS if values(before, layer) != values(after, layer)]


def validate_delivery_layer(artifact, layers):
    """A separately named final file cannot inherit unrelated layer approvals."""
    try:
        if sha256_file(artifact["path"]) != artifact["sha256"]:
            return ["scoped delivery artifact changed"]
        entries = [entry for name in LAYERS if name != "source" for entry in layers[name].values()]
        if not any(entry.get("path") and Path(entry["path"]).resolve() == Path(artifact["path"]).resolve()
                   and entry["sha256"] == artifact["sha256"] for entry in entries):
            return ["delivery artifact must be a bound content or render-layer input"]
        return []
    except (OSError, KeyError, TypeError):
        return ["scoped delivery-layer binding is unavailable"]


def add_review(required, reused, before_reviews, role):
    prior = before_reviews.get(role, {})
    if prior.get("verdict") == "PASS":
        reused.append(role)
    else:
        required.append(role)


def command_plan(args):
    before = load_json(args.before)
    after = load_json(args.after)
    if before.get("schema_version") != 1 or after.get("schema_version") != 1:
        raise SystemExit("Unsupported review manifest version")
    changes = changed_layers(before, after)
    if before.get("body_completion") != after.get("body_completion") and "content" not in changes:
        changes.append("content")
    old_artifact, new_artifact = before.get("delivery_artifact"), after.get("delivery_artifact")
    if new_artifact and (not old_artifact or old_artifact.get("sha256") != new_artifact.get("sha256")):
        same_content = (old_artifact and old_artifact.get("content_sha256")
                        and old_artifact["content_sha256"] == new_artifact.get("content_sha256"))
        if not same_content and "content" not in changes:
            changes.append("content")
    checks = []
    required_reviews = []
    reused_reviews = []
    prior_reviews = before.get("reviews", {})

    if "source" in changes or "content" in changes:
        checks = [
            "deterministic_source_and_content",
            "required_opening_answers",
            "render_and_target_validation",
            "visual_blind_replay",
            "full_page_visual_replay",
            "blind_reader_replay",
        ]
        required_reviews = list(ROLES)
        scope = "full_audit"
    elif "visual" in changes:
        checks = [
            "deterministic_visual",
            "render_and_target_validation",
            "visual_blind_replay",
            "full_page_visual_replay",
            "blind_reader_replay",
        ]
        required_reviews = ["reader", "visual"]
        add_review(required_reviews, reused_reviews, prior_reviews, "source")
        scope = "visual_and_reader"
    elif changes:
        checks = ["target_validator"]
        if "layout_desktop" in changes:
            checks.extend(["desktop_geometry", "full_page_visual_replay", "desktop_visual_review"])
        if "layout_mobile" in changes:
            checks.extend(["mobile_geometry", "mobile_visual_review"])
        add_review(required_reviews, reused_reviews, prior_reviews, "reader")
        add_review(required_reviews, reused_reviews, prior_reviews, "source")
        required_reviews.append("visual")
        scope = "layout_only"
    else:
        checks = ["live_target_verification"]
        for role in ROLES:
            add_review(required_reviews, reused_reviews, prior_reviews, role)
        scope = "publication_only"

    # Scope labels choose the main route; concurrent layer changes contribute
    # all their checks instead of disappearing behind an earlier branch.
    if "visual" in changes:
        checks.extend(["deterministic_visual", "render_and_target_validation", "visual_blind_replay",
                       "full_page_visual_replay", "blind_reader_replay"])
    if "layout_desktop" in changes:
        checks.extend(["target_validator", "desktop_geometry", "full_page_visual_replay", "desktop_visual_review"])
    if "layout_mobile" in changes:
        checks.extend(["target_validator", "mobile_geometry", "mobile_visual_review"])
    checks = list(dict.fromkeys(checks))

    required_reviews = list(dict.fromkeys(required_reviews))
    reused_reviews = [role for role in dict.fromkeys(reused_reviews) if role not in required_reviews]
    plan = {
        "schema_version": 1,
        "before_manifest_id": before.get("manifest_id"),
        "after_manifest_id": after.get("manifest_id"),
        "changed_layers": changes,
        "scope": scope,
        "required_checks": checks,
        "required_reviews": required_reviews,
        "reused_reviews": reused_reviews,
        "stop_when_required_scope_passes": True,
        "editorial_version": 1,
        "after_layers": after["layers"],
        "body_completion": after.get("body_completion"),
        "body_visible_text": after.get("body_visible_text"),
        "reused_review_inputs": {role: prior_reviews[role] for role in reused_reviews},
    }
    plan["plan_id"] = stable_id(plan)
    if after.get("delivery_artifact"):
        errors = validate_delivery_layer(after["delivery_artifact"], after["layers"])
        if errors:
            raise SystemExit("; ".join(errors))
        plan["delivery_artifact"] = after["delivery_artifact"]
        plan["reused_review_inputs"] = {role: prior_reviews[role] for role in reused_reviews}
        plan["plan_id"] = stable_id({key: value for key, value in plan.items() if key != "plan_id"})
    write_json(args.output, plan)
    print(
        f"PASS scope={scope} changed={','.join(changes) or 'none'} "
        f"checks={len(checks)} reviews={','.join(required_reviews) or 'none'}"
    )


def emit_native_result(args, receipt, status, issues):
    output = getattr(args, "output", None)
    if output:
        with Path(output).open("x", encoding="utf-8") as handle:
            Path(output).chmod(0o600)
            json.dump({**receipt, "status": status, "issues": issues}, handle, ensure_ascii=False, indent=2)


def command_verify(args, checked=None, *, incomplete=False):
    plan_bytes, receipt_bytes = Path(args.plan).read_bytes(), Path(args.receipt).read_bytes()
    plan, receipt = json.loads(plan_bytes), json.loads(receipt_bytes)
    verified_inputs = {str(Path(args.plan).resolve()): sha256_bytes(plan_bytes),
                       str(Path(args.receipt).resolve()): sha256_bytes(receipt_bytes)}
    errors = []
    artifact = plan.get("delivery_artifact")
    if artifact:
        errors.extend(validate_delivery_layer(artifact, plan["after_layers"]))
    errors.extend(validate_reused_reviews(plan, receipt, verified_inputs))
    if stable_id({k: v for k, v in plan.items() if k != "plan_id"}) != plan.get("plan_id"):
        errors.append("scope plan content changed")
    errors.extend(validate_editorial_scope(plan, receipt, incomplete=incomplete))
    if not incomplete and set(plan.get("required_reviews", [])) | set(plan.get("reused_reviews", [])) != set(ROLES):
        errors.append("scoped acceptance requires existing reader/source/visual results, including body judgments")
    if receipt.get("schema_version") != 1:
        errors.append("receipt schema_version must be 1")
    if receipt.get("plan_id") != plan.get("plan_id"):
        errors.append("receipt does not match the current scope plan")
    checks = receipt.get("checks", {})
    reviews = receipt.get("reviews", {})
    for name in plan.get("required_checks", []):
        if checks.get(name) not in ({"PASS", "FAIL"} if incomplete else {"PASS"}):
            errors.append(f"required check is not PASS: {name}")
    for role in plan.get("required_reviews", []):
        if reviews.get(role) not in ({"PASS", "FAIL"} if incomplete else {"PASS"}):
            errors.append(f"required review is not PASS: {role}")
    managed_bindings = dict(plan.get("reused_review_inputs", {}))
    for role in plan.get("required_reviews", []):
        entry = receipt.get("review_results", {}).get(role)
        if not isinstance(entry, dict) or not entry.get("path"):
            errors.append(f"required {role} review has no actual result file")
            continue
        try:
            original = load_json(entry["path"])
            if sha256_file(entry["path"]) != entry.get("sha256") or original.get("reviewer_role") != role or original.get("artifact_set_id") != plan["plan_id"]:
                errors.append(f"required {role} review is stale or belongs to another scope")
            elif not incomplete:
                errors.extend(editorial_gate.validate(original,
                    {"version": 1, "artifact_binding": plan["plan_id"], **receipt["editorial_inputs"]}))
            elif original.get("verdict") not in {"PASS", "FAIL"}:
                errors.append(f"required {role} review is incomplete")
            managed_bindings[role] = {"path": str(Path(entry["path"]).resolve()), "sha256": entry["sha256"]}
            verified_inputs[str(Path(entry["path"]).resolve())] = entry["sha256"]
        except (OSError, ValueError, KeyError, TypeError):
            errors.append(f"required {role} review could not be verified")
    unexpected_failed = [name for name, value in {**checks, **reviews}.items() if value == "FAIL"]
    if unexpected_failed and not incomplete:
        errors.append("receipt contains FAIL: " + ", ".join(sorted(unexpected_failed)))
    if incomplete:
        if receipt.get("status") != "fail" or not isinstance(receipt.get("issues"), list) or not receipt["issues"]:
            errors.append("incomplete scoped result must retain native failure and unresolved issues")
    elif receipt.get("status") == "fail" or receipt.get("issues"):
        errors.append("scoped result retains unresolved native failure")
    if plan.get("stop_when_required_scope_passes") is not True:
        errors.append("scope plan has no stop condition")
    if errors:
        emit_native_result(args, receipt, "fail", errors)
        print("FAIL\n- " + "\n- ".join(errors))
        return 1
    if checked is not None:
        checked.update(status="review-incomplete-draft" if incomplete else "pass", artifact_sha256=artifact["sha256"],
                       verified_inputs=verified_inputs, issues=receipt["issues"] if incomplete else [],
                       managed_review_bindings={r: {"path": str(Path(e["path"]).resolve()), "sha256": e["sha256"]}
                                                for r, e in managed_bindings.items()})
    if not incomplete:
        emit_native_result(args, receipt, "pass", [])
    label = "INCOMPLETE_NATIVE_SCOPED_BINDINGS_ONLY" if incomplete else "PASS_NATIVE_SCOPED_ONLY"
    print(f"{label} plan_id={plan['plan_id']}; writing lifecycle not checked; use deliver.py")
    return 0


def validate_reused_reviews(plan, receipt, verified_inputs=None):
    errors = []
    records = plan.get("reused_review_inputs", {})
    roles = plan.get("reused_reviews", [])
    if set(records) != set(roles):
        return ["scoped plan lacks its original reused reviews"]
    try:
        for role in roles:
            entry = records[role]
            raw = Path(entry["path"]).read_bytes()
            if verified_inputs is not None:
                verified_inputs[str(Path(entry["path"]).resolve())] = sha256_bytes(raw)
            original = json.loads(raw)
            if sha256_bytes(raw) != entry["sha256"]:
                errors.append(f"reused {role} review changed")
            if original.get("reviewer_role") != role or original.get("artifact_set_id") != entry["artifact_set_id"]:
                errors.append(f"reused {role} review binding changed")
            bundle = {"version": 1, "artifact_binding": entry["artifact_set_id"], **receipt["editorial_inputs"]}
            errors.extend(editorial_gate.validate(original, bundle))
    except (OSError, ValueError, KeyError, TypeError):
        errors.append("original reused review is missing or invalid")
    return errors


def validate_editorial_scope(plan, receipt, *, incomplete=False):
    """Reuse prior semantic judgments only after checking current layer bindings."""
    errors = []
    try:
        if plan.get("editorial_version") != 1:
            return ["scope plan predates mandatory editorial evidence; rebuild the plan"]
        layers = plan["after_layers"]
        inputs = receipt["editorial_inputs"]
        if inputs.get("body_completion") != plan.get("body_completion"):
            errors.append("scoped body plan differs from current inputs")
        data = body_completion.current(inputs["body_completion"])
        candidate = plan.get("delivery_artifact") or inputs.get("body_candidate")
        if not candidate:
            errors.append("scoped body candidate is missing")
        else:
            body_completion.read_ref(candidate, decode=False)
            if inputs.get("body_visible_text") != plan.get("body_visible_text"):
                errors.append("scoped rendered body text binding differs")
            errors.extend(body_completion.candidate_errors(data, candidate["path"], inputs.get("body_visible_text")))
        render_layers = [name for name in plan["changed_layers"] if name in {"visual", "layout_desktop", "layout_mobile"}]
        allowed_groups = {"text": ["content"], "source": ["source"],
                          "renders": render_layers or ["visual", "layout_desktop", "layout_mobile"]}
        for group, names in allowed_groups.items():
            allowed = {e["sha256"] for name in names for e in layers[name].values()}
            entries = inputs[group]
            if not entries:
                return [f"missing scoped editorial {group}"]
            for entry in entries:
                if reader_value.sha256(entry["path"]) != entry["sha256"] or entry["sha256"] not in allowed:
                    errors.append(f"scoped editorial {group} is stale or outside the current layers")
            if {entry["sha256"] for entry in entries} != allowed:
                errors.append(f"scoped editorial {group} omits current relevant files")
        text = "\n".join(reader_value.read_text(e["path"]) for e in inputs["text"])
        source = "\n".join(reader_value.read_text(e["path"]) for e in inputs["source"])
        if incomplete:
            # Failed semantic judgments remain failures; only their binding is checked.
            review = receipt.get("reader_value")
            if (not isinstance(review, dict) or review.get("version") != reader_value.VERSION or
                    review.get("artifact_binding") != plan["plan_id"]):
                errors.append("incomplete scoped editorial record is missing or stale")
        else:
            errors.extend(reader_value.validate(receipt.get("reader_value"),
                ("expression", "selection", "meaning", "unit_roles", "presentation"), plan["plan_id"],
                text, source=source, renders=[e["path"] for e in inputs["renders"]]))
    except (KeyError, OSError, ValueError, TypeError, AttributeError) as exc:
        errors.append(f"missing or invalid scoped editorial evidence: {exc}")
    return errors


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    snapshot = sub.add_parser("snapshot", help="Hash review inputs by independent layer")
    snapshot.add_argument("--input", action="append", default=[], help="layer:key=path")
    snapshot.add_argument("--review", action="append", default=[], help="role=review.json")
    snapshot.add_argument("--delivery-artifact", default="")
    snapshot.add_argument("--brief-json", default="", help="Required for a deliverable scoped snapshot")
    snapshot.add_argument("--body-visible-text", default="")
    snapshot.add_argument("--output", required=True)
    snapshot.set_defaults(func=command_snapshot)

    plan = sub.add_parser("plan", help="Compare manifests and emit the minimum safe rerun scope")
    plan.add_argument("--before", required=True)
    plan.add_argument("--after", required=True)
    plan.add_argument("--output", required=True)
    plan.set_defaults(func=command_plan)

    verify = sub.add_parser("verify", help="Verify every required scoped check passed")
    verify.add_argument("--plan", required=True)
    verify.add_argument("--receipt", required=True)
    verify.add_argument("--output", help="New native pass/fail scoped result for lifecycle registration; never overwrites")
    verify.set_defaults(func=command_verify)
    return parser


def main():
    args = build_parser().parse_args()
    result = args.func(args)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    sys.exit(main())
