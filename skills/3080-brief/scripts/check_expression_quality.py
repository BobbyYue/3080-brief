#!/usr/bin/env python3
"""Run source-faithful hard gates and cluster-based expression warnings."""

import argparse
import json
import re
import sys
from pathlib import Path

from validate_claim_ledger import validate as validate_claim_ledger


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config" / "3080-brief.json"


def detect_language(text):
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if cjk >= 20 and cjk >= latin * 0.18:
        return "zh"
    if latin >= 40:
        return "en"
    return "unknown"


def text_units(text):
    visible = re.sub(r"```.*?```", " ", text, flags=re.S)
    visible = re.sub(r"https?://\S+|<[^>]+>|!\[[^]]*\]\([^)]+\)|\[[^]]+\]\([^)]+\)", " ", visible)
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", visible))
    latin_words = len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9+._%/-]*\b", visible))
    return cjk + latin_words


def body_section_count(text):
    xml_headings = re.findall(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>", text, flags=re.I | re.S)
    if xml_headings:
        headings = [re.sub(r"<[^>]+>", " ", value) for value in xml_headings]
    else:
        headings = [match.group(1) for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", text)]
        if headings and headings[0].strip().casefold().startswith("3080 brief"):
            headings = headings[1:]
    return sum(1 for heading in headings if re.sub(r"\s+", " ", heading).strip().casefold() != "tldr")


def line_number(text, offset):
    return text.count("\n", 0, offset) + 1


def collect_warnings(text, language, config):
    warnings = []
    groups = config.get("expression_quality", {}).get("style_warning_groups", [])
    for group in groups:
        languages = group.get("languages", [])
        if languages and language not in languages:
            continue
        hits = []
        for pattern in group.get("patterns", []):
            for match in re.finditer(pattern, text, re.I):
                hits.append({"line": line_number(text, match.start()), "text": match.group(0)})
        minimum = group.get("minimum_hits", 2)
        if len(hits) >= minimum:
            warnings.append({
                "id": group.get("id", "unnamed_style_group"),
                "message": group.get("message", "clustered expression pattern may increase reader friction"),
                "hit_count": len(hits),
                "examples": hits[:5],
            })
    return warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    parser.add_argument("--claim-ledger", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--language", choices=["auto", "zh", "en"], default="auto")
    parser.add_argument("--non-appendix-source", type=Path, help="Normalized non-appendix source snapshot; required for thin/shorten")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors = []
    try:
        text = args.draft.read_text(encoding="utf-8")
        ledger = json.loads(args.claim_ledger.read_text(encoding="utf-8"))
        config = json.loads(args.config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"input is unavailable or invalid: {exc}")
        text, ledger, config = "", {}, {}

    if not errors:
        errors.extend(validate_claim_ledger(ledger, config))
    source_units = None
    draft_units = text_units(text) if text else 0
    body_sections = body_section_count(text) if text else 0
    output_unit_ceiling = None
    if not errors:
        sufficiency = ledger.get("source", {}).get("material_sufficiency", {})
        if sufficiency.get("status") == "thin":
            if sufficiency.get("handling") == "clarify":
                errors.append("thin source requires clarification; do not publish a final draft")
            elif sufficiency.get("handling") == "shorten":
                guardrail = config.get("expression_quality", {}).get("thin_source_guardrail", {})
                if guardrail.get("source_snapshot_required") and not args.non_appendix_source:
                    errors.append("thin/shorten requires --non-appendix-source for expansion control")
                elif args.non_appendix_source:
                    try:
                        source_text = args.non_appendix_source.read_text(encoding="utf-8")
                    except OSError as exc:
                        errors.append(f"non-appendix source snapshot is unavailable: {exc}")
                    else:
                        source_units = text_units(source_text)
                        ratio = float(guardrail.get("max_expansion_ratio", 4.0))
                        floor = int(guardrail.get("minimum_output_unit_ceiling", 240))
                        output_unit_ceiling = max(floor, int(source_units * ratio))
                        if draft_units > output_unit_ceiling:
                            errors.append(
                                f"thin-source output exceeds compact ceiling: {draft_units} units > {output_unit_ceiling} "
                                f"(source {source_units}, ratio {ratio:g})"
                            )
                        max_sections = int(guardrail.get("max_body_sections", 2))
                        if body_sections > max_sections:
                            errors.append(
                                f"thin-source output has too many body sections: {body_sections} > {max_sections}"
                            )
    language = detect_language(text) if args.language == "auto" else args.language
    warnings = collect_warnings(text, language, config) if not errors else []
    result = {
        "status": "FAIL" if errors else "PASS",
        "language": language,
        "draft_units": draft_units,
        "body_sections": body_sections,
        "source_units": source_units,
        "output_unit_ceiling": output_unit_ceiling,
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
        for error in errors:
            print(f"ERROR {error}")
        for warning in warnings:
            examples = ", ".join(f"line {item['line']}: {item['text']}" for item in warning["examples"])
            print(f"WARN {warning['id']}: {warning['message']} ({warning['hit_count']} hits; {examples})")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
