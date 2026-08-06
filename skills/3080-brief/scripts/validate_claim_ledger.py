#!/usr/bin/env python3
"""Validate the source-faithful claim-ledger runtime contract."""

import argparse
import json
import re
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config" / "3080-brief.json"
REQUIRED_RELATION_FIELDS = ("subject", "predicate", "object", "scope", "time_status", "qualifiers")
SOURCE_IDENTITIES = {"source_fact", "source_author_claim", "source_self_report", "agent_inference", "unknown"}


def load_json(path, label, errors):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} is unavailable or invalid JSON: {exc}")
        return {}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate(ledger, config):
    errors = []
    source = ledger.get("source")
    if not isinstance(source, dict):
        return ["source must be an object"]

    for field in ("title", "location", "language", "output_language", "output_language_basis"):
        if not nonempty(source.get(field)):
            errors.append(f"source.{field} must be a non-empty string")

    sufficiency = source.get("material_sufficiency")
    if not isinstance(sufficiency, dict):
        errors.append("source.material_sufficiency must be an object")
    else:
        status = sufficiency.get("status")
        handling = sufficiency.get("handling")
        allowed = {
            "sufficient": {"proceed"},
            "thin": {"shorten", "clarify"},
            "blocked": {"clarify"},
        }
        if status not in allowed:
            errors.append(f"invalid material sufficiency status: {status!r}")
        elif handling not in allowed[status]:
            errors.append(f"material sufficiency {status!r} cannot use handling {handling!r}")
        if not nonempty(sufficiency.get("rationale")):
            errors.append("material sufficiency requires a non-empty rationale")
        if status == "blocked":
            errors.append("material sufficiency is blocked; clarify before final drafting")

    expression = config.get("expression_quality", {})
    strength_order = expression.get(
        "claim_strength_order",
        ["unknown", "reported", "observed", "suggestive", "supported", "demonstrated", "causal"],
    )
    strength_rank = {value: index for index, value in enumerate(strength_order)}
    required_priorities = set(expression.get("required_relation_priorities", ["P0", "P1"]))

    claims = ledger.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty array")
        return errors

    ids = []
    for index, claim in enumerate(claims, 1):
        prefix = f"claim[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix} must be an object")
            continue
        claim_id = claim.get("id")
        ids.append(claim_id)
        if not isinstance(claim_id, str) or not re.fullmatch(r"C[0-9]{2,}", claim_id):
            errors.append(f"{prefix}.id must match C followed by at least two digits")
        for field in ("claim", "source_location"):
            if not nonempty(claim.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

        priority = claim.get("priority")
        requires_contract = priority in required_priorities and not claim.get("appendix", False)
        if not requires_contract:
            continue

        identity = claim.get("source_identity")
        if identity not in SOURCE_IDENTITIES:
            errors.append(f"{prefix}.source_identity is missing or invalid")
        if priority == "P0" and identity == "unknown":
            errors.append(f"{prefix} is P0 but source identity is unknown")

        ceiling = claim.get("evidence_ceiling")
        assertion = claim.get("output_assertion")
        if ceiling not in strength_rank:
            errors.append(f"{prefix}.evidence_ceiling is missing or invalid")
        if assertion not in strength_rank:
            errors.append(f"{prefix}.output_assertion is missing or invalid")
        if ceiling in strength_rank and assertion in strength_rank and strength_rank[assertion] > strength_rank[ceiling]:
            errors.append(f"{prefix} output assertion {assertion!r} exceeds evidence ceiling {ceiling!r}")

        inference = claim.get("inference", False)
        if identity == "agent_inference" and inference is not True:
            errors.append(f"{prefix} uses agent_inference but inference is not true")
        if inference is True and identity != "agent_inference":
            errors.append(f"{prefix} is marked inference but source_identity is not agent_inference")
        if identity == "agent_inference" and assertion in strength_rank and strength_rank[assertion] > strength_rank["suggestive"]:
            errors.append(f"{prefix} agent inference cannot exceed suggestive output assertion")

        relations = claim.get("protected_relations")
        if not isinstance(relations, list) or not relations:
            errors.append(f"{prefix}.protected_relations must contain at least one relation")
            continue
        for relation_index, relation in enumerate(relations, 1):
            relation_prefix = f"{prefix}.protected_relations[{relation_index}]"
            if not isinstance(relation, dict):
                errors.append(f"{relation_prefix} must be an object")
                continue
            for field in REQUIRED_RELATION_FIELDS:
                if not nonempty(relation.get(field)):
                    errors.append(f"{relation_prefix}.{field} must be a non-empty string")
            values = relation.get("values", [])
            if not isinstance(values, list) or any(not nonempty(value) for value in values):
                errors.append(f"{relation_prefix}.values must be an array of non-empty strings")
            elif len(values) != len(set(values)):
                errors.append(f"{relation_prefix}.values must be unique")

    present_ids = [claim_id for claim_id in ids if claim_id]
    if len(present_ids) != len(set(present_ids)):
        errors.append("claim IDs must be unique")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("claim_ledger", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    load_errors = []
    ledger = load_json(args.claim_ledger, "claim ledger", load_errors)
    config = load_json(args.config, "config", load_errors)
    errors = load_errors + (validate(ledger, config) if not load_errors else [])
    result = {"status": "FAIL" if errors else "PASS", "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("FAIL")
        for error in errors:
            print(f"ERROR {error}")
    else:
        print("CLAIM LEDGER PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
