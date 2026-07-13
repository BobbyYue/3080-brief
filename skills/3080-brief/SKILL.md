---
name: 3080-brief
description: Create a new source-grounded decision brief in the source format by default (Feishu/Lark creates a new Feishu/Lark doc; Word/docx creates a new Word/docx) with a reader-fit Pyramid opening, one editable/auditable visual covering at least 80% of value-weighted non-appendix claims, and one key-question table. Use when the user names 3080-brief, 3080 brief, 3080skill, 读者视角总结, 3080总结, 3080summary, or 3080-onepager, or asks for a new reader-perspective/cross-functional decision brief with both a 30-second takeaway and one-picture summary. Do not use for editing or polishing the source in place, a generic summary with no 3080/reader/visual requirement, or standalone whiteboard styling. Never modify the source; source-back every number, conclusion, risk, and action.
---

# 3080 Brief

**30-second judgment, 80% in one picture**

Create a new decision brief from a source document. By default, output the same document type as the input source. The opening `TLDR` must contain exactly three core content units:

1. **一句话 / one-sentence summary**: let readers get the source document's core value within 30 seconds.
2. **一张图 / one-picture summary**: let readers absorb at least 80% of the source's value-weighted non-appendix claims in one visual. For Feishu/Lark output, this must be an editable whiteboard.
3. **一个表 / one key-question table**: answer the questions readers most want to ask while reading the document.

## Operating Contract

### Positioning

`3080-brief` is not generic compression. It is a source-grounded, reader-layered decision-briefing skill for technical, product, strategy, experiment review, and data-analysis documents.

Use this mental model:

- First principle: switch from the author's "what do I want to say" to the reader's "what do I need to understand, trust, decide, or do".
- Output goal: rebuild the source into a clear, evidence-backed, professional, useful narrative.
- Visual goal: use charts and whiteboards as narrative evidence, not decoration.
- Primary invocation name: `3080-brief`; `3080skill` is a supported concise alias.

### Priority Order

When goals conflict, apply this order:

1. Source truth: never invent data, conclusions, risks, or causality.
2. Explicit user requirements: honor audience, scope, exclusions, format, and language when source truth is preserved.
3. Reader comprehension: optimize for what the target reader must understand, trust, decide, or do.
4. 30-second judgment: make the opening independently useful.
5. One-picture 80% understanding: make the whiteboard carry at least 80% of value-weighted non-appendix claims.
6. Professional expression and visual polish: aesthetics serve truth, evidence, and comprehension.

### Non-Negotiables

- Create a **new doc**; never edit, overwrite, reorder, comment on, or clean up the source doc.
- Follow the source document's primary language unless the user explicitly requests another output language. The language of the request, conversation, interface, locale, or surrounding context is not an override.
- Include the source document link in the generated doc.
- Ground every number, conclusion, risk, and recommendation in the source. Mark unsupported gaps as "原文未提供" / "not provided in the source" or "推断" / "inference".
- Exclude source appendix / 附录 / appendix content from the generated summary, opening whiteboard, body, and coverage expectations unless the user explicitly asks to include appendix material.
- Keep internal writing rationale, prompts, style names, and process justification out of the generated artifact. Apply machine-enforced expression restrictions from [config/3080-brief.json](config/3080-brief.json).
- Put business value or decision implication before technical detail unless the user explicitly targets implementers.
- Match output format to input format unless the user specifies otherwise: Feishu/Lark -> Feishu/Lark, Word/docx -> Word/docx.
- Use the correct output tool for the selected format: `lark-doc` for Feishu/Lark docs, `documents:documents` for Word `.docx`, `lark-whiteboard` for Feishu live preview checks, and `beautiful-feishu-whiteboard` for Feishu whiteboard style systems.

## Resource Map

Optimize for progressive disclosure. For normal execution, read only the compact runtime files first; load deep references only when the routing condition applies.

