---
name: 3080-brief
description: Create a new source-grounded decision brief in the source format by default (Feishu/Lark creates a new Feishu/Lark doc; Word/docx creates a new Word/docx) with a reader-fit Pyramid opening, one editable/auditable visual covering at least 80% of value-weighted non-appendix claims, and one key-question table. Use when the user names 3080-brief, 3080 brief, 3080skill, 读者视角总结, 3080总结, 3080summary, or 3080-onepager, or asks for a new reader-perspective/cross-functional decision brief with both a 30-second takeaway and one-picture summary. Do not use for editing or polishing the source in place, a generic summary with no 3080/reader/visual requirement, or standalone whiteboard styling. Never modify the source; source-back every number, conclusion, risk, and action.
---

# 3080 Brief

**30-second judgment, 80% in one picture**

Create a new reader-first decision brief from a source document. Match the source format by default and keep the source unchanged.

## Action-First Contract

For an explicit creation request, start tool work in the same turn. Do not end a turn with an acknowledgement, plan, status recap, capability description, or promise to continue. The first externally observable action must be the required dependency diagnostic when readiness is unknown; otherwise it must be the source fetch. Only a required approval or genuinely blocking clarification may interrupt execution. After either is resolved, resume immediately without asking whether to continue. Keep working until an output link/path exists or an exact blocker with its concrete next action is returned.

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
| Feishu output is selected, or dependency status is not PASS | Run `scripts/check_dependencies.py --mode feishu --json`; add `--host-capability lark-doc` and/or `--host-capability lark-whiteboard` only after confirming each workflow is actually callable; then read [references/dependency-and-installation.md](references/dependency-and-installation.md) only for BLOCKED/SKIP/FAIL |
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

### 1. Gate, Then Fetch

Determine source/output type, constraints, and explicit language override. For Feishu, run the dependency diagnostic first and declare `lark-doc` / `lark-whiteboard` host capabilities only when their workflows are actually callable. If anything is missing, display the complete `approval_bundle`, ask once to install or enable all listed items, execute the approved host actions, reload when required, and rerun the diagnostic. Keep Node.js installation without an exact command plus Feishu authentication/permissions as separate approvals. A document request is not installation approval. Non-Feishu work never prompts for Feishu dependencies.

Once ready, fetch the source immediately. A Skill specification, plan, or acknowledgement is not a read result. If no document content returns, report `BLOCKED: lark-doc runtime capability unavailable` plus the concrete host action; never ask a generic “continue?” question. Inventory embedded sheets, Base, images, charts, and whiteboards; inspect every object carrying P0/P1 evidence or chartable data. Build `source_inventory.md` and `claim_ledger.json`, including source/output language, excluded appendix, stable claim IDs, source locations, risks, actions, board/body mappings, and omission reasons.

### 2. Draft And Preflight

Ask at most three questions only when ambiguity can change the main conclusion, metric meaning/scope, risk boundary, reader, next action, or language decision. Otherwise continue with explicit missing-source/inference labels. Rebuild the narrative around the reader decision path; use short judgment headings, the required Pyramid opening, and the key-question table.

Create `visual_spec.json` before drawing and map each block to claim IDs. Preserve P0 claims and required weighted coverage. Use real quantitative encoding when the source supports it; otherwise show a truthful boundary. For Feishu, select an allowed `beautiful-feishu-whiteboard` style, use editable native-shape SVG, preserve semantic meaning beyond color, and validate the board.

Run and fix all deterministic gates before creating the output:

```bash
scripts/preflight_check.py DRAFT --source-inventory source_inventory.md --claim-ledger claim_ledger.json
scripts/check_coverage.py claim_ledger.json
scripts/validate_visual_spec.py visual_spec.json claim_ledger.json
```

Validate the rendered visual for its target format; for Feishu use `scripts/validate_whiteboard.sh`. Fix deterministic failures before review.

### 3. Create The Review Draft

Immediately after deterministic preflight passes, create the new output and store its URL/path; do not wait for independent reviewers. Write a complete review draft, not an empty placeholder. Feishu/Lark input must create a native Feishu/Lark document with an editable whiteboard; never silently substitute `.docx` unless the user explicitly requests Word. Keep the source unchanged. All later revisions update only this generated draft.

### 4. Review Without Stalling

When independent reviewer execution is available, build the three hash-locked role packets, run reviewers independently, aggregate matching artifact hashes, revise on any blocker, and rerun all three up to three rounds. After PASS, run Blind Reader Replay from Primary and escalate only under its configured conditions.

When independent reviewers are unavailable, do not stop or pretend they ran. Perform three sequential, role-separated self-checks using the same Reader, Source, and Visualization gates; fix every deterministic, grounding, or comprehension blocker; set `review_status=LIMITED` and `blind_reader_status=UNAVAILABLE`; then continue unless the user explicitly required independent review. This fallback may reduce validation strength but must not turn a document-creation request into a plan-only response.

### 5. Update, Verify, Deliver

Apply review fixes to the generated draft, never the source. For Feishu, inspect the live board for clipping, overlap, overflow, and stale rendering. Verify source unchanged, native output type, language, citation, TLDR units, coverage, semantic consistency, accessibility, and final artifact hashes with `scripts/verify_reviewed_artifacts.py`. A run is complete only when the new URL/path is accessible and distinct from the source. Progress text, Skill instructions, plans, acknowledgements, or promises to continue are never delivery; keep using tools or return the exact blocker.

## Delivery

Respond briefly with:

- generated output link or absolute file path;
- source link or absolute file path;
- verification notes covering source unchanged, format/language decision, dependency status when applicable, clarification result, three-review status or blocker, blind-reader status or limitation, visual validation, and Feishu live-preview inspection when applicable.

Never report success without the generated output link or absolute file path. For a blocked Feishu run, name the missing executable capability and the concrete host enablement/authentication action; do not present loaded Skill instructions as output.

If `lark-cli` returns `_notice.update`, mention `lark-cli update` only after completing the task.
