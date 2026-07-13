#!/usr/bin/env python3
import argparse
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config" / "3080-brief.json"
SIGNED_METRIC_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:[+\-\u2212]\s*\d+(?:\.\d+)?\s*(?:%|pp|bps|x|\u500d)?)", re.I)


def display_width(text):
    return sum(2 if unicodedata.east_asian_width(char) in {"W", "F", "A"} else 1 for char in text)


def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def is_forbidden_heading(heading, forbidden, fragments):
    value = normalize(heading)
    for item in forbidden:
        if value == item or re.match(rf"^{re.escape(item)}\s*[:：|｜\-—]", value):
            return True
    compact = re.sub(r"\s+", " ", heading).casefold()
    return any(fragment in compact for fragment in fragments)


def add_pattern_errors(text, config, errors):
    for phrase in config["forbidden_meta_statements"]:
        for match in re.finditer(re.escape(phrase), text, re.I):
            line = text.count("\n", 0, match.start()) + 1
            errors.append((line, "forbidden process/meta statement", phrase))
    for placeholder in config["forbidden_placeholders"]:
        for match in re.finditer(re.escape(placeholder), text, re.I):
            line = text.count("\n", 0, match.start()) + 1
            errors.append((line, "unresolved placeholder", placeholder))


def add_expression_warnings(text, config, warnings):
    for phrase in config.get("discouraged_phrases", []):
        for match in re.finditer(re.escape(phrase), text, re.I):
            line = text.count("\n", 0, match.start()) + 1
            warnings.append((line, f"discouraged vague phrase; verify source-specific meaning: {phrase}"))


def inventory_value(text, *labels):
    for label in labels:
        match = re.search(rf"(?im)^\s*-\s*{re.escape(label)}\s*:\s*(.+?)\s*$", text)
        if match:
            return match.group(1).strip()
    return ""


def canonical_language(value):
    cleaned = normalize(value).split(";", 1)[0].strip()
    aliases = {
        "english": "en",
        "en": "en",
        "en-us": "en",
        "en-gb": "en",
        "中文": "zh",
        "简体中文": "zh",
        "繁體中文": "zh",
        "chinese": "zh",
        "zh": "zh",
        "zh-cn": "zh",
        "zh-tw": "zh",
    }
    if cleaned in aliases:
        return aliases[cleaned]
    return cleaned.split("-", 1)[0] if cleaned else ""


def detect_primary_language(text):
    visible = re.sub(r"```.*?```", " ", text, flags=re.S)
    visible = re.sub(r"https?://\S+|<[^>]+>|\]\([^)]+\)", " ", visible)
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", visible))
    latin = len(re.findall(r"[A-Za-z]", visible))
    total = cjk + latin
    if total < 120:
        return ""
    if cjk >= 60 and cjk / total >= 0.20:
        return "zh"
    if latin >= 180 and latin / total >= 0.75:
        return "en"
    return ""


def add_language_checks(text, inventory_text, config, errors):
    policy = config.get("language_policy", {})
    source_raw = inventory_value(inventory_text, "Source language", "Language")
    output_raw = inventory_value(inventory_text, "Output language")
    basis = normalize(inventory_value(inventory_text, "Output-language basis", "Output language basis"))
    override_evidence = inventory_value(inventory_text, "Explicit language override evidence")

    for label, value in (
        ("source language", source_raw),
        ("output language", output_raw),
        ("output-language basis", basis),
    ):
        if not value:
            errors.append((1, f"source inventory is missing {label}", ""))

    source_language = canonical_language(source_raw)
    output_language = canonical_language(output_raw)
    source_basis = normalize(policy.get("default_output_basis", "source_primary_language"))
    override_basis = normalize(policy.get("allowed_override_basis", "explicit_user_request"))
    if basis and basis not in {source_basis, override_basis}:
        errors.append((1, "invalid output-language basis", basis))
    if source_language and output_language and basis == source_basis and source_language != output_language:
        errors.append((1, "output language must match source primary language", f"{source_raw} -> {output_raw}"))
    if basis == override_basis:
        if not override_evidence or normalize(override_evidence) in {"none", "not provided", "n/a", "无", "未提供"}:
            errors.append((1, "explicit language override requires exact user evidence", override_evidence))
    elif source_language and output_language and source_language != output_language:
        errors.append((1, "language change requires explicit_user_request basis", f"{source_raw} -> {output_raw}"))

    detected = detect_primary_language(text)
    if detected and output_language in {"en", "zh"} and detected != output_language:
        errors.append((1, "draft language conflicts with declared output language", f"declared {output_raw}, detected {detected}"))