| Resource | Use when |
| --- | --- |
| [references/runtime-core.md](references/runtime-core.md) | Always read for every run; compact execution contract and routing. |
| [references/user-supplements-rules.md](references/user-supplements-rules.md) | Always read for every run; synced user rules. |
| [docs/user-supplements-template.md](docs/user-supplements-template.md) | Read only when modifying supplement source or this skill. Do not read during normal execution. |
| [references/dependency-and-installation.md](references/dependency-and-installation.md) | Feishu/Lark output needs CLI or style-skill dependencies, or dependency diagnostics return BLOCKED/SKIP/FAIL. |
| [references/source-inventory-template.md](references/source-inventory-template.md) | Build compact source inventory after fetching source. |
| [references/claim-ledger.schema.json](references/claim-ledger.schema.json) | Build the value-weighted source claim ledger and board/body traceability map. |
| [references/visual-spec.schema.json](references/visual-spec.schema.json) | Define claim-to-visual-block mapping before rendering the whiteboard. |
| [references/review-packet-template.md](references/review-packet-template.md) | Build role-specific reviewer packets and lock artifact hashes. |
| [config/3080-brief.json](config/3080-brief.json) | Machine-readable aliases, thresholds, banned styles, prohibited headings/meta/placeholders, discouraged phrases, and review roles. |
| [references/output-format-rules.md](references/output-format-rules.md) | Output type is ambiguous or user requests conversion/non-default output. |
| [references/evidence-and-risk-rules.md](references/evidence-and-risk-rules.md) | Data/experiment/risk/causal claims, missing denominators, conflicting metrics. |
| [references/reader-optimization.md](references/reader-optimization.md) | Narrative is unclear, source is jargon-heavy, or readability/preflight/reviewer fails. |
| [references/expression-anti-patterns.md](references/expression-anti-patterns.md) | Draft looks templated/vague, preflight emits expression warnings, or a reviewer fails narrative/readability/visual-expression gates. |
| [references/semantic-color-system.md](references/semantic-color-system.md) | Source/draft contains directional metrics, signed deltas, gains/losses, risks, exceptions, or status judgments. |
| [references/visual-pattern-library.md](references/visual-pattern-library.md) | Select visual/chart form. |
| [references/whiteboard-patterns.md](references/whiteboard-patterns.md) | Build or debug Feishu whiteboard SVG. |
| [references/image2-auxiliary-rules.md](references/image2-auxiliary-rules.md) | Considering image generation for inspiration. |
| [references/feishu-doc-output.md](references/feishu-doc-output.md) | Create/update Feishu XML or debug Feishu output. |
| [references/review-loop.md](references/review-loop.md) | Need full reviewer scoring/protocol beyond runtime-core compact protocol. |
| [references/blind-reader-replay.md](references/blind-reader-replay.md) | Run reader replay after all three audit reviewers pass. |

Reusable scripts:

- `scripts/extract_lark_doc_token.js`: extract a doc/wiki token from a Feishu/Lark URL.
- `scripts/validate_skill.py`: validate the installable skill with Python standard library only.
- `scripts/check_dependencies.py`: report core/optional dependency status and emit an approval-safe install plan.
- `scripts/install_optional_dependencies.py`: install only user-approved, exact-version Feishu adapters into an isolated cache.
- `scripts/install_skill_dependency.py`: install only a user-approved `beautiful-feishu-whiteboard` dependency through the official Codex skill installer.
- `scripts/build_review_packet.py`: assemble role-specific, hash-locked reviewer packets.
- `scripts/check_coverage.py`: calculate value-weighted board coverage from `claim_ledger.json`.
- `scripts/render_visual_spec.py`: render common native-shape visual blocks from `visual_spec.json`.
- `scripts/validate_visual_spec.py`: verify claim-to-block mapping and reject banned styles before rendering.
- `scripts/preflight_check.py`: deterministic draft checks before reviewer subagents.
- `scripts/aggregate_reviews.py`: verify and aggregate the three reviewer results.
- `scripts/verify_reviewed_artifacts.py`: prove final files still match the reviewer-approved artifact set.
- `scripts/validate_whiteboard.sh`: render and check SVG via `@larksuite/whiteboard-cli`.
- `scripts/wrap_svg_as_whiteboard.js`: wrap SVG as `<whiteboard type="svg">...</whiteboard>`.
- `scripts/sync_user_supplements.sh`: sync user supplement rules into this canonical skill and run local validation.

