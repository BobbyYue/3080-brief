# 3080 Brief Runtime Core

Read this file for every `3080-brief` run. It is the compact execution contract. Read deeper references only when the routing rules below require them.

## Non-Negotiables

- Create a new output; never edit the source document.
- Match output type to input type unless the user explicitly asks otherwise.
- Follow the source primary language unless the user explicitly requests another output language. Request/conversation/interface/locale language is not override evidence.
- Use only non-appendix source content unless the user explicitly includes appendix material.
- Every number, conclusion, risk, and recommendation must be source-backed or explicitly labeled `原文未提供` / `not provided in the source` or `推断` / `inference`.
- Keep internal process language out of the generated artifact; exact restrictions live in `config/3080-brief.json`.
- Put the source link near the top as compact, low-emphasis citation metadata.

## Runtime Loading

Default runtime reads:

1. `SKILL.md`
2. `references/runtime-core.md`
3. `references/user-supplements-rules.md`

Do not read `docs/user-supplements-template.md` during normal execution; read it only when modifying the skill or user supplement source.

Read deeper references only when needed:

- `references/output-format-rules.md`: source/output type is ambiguous, non-Feishu/non-Word, or user requests conversion.
- `references/dependency-and-installation.md`: Feishu/Lark output needs CLI or style-skill dependencies, or dependency diagnostics return `BLOCKED`, `SKIP`, or `FAIL`.
- `references/evidence-and-risk-rules.md`: source contains experiment/data claims, risks, causal language, missing denominators, or conflicting metrics.
- `references/reader-optimization.md`: narrative structure is unclear, source is jargon-heavy, or first draft fails readability.
- `references/expression-anti-patterns.md`: draft looks templated/vague, preflight emits expression warnings, or a reviewer fails wording/narrative/visual-expression gates.
- `references/semantic-color-system.md`: directional metrics, signed deltas, gains/losses, risk/exception states, or status judgments appear.
- `references/visual-pattern-library.md`: selecting the visual form or chart type.
- `references/whiteboard-patterns.md`: building or debugging the whiteboard SVG.
- `references/image2-auxiliary-rules.md`: considering image generation for inspiration.
- `references/feishu-doc-output.md`: creating/updating Feishu XML or debugging Feishu output.
- `references/review-loop.md`: full reviewer protocol is needed beyond the compact protocol below.
- `references/blind-reader-replay.md`: all three audit reviewers passed and post-review reader replay is ready to run.

## Dependency Gate And Installation Approval

- Keep core validation offline and Python-standard-library-only: run `scripts/check_dependencies.py --mode core` and `scripts/validate_skill.py`.
- Before any Feishu/Lark fetch or write, run `scripts/check_dependencies.py --mode feishu --json`. Required CLI paths/versions and the `beautiful-feishu-whiteboard` contract/version must be verified.
- When `installation_request.required` is true, show each exact package or GitHub skill source/version, install root, network access, created files, restart effect, and command; then request explicit user approval and stop the installation path for that turn.
- After approval, run only the emitted `approval_commands` with `--user-approved`, then rerun the Feishu diagnostic. Never add the approval flag without explicit approval. A newly installed skill requires restarting Codex before it can be used.
- Treat missing optional Feishu dependencies as `SKIP` for non-Feishu tasks and `BLOCKED` for Feishu tasks. Never call either state `PASS`.
- If the user declines, installation fails, or the required Codex restart has not occurred, keep Feishu delivery blocked. Offer another output format only if the user explicitly chooses it.
- Keep CLI installation separate from Feishu configuration/authentication; follow `lark-shared` after installation.

## Source Inventory First

After fetching the source, write a compact `source_inventory.md` and `claim_ledger.json` before drafting. Use `references/source-inventory-template.md` and `references/claim-ledger.schema.json`.

The inventory and ledger are the default evidence objects for drafting and whiteboard design. Assign stable claim IDs and P0/P1/P2 importance. Map every claim to its source location, board block, body section, and omission reason. Re-open the source only to resolve a missing fact, citation, embedded object, reviewer excerpt, or disputed finding.

Inventory must include:

- source title/link/type/language;
- output language plus `source_primary_language | explicit_user_request` basis and exact override evidence;
- excluded appendix sections;
- core value / main judgment;
- key facts and metrics with period, denominator, scope, source location;
- chartable data;
- risks, caveats, confidence boundaries;
- next actions or open questions;
- terms/口径 needed for TLDR table;
- source-backed vs inferred claims.
- complete embedded-object inventory and which P0/P1 objects were inspected;
- value-weighted claim coverage using configured P0/P1/P2 weights.

## TLDR Contract