def markdown_table_info(lines):
    tables = []
    for index in range(len(lines) - 1):
        if not lines[index].lstrip().startswith("|"):
            continue
        separator = lines[index + 1].strip().strip("|").split("|")
        if not separator or not all(re.fullmatch(r"\s*:?-{3,}:?\s*", cell) for cell in separator):
            continue
        headers = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
        rows = []
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            rows.append([cell.strip() for cell in lines[cursor].strip().strip("|").split("|")])
            cursor += 1
        tables.append((index, headers, rows))
    return tables


def check_markdown(text, config, errors, warnings):
    lines = text.splitlines()
    headings = []
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2).strip()))

    if not headings:
        errors.append((1, "missing document title and TLDR heading", ""))
        return
    if not normalize(headings[0][2]).startswith("3080 brief"):
        errors.append((headings[0][0] + 1, "title must start with 3080 Brief", headings[0][2]))

    forbidden = {normalize(item) for item in config["forbidden_headings"]}
    fragments = [normalize(item) for item in config.get("forbidden_heading_fragments", [])]
    for index, _, heading in headings[1:]:
        if is_forbidden_heading(heading, forbidden, fragments):
            errors.append((index + 1, "forbidden or audience-labeled heading", heading))

    tldr_candidates = [item for item in headings[1:] if normalize(item[2]) == "tldr"]
    if not tldr_candidates:
        errors.append((1, "missing TLDR heading", ""))
        return
    tldr_index = tldr_candidates[0][0]
    if headings[1][0] != tldr_index:
        errors.append((tldr_index + 1, "TLDR must be the first content section", headings[1][2]))

    next_heading = next((index for index, _, _ in headings if index > tldr_index), len(lines))
    section = lines[tldr_index + 1:next_heading]
    section_offset = tldr_index + 1
    summary_positions = [i for i, line in enumerate(section) if line.lstrip().startswith(">") and not re.match(r"^>\s*(来源|Source)\s*[:：]", line, re.I)]
    picture_positions = [
        i for i, line in enumerate(section)
        if "<whiteboard" in line or re.search(r"!\[[^]]*\]\([^)]+\)", line) or re.search(r"<img\b", line, re.I)
    ]
    tables = markdown_table_info(section)
    source_positions = [i for i, line in enumerate(section) if re.match(r"^>\s*(来源|Source)\s*[:：]", line, re.I)]

    if not summary_positions:
        errors.append((tldr_index + 2, "missing one-sentence/Pyramid opening callout", ""))
    if not picture_positions:
        errors.append((tldr_index + 2, "missing one-picture summary", ""))
    elif len(picture_positions) != 1:
        errors.append((section_offset + picture_positions[1] + 1, "TLDR must contain exactly one picture summary", str(len(picture_positions))))
    if not tables:
        errors.append((tldr_index + 2, "missing TLDR key-question table", ""))
    elif len(tables) != 1:
        errors.append((section_offset + tables[1][0] + 1, "TLDR must contain exactly one key-question table", str(len(tables))))
    if not source_positions:
        errors.append((tldr_index + 2, "missing compact source citation in TLDR", ""))

    if summary_positions and picture_positions and tables:
        if not summary_positions[0] < picture_positions[0] < tables[0][0]:
            errors.append((section_offset + 1, "TLDR order must be summary -> picture -> table", ""))

    expected_headers = [
        [normalize(value) for value in config["tldr"]["default_table_headers"]],
        [normalize(value) for value in config["tldr"]["english_table_headers"]],
    ]
    if tables:
        headers = [normalize(value) for value in tables[0][1]]
        if headers not in expected_headers:
            errors.append((section_offset + tables[0][0] + 1, "unexpected TLDR table headers", " / ".join(tables[0][1])))
        row_count = len(tables[0][2])
        minimum = config["tldr"]["questions_min"]
        maximum = config["tldr"]["questions_max"]
        if not minimum <= row_count <= maximum:
            errors.append((section_offset + tables[0][0] + 1, f"TLDR table must have {minimum}-{maximum} question rows", str(row_count)))
        for row_index, row in enumerate(tables[0][2], section_offset + tables[0][0] + 3):
            for cell_index, cell in enumerate(row, 1):
                if display_width(cell) > 120 or cell.count("<br") >= 3 or cell.count("；") >= 3:
                    warnings.append((row_index, f"table cell {cell_index} may be cramped"))