Examples and eval fixtures:

- `examples/source-type-openings.md`: structural variation across data analysis, product planning, technical design, status inventory, and risk review.
- `examples/bad-vs-good-whiteboard.md`: visual anti-pattern reasoning.
- `examples/three-reviewer-report.md`: human-readable review behavior only; runtime reviewer output uses JSON.
- `evals/trigger_cases.json`: 20 balanced train/validation prompts for real trigger-rate evaluation; pass only each `query` to the evaluated agent.
- `evals/boundary_cases.json`: unresolved product-boundary prompts for human policy review; do not include them in automated trigger scoring.
- `evals/output_coverage.json`: source and failure archetypes for generation-quality coverage, separate from trigger evaluation.
- `evals/fixtures/valid-brief.md`: complete synthetic structure fixture validated by `scripts/run_evals.py`.

## Workflow

### 1. Read And Ground

1. Read [references/runtime-core.md](references/runtime-core.md) and [references/user-supplements-rules.md](references/user-supplements-rules.md). Do not read [docs/user-supplements-template.md](docs/user-supplements-template.md) during normal execution.
2. Determine the source type from the user input and set the default output type to match it unless the user explicitly requests another output type. Read [references/output-format-rules.md](references/output-format-rules.md) only if the type or conversion is ambiguous.
3. For Feishu/Lark output, run `python3 scripts/check_dependencies.py --mode feishu --json` before fetching or writing. This gate verifies the CLI adapters and `beautiful-feishu-whiteboard`. If it returns `BLOCKED`, read [references/dependency-and-installation.md](references/dependency-and-installation.md), show every exact install plan, and request explicit user approval. Do not install in the same turn or treat the document request as approval. Non-Feishu output does not prompt for Feishu dependencies.
4. Determine the source's primary language independently of the user's request language. Set output language to the source language unless the user explicitly requests another; record the exact override instruction when present. Ask if source-language primacy is ambiguous.
5. Fetch/read the source with the matching tool: use `lark-doc` for Feishu/Lark docs, `documents:documents` for Word `.docx`, and local file tools for local Markdown/text.
6. Inventory every embedded sheet, Base, image, chart, and whiteboard by type and location before deciding relevance; inspect every object that carries P0/P1 evidence or chartable data.
7. Build `source_inventory.md` and `claim_ledger.json` using [references/source-inventory-template.md](references/source-inventory-template.md) and [references/claim-ledger.schema.json](references/claim-ledger.schema.json). Record source language, output language, `source_primary_language | explicit_user_request` basis, and exact override evidence. Give every valuable non-appendix claim a stable ID, P0/P1/P2 priority, source location, board status, and body location.
8. Use the inventory and ledger as the default evidence objects for drafting, visual design, and reviewers. Re-open the full source only for missing facts, source excerpts, embedded objects, or reviewer disputes. Read [references/evidence-and-risk-rules.md](references/evidence-and-risk-rules.md) when the source has data/experiment/risk/causal claims or unclear/conflicting metrics.

### 2. Clarify Before Drafting

Use the Clarification Gate in [references/runtime-core.md](references/runtime-core.md). Read [references/review-loop.md](references/review-loop.md) only if ambiguity is complex or the compact gate is insufficient.

Ask the user before drafting if uncertainty can change:

- main conclusion or 30-second takeaway;
- metric interpretation, denominator, period, sample, scope, or source;
- risk boundary, target reader, or next action;
- unsupported conclusions or conflicting source/user requirements.
- ambiguous source-language primacy, or a claimed language override that was not explicitly requested.

Ask at most 3 blocking questions at a time. Non-blocking gaps may proceed only when labeled as "原文未提供" / "not provided in the source" or "推断" / "inference".

### 3. Design The Narrative And Check Reader Gaps

Identify likely reader gaps from `source_inventory.md`:

- decision maker;
- cross-functional collaborator;
- domain reader;
- implementer;
- skeptical reviewer.

Use SUCCESs Framework and Stepwise Information Delivery to choose the body narrative from the source's actual logic and reader decision path. Read [references/reader-optimization.md](references/reader-optimization.md) when the narrative is unclear, source is jargon-heavy, or readability fails.

Run Novice Reverse Review after drafting the structure. Identify what a capable newcomer or cross-functional reader would not know, misunderstand, or ask next; then add only the explanations, definitions, or reader-question bridges that reduce that friction.

### 4. Draft The Brief

Required first-screen order:

1. First-level heading: `TLDR` by default, or a short source-language equivalent when the user explicitly prefers localized wording.
2. One-sentence summary callout: help readers get the source document's core value within 30 seconds.
3. One-picture whiteboard: cover at least 80% of value-weighted non-appendix claims in one visual.
4. One compact key-question table: answer the questions readers most want to ask while reading the document.
5. Compact source citation/reference near the top.

Present the source link as compact, low-emphasis metadata near the top using the target format's reference style. Heading and placeholder restrictions are enforced by [config/3080-brief.json](config/3080-brief.json) and `scripts/preflight_check.py`.

Treat the one-sentence summary as one short Pyramid Principle opening unit. Start with the highest-level reader judgment, then use 1-3 stepwise lines for the evidence, implication, action, or uncertainty needed to trust it. Match the top judgment to source purpose: insight, plan, experiment judgment, strategic change, current priority, root issue, risk posture, or capability change. Use 2-4 short lines by default, one information unit per line. Put boundaries in the opening only when they change the recommended action.

Keep the key-question table inside `TLDR`. Answer 3-5 questions that unlock comprehension, trust, or action, using source-grounded answers and output-language headers: `问题 / 结论 / 为什么` for Chinese and `Question / Conclusion / Why` for English. Increase row height, split the question, or move detail into the body when a cell becomes dense.

Then structure the body by the source's own narrative need. There is no default section order. Use SUCCESs to make the body simple, concrete, credible, memorable, and story-like where the source supports it. Use Stepwise Information Delivery so each section has one job, starts with the point, and reveals detail only after the reader understands why it matters.

Write body first-level headings as short judgments that advance the narrative. A reader should understand the reasoning path by scanning headings alone; exact heading restrictions are machine-enforced from the config.

Choose prose, bullets, callouts, tables, charts, timelines, examples, or short stories from the relationship being expressed. Start important dense sections with a short explanatory paragraph.

When the source or draft contains decision-relevant directional values or statuses, read [references/semantic-color-system.md](references/semantic-color-system.md). Classify business meaning in `claim_ledger.json` before styling; do not equate a plus sign with favorable or a minus sign with unfavorable. Apply the configured semantic color to compact body values/status labels and preserve a sign, arrow, or explicit wording as a redundant cue.

Read [references/expression-anti-patterns.md](references/expression-anti-patterns.md) only when the draft looks templated or vague, preflight emits expression warnings, or reviewer feedback identifies narrative, wording, heading, table, or visual-expression problems.

### 5. Create The Whiteboard

Use `source_inventory.md` and `claim_ledger.json` to list chartable data and the one-picture claim spine. Create `visual_spec.json` from [references/visual-spec.schema.json](references/visual-spec.schema.json) before drawing, declare the same output language, and map every visual block to claim IDs. Read [references/visual-pattern-library.md](references/visual-pattern-library.md) to select the visual/chart form. Read [references/whiteboard-patterns.md](references/whiteboard-patterns.md) only when building or debugging the Feishu whiteboard SVG. Use `scripts/render_visual_spec.py` for supported quantitative blocks when it reduces hand-written SVG risk.

