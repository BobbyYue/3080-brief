#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


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

    for field in ("title", "language", "style", "reading_path", "blocks"):
        if not spec.get(field):
            errors.append(f"visual spec missing required field: {field}")
    expected_language = ledger.get("source", {}).get("output_language")
    if expected_language and str(spec.get("language", "")).casefold() != str(expected_language).casefold():
        errors.append(f"visual spec language {spec.get('language', '<missing>')} does not match output language {expected_language}")
    canonical_style = lambda value: re.sub(r"[^a-z0-9]+", "", str(value).casefold())
    banned = {canonical_style(name) for name in config["banned_whiteboard_styles"]}
    if canonical_style(spec.get("style", "")) in banned:
        errors.append(f"visual spec uses banned style: {spec.get('style')}")

    claims = {claim.get("id"): claim for claim in ledger.get("claims", []) if claim.get("id")}
    block_ids = set()
    block_claims = {}
    block_semantics = {}
    for block in spec.get("blocks", []):
        block_id = block.get("id")
        if not block_id or block_id in block_ids:
            errors.append(f"duplicate or missing visual block id: {block_id or '<empty>'}")
            continue
        block_ids.add(block_id)
        if not block.get("title") or not block.get("type"):
            errors.append(f"{block_id}: missing title or type")
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
