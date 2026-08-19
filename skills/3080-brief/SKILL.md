---
name: 3080-brief
description: Create a new source-grounded decision brief in the source format by default (Feishu/Lark, Word/docx, Markdown, or self-contained HTML) with a reader-fit Pyramid opening, one editable or auditable visual covering at least 80% of value-weighted non-appendix claims, and one key-question table. Use when the user names 3080-brief, 3080 brief, 3080skill, 读者视角总结, 3080总结, 3080summary, or 3080-onepager, or asks for a new reader-perspective/cross-functional decision brief with both a 30-second takeaway and one-picture summary. Do not use for editing or polishing the source in place, a generic summary with no 3080/reader/visual requirement, or standalone whiteboard styling. Never modify the source; source-back every number, conclusion, risk, and action.
---

# 3080 Brief

**30-second judgment, 80% in one picture**

Create a new reader-first decision brief from a source document. Match the source format by default and keep the source unchanged.

## Output Contract

Open with `TLDR`, or a short source-language equivalent explicitly requested by the user. It contains exactly three core units:

1. **一句话 / one-sentence judgment**: the first line carries exactly one highest-level judgment; 1–3 short lines may follow only as evidence, action, or boundary support. Together they form one opening unit that works within 30 seconds.
2. **一张图 / one-picture summary**: one auditable visual covering at least 80% of value-weighted non-appendix claims; Feishu/Lark uses an editable whiteboard.
3. **一个表 / one key-question table**: 3–5 source-grounded questions using `问题 / 结论 / 为什么` or `Question / Conclusion / Why`.

Title the new artifact `3080 Brief｜原文标题`. Put a compact source link near the top without a standalone source heading.

## Core Contract

Apply this priority when goals conflict: source truth → explicit user requirements → reader comprehension → 30-second judgment → one-picture 80% understanding → visual polish.

- Create a new output. Never edit, overwrite, reorder, comment on, clean up, rename, move, or change permissions on the source.
- Match output type to input type unless explicitly overridden: Feishu/Lark → new Feishu/Lark doc; Word/docx → new `.docx`; Markdown → new Markdown; HTML → new self-contained HTML. Ask only when type/support is genuinely ambiguous.
- Follow the source primary language unless the user explicitly names another output language. Request/conversation/interface/locale language is not override evidence. Apply the selected language to title, TLDR, table, body, and visual.
- Exclude source appendix / 附录 / Appendix content unless the user explicitly includes it.
- Source-back every number, conclusion, risk, and recommendation. Preserve denominator, period, sample, scope, significance, confidence, and metric definition when present. Mark unsupported gaps `原文未提供` / `not provided in the source` or `推断` / `inference`.
- Rebuild the narrative around what readers must understand, trust, decide, or do. Put decision implication before implementation detail unless implementers are the explicit audience; do not impose a fixed body section order.
- For every value-bearing title, heading, or lead, map `specific object -> source-backed action or change -> reader-observable result`, then write it naturally. Remove method, process, and generic benefit wording only when no necessary fact, term, boundary, or uncertainty is lost; never force a fixed sentence pattern.
- Keep prompts, process rationale, style names, tool notes, placeholders, and internal method language out of the artifact. Machine-enforced restrictions and semantic colors live in [config/3080-brief.json](config/3080-brief.json).
- Keep generated time, owner, version, location, permissions, and sharing defaults unless the user requests or operations require a change.
- Use `lark-doc` for Feishu docs, `documents:documents` for Word, `lark-whiteboard` for live Feishu preview, and `beautiful-feishu-whiteboard` for Feishu style selection.

## Conditional Routing

Do not preload references. Read a resource only when its condition becomes true.