For Feishu/Lark output, choose a `beautiful-feishu-whiteboard` candidate style from `CATALOG.md` based on source content, tone, audience, information density, and any explicit preference. In the 3080 workflow, select automatically when the user did not state a preference; do not pause only to ask for a vibe. Read only the selected template's `design.md`. Filter the banned styles from [config/3080-brief.json](config/3080-brief.json). If the user requests a banned style, state that it is unavailable for this skill and choose the closest allowed alternative.

If considering image2 or any bitmap generation, read [references/image2-auxiliary-rules.md](references/image2-auxiliary-rules.md) first. Image2 is optional and may only be used for composition/style inspiration; it must not carry source-critical evidence, numbers, charts, risks, thresholds, formulas, or recommendations. Never send internal source text, project/customer names, document links, identifiers, or real metrics to image generation; use abstract placeholders. The final 80% whiteboard must be rebuilt as editable, source-grounded Feishu whiteboard elements.

Run the Quantitative Visual Encoding Gate before choosing a board layout:

- Inventory chartable source data: percentages, rates, counts, before/after deltas, thresholds, formulas, correlations, distributions, segment comparisons, funnels, ranks, or time series.
- If the source contains 3 or more quantitative claims, or if the main conclusion depends on quantitative evidence, the whiteboard must include at least one quantitative visual encoding beyond text cards: bar/dot plot, slope chart, scatter or calibration sketch, threshold chart, matrix, funnel, distribution strip, or similar native-shape chart.
- If key chart data is embedded in sheets, charts, or images and materially affects the conclusion, inspect it with the relevant tool before drawing. If the data cannot be extracted reliably, label the limitation and use a safer boundary visual instead of pretending precision.
- Use a boxes-and-prose board only when the source has no chartable data or when chartable data is insufficient for a truthful visual; record that fallback in verification.
- Run `scripts/check_coverage.py claim_ledger.json`; the board must reach the configured value-weighted coverage threshold and must not silently omit a P0 claim.
- Run `scripts/validate_visual_spec.py visual_spec.json claim_ledger.json` before rendering.

Select the visual form from reader question and source relationship:

- change/deviation, evidence/magnitude, comparison/segmentation, flow/process, funnel/filter, hierarchy/architecture, prioritization/trade-off, risk/guardrail, time/roadmap, composition/contribution, relationship/network, or scenario/spatial map.

Apply these rules:

- One visual block equals one claim; titles state conclusions.
- Every visual element must answer a reader question or support a source-backed claim.
- Position, size, color, line, grouping, and boundary boxes must encode meaning.
- For directional values/statuses, use the same `config/3080-brief.json > semantic_colors` meaning in the body and whiteboard. Candidate style palettes may not override semantic colors; use strong colors for marks/labels and configured tints for large fills.
- Visualize benefits and risks when both exist in the source.
- Keep the opening whiteboard as an executive overview; move business and professional detail views into the body or generated appendix / 后置补充区. Do not import source appendix content unless explicitly requested.
- For Feishu/Lark output, use native-shape SVG only: `rect`, `circle`, `ellipse`, `line`, `polyline`, `text`, `tspan`, plus `defs/marker` and one simple straight-line `<path>` inside a marker for native arrowheads. No structural/freeform path, gradients, filters, masks, clipPath, image, external reference, font-family, or opacity.
- For Word/Markdown output, preserve the same visual logic as a rendered visual; keep source SVG/chart data as an auditable companion artifact when practical.
- Validate Feishu whiteboards with `scripts/validate_whiteboard.sh`; verify Word/Markdown visuals render in their target format.

### 6. Preflight And Run Three Independent Reviews