def xml_children(text):
    sanitized = re.sub(r"&(?!#?[A-Za-z0-9]+;)", "&amp;", text)
    try:
        root = ET.fromstring(f"<document>{sanitized}</document>")
    except ET.ParseError as exc:
        return None, str(exc)
    return list(root), None


def element_text(node):
    return " ".join("".join(node.itertext()).split())


def semantic_claims(ledger):
    if not ledger:
        return []
    return [
        claim for claim in ledger.get("claims", [])
        if claim.get("semantic_direction") and claim.get("display_values") and claim.get("body_section")
    ]


def add_semantic_encoding_checks(text, file_format, config, ledger, errors, warnings):
    claims = semantic_claims(ledger)
    semantic_colors = config.get("semantic_colors", {})
    if file_format != "xml":
        for claim in claims:
            for value in claim.get("display_values", []):
                if value in text:
                    warnings.append((1, f"cannot verify semantic styling for {value} in non-XML draft"))
        return

    nodes, parse_error = xml_children(text)
    if parse_error or not nodes:
        return
    content_nodes = nodes[1:]
    body_start = next((index for index, node in enumerate(content_nodes[1:], 1) if node.tag == "h1"), len(content_nodes))
    body_nodes = content_nodes[body_start:]
    body_text = " ".join(element_text(node) for node in body_nodes)
    spans = [span for node in body_nodes for span in node.iter("span")]

    for claim in claims:
        direction = claim["semantic_direction"]
        mapping = semantic_colors.get(direction)
        if not mapping:
            errors.append((1, "unknown semantic direction in claim ledger", direction))
            continue
        expected = normalize(mapping["body"])
        for value in claim.get("display_values", []):
            if value not in body_text:
                continue
            matching_spans = [span for span in spans if value in element_text(span)]
            if not matching_spans:
                errors.append((1, "directional body value is missing semantic color", f"{value} -> {direction}"))
            elif not any(normalize(span.attrib.get("text-color", "")) == expected for span in matching_spans):
                actual = ", ".join(sorted({span.attrib.get("text-color", "<none>") for span in matching_spans}))
                errors.append((1, "directional body value uses conflicting semantic color", f"{value}: expected {mapping['body']}, got {actual}"))

    signed_values = SIGNED_METRIC_PATTERN.findall(body_text)
    semantic_body_colors = {normalize(mapping.get("body", "")) for mapping in semantic_colors.values()}
    colored_directional_spans = [
        span for span in spans
        if normalize(span.attrib.get("text-color", "")) in semantic_body_colors
        and SIGNED_METRIC_PATTERN.search(element_text(span))
    ]
    if len(signed_values) >= 2 and not colored_directional_spans:
        warnings.append((1, "body contains multiple signed metrics but no semantic numeric encoding; classify business direction before styling"))


