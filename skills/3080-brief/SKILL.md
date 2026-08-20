---
name: 3080-brief
description: Create a new source-grounded decision brief in the source format by default (Feishu/Lark, Word/docx, Markdown, or self-contained HTML) with a reader-fit Pyramid opening, one editable or auditable visual covering at least 80% of value-weighted non-appendix claims, and one key-question table. Use when the user names 3080-brief, 3080 brief, 3080skill, 读者视角总结, 3080总结, 3080summary, or 3080-onepager, or asks for a new reader-perspective/cross-functional decision brief with both a 30-second takeaway and one-picture summary. Do not use for editing or polishing the source in place, a generic summary with no 3080/reader/visual requirement, or standalone whiteboard styling. Never modify the source; source-back every number, conclusion, risk, and action.
---

# 3080 Brief

**30-second judgment, 80% in one picture**

Create a new reader-first decision brief from a source document. Match the source format by default and keep the source unchanged.

## Output Contract

Open with `TLDR`, containing exactly three core units:

1. **一句话 / one-sentence judgment**: one highest-level judgment on the first line, followed only when needed by 1–3 short evidence, action, or boundary lines; the whole unit must work within 30 seconds.
2. **一张图 / one-picture summary**: one auditable visual covering at least 80% of value-weighted non-appendix claims; Feishu/Lark uses an editable whiteboard.
3. **一个表 / one key-question table**: 3–5 source-grounded questions with `问题 / 结论 / 为什么` or `Question / Conclusion / Why`.

Title the new artifact `3080 Brief｜原文标题`. Put a compact source link near the top without a standalone source heading.

## Core Contract

When goals conflict, apply: source truth → explicit user requirements → reader comprehension → 30-second judgment → one-picture 80% understanding → visual polish.

- Create a new output. Never edit, overwrite, reorder, comment on, clean up, rename, move, or change permissions on the source.
- Match output type to input type unless explicitly overridden: Feishu/Lark → new Feishu/Lark doc; Word/docx → new `.docx`; Markdown → new Markdown; HTML → new self-contained HTML. Ask only when type/support is materially ambiguous.
- Use the source's primary language unless the user explicitly requests another output language. Conversation, interface, request, or locale language is not an override. Apply the decision to title, TLDR, table, body, and visual.
- Exclude source appendix / 附录 / Appendix content unless the user explicitly includes it.
- Source-back every number, conclusion, risk, and recommendation. Preserve material denominator, period, sample, scope, significance, confidence, and metric definition. Mark unsupported gaps `原文未提供` / `not provided in the source` or `推断` / `inference`.
- Rebuild the narrative around what readers must understand, trust, decide, or do. Do not compress the source mechanically or impose a fixed body order; put decision implication before implementation detail unless implementers are the explicit audience.
- Every rendered brief must carry the mandatory `reading_path` contract defined in [reading-layout-contract.md](references/reading-layout-contract.md): state the reader decision, map one reader question and density level to every body section, put a takeaway before dense evidence, and bridge adjacent dense objects with explanation. This contract is validated by the shared `validate_brief.py` gate and cannot be skipped by changing output format.
- For each value-bearing title, heading, and lead, map `specific object -> source-backed action or change -> reader-observable result`, then write it naturally without forcing a sentence template. Record the object-action/result map for each value-bearing title, heading, and lead.
- Keep prompts, internal process/method language, style names, tool notes, and placeholders out of the artifact. Machine restrictions and semantic colors live in [config/3080-brief.json](config/3080-brief.json).
- Keep generated time, owner, version, location, permissions, and sharing defaults unless requested or operationally required.
- Use `lark-doc` for Feishu docs, `documents:documents` for Word, `lark-whiteboard` for live Feishu preview, and `beautiful-feishu-whiteboard` for Feishu style selection.

## Conditional Routing

Do not preload references. Read only resources whose condition is true.

| Need | Read / run |
| --- | --- |
| Resolve output format or conversion | [output-format-rules.md](references/output-format-rules.md) |
| Create Feishu output or diagnose dependencies | `scripts/check_dependencies.py --mode feishu --json`; read [dependency-and-installation.md](references/dependency-and-installation.md) only on BLOCKED/SKIP/FAIL |
| Inventory sources and claims | [source-inventory-template.md](references/source-inventory-template.md), [claim-ledger.schema.json](references/claim-ledger.schema.json); add [evidence-and-risk-rules.md](references/evidence-and-risk-rules.md) for material data, experiment, causal, metric, or risk claims |
| Plan batch execution and review readiness | [execution-efficiency.md](references/execution-efficiency.md); run `scripts/validate_review_readiness.py` before independent review |
| Draft/revise reader-facing content | [source-faithful-expression.md](references/source-faithful-expression.md); add [reader-optimization.md](references/reader-optimization.md) for clarity/jargon failures and [expression-anti-patterns.md](references/expression-anti-patterns.md) only for a concrete wording signal |
| Plan the cross-section reading path | [reading-layout-contract.md](references/reading-layout-contract.md); create the required `reading_path` object before rendering any format |
| Plan the brief and visual | [brief.schema.json](references/brief.schema.json), [visual-spec.schema.json](references/visual-spec.schema.json), [visual-pattern-library.md](references/visual-pattern-library.md), [theme-selection.md](references/theme-selection.md); add [semantic-color-system.md](references/semantic-color-system.md) for directional values/statuses |
| Build target-specific visuals | Feishu: [whiteboard-patterns.md](references/whiteboard-patterns.md), [feishu-doc-output.md](references/feishu-doc-output.md); HTML: [html-visualization.md](references/html-visualization.md), [html-design.schema.json](references/html-design.schema.json), [font-catalog.json](assets/html-kit/font-catalog.json) |
| Consider bitmap/image generation | Read [image2-auxiliary-rules.md](references/image2-auxiliary-rules.md) before sending any content |
| Run visual, audit, and comprehension review | [visual-blind-replay.md](references/visual-blind-replay.md), [review-packet-template.md](references/review-packet-template.md), [review-loop.md](references/review-loop.md); after all three audit reviewers pass, read [blind-reader-replay.md](references/blind-reader-replay.md) |

