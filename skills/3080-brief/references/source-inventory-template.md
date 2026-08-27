# Source Inventory Template

Keep this compact. It is the source-of-truth working object for drafting, visuals, and review packets.

## Source

- Title:
- Link / path:
- Type:
- Source mutability: `stable`, `mutable`, or `unknown`
- Published / updated / version marker: record only what the source exposes; otherwise `not visible`
- Observed / retrieved at: required for `mutable` or `unknown` online sources; use the actual access time, never a guessed publication time
- Source language: inspect the normalized non-appendix source itself and use a primary BCP 47 tag such as `en`, `zh-CN`, or `ja`
- Output language: match source language unless the user explicitly requests another language
- Output-language basis: `source_primary_language` or `explicit_user_request`
- Explicit language override evidence: `none` or the user's exact instruction requesting another output language
- Requested audience / scene:
- User constraints:
- Material sufficiency: `sufficient / proceed`, `thin / shorten`, `thin / clarify`, or `blocked / clarify`
- Sufficiency rationale:

The normalized snapshot must preserve the source language; do not translate it. Preflight verifies the declared source language against this file before it checks the output. The language used in the user's message, conversation, interface, locale, or surrounding context is not an output-language override. If source language is unclear or multiple languages compete for primacy, ask before drafting. Keep source timing in this inventory by default; show it in the brief only when page mutability changes how a claim should be interpreted or reproduced.

## Scope

- Included non-appendix sections:
- Excluded appendix / 附录 / Appendix sections:
- Normalized non-appendix snapshot path: `source_non_appendix.md`
- Embedded objects inspected:
- Embedded objects not inspected and why:

## Core Value

- Main reader judgment:
- Why this matters:
- Decision/action/understanding enabled:
- Confidence level and why:

## Claim Ledger

Create `claim_ledger.json` beside this inventory using `claim-ledger.schema.json`. The ledger, not raw word count, defines the one-picture 80% target.

Priority rules:

- `P0` (weight 3): omitting it can change the reader's decision, trust, risk understanding, or next action.
- `P1` (weight 2): material supporting logic, evidence, boundary, or context.
- `P2` (weight 1): useful detail that can stay in the body without changing the main judgment.

Give every claim a stable ID and map it to the board and body. Source appendix claims use `appendix: true` and are excluded from the denominator unless explicitly requested.

For every non-appendix P0/P1 claim, also record:

- `source_identity`: `source_fact`, `source_author_claim`, `source_self_report`, `agent_inference`, or `unknown`.
- `evidence_ceiling` and `output_assertion` on the ordered scale in `source-faithful-expression.md`; output must not exceed evidence.
- `protected_relations`: subject, predicate, object, scope, time/status, qualifiers, and exact values attached to their objects.

If the source is thin, shorten or clarify; never pad it with external facts, invented specificity, personal experience, or emotion.

## Evidence Inventory

| Claim ID | Priority | Claim / Fact | Source identity | Evidence → output strength | Protected relation | Source location | Metric / value | Scope / time / qualifier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | P0 |  | source_fact / source_author_claim / source_self_report / agent_inference / unknown | observed → observed | subject → predicate → object |  |  |  |

## Chartable Data

| Relationship | Values | Best visual candidate | Required caveat |
| --- | --- | --- | --- |
|  |  |  |  |

For decision-relevant directional metrics/statuses, copy `semantic_direction` and exact `display_values` into `claim_ledger.json`. Classify business meaning rather than mathematical sign; read `semantic-color-system.md` when any such value exists.

## Risks And Boundaries

| Risk / caveat | Source-backed or inference | Impact | Trigger / monitor | Fallback / next action |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## TLDR Inputs

- One-sentence core value:
- One-picture claim spine:
- Value-weighted board coverage target and current estimate:
- Key questions for table:
  - 问题:
    - 结论:
    - 为什么:

## Body Narrative Inputs

- Suggested body reasoning path, without fixed template:
- Candidate body headings:
- Concrete case/story/example from source:
- Details to keep out of TLDR but preserve in body:

## Open Questions

| Question | Blocking? | Why it matters | Default if unanswered |
| --- | --- | --- | --- |
|  |  |  |  |