def check_xml(text, config, errors, warnings):
    nodes, parse_error = xml_children(text)
    if parse_error:
        errors.append((1, "invalid XML", parse_error))
        return
    if not nodes or nodes[0].tag != "title":
        errors.append((1, "first XML block must be <title>", ""))
        return
    if not normalize(element_text(nodes[0])).startswith("3080 brief"):
        errors.append((1, "title must start with 3080 Brief", element_text(nodes[0])))
    content_nodes = nodes[1:]
    if not content_nodes or content_nodes[0].tag != "h1" or normalize(element_text(content_nodes[0])) != "tldr":
        errors.append((1, "first content block must be <h1>TLDR</h1>", ""))
        return

    section = []
    for node in content_nodes[1:]:
        if node.tag == "h1":
            break
        section.append(node)
    tags = [node.tag for node in section]
    required = ["callout", "whiteboard", "table"]
    for tag in required:
        if tag not in tags:
            errors.append((1, f"missing <{tag}> in TLDR", ""))
        elif tags.count(tag) != 1:
            errors.append((1, f"TLDR must contain exactly one <{tag}>", str(tags.count(tag))))
    if all(tag in tags for tag in required):
        positions = [tags.index(tag) for tag in required]
        if positions != sorted(positions):
            errors.append((1, "TLDR order must be callout -> whiteboard -> table", ""))
    source_nodes = [node for node in section if node.tag in {"blockquote", "p"} and re.match(r"^(来源|Source)\s*[:：]", element_text(node), re.I)]
    if not source_nodes:
        errors.append((1, "missing compact source citation in TLDR", ""))

    table_nodes = [node for node in section if node.tag == "table"]
    if table_nodes:
        rows = table_nodes[0].findall(".//tr")
        if len(rows) - 1 not in range(config["tldr"]["questions_min"], config["tldr"]["questions_max"] + 1):
            errors.append((1, "TLDR table question-row count is outside configured range", str(max(0, len(rows) - 1))))
        headers = [normalize(element_text(cell)) for cell in rows[0] if cell.tag in {"th", "td"}] if rows else []
        expected = [
            [normalize(value) for value in config["tldr"]["default_table_headers"]],
            [normalize(value) for value in config["tldr"]["english_table_headers"]],
        ]
        if headers not in expected:
            errors.append((1, "unexpected TLDR table headers", " / ".join(headers)))
        for row in rows[1:]:
            for cell_index, cell in enumerate(list(row), 1):
                if display_width(element_text(cell)) > 120:
                    warnings.append((1, f"XML table cell {cell_index} may be cramped"))

    forbidden = {normalize(item) for item in config["forbidden_headings"]}
    fragments = [normalize(item) for item in config.get("forbidden_heading_fragments", [])]
    for node in content_nodes:
        if node.tag in {"h1", "h2", "h3"}:
            heading = element_text(node)
            if is_forbidden_heading(heading, forbidden, fragments):
                errors.append((1, "forbidden or audience-labeled heading", heading))


def main():
    parser = argparse.ArgumentParser(description="Structured preflight checks for 3080-brief drafts.")
    parser.add_argument("draft", help="Draft Markdown or Feishu XML file")
    parser.add_argument("--format", choices=["auto", "markdown", "xml"], default="auto")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--claim-ledger", default="", help="Optional claim ledger for deterministic semantic-color checks")
    parser.add_argument("--source-inventory", required=True, help="Source inventory containing the language decision record")
    args = parser.parse_args()

    path = Path(args.draft)
    text = path.read_text(encoding="utf-8")
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    ledger = json.loads(Path(args.claim_ledger).read_text(encoding="utf-8")) if args.claim_ledger else None
    inventory_text = Path(args.source_inventory).read_text(encoding="utf-8")
    errors = []
    warnings = []
    add_pattern_errors(text, config, errors)
    add_expression_warnings(text, config, warnings)

    file_format = args.format
    if file_format == "auto":
        file_format = "xml" if re.search(r"<(title|h1|callout|whiteboard|table)\b", text) else "markdown"
    if file_format == "xml":
        check_xml(text, config, errors, warnings)
    else:
        check_markdown(text, config, errors, warnings)
    add_language_checks(text, inventory_text, config, errors)
    add_semantic_encoding_checks(text, file_format, config, ledger, errors, warnings)

    if re.search(r"(?im)^#{1,6}\s*(附录|Appendix)\b|<h[1-6]>\s*(附录|Appendix)\b", text):
        warnings.append((1, "possible source appendix section; verify it was explicitly requested"))

    print("FAIL" if errors else "PASS")
    for line, label, snippet in errors:
        print(f"ERROR line {line}: {label}{': ' + snippet if snippet else ''}")
    for line, warning in warnings:
        print(f"WARN line {line}: {warning}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