| Condition | Read / run |
| --- | --- |
| Output type is ambiguous or conversion is requested | [references/output-format-rules.md](references/output-format-rules.md) |
| Feishu output is selected, or dependency status is not PASS | `scripts/check_dependencies.py --mode feishu --json`; then [references/dependency-and-installation.md](references/dependency-and-installation.md) only for BLOCKED/SKIP/FAIL |
| Building evidence artifacts | [references/source-inventory-template.md](references/source-inventory-template.md) and [references/claim-ledger.schema.json](references/claim-ledger.schema.json) |
| Data, experiment, causal, metric, or risk evidence is material/unclear | [references/evidence-and-risk-rules.md](references/evidence-and-risk-rules.md) |
| First reader-structured draft exists, source material is thin, claim strength is uncertain, or expression needs revision | [references/source-faithful-expression.md](references/source-faithful-expression.md); add [references/expression-anti-patterns.md](references/expression-anti-patterns.md) only for a concrete wording signal |
| Narrative is unclear, jargon-heavy, or fails readability | [references/reader-optimization.md](references/reader-optimization.md) |
| Planning structured content or the one-picture summary | [references/brief.schema.json](references/brief.schema.json), [references/visual-spec.schema.json](references/visual-spec.schema.json), [references/visual-pattern-library.md](references/visual-pattern-library.md), and [references/theme-selection.md](references/theme-selection.md) |
| Directional values/statuses appear | [references/semantic-color-system.md](references/semantic-color-system.md) |
| Building/debugging a Feishu SVG | [references/whiteboard-patterns.md](references/whiteboard-patterns.md) |
| HTML output is selected | [references/html-visualization.md](references/html-visualization.md) |
| Considering bitmap/image generation | [references/image2-auxiliary-rules.md](references/image2-auxiliary-rules.md) before sending any content |
| Preparing audit review | [references/review-packet-template.md](references/review-packet-template.md) and [references/review-loop.md](references/review-loop.md) |
| All three audit reviewers pass | [references/blind-reader-replay.md](references/blind-reader-replay.md) |
| Creating/debugging Feishu XML or final Feishu output | [references/feishu-doc-output.md](references/feishu-doc-output.md) |

## Runtime State Machine

Use `standard` by default. Use `fast` only when the user explicitly prioritizes speed or asks to skip independent review; all source, language, relation, assertion, TLDR, coverage, and visual hard gates still run, and skipped review/replay must be disclosed. In Fast, stop the audit sequence after the self-check: do not build reviewer packets or start Blind Reader Replay, then create and verify the output. Use `strict` when explicitly requested or when conclusions affect material resources, policy/rules, causal claims, risk, or broad rollout; it adds exact P0/P1 relation replay before the normal review and configured reader escalation. See [references/review-loop.md](references/review-loop.md) for profile details.

### 1. Route And Gate

Determine source type, output type, constraints, and explicit language override. For Feishu/Lark, run the dependency diagnostic before fetching or writing. If `installation_request.required` is true, show exact source/version, destination, network/file/restart effect, and command; request explicit approval and stop installation for that turn. A document request is not installation or authentication approval. HTML uses the bundled offline renderer without another report skill, CDN, or runtime installation.

### 2. Ground The Source

Fetch with the matching tool and inventory embedded sheets, Bases, images, charts, and whiteboards. Inspect objects carrying P0/P1 evidence or chartable data. Build `source_inventory.md`, normalized `source_non_appendix.md`, and `claim_ledger.json`; record language basis/override, excluded appendix, sufficiency, stable claim/source identity, evidence ceiling/assertion, chartable data, risks/actions, mappings, and omissions. For each non-appendix P0/P1 claim, protect a subject-predicate-object relation plus scope, time/status, qualifiers, and exact value attachment. Reopen the source only to resolve a missing fact or dispute.

### 3. Clarify Blocking Ambiguity

Ask before drafting only when uncertainty can change the main conclusion, metric meaning/denominator/period/sample/scope, risk boundary, target reader, next action, source-language decision, or protected source relation. Ask at most three blocking questions at a time. If the material is thin, shorten the output or clarify; never make a thin source appear rich. Proceed through non-blocking gaps only with an explicit missing-source or inference label.

### 4. Draft And Revise For The Reader

Identify decision-maker, cross-functional, domain, implementer, and skeptical-reader gaps that actually matter. Structure the body from the source logic and reader decision path; make headings short judgments whose scan order explains the argument. Start the Pyramid opening with one primary judgment line, followed by 1–3 short evidence/action/boundary support lines; support lines must not introduce a second peer conclusion. Keep the question table inside TLDR; split dense rows or move detail to the body. Apply semantic meaning before color and retain signs/arrows/wording as non-color cues. Store the reviewed reader-facing content in one `brief.json` conforming to `references/brief.schema.json`; Feishu and HTML render from this same artifact.