`TLDR` contains exactly three core content units:

1. 一句话: readers get the source document's core value within 30 seconds.
2. 一张图: readers get at least 80% of value-weighted non-appendix claims in one visual.
3. 一个表: readers get answers to the questions they most want to ask while reading.

TLDR table:

- Output-language headers: `问题 / 结论 / 为什么` for Chinese; `Question / Conclusion / Why` for English; use an equally direct equivalent for other languages.
- If a cell needs more than 3 visual lines, increase row height/vertical spacing, split the row, or move detail to the body.

## Visual Rules

- If the source has 3+ quantitative claims, or the main conclusion depends on quantitative evidence, the opening visual must include at least one quantitative encoding beyond boxes and prose.
- Prefer source-grounded native/editable Feishu whiteboard elements for Feishu output.
- Do not paste full SVG/XML into reviewer prompts. Pass a preview path, board summary, and validation result.
- Create `visual_spec.json` before rendering and map each visual block to source claim IDs.
- Classify decision-relevant directional claims in `claim_ledger.json`; use the same configured semantic meaning and color in body and board, with a non-color cue.
- Run `scripts/check_coverage.py claim_ledger.json`; do not release below the configured threshold or with an unexplained omitted P0 claim.
- Run `scripts/validate_visual_spec.py visual_spec.json claim_ledger.json`; reject unknown claims, missing blocks, or a banned style.

## Review Packet Protocol

Before reviewer subagents, create three role-specific packets using `references/review-packet-template.md` and `scripts/build_review_packet.py --role all`.

Shared packet data should include:

- user request and constraints;
- source inventory and claim ledger;
- TLDR text/table;
- whiteboard preview path plus board summary, not full SVG;
- artifact hashes and review-round ID.

Role-specific evidence:

- Reader: full readable/rendered draft.
- Source: non-appendix source outline plus P0/P1 excerpts and locations.
- Visual: whiteboard preview, document preview, visual spec, coverage result, semantic-direction mapping, and validation summary.

Second and later rounds should pass only:

- previous blocking issues;
- revision diff/summary;
- changed excerpts;
- unchanged packet sections only when needed.

Keep reviewer isolation: do not reveal one reviewer's comments to another until all three reviews are submitted.
After all three reports arrive, run `scripts/aggregate_reviews.py`; reject mismatched artifact hashes, rounds, or roles.

## Blind Reader Replay

Run only after preflight and all three audit reviewers pass the same artifact set. Start with the Primary Blind Reader, whose role is `理解业务、产品和常见指标，不了解技术实现，无决策能力`. Give it only the rendered reader-facing artifact and require exactly three document-specific question-answer replays without `PASS/FAIL` grading.

Launch the Technical and Decision roles in parallel only when any escalation condition applies: multi-functional audience; Primary cannot replay the P0 conclusion, next action, value, or feasibility; or the conclusion affects resources, risk, or broad rollout. Do not reveal sources, expected answers, reviewer outputs, the Primary replay, or the escalation reason to any blind reader.

If replay reveals a blocking comprehension defect, revise and restart from preflight plus all three audit reviewers; then restart with Primary. Full roles, isolation, output schema, escalation, and evaluation rules live in `references/blind-reader-replay.md`.

## Preflight Before Review

Run `scripts/preflight_check.py DRAFT --source-inventory source_inventory.md` before reviewer subagents. When the ledger contains semantic directions/display values, pass it with `--claim-ledger`. Fix deterministic failures before spending reviewer tokens:

- configured headings, audience labels, meta-statements, and placeholders;
- discouraged vague expressions requiring source-specific review;
- missing TLDR units;
- cramped table warning candidates;
- source appendix inclusion markers.
- invalid language basis, source/output language conflict, or an obvious draft/output language mismatch;
- unstyled or conflicting decision-relevant directional values, plus heuristic warnings when signed metrics appear without any semantic encoding.

## Delivery Check

Before final delivery:

- source unchanged;
- Feishu/Lark dependency diagnostic passed when that output path was used; no required adapter or style skill remains skipped or blocked;
- output format matched or user override honored;
- output language matched source primary language or an exact explicit user override, consistently across title, TLDR, table, body, and visual;
- source citation present and low-emphasis;
- TLDR has one-sentence, one-picture, one table;
- visual rendered/validated;
- live Feishu preview inspected when applicable;
- body and whiteboard semantic colors agree and retain redundant text/sign/shape cues;
- three reviewers PASS, or blockers escalated.
- Primary Blind Reader Replay completed; Technical and Decision replays completed when escalation conditions applied.
- final artifacts match the hashes approved by all three reviewers.