Before reviewer subagents, run deterministic checks when practical:

```bash
scripts/preflight_check.py path/to/draft.md --format auto --source-inventory source_inventory.md
scripts/check_coverage.py path/to/claim_ledger.json
```

Always pass `--source-inventory`; the Language Gate rejects undeclared language decisions, conversation-language overrides, and obvious draft/output mismatches. Pass `--claim-ledger path/to/claim_ledger.json` whenever semantic directions/display values are recorded. Fix deterministic failures before spending reviewer tokens.

Then create three role-specific, hash-locked packets using [references/review-packet-template.md](references/review-packet-template.md). Independence means no reviewer sees another reviewer's opinion; it does not require identical evidence. The Reader reviewer receives the full rendered/readable draft, the Source reviewer receives the non-appendix source outline plus P0/P1 excerpts and claim ledger, and the Visualization reviewer receives the preview, visual spec, validation result, and claim-to-block mapping. Do not pass full XML/SVG or unrelated source material.

When the inputs already exist as files, prefer:

```bash
scripts/build_review_packet.py --role all --inventory source_inventory.md --claim-ledger claim_ledger.json --tldr tldr_excerpt.md --body body_summary.md --draft draft.md --source-outline source_outline.md --source-excerpts p0_p1_excerpts.md --visual-spec visual_spec.json --whiteboard-summary board_summary.md --whiteboard-preview path/to/live_preview.png --output review_packets
```

Send the review packet to three reviewer subagents in parallel:

1. **Reader Comprehension Reviewer**: 30-second judgment, narrative clarity, jargon, background, likely questions.
2. **Source Coverage And Grounding Reviewer**: valuable source coverage, source-backed data, conclusions, risks, and labeled inferences.
3. **Visualization And Expression Reviewer**: one-picture 80% coverage, visual form/content fit, body-level visual usefulness, and cross-artifact semantic-color consistency.

Isolation rule: until all three reviews are submitted, the main agent must not expose, quote, summarize, hint at, or use any reviewer's comments in prompts to other reviewers.

Treat any `FAIL`, blocking issue, unsupported claim, or failed role gate as mandatory revision. Aggregate only after all three reports arrive. Use `scripts/aggregate_reviews.py` to verify that the three roles reviewed the same artifact hashes and round. For second and later rounds, send only previous blocking issues, revision diff/summary, changed excerpts, and any unchanged packet sections needed to verify the fix. Re-run all three reviewers up to 3 rounds. Do not proceed to reader replay until all three return `PASS`, unless the user explicitly asks to publish despite unresolved issues. If subagent capability is unavailable, disclose the limitation and do not claim that independent review occurred.

### 7. Run Blind Reader Replay

After all three audit reviewers pass, read [references/blind-reader-replay.md](references/blind-reader-replay.md) and run the Primary Blind Reader against only the reviewer-approved rendered artifact. The reader independently derives and answers exactly three document-specific questions; do not provide source evidence, expected answers, reviewer outputs, or other replay results.

Launch the Technical and Decision blind readers in parallel only when the Primary replay or document meets an escalation condition: multi-functional audience; inability to replay the P0 conclusion, next action, value, or feasibility; or a conclusion affecting resources, risk, or broad rollout. Do not expose the Primary replay or escalation reason to them.

Blind readers do not grade `PASS/FAIL`. The main agent compares their replay with the hidden P0/P1 ledger and user intent. If a replay exposes a blocking comprehension defect, revise the artifact, restart from preflight, re-run all three audit reviewers, and then restart with the Primary Blind Reader. Do not publish until the selected replay roles complete without a blocking comprehension failure. If blind-reader subagents are unavailable, disclose the limitation and do not claim replay occurred.

### 8. Create And Verify The New Output

If the selected output is Feishu/Lark, read [references/feishu-doc-output.md](references/feishu-doc-output.md) only when creating/updating XML or debugging output. Keep generated SVG/XML in files and pass paths/summaries through the workflow instead of pasting full structures into prompts.

