#!/usr/bin/env python3
"""Shared validation and visual-subset helpers for 3080 document renderers."""

import json


SEMANTIC_DIRECTIONS = {"favorable", "unfavorable", "warning", "neutral", "unknown"}
BLOCK_TYPES = {"paragraph", "bullets", "callout", "table", "figure", "details"}
QUANTITATIVE_TYPES = {"bar", "diverging_bar", "stacked_bar", "dot", "slope", "line", "scatter", "threshold", "range", "distribution", "heatmap", "funnel"}


def plain_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(str(item.get("text", "")) for item in value if isinstance(item, dict))
    return ""


def validate_rich_text(value, label, errors):
    if isinstance(value, str):
        return
    if not isinstance(value, list):
        errors.append(f"{label} must be a string or rich-text spans")
        return
    for index, span in enumerate(value, 1):
        if not isinstance(span, dict) or "text" not in span:
            errors.append(f"{label} span {index} requires text")
            continue
        direction = span.get("semantic_direction")
        if direction and direction not in SEMANTIC_DIRECTIONS:
            errors.append(f"{label} span {index} has unknown semantic direction {direction}")


def validate_document(document, visual_spec=None, config=None):
    errors = []
    warnings = []
    if not str(document.get("title", "")).casefold().startswith("3080 brief"):
        errors.append("title must start with 3080 Brief")
    if not document.get("language"):
        errors.append("language is required")
    if not (document.get("source") or {}).get("title"):
        errors.append("source.title is required")
    lines = (document.get("opening") or {}).get("lines") or []
    if not 2 <= len(lines) <= 4:
        errors.append("opening.lines must contain one judgment plus 1-3 support lines")
    for index, line in enumerate(lines, 1):
        validate_rich_text(line, f"opening line {index}", errors)
    questions = document.get("questions") or []
    if not 3 <= len(questions) <= 5:
        errors.append("questions must contain 3-5 rows")
    for index, question in enumerate(questions, 1):
        for field in ("question", "conclusion", "why"):
            if not question.get(field):
                errors.append(f"question {index} is missing {field}")
            else:
                validate_rich_text(question[field], f"question {index} {field}", errors)

    body_sections = document.get("body") or []
    path_config = (config or {}).get("reading_path_contract", {})
    reading_path = document.get("reading_path")
    if path_config.get("required", True):
        if not isinstance(reading_path, dict):
            errors.append("reading_path is required for every rendered brief")
            reading_path = {}
        expected_version = str(path_config.get("contract_version", "1.0"))
        if str(reading_path.get("contract_version", "")) != expected_version:
            errors.append(f"reading_path.contract_version must be {expected_version}")
        reader_decision = str(reading_path.get("reader_decision", "")).strip()
        minimum_decision = int(path_config.get("minimum_reader_decision_characters", 8))
        if len(reader_decision) < minimum_decision:
            errors.append("reading_path.reader_decision must state the judgment the reader needs to make")
        section_questions = reading_path.get("section_questions") or []
        section_density = reading_path.get("section_density") or []
        if len(section_questions) != len(body_sections):
            errors.append("reading_path.section_questions must map every body section exactly once")
        if len(section_density) != len(body_sections):
            errors.append("reading_path.section_density must map every body section exactly once")
        allowed_density = set(path_config.get("allowed_section_density") or ["light", "balanced", "dense"])
        for index, density in enumerate(section_density, 1):
            if density not in allowed_density:
                errors.append(f"reading_path.section_density {index} has unsupported value {density}")
        minimum_question = int(path_config.get("minimum_section_question_characters", 4))
        for index, question in enumerate(section_questions, 1):
            if len(str(question).strip()) < minimum_question:
                errors.append(f"reading_path.section_questions {index} must name the reader question")

    callout_count = 0
    body_block_types = []
    body_text_length = 0
    for section_index, section in enumerate(body_sections, 1):
        if not section.get("heading") or not isinstance(section.get("blocks"), list):
            errors.append(f"body section {section_index} requires heading and blocks")
            continue
        validate_rich_text(section["heading"], f"body section {section_index} heading", errors)
        blocks = section["blocks"]
        dense_types = set(path_config.get("dense_block_types") or ["table", "figure"])
        dense_positions = [index for index, block in enumerate(blocks) if block.get("type") in dense_types]
        if dense_positions and dense_positions[0] == 0:
            errors.append(f"body section {section_index} must explain the judgment before its first table or figure")
        if blocks and path_config.get("require_takeaway_before_dense_evidence", True):
            allowed_openings = set(path_config.get("allowed_section_opening_types") or ["paragraph", "bullets", "callout"])
            if blocks[0].get("type") not in allowed_openings:
                errors.append(f"body section {section_index} must open with a reader-facing takeaway")
        maximum_dense = int(path_config.get("maximum_consecutive_dense_blocks", 1))
        dense_run = 0
        for block in blocks:
            dense_run = dense_run + 1 if block.get("type") in dense_types else 0
            if dense_run > maximum_dense:
                errors.append(
                    f"body section {section_index} has consecutive dense evidence without an explanatory bridge"
                )
                break
        for block_index, block in enumerate(blocks, 1):
            block_type = block.get("type")
            body_block_types.append(block_type)
            if block_type not in BLOCK_TYPES:
                errors.append(f"body section {section_index} block {block_index} has unsupported type {block_type}")
                continue
            if block_type == "paragraph":
                validate_rich_text(block.get("text", ""), f"body paragraph {section_index}.{block_index}", errors)
                body_text_length += len(plain_text(block.get("text", "")))
            elif block_type == "bullets":
                if not block.get("items"):
                    errors.append(f"body bullets {section_index}.{block_index} require items")
                for item_index, item in enumerate(block.get("items") or [], 1):
                    validate_rich_text(item, f"body bullet {section_index}.{block_index}.{item_index}", errors)
                body_text_length += sum(len(plain_text(item)) for item in block.get("items") or [])
            elif block_type == "callout":
                callout_count += 1
                if block.get("tone", "neutral") not in SEMANTIC_DIRECTIONS:
                    errors.append(f"body callout {section_index}.{block_index} has unknown tone")
                if block.get("title"):
                    validate_rich_text(block["title"], f"body callout title {section_index}.{block_index}", errors)
                validate_rich_text(block.get("text", ""), f"body callout {section_index}.{block_index}", errors)
            elif block_type == "table":
                headers = block.get("headers") or []
                rows = block.get("rows") or []
                if not headers or not rows or any(len(row) != len(headers) for row in rows):
                    errors.append(f"body table {section_index}.{block_index} requires aligned headers and rows")
                for cell_index, cell in enumerate(headers, 1):
                    validate_rich_text(cell, f"body table header {section_index}.{block_index}.{cell_index}", errors)
                for row_index, row in enumerate(rows, 1):
                    for cell_index, cell in enumerate(row, 1):
                        validate_rich_text(cell, f"body table cell {section_index}.{block_index}.{row_index}.{cell_index}", errors)
                widths = block.get("widths") or []
                if widths and len(widths) != len(headers):
                    errors.append(f"body table {section_index}.{block_index} widths must match headers")
            elif block_type == "figure":
                if not block.get("title") or not block.get("alt_text"):
                    errors.append(f"body figure {section_index}.{block_index} requires a judgment title and alt_text")
                if block.get("title"):
                    validate_rich_text(block["title"], f"body figure title {section_index}.{block_index}", errors)
                if block.get("note"):
                    validate_rich_text(block["note"], f"body figure note {section_index}.{block_index}", errors)
                if bool(block.get("visual_block_ids")) == bool(block.get("svg")):
                    errors.append(f"body figure {section_index}.{block_index} requires exactly one of visual_block_ids or svg")
            elif block_type == "details":
                if block.get("priority") != "P2":
                    errors.append(f"body details {section_index}.{block_index} are allowed only for P2")
                validate_rich_text(block.get("summary", ""), f"body details summary {section_index}.{block_index}", errors)
                for paragraph_index, paragraph in enumerate(block.get("paragraphs") or [], 1):
                    validate_rich_text(paragraph, f"body details paragraph {section_index}.{block_index}.{paragraph_index}", errors)

    max_callouts = int((config or {}).get("feishu_render", {}).get("max_body_callouts", 1))
    if callout_count > max_callouts:
        errors.append(f"body uses {callout_count} callouts; maximum is {max_callouts}")
    if body_block_types and set(body_block_types) <= {"table", "callout"}:
        errors.append("body cannot consist only of tables and callouts")
    dense_types = set(path_config.get("dense_block_types") or ["table", "figure"])
    if any(first in dense_types and second in dense_types for first, second in zip(body_block_types, body_block_types[1:])):
        errors.append("body cannot contain consecutive dense evidence blocks without explanatory prose")

    if visual_spec:
        if str(document.get("language", "")).casefold() != str(visual_spec.get("language", "")).casefold():
            errors.append("brief language must match visual spec language")
        known_blocks = {block.get("id") for block in visual_spec.get("blocks", [])}
        body_visuals = []
        for section in document.get("body") or []:
            for block in section.get("blocks") or []:
                if block.get("type") == "figure":
                    body_visuals.append(block)
                    for block_id in block.get("visual_block_ids") or []:
                        if block_id not in known_blocks:
                            errors.append(f"body figure references unknown visual block {block_id}")
        quantitative = sum(block.get("type") in QUANTITATIVE_TYPES for block in visual_spec.get("blocks", []))
        threshold = int((config or {}).get("feishu_render", {}).get("body_visualization_text_threshold", 1600))
        if quantitative >= 2 and body_text_length >= threshold and not body_visuals:
            errors.append("long quantitative body requires at least one source-grounded body figure")
        elif quantitative >= 2 and body_text_length >= threshold // 2 and not body_visuals:
            warnings.append("quantitative body may benefit from a source-grounded body figure")
    if errors:
        raise ValueError("; ".join(errors))
    return warnings


def subset_visual_spec(visual_spec, block_ids, title, alt_text):
    wanted = set(block_ids)
    blocks = [block for block in visual_spec.get("blocks", []) if block.get("id") in wanted]
    missing = wanted - {block.get("id") for block in blocks}
    if missing:
        raise ValueError(f"body figure references unknown visual blocks: {', '.join(sorted(missing))}")
    subset = json.loads(json.dumps(visual_spec))
    subset["title"] = plain_text(title)
    subset["reading_path"] = alt_text
    subset["alt_text"] = alt_text
    subset["blocks"] = blocks
    subset["composition"] = "comparison_grid" if len(blocks) > 1 else "vertical_story"
    subset["body_figure"] = True
    return subset
