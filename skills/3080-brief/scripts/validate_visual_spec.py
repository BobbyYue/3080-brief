#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

from theme_registry import resolve_visual_theme


SKILL_DIR = Path(__file__).resolve().parents[1]
ALLOWED_TYPES = {
    "bar", "diverging_bar", "stacked_bar", "dot", "slope", "line", "scatter",
    "threshold", "range", "distribution", "matrix", "heatmap", "funnel",
    "timeline", "flow", "sequence", "hierarchy", "network", "annotation",
}
QUANTITATIVE_TYPES = {
    "bar", "diverging_bar", "stacked_bar", "dot", "slope", "line", "scatter",
    "threshold", "range", "distribution", "heatmap", "funnel",
}
ALLOWED_TARGETS = {"feishu", "html", "word", "markdown", "portable"}
ALLOWED_COMPOSITIONS = {"vertical_story", "stage_story", "anchor_support", "comparison_grid"}


def has_visible_payload(block):
    block_type = block.get("type")
    if block_type == "annotation":
        return bool(str(block.get("note", "")).strip() or block.get("items") or block.get("cells"))
    if block_type in {"matrix", "heatmap"}:
        return bool(block.get("rows") and block.get("columns") and block.get("cells"))
    if block_type == "threshold":
        return all(isinstance(block.get(field), (int, float)) for field in ("minimum", "maximum", "threshold", "value"))
    return bool(block.get("items"))