Create the new output in the selected format:

- title/name: `3080 Brief｜原文标题`;
- first content block: first-level heading `TLDR` or source-language equivalent when explicitly preferred;
- second content block: one-sentence summary that surfaces the source document's core value within 30 seconds;
- third content block: one-picture visual summary covering at least 80% of value-weighted non-appendix claims;
- fourth content block: key-question table that answers readers' most likely questions and includes necessary term/口径 explanations;
- compact source citation/reference near the top, low-emphasis and without a standalone source heading.

Then verify:

- source doc was not modified;
- output type matches input type unless the user specified otherwise;
- output language matches the source primary language unless the inventory contains an exact explicit user override; title, TLDR, table, body, and visual use that language consistently;
- visual summary passed the relevant render/check for the output type;
- decision-relevant directional values use consistent, redundant semantic encoding in both body and whiteboard;
- for Feishu/Lark output, live whiteboard image was queried and inspected for clipping, overlap, overflow, and stale rendering;
- generated output link/path and source citation/reference are accessible.
- final draft, whiteboard, visual spec, inventory, and claim-ledger hashes match the artifact set approved by reviewers.
- Blind Reader Replay used the same reviewer-approved artifact set and completed without a blocking comprehension failure.

Verify the final artifact set with `scripts/verify_reviewed_artifacts.py` before delivery.

<!-- USER_SUPPLEMENTS_START -->
## User Supplements Index

Detailed user supplements are intentionally kept out of `SKILL.md` to keep the main workflow concise.

For normal execution, read:

- [references/user-supplements-rules.md](references/user-supplements-rules.md): synced runtime copy of the same detailed rules.

For modifying the skill or supplement source, also read:

- [docs/user-supplements-template.md](docs/user-supplements-template.md): user-editable source of supplemental rules.

Apply the supplement rules for:

- trigger aliases and non-trigger cases;
- reader-first thinking and clarification categories;
- source/new-doc/data credibility constraints;
- output format, title, and first-screen structure;
- one-sentence and one-picture summary rules;
- body-level visualization requirements;
- evidence, risk, Feishu output, three-reviewer rules, and post-review Blind Reader Replay;
- quality bar, common failure modes, example slots, and open questions.

Do not treat this index as a replacement for the detailed supplement rules.
<!-- USER_SUPPLEMENTS_END -->

## Quality Gates

Use the compact gates in [references/runtime-core.md](references/runtime-core.md), deterministic checks from `scripts/preflight_check.py`, and reviewer packet gates from [references/review-packet-template.md](references/review-packet-template.md). Load [references/review-loop.md](references/review-loop.md) only when full scoring or complex review handling is needed.

Minimum final checks:

- source unchanged; output type and language match requirements;
- Feishu/Lark dependency diagnostic is `PASS` when that output path is used; no required adapter or style skill remains `SKIP` or `BLOCKED`;
- source inventory exists and excludes appendix unless requested;
- source/output language, basis, and override evidence are recorded; conversation language was not treated as an override;
- TLDR contains one-sentence, one-picture, and one table;
- source citation is compact and low-emphasis;
- no unsupported data, invented conclusion, or internal process statement;
- whiteboard/render/live preview checked when applicable;
- three independent reviewers return `PASS`, or unresolved blockers are escalated.
- Primary Blind Reader Replay completes; Technical and Decision replays complete when escalation conditions apply.

## Final Response

Respond briefly with:

- generated output link or file path;
- source link or file path;
- verification notes: source not modified, output type matched input type unless overridden, dependency gate passed when applicable, clarification gate completed, three reviewers PASS or blockers escalated, Blind Reader Replay completed or limitation disclosed, visual summary written, render/check completed, live preview inspected when applicable.

If `lark-cli` returns `_notice.update`, mention that the CLI can be updated with `lark-cli update` after finishing the task.
