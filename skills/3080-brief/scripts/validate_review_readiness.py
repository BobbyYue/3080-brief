#!/usr/bin/env python3
"""Fail closed before spending independent 3080 review rounds."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_file(value: str, label: str, errors: list[str]) -> Path | None:
    path = Path(value)
    if not path.is_file():
        errors.append(f"missing {label}: {path}")
        return None
    if not path.read_bytes().strip():
        errors.append(f"empty {label}: {path}")
        return None
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate 3080 review inputs before launching reviewers.")
    parser.add_argument("--source-snapshot", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--claim-ledger", required=True)
    parser.add_argument("--tldr", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--draft", required=True)
    parser.add_argument("--source-outline", required=True)
    parser.add_argument("--source-excerpts", required=True)
    parser.add_argument("--validation-notes", required=True)
    parser.add_argument("--document-preview", required=True)
    parser.add_argument("--visual-spec", default="")
    parser.add_argument("--html-design-plan", default="")
    parser.add_argument("--visual-preview", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    errors: list[str] = []
    required = {
        "source_snapshot": args.source_snapshot,
        "inventory": args.inventory,
        "claim_ledger": args.claim_ledger,
        "tldr": args.tldr,
        "body": args.body,
        "draft": args.draft,
        "source_outline": args.source_outline,
        "source_excerpts": args.source_excerpts,
        "validation_notes": args.validation_notes,
        "document_preview": args.document_preview,
    }
    optional = {
        "visual_spec": args.visual_spec,
        "html_design_plan": args.html_design_plan,
        "visual_preview": args.visual_preview,
    }
    paths = {key: require_file(value, key, errors) for key, value in required.items()}
    for key, value in optional.items():
        if value:
            paths[key] = require_file(value, key, errors)

    if args.visual_spec and not args.visual_preview:
        errors.append("visual_spec requires visual_preview")

    p01_ids: list[str] = []
    ledger_path = paths.get("claim_ledger")
    if ledger_path:
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"invalid claim_ledger: {exc}")
        else:
            claims = ledger.get("claims")
            if not isinstance(claims, list) or not claims:
                errors.append("claim_ledger has no claims")
            else:
                for claim in claims:
                    if not isinstance(claim, dict) or claim.get("appendix") is True:
                        continue
                    if claim.get("priority") not in {"P0", "P1"}:
                        continue
                    claim_id = str(claim.get("id", "")).strip()
                    p01_ids.append(claim_id)
                    for field in ("id", "source_location", "source_identity", "evidence_ceiling", "output_assertion"):
                        if not str(claim.get(field, "")).strip():
                            errors.append(f"{claim_id or '<unknown>'} missing {field}")
                    if not isinstance(claim.get("protected_relations"), list) or not claim["protected_relations"]:
                        errors.append(f"{claim_id or '<unknown>'} missing protected_relations")
                if not p01_ids:
                    errors.append("claim_ledger has no non-appendix P0/P1 claims")

    file_hashes = {key: digest(path) for key, path in paths.items() if path is not None}
    receipt = {
        "schema_version": 1,
        "status": "ready" if not errors else "blocked",
        "files": file_hashes,
        "p01_claim_ids": p01_ids,
        "errors": errors,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        print("FAIL review readiness: " + "; ".join(errors))
        return 1
    print(f"PASS review readiness | p01={len(p01_ids)} | receipt={output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
