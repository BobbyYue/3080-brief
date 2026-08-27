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
        "The target reader can access relevant information, find the decision spine, restate the meaning accurately, and use it; revise sentence or paragraph patterns only when they obstruct that path.",
        "Every value-bearing title, heading, and lead identifies the actual object plus a source-supported action, change, or result instead of relying on method labels or generic benefit language.",
        "Expression edits are minimal and contextual; legitimate technical terms, uncertainty, passive voice, neutral tone, and punctuation are not penalized in isolation.",
        "The title, TLDR, table, body, and visual use the declared output language; conversation language is not treated as an override.",
        "A capable newcomer can restate the problem, solution, memorable example, and next action when source-backed.",
        "The TLDR table answers real reader questions and does not become a terminology dump.",
        "The body uses prose, lists, tables, and figures according to the content; it is neither a text wall nor a sequence of tables/cards without explanation.",
        "Decision-relevant directional values are understandable through accurate semantic color plus a redundant sign, arrow, label, or wording cue.",
        "Critical conclusions, evidence, risks, and actions remain understandable without hover, animation, filtering, or opening a collapsed block.",
    ],
    "source": [
        "Every P0/P1 conclusion, metric, risk, and action is traceable to the supplied source outline or excerpt.",
        "Every non-appendix P0/P1 protected relation preserves subject, predicate, object, scope, time/status, qualifiers, and numeric attachment.",
        "Each output assertion stays at or below its evidence ceiling; source facts, author claims, self-reports, inferences, and unknowns remain distinct.",
        "The declared source primary language is independently verified from the normalized non-appendix source, and output matches it unless the packet contains the user's exact explicit instruction requesting another language.",
        "The claim ledger covers valuable non-appendix source information and excludes appendix material.",
        "No causal, quantitative, or recommendation claim is stronger than its evidence.",
        "Thin or blocked material is shortened or clarified rather than padded with external facts, invented specificity, experience, or emotion.",
        "Missing denominators, periods, samples, conflicts, mutable-source observation time or version markers, and inferences are visible and handled safely without invented dates.",
        "Every visual title and label stays at or below the mapped claim's evidence ceiling and preserves its protected relation.",
    ],
    "visual": [
        "Recompute visible coverage from claim visual_required_tokens; do not trust the declared coverage percentage or block mapping alone.",
        "The visual language matches the declared document output language, except for source-native proper nouns and necessary terms.",
        "The preview uses content-fit visual encoding rather than boxes plus prose when chartable data exists.",
        "Exactly one allowed theme was selected from document type, audience, tone, relationship, and density; its rationale is content-based rather than a silent default.",
        "The one-picture visual, body figures, and HTML page use the same theme while preserving the canonical semantic colors.",
        "The rendered board has a clear reading path, uses proximity to bind labels, captions, and sources to their objects, separates larger reader questions with wider gaps, and has no visible clipping, overlap, overflow, or misleading precision.",
        "The body and whiteboard use the same source-grounded semantic mapping; mathematical sign alone does not determine favorable or unfavorable color.",
        "Each figure uses a judgment title, preserves metric scope, labels decision-bearing values, and provides useful alt text when the target format supports it.",
        "The rendered preview visibly carries the conclusion and decision path; a title that promises a leader, actor, segment, or object visibly names it rather than relying on hidden alt text or the spec.",
        "The declared composition creates real hierarchy: anchor_support has one dominant anchor and smaller supports, while comparison_grid keeps peers directly comparable.",
        "Values sharing one quantitative axis use the same metric, unit, period, and denominator; different scopes are split or explicitly cross-labeled.",
        "Visual titles and annotations do not use causal wording above the mapped evidence ceiling.",
        "Missing values remain N/A rather than zero; scatter points, funnel stages, area, size, and flow magnitude are used only when source data supports them.",
        "For HTML, critical information is visible without interaction, the rendered document is readable, and no runtime resource is external.",
        "For HTML, the design plan fits the source; accessibility and 14px body text remain hard floors; 16px body text, 1.5 line height, and controlled prose measure are preferred signals rather than automatic failures; and the renderer or native-SVG fallback preserves the full evidence payload.",
        "For HTML, a source-isolated full-page replay confirms that title hierarchy, TLDR distinction, heading narrative, page rhythm, and one-picture dominance are visible in the rendered page; deterministic geometry evidence reports no overlap, clipping, or horizontal overflow.",
        "For Feishu, body figures use editable native shapes, judgment titles, compact captions, and readable table widths/alignment.",
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


def validate_readiness(args):
    receipt_path = Path(args.readiness_receipt)
    if not receipt_path.is_file():
        raise SystemExit(f"missing review readiness receipt: {receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != 1 or receipt.get("status") != "ready" or receipt.get("errors") not in ([], None):
        raise SystemExit("review readiness receipt is not ready")
    current = {
        "source_snapshot": digest(args.source_snapshot),
        "inventory": digest(args.inventory),
        "claim_ledger": digest(args.claim_ledger),
        "tldr": digest(args.tldr),
        "body": digest(args.body),
        "draft": digest(args.draft),
        "source_outline": digest(args.source_outline),
        "source_excerpts": digest(args.source_excerpts),
        "validation_notes": digest(args.validation_notes),
        "document_preview": digest(args.document_preview),
        "visual_spec": digest(args.visual_spec),
        "html_design_plan": digest(args.html_design_plan),
        "visual_preview": digest(args.whiteboard_preview),
        "full_page_preview": digest(args.full_page_preview),
        "geometry_report": digest(args.geometry_report),
        "full_page_replay": digest(args.full_page_replay),
    }
    current = {key: value for key, value in current.items() if value}
    if current != receipt.get("files"):
        raise SystemExit("review inputs changed after readiness validation")


def packet_for(role, args):
    hashes = {
        "source_snapshot": digest(args.source_snapshot),
        "inventory": digest(args.inventory),
        "claim_ledger": digest(args.claim_ledger),
        "tldr": digest(args.tldr),
        "body": digest(args.body),
        "draft": digest(args.draft),
        "visual_spec": digest(args.visual_spec),
        "html_design_plan": digest(args.html_design_plan),
        "validation_notes": digest(args.validation_notes),
        "whiteboard_preview": digest(args.whiteboard_preview),
        "document_preview": digest(args.document_preview),
        "full_page_preview": digest(args.full_page_preview),
        "geometry_report": digest(args.geometry_report),
        "full_page_replay": digest(args.full_page_replay),
        "source_outline": digest(args.source_outline),
        "source_excerpts": digest(args.source_excerpts),
        "readiness_receipt": digest(args.readiness_receipt),
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

## Visual Claim Labels

{read_optional(args.visual_spec) or '- Not provided; FAIL if visual claim wording cannot be checked against evidence ceilings.'}
"""
    else:
        evidence = f"""
## Visual Spec

{read_optional(args.visual_spec) or '- Not provided; FAIL if claim-to-block mapping cannot be verified.'}

## HTML Design Plan

{read_optional(args.html_design_plan) or '- Not applicable or not provided. For HTML output, FAIL if layout, typography, renderer, anchor, or fallback choice cannot be verified.'}

## Whiteboard Evidence

- Preview/path: {args.whiteboard_preview or 'Not provided.'}

{read_optional(args.whiteboard_summary) or '- Validation summary not provided.'}

## Deterministic Validation Evidence

{read_optional(args.validation_notes) or '- Not provided; FAIL any gate that depends on unavailable structural or runtime-resource evidence.'}

## Body Visual Evidence

- Rendered document preview/path: {args.document_preview or 'Not provided; FAIL semantic-color consistency when it cannot be verified.'}
- Full-page screenshot/path: {args.full_page_preview or 'Not provided; FAIL HTML page-level hierarchy and rhythm.'}
- Geometry report/path: {args.geometry_report or 'Not provided; FAIL HTML overlap and clipping evidence.'}
- Blind full-page replay/path: {args.full_page_replay or 'Not provided; FAIL HTML report-level visual comprehension.'}
- Use the claim ledger's `semantic_direction` and `display_values` as the cross-artifact comparison map.
"""

    output_contract = f"""
## Required Output

Return JSON only. Validate against `references/independent-review.schema.json`; do not use the simplified `evals/review.schema.json`:

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
    parser.add_argument("--source-snapshot", default="", help="Normalized non-appendix source snapshot")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--claim-ledger", required=True)
    parser.add_argument("--tldr", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--draft", default="")
    parser.add_argument("--user-request", default="")
    parser.add_argument("--source-outline", default="")
    parser.add_argument("--source-excerpts", default="")
    parser.add_argument("--visual-spec", default="")
    parser.add_argument("--html-design-plan", default="")
    parser.add_argument("--validation-notes", default="", help="Deterministic validation summary for the final rendered artifact")
    parser.add_argument("--whiteboard-summary", default="")
    parser.add_argument("--whiteboard-preview", default="")
    parser.add_argument("--document-preview", default="")
    parser.add_argument("--full-page-preview", default="")
    parser.add_argument("--geometry-report", default="")
    parser.add_argument("--full-page-replay", default="")
    parser.add_argument("--readiness-receipt", required=True)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--output", required=True, help="Output file for one role, or directory for --role all")
    args = parser.parse_args()
    validate_readiness(args)

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
