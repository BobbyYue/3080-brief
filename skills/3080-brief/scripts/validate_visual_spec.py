#!/usr/bin/env python3
import argparse
import json
import re
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
CAUSAL_TITLE_PATTERN = re.compile(
    r"\b(?:causes?|caused by|drives? (?:growth|decline|outcomes?|results?)|shapes? outcomes?|results? in)\b|"
    r"(?:导致|造成|驱动(?:增长|下降|结果)|决定了?结果)",
    re.I,
)


def normalized_scope(scope):
    return tuple(str(scope.get(field, "")).strip().casefold() for field in ("metric", "unit", "period", "denominator"))


def claim_ceiling_rank(claim):
    order = ["unknown", "reported", "observed", "suggestive", "supported", "demonstrated", "causal"]
    value = claim.get("evidence_ceiling", "unknown")
    return order.index(value) if value in order else 0


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
    if CAUSAL_TITLE_PATTERN.search(str(spec.get("title", ""))):
        mapped_claims = [claims.get(claim_id) for block in spec.get("blocks", []) for claim_id in block.get("claim_ids", [])]
        mapped_claims = [claim for claim in mapped_claims if claim]
        if mapped_claims and max(claim_ceiling_rank(claim) for claim in mapped_claims) < claim_ceiling_rank({"evidence_ceiling": "causal"}):
            errors.append("visual title uses causal language but mapped source claims do not have a causal evidence ceiling")
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
        if block_type in QUANTITATIVE_TYPES and len(block.get("items") or []) > 1:
            item_scopes = []
            scoped_items = []
            for index, item in enumerate(block.get("items") or [], 1):
                item_scope = item.get("metric_scope")
                if not isinstance(item_scope, dict):
                    errors.append(f"{block_id}: multi-item quantitative visual requires item-level metric_scope for item {index}")
                    continue
                missing_scope = [field for field in ("metric", "unit", "period", "denominator", "segment") if not str(item_scope.get(field, "")).strip()]
                if missing_scope:
                    errors.append(f"{block_id}: item {index} metric_scope is missing {', '.join(missing_scope)}")
                    continue
                normalized = normalized_scope(item_scope)
                item_scopes.append(normalized)
                scoped_items.append((item, normalized))
            grouped_stacked = block_type == "stacked_bar" and scoped_items and all(str(item.get("series", "")).strip() for item, _ in scoped_items)
            if grouped_stacked:
                shared_axis = {scope[:3] for _, scope in scoped_items}
                denominators_by_group = {}
                totals_by_group = {}
                for item, scope in scoped_items:
                    group = str(item["series"])
                    denominators_by_group.setdefault(group, set()).add(scope[3])
                    totals_by_group[group] = totals_by_group.get(group, 0.0) + float(item.get("value", 0))
                if len(shared_axis) > 1 or any(len(values) > 1 for values in denominators_by_group.values()):
                    errors.append(f"{block_id}: grouped stacked bars must share metric/unit/period and one denominator within each row")
                expected_total = float(block.get("maximum", 100))
                if any(abs(total - expected_total) > 0.001 for total in totals_by_group.values()):
                    errors.append(f"{block_id}: each grouped stacked-bar row must total the declared maximum")
            elif len(set(item_scopes)) > 1:
                errors.append(f"{block_id}: one quantitative axis mixes different metrics, units, periods, or denominators; split into separate blocks")
        if CAUSAL_TITLE_PATTERN.search(str(block.get("title", ""))):
            block_claims_for_ceiling = [claims.get(claim_id) for claim_id in block.get("claim_ids", []) if claims.get(claim_id)]
            if block_claims_for_ceiling and max(claim_ceiling_rank(claim) for claim in block_claims_for_ceiling) < claim_ceiling_rank({"evidence_ceiling": "causal"}):
                errors.append(f"{block_id}: visual title uses causal language above its mapped evidence ceiling")
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

    role_counts = {role: sum(value == role for _, value in explicit_roles) for role in ("anchor", "support", "caveat")}
    if composition == "anchor_support":
        if role_counts["anchor"] != 1:
            errors.append("anchor_support requires exactly one anchor")
        if role_counts["support"] + role_counts["caveat"] < 1:
            errors.append("anchor_support requires at least one supporting or caveat block")
        if len(explicit_roles) != len(spec.get("blocks", [])):
            errors.append("anchor_support requires an explicit visual_role on every block")
    if composition == "comparison_grid":
        comparison_count = len(spec.get("blocks", [])) - role_counts["caveat"]
        if comparison_count < 2:
            errors.append("comparison_grid requires at least two comparison blocks")
        if len(explicit_roles) != len(spec.get("blocks", [])):
            errors.append("comparison_grid requires an explicit visual_role on every block")

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
