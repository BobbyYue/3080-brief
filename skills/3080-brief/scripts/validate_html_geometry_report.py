#!/usr/bin/env python3
"""Validate the browser-collected geometry audit for a 3080 HTML artifact."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--html", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL\nERROR geometry report unavailable: {exc}")
        return 1
    try:
        html = args.html.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL\nERROR HTML artifact unavailable: {exc}")
        return 1

    contract_match = re.search(r'data-contract-id="([a-f0-9]{64})"', html)
    expected_contract = contract_match.group(1) if contract_match else ""
    if report.get("schema_version") != 1:
        errors.append("geometry report schema_version must be 1")
    if report.get("contract_id") != expected_contract or not expected_contract:
        errors.append("geometry report is not bound to the delivered HTML contract")
    if report.get("status") != "PASS":
        errors.append("rendered geometry audit did not pass")
    issues = report.get("issues")
    if not isinstance(issues, list) or issues:
        errors.append("geometry report must contain an empty issues array")
    if not isinstance(report.get("checked_scopes"), int) or report.get("checked_scopes", 0) < 1:
        errors.append("geometry report did not inspect any figure scope")
    viewport = report.get("viewport") or {}
    if not isinstance(viewport.get("width"), (int, float)) or viewport.get("width", 0) < 1000:
        errors.append("geometry report must come from a normal desktop reading width")
    if "__3080GeometryAudit" not in html:
        errors.append("HTML artifact does not contain the geometry audit runtime")

    print("FAIL" if errors else "PASS")
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
