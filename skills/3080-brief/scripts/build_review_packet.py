#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


CONFIG = json.loads((Path(__file__).resolve().parents[1] / "config" / "3080-brief.json").read_text(encoding="utf-8"))
ROLE_NAMES = CONFIG["review_roles"]

ROLE_GATES = {
    "reader": [
        "The opening produces a useful judgment within 30 seconds without a fixed phrase template.",
        "The full rendered draft is readable, source-fit, and follows a coherent reasoning path.",
        "The title, TLDR, table, body, and visual use the declared output language; conversation language is not treated as an override.",
        "A capable newcomer can restate the problem, solution, memorable example, and next action when source-backed.",
        "The TLDR table answers real reader questions and does not become a terminology dump.",
        "Decision-relevant directional values are understandable through accurate semantic color plus a redundant sign, arrow, label, or wording cue.",
    ],
    "source": [
        "Every P0/P1 conclusion, metric, risk, and action is traceable to the supplied source outline or excerpt.",
        "The declared output language matches the source primary language unless the packet contains an explicit user instruction requesting another language.",
        "The claim ledger covers valuable non-appendix source information and excludes appendix material.",
        "No causal, quantitative, or recommendation claim is stronger than its evidence.",
        "Missing denominators, periods, samples, conflicts, or inferences are visible and handled safely.",
    ],
    "visual": [
        "The visual spec maps every board block to source claim IDs and value-weighted board coverage is at least 80%.",
        "The visual language matches the declared document output language, except for source-native proper nouns and necessary terms.",
        "The preview uses content-fit visual encoding rather than boxes plus prose when chartable data exists.",
        "The chosen style fits the source and is not banned; image2 is not an evidence carrier.",
        "The rendered board has a clear reading path and no visible clipping, overlap, overflow, or misleading precision.",
        "The body and whiteboard use the same source-grounded semantic mapping; mathematical sign alone does not determine favorable or unfavorable color.",
    ],
}


def read_optional(value):
    if not value:
        return ""
    candidate = Path(value)
    if candidate.exists():
        return candidate.read_text(encoding="utf-8").strip()
    return value.strip()


def digest(path):
    if not path:
        return None
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return None
    return hashlib.sha256(candidate.read_bytes()).hexdigest()


def packet_for(role, args):
    hashes = {
        "inventory": digest(args.inventory),
        "claim_ledger": digest(args.claim_ledger),
        "tldr": digest(args.tldr),
        "body": digest(args.body),
        "draft": digest(args.draft),
        "visual_spec": digest(args.visual_spec),
        "whiteboard_preview": digest(args.whiteboard_preview),
        "document_preview": digest(args.document_preview),
    }
    hashes = {k: v for k, v in hashes.items() if v}
    artifact_set_id = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode("utf-8")).hexdigest()
    gates = "\n".join(f"- {gate}" for gate in ROLE_GATES[role])

    common = f"""# 3080 Brief Independent Review Packet

## Review Identity

- Role key: `{role}`
- Reviewer role: {ROLE_NAMES[role]}
- Review round: {args.round}
- Artifact set ID: `{artifact_set_id}`
- Isolation: do not request, infer, or reference another reviewer's opinion.

## Artifact Hashes

```json
{json.dumps(hashes, ensure_ascii=False, indent=2)}
```

## User Request

{read_optional(args.user_request) or '- Not provided separately.'}

## Source Inventory

{read_optional(args.inventory)}

## Claim Ledger

{read_optional(args.claim_ledger)}

## Draft TLDR

{read_optional(args.tldr)}

## Role-Specific PASS Gates

{gates}
"""

    if role == "reader":
        evidence = f"""
## Full Reader-Facing Draft

{read_optional(args.draft) or read_optional(args.body)}

## Rendered Document

- Preview/path: {args.document_preview or 'Not provided.'}
"""
    elif role == "source":
        evidence = f"""
## Independent Source Evidence

### Non-Appendix Source Outline

{read_optional(args.source_outline) or '- Not provided; FAIL if independent coverage cannot be verified.'}

### P0/P1 Source Excerpts

{read_optional(args.source_excerpts) or '- Not provided; use source locations in the claim ledger and report any verification limit.'}

## Draft Body Mapping

{read_optional(args.body)}
"""
    else:
        evidence = f"""
## Visual Spec

{read_optional(args.visual_spec) or '- Not provided; FAIL if claim-to-block mapping cannot be verified.'}

## Whiteboard Evidence

- Preview/path: {args.whiteboard_preview or 'Not provided.'}

{read_optional(args.whiteboard_summary) or '- Validation summary not provided.'}

## Body Visual Evidence

- Rendered document preview/path: {args.document_preview or 'Not provided; FAIL semantic-color consistency when it cannot be verified.'}
- Use the claim ledger's `semantic_direction` and `display_values` as the cross-artifact comparison map.
"""

    output_contract = f"""
## Required Output

Return JSON only:

```json
{{
  "reviewer_role": "{role}",
  "artifact_set_id": "{artifact_set_id}",
  "review_round": {args.round},
  "verdict": "PASS or FAIL",
  "checks": [{{"name": "gate", "result": "PASS or FAIL", "reason": "concise evidence"}}],
  "blocking_issues": [],
  "unsupported_claims": [],
  "missing_coverage": [],
  "required_fixes": []
}}
```

Return `FAIL` when required evidence is absent or a gate cannot be verified. Do not rewrite the brief.
"""
    return common + evidence + output_contract, artifact_set_id


def main():
    parser = argparse.ArgumentParser(description="Build role-specific, hash-locked 3080 reviewer packets.")
    parser.add_argument("--role", choices=["reader", "source", "visual", "all"], default="all")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--claim-ledger", required=True)
    parser.add_argument("--tldr", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--draft", default="")
    parser.add_argument("--user-request", default="")
    parser.add_argument("--source-outline", default="")
    parser.add_argument("--source-excerpts", default="")
    parser.add_argument("--visual-spec", default="")
    parser.add_argument("--whiteboard-summary", default="")
    parser.add_argument("--whiteboard-preview", default="")
    parser.add_argument("--document-preview", default="")
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--output", required=True, help="Output file for one role, or directory for --role all")
    args = parser.parse_args()

    roles = list(ROLE_NAMES) if args.role == "all" else [args.role]
    output = Path(args.output)
    if len(roles) > 1:
        output.mkdir(parents=True, exist_ok=True)

    artifact_ids = set()
    for role in roles:
        packet, artifact_set_id = packet_for(role, args)
        artifact_ids.add(artifact_set_id)
        target = output / f"review_packet_{role}.md" if len(roles) > 1 else output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(packet, encoding="utf-8")
        print(target)
    if len(artifact_ids) != 1:
        raise SystemExit("review packets were not built from one artifact set")


if __name__ == "__main__":
    main()