def main():
    parser = argparse.ArgumentParser(description="Cross-check 3080 visual_spec.json against claim_ledger.json.")
    parser.add_argument("visual_spec")
    parser.add_argument("claim_ledger")
    parser.add_argument("--config", default=str(SKILL_DIR / "config" / "3080-brief.json"))
    args = parser.parse_args()

    spec = json.loads(Path(args.visual_spec).read_text(encoding="utf-8"))
    ledger = json.loads(Path(args.claim_ledger).read_text(encoding="utf-8"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    errors = []
    semantic_colors = config.get("semantic_colors", {})
    semantic_directions = set(semantic_colors)
    for direction, mapping in semantic_colors.items():
        if not all(mapping.get(key) for key in ("body", "svg", "svg_tint")):
            errors.append(f"semantic color {direction} is missing body/svg/svg_tint mapping")

    for field in ("title", "language", "style", "style_rationale", "reading_path", "composition", "blocks"):
        if not spec.get(field):
            errors.append(f"visual spec missing required field: {field}")
    if spec.get("style_rationale") and len(str(spec["style_rationale"]).strip()) < 8:
        errors.append("visual spec style_rationale must explain content fit")
    render_target = spec.get("render_target", "portable")
    if render_target not in ALLOWED_TARGETS:
        errors.append(f"visual spec uses unknown render_target: {render_target}")
    if render_target == "html":
        if not spec.get("alt_text"):
            errors.append("HTML visual spec requires conclusion-bearing alt_text")
        if float(spec.get("coverage_percent", 0)) < float(config.get("coverage", {}).get("minimum_percent", 80)):
            errors.append("HTML one-picture visual must declare configured minimum coverage_percent")
    composition = spec.get("composition")
    if composition and composition not in ALLOWED_COMPOSITIONS:
        errors.append(f"visual spec uses unsupported composition: {composition}")
    expected_language = ledger.get("source", {}).get("output_language")
    if expected_language and str(spec.get("language", "")).casefold() != str(expected_language).casefold():
        errors.append(f"visual spec language {spec.get('language', '<missing>')} does not match output language {expected_language}")
    try:
        resolve_visual_theme(spec, config)
    except ValueError as exc:
        errors.append(str(exc))

    claims = {claim.get("id"): claim for claim in ledger.get("claims", []) if claim.get("id")}
    block_ids = set()
    block_claims = {}
    block_semantics = {}
    explicit_roles = []
    for block in spec.get("blocks", []):
        block_id = block.get("id")
        if not block_id or block_id in block_ids:
            errors.append(f"duplicate or missing visual block id: {block_id or '<empty>'}")
            continue
        block_ids.add(block_id)
        if not block.get("title") or not block.get("type"):
            errors.append(f"{block_id}: missing title or type")
        block_type = block.get("type")
        if block_type and block_type not in ALLOWED_TYPES:
            errors.append(f"{block_id}: unsupported visual type {block_type}")
        if block_type in ALLOWED_TYPES and not has_visible_payload(block):
            errors.append(f"{block_id}: block has a title but no visible payload")
        if block.get("visual_role"):
            explicit_roles.append((block_id, block.get("visual_role")))
        block_target = block.get("render_target", render_target)
        if block_target not in ALLOWED_TARGETS:
            errors.append(f"{block_id}: unknown render_target {block_target}")
        interaction = block.get("interaction", "none")
        if interaction != "none" and not block.get("fallback"):
            errors.append(f"{block_id}: interactive visual requires a visible fallback")
        if block_target == "html" and not (block.get("alt_text") or spec.get("alt_text")):
            errors.append(f"{block_id}: HTML visual requires alt text")
        if block_type in QUANTITATIVE_TYPES and not block.get("metric_scope"):
            errors.append(f"{block_id}: quantitative visual requires metric_scope")
        if block_type == "scatter":
            for index, item in enumerate(block.get("items") or [], 1):
                if not isinstance(item.get("x"), (int, float)) or not isinstance(item.get("y"), (int, float)):
                    errors.append(f"{block_id}: scatter item {index} requires source-backed numeric x and y")
        if block_type in {"flow", "sequence", "timeline", "hierarchy", "network"}:
            for index, item in enumerate(block.get("items") or [], 1):
                if not str(item.get("label", "")).strip():
                    errors.append(f"{block_id}: sequence item {index} requires a visible label")
        if block_type == "annotation":
            for index, item in enumerate(block.get("items") or [], 1):
                if not str(item.get("label", "")).strip():
                    errors.append(f"{block_id}: annotation item {index} requires a visible label")
                if item.get("display") in (None, "") and item.get("value") is None:
                    errors.append(f"{block_id}: annotation item {index} requires a visible value")
        if block_type == "heatmap":
            rows = set(block.get("rows") or [])
            columns = set(block.get("columns") or [])
            cells = block.get("cells") or []
            seen_rows = {cell.get("row") for cell in cells}
            seen_columns = {cell.get("column") for cell in cells}
            for row in sorted(rows - seen_rows):
                errors.append(f"{block_id}: heatmap row {row} has no source data")
            for column in sorted(columns - seen_columns):
                errors.append(f"{block_id}: heatmap column {column} has no source data")
        claim_ids = block.get("claim_ids") or []
        if not claim_ids:
            errors.append(f"{block_id}: claim_ids cannot be empty")
        block_claims[block_id] = set(claim_ids)
        declared_semantics = set()
        if block.get("semantic_direction"):
            declared_semantics.add(block["semantic_direction"])
        for item in (block.get("items") or []) + (block.get("cells") or []):
            if item.get("semantic_direction"):
                declared_semantics.add(item["semantic_direction"])
        unknown_semantics = declared_semantics - semantic_directions
        if unknown_semantics:
            errors.append(f"{block_id}: unknown semantic direction(s): {', '.join(sorted(unknown_semantics))}")
        block_semantics[block_id] = declared_semantics
        for claim_id in claim_ids:
            if claim_id not in claims:
                errors.append(f"{block_id}: unknown claim id {claim_id}")

    if explicit_roles and sum(role == "anchor" for _, role in explicit_roles) != 1:
        errors.append("visual spec with explicit roles must contain exactly one anchor block")
    if render_target == "html" and sum(role == "anchor" for _, role in explicit_roles) != 1:
        errors.append("HTML one-picture visual must declare exactly one anchor block")
    if render_target == "html" and len(explicit_roles) != len(spec.get("blocks", [])):
        errors.append("every HTML one-picture block must declare anchor, support, or caveat role")

    stage_count = sum(block.get("type") in {"flow", "sequence", "timeline"} for block in spec.get("blocks", []))
    if composition == "stage_story" and not 3 <= stage_count <= 4:
        errors.append("stage_story composition requires 3-4 flow, sequence, or timeline stage blocks")

    for claim_id, claim in claims.items():
        if claim.get("appendix", False) or claim.get("board_status") == "omitted":
            continue
        block_id = claim.get("board_block")
        if not block_id:
            errors.append(f"{claim_id}: covered/partial claim is missing board_block")
        elif block_id not in block_ids:
            errors.append(f"{claim_id}: board_block {block_id} does not exist in visual spec")
        elif claim_id not in block_claims.get(block_id, set()):
            errors.append(f"{claim_id}: visual block {block_id} does not declare this claim id")
        semantic_direction = claim.get("semantic_direction")
        if semantic_direction and semantic_direction not in semantic_directions:
            errors.append(f"{claim_id}: unknown semantic direction {semantic_direction}")
        elif semantic_direction and semantic_direction not in block_semantics.get(block_id, set()):
            errors.append(f"{claim_id}: visual block {block_id} does not preserve semantic direction {semantic_direction}")

    print("FAIL" if errors else "PASS")
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
