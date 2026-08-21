#!/usr/bin/env python3
"""Plan and verify scoped 3080 revalidation from layer-level hashes."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


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
        layers[layer][key] = {"sha256": sha256_file(path), "size": path.stat().st_size}
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
            "verdict": data["verdict"],
            "artifact_set_id": data.get("artifact_set_id", ""),
            "sha256": sha256_file(path),
        }

    manifest = {"schema_version": 1, "layers": layers, "reviews": reviews}
    manifest["manifest_id"] = stable_id(manifest)
    write_json(args.output, manifest)
    print(f"PASS snapshot manifest_id={manifest['manifest_id']}")


def changed_layers(before, after):
    return [layer for layer in LAYERS if before["layers"].get(layer) != after["layers"].get(layer)]


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
    checks = []
    required_reviews = []
    reused_reviews = []
    prior_reviews = before.get("reviews", {})

    if "source" in changes or "content" in changes:
        checks = [
            "deterministic_source_and_content",
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
        scope = "layout_only"
    else:
        checks = ["live_target_verification"]
        for role in ROLES:
            add_review(required_reviews, reused_reviews, prior_reviews, role)
        scope = "publication_only"

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
    }
    plan["plan_id"] = stable_id(plan)
    write_json(args.output, plan)
    print(
        f"PASS scope={scope} changed={','.join(changes) or 'none'} "
        f"checks={len(checks)} reviews={','.join(required_reviews) or 'none'}"
    )


def command_verify(args):
    plan = load_json(args.plan)
    receipt = load_json(args.receipt)
    errors = []
    if receipt.get("schema_version") != 1:
        errors.append("receipt schema_version must be 1")
    if receipt.get("plan_id") != plan.get("plan_id"):
        errors.append("receipt does not match the current scope plan")
    checks = receipt.get("checks", {})
    reviews = receipt.get("reviews", {})
    for name in plan.get("required_checks", []):
        if checks.get(name) != "PASS":
            errors.append(f"required check is not PASS: {name}")
    for role in plan.get("required_reviews", []):
        if reviews.get(role) != "PASS":
            errors.append(f"required review is not PASS: {role}")
    unexpected_failed = [name for name, value in {**checks, **reviews}.items() if value == "FAIL"]
    if unexpected_failed:
        errors.append("receipt contains FAIL: " + ", ".join(sorted(unexpected_failed)))
    if plan.get("stop_when_required_scope_passes") is not True:
        errors.append("scope plan has no stop condition")
    if errors:
        print("FAIL\n- " + "\n- ".join(errors))
        return 1
    print(f"PASS scoped release plan_id={plan['plan_id']}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    snapshot = sub.add_parser("snapshot", help="Hash review inputs by independent layer")
    snapshot.add_argument("--input", action="append", default=[], help="layer:key=path")
    snapshot.add_argument("--review", action="append", default=[], help="role=review.json")
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
    verify.set_defaults(func=command_verify)
    return parser


def main():
    args = build_parser().parse_args()
    result = args.func(args)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    sys.exit(main())