## Runtime

Use `standard` by default. Use `fast` only when the user explicitly prioritizes speed or skips independent review; hard source, language, relation, assertion, TLDR, coverage, and visual gates still apply, while audit/replay are skipped and disclosed. Use `strict` when requested or when conclusions affect material resources, policy/rules, causal claims, risk, or broad rollout; it adds exact P0/P1 relation replay and configured reader escalation. Mode details and retry limits are in [review-loop.md](references/review-loop.md).

1. **Route**: determine source/output type, language override, scope, constraints, and artifact lanes. For multiple briefs, follow the efficiency contract. For Feishu, check dependencies before fetch/write; installation or authentication needs separate approval.
2. **Ground**: before rendering, inspect all material non-appendix evidence. Build `source_inventory.md`, untranslated `source_non_appendix.md`, P0/P1 excerpts, and `claim_ledger.json`; record language basis, exclusions, sufficiency, source identity, evidence ceilings, protected relations, chartable data, risks/actions, mappings, and omissions. Reopen the source only for a missing fact or dispute.
3. **Clarify**: before drafting, ask up to three blocking questions only when ambiguity can change the main conclusion, metric meaning/scope, risk boundary, audience, next action, language, or protected relation. For non-blocking gaps, use explicit missing-source/inference labels. Shorten thin-source output instead of making it appear rich.
4. **Draft**: create one `brief.json` conforming to [brief.schema.json](references/brief.schema.json), used by every renderer. Before rendering, create its mandatory `reading_path`: one reader decision plus exactly one reader question and density level for each body section. Build a Pyramid opening and a source-shaped reader path with short judgment headings. Apply source-faithful expression only after the first draft; keep each assertion below its evidence ceiling and preserve valid terms, uncertainty, neutral tone, and necessary boundaries.
5. **Visualize**: create `visual_spec.json` before drawing and map every block to claim IDs. Choose the smallest content-fit relationship and exactly one allowed theme, with no fixed/silent default. Reach configured weighted coverage without omitting P0 claims. When three or more quantitative claims exist, or the conclusion depends on quantitative evidence, use a real quantitative encoding beyond boxes/prose; show a truthful boundary when extraction is unreliable. Keep semantic colors consistent across visual and body. Image generation is private-safe inspiration only, never the final evidence carrier. For HTML, also create reviewed `html_design.json` and preserve an auditable native-SVG fallback.
6. **Gate and readiness**: run deterministic checks before human-like review:

```bash
scripts/validate_claim_ledger.py claim_ledger.json
scripts/preflight_check.py DRAFT --source-inventory source_inventory.md --claim-ledger claim_ledger.json
scripts/check_expression_quality.py DRAFT --claim-ledger claim_ledger.json --non-appendix-source source_non_appendix.md
scripts/check_coverage.py claim_ledger.json --visual-spec visual_spec.json
scripts/validate_visual_spec.py visual_spec.json claim_ledger.json
scripts/validate_brief.py brief.json visual_spec.json
```

Validate the target render with `validate_whiteboard.sh` or `validate_html_output.py`. Fix deterministic failures, rerun checks by change impact, then run `validate_review_readiness.py`. A blocked or stale receipt blocks review.

### 7. Stabilize Comprehension Before Audit

In standard/strict, run Visual Blind Replay on the cropped picture, then Blind Reader Replay on the full render. Start with Primary and escalate only when configured. Resolve blocking comprehension issues before audit; fast mode uses disclosed self-checks.

### 8. Run The Final Independent Audit

After readiness and both replays pass, send one hash-locked batch to Reader, Source, and Visualization reviewers concurrently. Wait for all results. On failure, merge fixes, revise once, rerun affected pre-audit gates, then start the next complete batch for the new hash. Extra batches require a prior failure and remain capped at three; external blockers require a stop, not a retry.

### 9. Create And Verify

Create the new output only after applicable gates pass. Render Feishu with native XML and inspect the live board; build HTML with `scripts/build_html_brief.py brief.json visual_spec.json OUTPUT --design-plan html_design.json`, inspect rich/fallback views, and revalidate. Verify source unchanged, format/language, source citation, TLDR, claim coverage, theme/colors, accessibility, artifact hashes, and dependency status.

## Delivery

Return the generated link or absolute path, the source link/path, and concise verification notes: source unchanged; format/language basis; dependency/clarification status when relevant; Visual Blind Replay, three-review, and Blind Reader status or limitation; visual validation; and Feishu live-preview status when applicable. If `lark-cli` returns `_notice.update`, mention `lark-cli update` only after completing the task.
