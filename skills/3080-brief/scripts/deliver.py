#!/usr/bin/env python3
"""Bind native review and writing history before returning local artifact bytes."""
import contextlib
import argparse
import io
import json
import sys
from pathlib import Path

import checked_delivery as delivery
import verify_reviewed_artifacts as verification
import plan_review_scope as scoped
import lifecycle_delivery as lifecycle
import editorial_gate
import writing_execution


def checked_brief(arguments, *, draft=False):
    parser = verification.build_parser()
    parser.add_argument("--lifecycle-run", required=True, help="Writing run directory containing lifecycle.json")
    args = parser.parse_args(arguments)
    if not args.delivery_artifact:
        raise delivery.DeliveryBlocked("Exact delivery artifact was not included in review")
    paths = [Path(value) for name, value in vars(args).items() if value and name != "lifecycle_run"]
    paths.append(lifecycle.state_path(args.lifecycle_run))
    paths.extend(map(Path, writing_execution.evidence_paths(args.lifecycle_run)))
    scripts = Path(__file__).resolve().parent
    paths.extend(scripts.glob("*.py"))
    paths.append(scripts.parent / "config" / "3080-brief.json")

    def verify():
        reviewed = json.loads(Path(args.review_result).read_text(encoding="utf-8"))
        if reviewed.get("review_method") != "independent" or reviewed.get("verdict") != ("FAIL" if draft else "PASS"):
            raise delivery.DeliveryBlocked("A finished independent review is required")
        result = {}
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            verify_native = verification.verify_incomplete if draft else verification.verify
            if verify_native(args, receipt=result) != 0:
                raise delivery.DeliveryBlocked("Review no longer matches delivery inputs")
        return lifecycle.verify(args.lifecycle_run, args.delivery_artifact, [args.review_result],
                                {**result, "review_method": "independent"}, draft=draft,
                                sources=[args.source_snapshot],
                                reader_lock=lifecycle.reader_lock_from_readiness(args.readiness_receipt))

    return delivery.pack(args.delivery_artifact, paths, verify)


def checked_scoped(arguments, *, draft=False):
    parser = argparse.ArgumentParser(description="Return the current scoped-revalidation artifact without a new full audit")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--lifecycle-run", required=True)
    args = parser.parse_args(arguments)
    plan = scoped.load_json(args.plan)
    artifact = plan.get("delivery_artifact")
    if not isinstance(artifact, dict) or not artifact.get("path"):
        raise delivery.DeliveryBlocked("Scope plan must bind the exact final artifact")

    def verify():
        result = {}
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            if scoped.command_verify(args, checked=result, incomplete=draft) != 0:
                raise delivery.DeliveryBlocked("Scoped revalidation failed")
        return lifecycle.verify(args.lifecycle_run, artifact["path"], [args.receipt],
                                {**result, "review_method": "scoped-revalidation"}, draft=draft,
                                sources=[entry["path"] for entry in scoped.load_json(args.receipt)["editorial_inputs"]["source"]])

    scripts = Path(__file__).resolve().parent
    return delivery.pack(artifact["path"], [args.plan, args.receipt, lifecycle.state_path(args.lifecycle_run),
                                           *writing_execution.evidence_paths(args.lifecycle_run),
                                           *scripts.glob("*.py"), scripts.parent / "config" / "3080-brief.json"], verify)


def checked_fast(arguments):
    parser = argparse.ArgumentParser(description="Exact-file Fast self-check delivery; no independent-review claim")
    for name in ("text", "source", "renders"):
        parser.add_argument("--" + name, action="append", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--delivery-artifact", required=True)
    parser.add_argument("--brief-json", required=True)
    parser.add_argument("--body-visible-text", default="")
    parser.add_argument("--lifecycle-run", required=True)
    parser.add_argument("--explicit-fast-choice", action="store_true", required=True,
                        help="Use only after the user explicitly requested Fast/self-check")
    args = parser.parse_args(arguments)
    if Path(args.delivery_artifact).resolve() != Path(args.text[0]).resolve():
        raise delivery.DeliveryBlocked("Exact Fast artifact must be the first reviewed text input")

    def verify():
        raw = Path(args.result).read_bytes()
        result = json.loads(raw)
        bundle = editorial_gate.fast_inputs(args)
        if (result.get("review_method") != "self-check" or result.get("verdict") != "PASS" or
                editorial_gate.verify_receipt(result, bundle)):
            raise delivery.DeliveryBlocked("Fast native self-check is missing, failed or stale")
        native = {"status": "pass", "review_method": "self-check",
                  "artifact_sha256": delivery.digest(Path(args.delivery_artifact).read_bytes()),
                  "verified_inputs": {str(Path(args.result).resolve()): delivery.digest(raw),
                    **{str(Path(e["path"]).resolve()): e["sha256"] for group in ("text", "source", "renders") for e in bundle[group]}}}
        return lifecycle.verify(args.lifecycle_run, args.delivery_artifact, [args.result], native, sources=args.source)

    scripts = Path(__file__).resolve().parent
    return delivery.pack(args.delivery_artifact, [args.result, args.brief_json, args.body_visible_text, *args.text, *args.source, *args.renders,
        *writing_execution.evidence_paths(args.lifecycle_run),
        lifecycle.state_path(args.lifecycle_run), *scripts.glob("*.py"), scripts.parent / "config/3080-brief.json"], verify)


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output", type=Path)
    options, arguments = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    try:
        if arguments and arguments[0] == "scoped":
            envelope = checked_scoped(arguments[1:])
        elif arguments and arguments[0] == "fast":
            envelope = checked_fast(arguments[1:])
        elif arguments and arguments[0] == "draft":
            envelope = (checked_scoped(arguments[2:], draft=True) if arguments[1:2] == ["scoped"] else
                        checked_brief(arguments[1:], draft=True))
        else:
            envelope = checked_brief(arguments)
        delivery.emit(envelope, options.output)
        if options.output:
            print(json.dumps({"delivery_state": envelope["delivery_state"], "envelope": str(options.output.resolve()),
                              "artifact_sha256": envelope["artifact"]["sha256"]}))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        return delivery.blocked()


if __name__ == "__main__":
    raise SystemExit(main())
