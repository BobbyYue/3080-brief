# Source Inventory Template

Keep this compact. It is the source-of-truth working object for drafting, visuals, and review packets.

## Source

- Title:
- Link / path:
- Type:
- Source language: use a primary BCP 47 tag such as `en`, `zh-CN`, or `ja`
- Output language: match source language unless the user explicitly requests another language
- Output-language basis: `source_primary_language` or `explicit_user_request`
- Explicit language override evidence: `none` or the user's exact instruction requesting another output language
- Requested audience / scene:
- User constraints:

The language used in the user's message, conversation, interface, locale, or surrounding context is not an output-language override. If source language is unclear or multiple languages compete for primacy, ask before drafting.

## Scope

- Included non-appendix sections:
- Excluded appendix / 附录 / Appendix sections:
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

## Evidence Inventory

| Claim ID | Priority | Claim / Fact | Source location | Metric / value | Semantic direction | Period | Denominator / sample | Scope / filter | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | P0 |  |  |  | favorable / unfavorable / warning / neutral / unknown |  |  |  |  |

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
