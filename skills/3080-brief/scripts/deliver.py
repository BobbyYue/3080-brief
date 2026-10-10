#!/usr/bin/env python3
"""Consume the final independent audit and return the bound local artifact bytes."""
import contextlib
import argparse
import io
import json
import sys
from pathlib import Path

import checked_delivery as delivery
import verify_reviewed_artifacts as verification
import plan_review_scope as scoped


def checked_brief(arguments):
    args = verification.build_parser().parse_args(arguments)
    if not args.delivery_artifact:
        raise delivery.DeliveryBlocked("Exact delivery artifact was not included in review")
    paths = [Path(value) for value in vars(args).values() if value]
    scripts = Path(__file__).resolve().parent
    paths.extend(scripts.glob("*.py"))
    paths.append(scripts.parent / "config" / "3080-brief.json")

    def verify():
        reviewed = json.loads(Path(args.review_result).read_text(encoding="utf-8"))
        if reviewed.get("verdict") != "PASS" or reviewed.get("review_method") != "independent":
            raise delivery.DeliveryBlocked("A finished independent review is required")
        result = {}
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            if verification.verify(args, receipt=result) != 0:
                raise delivery.DeliveryBlocked("Review no longer matches delivery inputs")
        return {**result, "review_method": "independent"}

    return delivery.pack(args.delivery_artifact, paths, verify)


def checked_scoped(arguments):
    parser = argparse.ArgumentParser(description="Return the current scoped-revalidation artifact without a new full audit")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args(arguments)
    plan = scoped.load_json(args.plan)
    artifact = plan.get("delivery_artifact")
    if not isinstance(artifact, dict) or not artifact.get("path"):
        raise delivery.DeliveryBlocked("Scope plan must bind the exact final artifact")

    def verify():
        result = {}
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            if scoped.command_verify(args, checked=result) != 0:
                raise delivery.DeliveryBlocked("Scoped revalidation failed")
        return {**result, "review_method": "scoped-revalidation"}

    scripts = Path(__file__).resolve().parent
    return delivery.pack(artifact["path"], [args.plan, args.receipt, *scripts.glob("*.py")], verify)


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output", type=Path)
    options, arguments = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    try:
        envelope = checked_scoped(arguments[1:]) if arguments and arguments[0] == "scoped" else checked_brief(arguments)
        delivery.emit(envelope, options.output)
        if options.output:
            print(json.dumps({"delivery_state": envelope["delivery_state"], "envelope": str(options.output.resolve()),
                              "artifact_sha256": envelope["artifact"]["sha256"]}))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        return delivery.blocked()


if __name__ == "__main__":
    raise SystemExit(main())
