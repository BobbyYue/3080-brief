---
name: 3080-brief
description: Create a new source-grounded decision brief in the source format by default (Feishu/Lark creates a new Feishu/Lark doc; Word/docx creates a new Word/docx) with a reader-fit Pyramid opening, one editable/auditable visual covering at least 80% of value-weighted non-appendix claims, and one key-question table. Use when the user names 3080-brief, 3080 brief, 3080skill, 读者视角总结, 3080总结, 3080summary, or 3080-onepager, or asks for a new reader-perspective/cross-functional decision brief with both a 30-second takeaway and one-picture summary. Do not use for editing or polishing the source in place, a generic summary with no 3080/reader/visual requirement, or standalone whiteboard styling. Never modify the source; source-back every number, conclusion, risk, and action.
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
- Match output type to input type unless explicitly overridden: Feishu/Lark → new Feishu/Lark doc; Word/docx → new `.docx`; Markdown → new Markdown. Ask only when type/support is genuinely ambiguous.
- Follow the source primary language unless the user explicitly names another output language. Request/conversation/interface/locale language is not override evidence. Apply the selected language to title, TLDR, table, body, and visual.
- Exclude source appendix / 附录 / Appendix content unless the user explicitly includes it.
- Source-back every number, conclusion, risk, and recommendation. Preserve denominator, period, sample, scope, significance, confidence, and metric definition when present. Mark unsupported gaps `原文未提供` / `not provided in the source` or `推断` / `inference`.
- Rebuild the narrative around what readers must understand, trust, decide, or do. Put decision implication before implementation detail unless implementers are the explicit audience; do not impose a fixed body section order.
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
| Narrative is unclear, jargon-heavy, or fails readability | [references/reader-optimization.md](references/reader-optimization.md); add [references/expression-anti-patterns.md](references/expression-anti-patterns.md) only after a wording/expression signal |
| Planning the one-picture summary | [references/visual-spec.schema.json](references/visual-spec.schema.json) and [references/visual-pattern-library.md](references/visual-pattern-library.md) |
| Directional values/statuses appear | [references/semantic-color-system.md](references/semantic-color-system.md) |
| Building/debugging a Feishu SVG | [references/whiteboard-patterns.md](references/whiteboard-patterns.md) |
| Considering bitmap/image generation | [references/image2-auxiliary-rules.md](references/image2-auxiliary-rules.md) before sending any content |
| Preparing audit review | [references/review-packet-template.md](references/review-packet-template.md) and [references/review-loop.md](references/review-loop.md) |
| All three audit reviewers pass | [references/blind-reader-replay.md](references/blind-reader-replay.md) |
| Creating/debugging Feishu XML or final Feishu output | [references/feishu-doc-output.md](references/feishu-doc-output.md) |

## Runtime State Machine

### 1. Route And Gate

Determine source type, requested output type, user constraints, and explicit language override. During `3080-brief` installation, register the primary Skill first, run the Feishu dependency diagnostic, display the complete `approval_bundle`, and ask exactly once whether to install every listed missing dependency. One explicit approval authorizes all displayed CLI commands and host-native companion-Skill registration actions; never ask once per dependency. A decline keeps the primary Skill installed for non-Feishu output and the Feishu path blocked. For later Feishu/Lark runs, use the same bundle flow before fetching or writing. Show every known exact source/version, destination, network/file/restart effect, and either the emitted command or `host_install_prompt`; stop before installation until approval. When `host_registration_required` is true, use the current host's native Skill installer/import flow after approval; if that capability is unavailable, present `host_install_prompt` and keep the task blocked. Never infer a registry root from the script location. Node.js installation without an exact platform command and Feishu authentication remain separate approvals. A document request is not installation or authentication approval. Non-Feishu work never prompts for Feishu dependencies.

### 2. Ground The Source

Fetch with the matching tool and inventory every embedded sheet, Base, image, chart, and whiteboard before deciding relevance. Inspect every embedded object carrying P0/P1 evidence or chartable data. Build `source_inventory.md` and `claim_ledger.json`; record source/output language, valid language basis, exact override evidence, excluded appendix, stable P0/P1/P2 claim IDs, source locations, chartable data, risks, actions, board/body mappings, and omission reasons. Use these compact artifacts by default and reopen the source only to resolve a missing fact, excerpt, object, or dispute.

