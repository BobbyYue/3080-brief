#!/usr/bin/env python3
"""Validate the blind full-page visual replay used by HTML review."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


REQUIRED_GATES = (
    "title_hierarchy_clear",
    "tldr_is_distinct_opening_unit",
    "heading_path_restates_story",
    "no_overlap_or_clipping",
    "not_a_component_wall",
    "one_picture_is_dominant",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a 3080 HTML full-page blind visual replay.")
    parser.add_argument("--report", required=True)
    parser.add_argument("--preview", required=True)
    parser.add_argument("--html", required=True)
    args = parser.parse_args()

    errors: list[str] = []
    report_path = Path(args.report)
    preview_path = Path(args.preview)
    html_path = Path(args.html)
    for label, path in (("report", report_path), ("preview", preview_path), ("html", html_path)):
        if not path.is_file() or not path.read_bytes().strip():
            errors.append(f"missing or empty {label}: {path}")

    if errors:
        print("FAIL full-page replay: " + "; ".join(errors))
        return 1

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"FAIL full-page replay: invalid report: {exc}")
        return 1

    if report.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if report.get("reviewer_role") != "full_page_visual":
        errors.append("reviewer_role must be full_page_visual")
    if report.get("verdict") != "PASS":
        errors.append("verdict must be PASS")
    if report.get("preview_sha256") != digest(preview_path):
        errors.append("preview_sha256 does not match the reviewed preview")

    html_text = html_path.read_text(encoding="utf-8")
    contract_marker = 'data-contract-id="'
    if contract_marker not in html_text:
        errors.append("HTML has no runtime contract id")
    else:
        contract_id = html_text.split(contract_marker, 1)[1].split('"', 1)[0]
        if report.get("contract_id") != contract_id:
            errors.append("report contract_id does not match HTML")

    gates = report.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
    else:
        for gate in REQUIRED_GATES:
            if gates.get(gate) is not True:
                errors.append(f"gate must PASS: {gate}")

    heading_path = report.get("heading_path")
    if not isinstance(heading_path, list) or len([item for item in heading_path if str(item).strip()]) < 2:
        errors.append("heading_path must contain at least two meaningful headings")
    if not str(report.get("first_screen_judgment", "")).strip():
        errors.append("first_screen_judgment is required")
    if not str(report.get("rhythm_assessment", "")).strip():
        errors.append("rhythm_assessment is required")
    if report.get("blocking_issues") not in ([], None):
        errors.append("blocking_issues must be empty for PASS")

    if errors:
        print("FAIL full-page replay: " + "; ".join(errors))
        return 1
    print(f"PASS full-page replay | preview={preview_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