Only after this first draft exists, run the source-faithful expression pass. Record the object-action/result map for each value-bearing title, heading, and lead; revise any line that leaves the object or supported result implicit behind a method label, process description, generic benefit, or negative problem statement. Keep each output assertion at or below its evidence ceiling and make only the smallest edit that resolves a concrete reading problem. Treat vague/template patterns as contextual clusters, not banned words. Preserve valid technical terms, uncertainty, passive voice, neutral tone, and punctuation; never add personal experience, emotion, examples, facts, precision, or a named person's voice.

### 5. Design The Visual

Create `visual_spec.json` before drawing and map each block to claim IDs. The visual must reach configured value-weighted coverage and cannot silently omit P0 claims. Select the relationship once, then render the same approved spec for the target format. If the source has at least three quantitative claims, or the main conclusion depends on quantitative evidence, include a real quantitative encoding beyond boxes and prose; if data cannot be extracted reliably, show a truthful boundary instead of false precision.

Select exactly one allowed `beautiful-feishu-whiteboard` theme for every visual output from document type, reader, tone, relationship, and density; never use a fixed or silent default. Record the choice and content-based rationale in `visual_spec.json`. Feishu reads only that theme's `design.md`; HTML uses the bundled adaptation of the same theme. Keep semantic colors consistent with the body. Use editable native-shape SVG and validate it. Bitmap generation is inspiration only: never send internal source text, identifiers, links, names, or real metrics, and never let bitmap output carry critical evidence or conclusions.

For HTML, render only the approved brief and visual spec with their selected theme. Use one dominant source relationship, judgment titles, visible value labels, metric scope, alt text, responsive/print CSS, and the canonical semantic colors. Critical conclusions, evidence, risks, and actions must remain visible without hover, animation, filtering, or expansion; collapsed blocks are P2 only.

### 6. Preflight And Audit

Run deterministic gates before reviewers:

```bash
scripts/validate_claim_ledger.py claim_ledger.json
scripts/preflight_check.py DRAFT --source-inventory source_inventory.md --claim-ledger claim_ledger.json
scripts/check_expression_quality.py DRAFT --claim-ledger claim_ledger.json --non-appendix-source source_non_appendix.md
scripts/check_coverage.py claim_ledger.json
scripts/validate_visual_spec.py visual_spec.json claim_ledger.json
scripts/validate_brief.py brief.json visual_spec.json
```

Validate the rendered visual for its target format; for Feishu use `scripts/validate_whiteboard.sh`; for HTML use `scripts/validate_html_output.py OUTPUT --visual-spec visual_spec.json`. Fix deterministic failures before review.

Build role-specific, hash-locked packets: Reader gets the readable draft; Source gets non-appendix outline, P0/P1 excerpts, protected relations, ceilings, and ledger; Visualization gets preview, spec, coverage, validation, and semantic mapping. Launch all three independently. Reader checks clarity without blanket language bans; Source fails relation drift, invented specificity, or overclaiming. Do not share reviewer comments before all submit. Any FAIL/blocker requires revision and all three rerun, up to three rounds. Never claim unavailable independent review.

Aggregate only matching roles, rounds, and artifact hashes with `scripts/aggregate_reviews.py`.

### 7. Replay Reader Understanding

After all three reviewers pass the same artifact set, follow the blind-reader reference. Start with Primary using only the rendered artifact and exactly three document-specific question-answer replays. Add Technical and Decision readers only under the configured escalation conditions; do not expose sources, expected answers, reviewer output, another replay, or the escalation reason. A blocking comprehension defect restarts preflight, all three reviews, and Primary replay.

### 8. Create And Verify The New Output

Create output only after gates pass. Feishu: build native XML with `scripts/build_feishu_brief.py`, then inspect the live board for clipping, overlap, overflow, and staleness. HTML: build the same reviewed inputs with `scripts/build_html_brief.py`, inspect desktop/mobile/print, and rerun validation. Verify source unchanged, format/language, citation, TLDR units, coverage, theme/semantic consistency, accessibility, and final hashes. Never publish Feishu while a dependency is SKIP/BLOCKED or a new skill awaits restart registration.

## Delivery

Respond briefly with:

- generated output link or absolute file path;
- source link or absolute file path;
- verification notes covering source unchanged, format/language decision, dependency status when applicable, clarification result, three-review status or blocker, blind-reader status or limitation, visual validation, and Feishu live-preview inspection when applicable.

If `lark-cli` returns `_notice.update`, mention `lark-cli update` only after completing the task.