### 3. Clarify Blocking Ambiguity

Ask before drafting only when uncertainty can change the main conclusion, metric meaning/denominator/period/sample/scope, risk boundary, target reader, next action, or source-language decision. Ask at most three blocking questions at a time. Proceed through non-blocking gaps only with an explicit missing-source or inference label.

### 4. Draft For The Reader

Identify decision-maker, cross-functional, domain, implementer, and skeptical-reader gaps that actually matter. Structure the body from the source logic and reader decision path; make headings short judgments whose scan order explains the argument. Start the Pyramid opening with one primary judgment line, followed by 1–3 short evidence/action/boundary support lines; support lines must not introduce a second peer conclusion. Keep the question table inside TLDR; split dense rows or move detail to the body. Apply semantic meaning before color and retain signs/arrows/wording as non-color cues.

### 5. Design The Visual

Create `visual_spec.json` before drawing and map each block to claim IDs. The board must reach configured value-weighted coverage and cannot silently omit P0 claims. If the source has at least three quantitative claims, or the main conclusion depends on quantitative evidence, include a real quantitative encoding beyond boxes and prose; if data cannot be extracted reliably, show a truthful boundary instead of false precision.

For Feishu, choose an allowed `beautiful-feishu-whiteboard` style automatically from `CATALOG.md` unless the user already chose one; read only that style's `design.md`. Keep semantic colors consistent with the body. Use editable native-shape SVG and validate it. Bitmap generation is inspiration only: never send internal source text, identifiers, links, names, or real metrics, and never let bitmap output carry critical evidence or conclusions.

### 6. Preflight And Audit

Run deterministic gates before reviewers:

```bash
scripts/preflight_check.py DRAFT --source-inventory source_inventory.md --claim-ledger claim_ledger.json
scripts/check_coverage.py claim_ledger.json
scripts/validate_visual_spec.py visual_spec.json claim_ledger.json
```

Validate the rendered visual for its target format; for Feishu use `scripts/validate_whiteboard.sh`. Fix deterministic failures before review.

Build three role-specific, hash-locked packets: Reader receives the readable draft; Source receives non-appendix outline, P0/P1 excerpts, and ledger; Visualization receives preview, visual spec, coverage, validation, and semantic mapping. Launch Reader Comprehension, Source Coverage And Grounding, and Visualization And Expression reviewers independently. Until all submit, never reveal or use one reviewer's comments with another. Any FAIL, unsupported claim, blocking issue, or failed gate requires revision and all three reviewers rerun, up to three rounds. Do not claim independent review when unavailable.

Aggregate only matching roles, rounds, and artifact hashes with `scripts/aggregate_reviews.py`.

### 7. Replay Reader Understanding

After all three reviewers pass the same artifact set, follow the blind-reader reference. Start with Primary using only the rendered artifact and exactly three document-specific question-answer replays. Add Technical and Decision readers only under the configured escalation conditions; do not expose sources, expected answers, reviewer output, another replay, or the escalation reason. A blocking comprehension defect restarts preflight, all three reviews, and Primary replay.

### 8. Create And Verify The New Output

Create the new output only after the selected gates pass. For Feishu, query and inspect the live board for clipping, overlap, overflow, and stale rendering. Verify source unchanged, format/language correctness, source citation, TLDR's three units, coverage, semantic consistency, accessible output, and final artifact hashes with `scripts/verify_reviewed_artifacts.py`. Never publish a Feishu artifact while a required dependency is SKIP/BLOCKED or before a newly installed skill is registered after reloading the current agent.

## Delivery

Respond briefly with:

- generated output link or absolute file path;
- source link or absolute file path;
- verification notes covering source unchanged, format/language decision, dependency status when applicable, clarification result, three-review status or blocker, blind-reader status or limitation, visual validation, and Feishu live-preview inspection when applicable.

If `lark-cli` returns `_notice.update`, mention `lark-cli update` only after completing the task.
