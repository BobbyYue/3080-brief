---
name: 3080-brief
description: Create a new source-grounded decision brief in the source format by default (Feishu/Lark creates a new Feishu/Lark doc; Word/docx creates a new Word/docx) with a reader-fit Pyramid opening, one editable/auditable visual covering at least 80% of value-weighted non-appendix claims, and one key-question table. Use when the user names 3080-brief, 3080 brief, 3080skill, 读者视角总结, 3080总结, 3080summary, or 3080-onepager, or asks for a new reader-perspective/cross-functional decision brief with both a 30-second takeaway and one-picture summary. Do not use for editing or polishing the source in place, a generic summary with no 3080/reader/visual requirement, or standalone whiteboard styling. Never modify the source; source-back every number, conclusion, risk, and action.
---

# 3080 Brief

**30-second judgment, 80% in one picture**

Create a new reader-first decision brief from a source document. Match the source format by default and keep the source unchanged.

## Non-Skippable Runtime

Use `scripts/run_3080.py` for every production run. It is the only execution entrypoint: it freezes source evidence, runs deterministic checks, records the generated review draft, enforces review isolation, verifies the live output, and emits `delivery_receipt.json`.

Start execution in the same turn. Do not end with an acknowledgement, plan, status recap, or promise to continue. Never report success unless `run_state.json` has `delivery_allowed: true` and `delivery_receipt.json` has `verdict: PASS`. If the current host cannot execute the runner or a required document/whiteboard workflow, return `BLOCKED` with the exact missing capability; do not silently use a shorter manual flow.

Use `standard` by default. Use `fast` only when the user explicitly prioritizes speed or skips independent review; it retains every deterministic gate and requires three role-separated structured self-checks. Use `strict` when explicitly requested or when conclusions affect material resources, policy/rules, causality, risk, or broad rollout; replay every non-appendix P0/P1 relation before normal independent review.

## Output Contract

Open with `TLDR`, or a short source-language equivalent explicitly requested by the user. It contains exactly three core units:

1. **一句话 / one-sentence judgment**: exactly one highest-level judgment, followed by 1–3 short evidence, action, or boundary support lines.
2. **一张图 / one-picture summary**: cover at least 80% of value-weighted non-appendix claims; Feishu/Lark requires an editable native whiteboard.
3. **一个表 / one key-question table**: 3–5 source-grounded questions using `问题 / 结论 / 为什么` or `Question / Conclusion / Why`.

Build the body as **一条线 / one clear story line** that helps the reader follow the source logic. Title the new artifact `3080 Brief｜原文标题`. Put a compact source link near the top without a standalone source heading.

## Core Rules

Apply this priority: source truth → explicit user requirements → reader comprehension → 30-second judgment → one-picture understanding → visual polish.

- Create a new output. Never edit, overwrite, reorder, comment on, rename, move, or change permissions on the source.
- Match output type to input type unless explicitly overridden: Feishu/Lark → new Feishu/Lark doc; Word/docx → new `.docx`; Markdown → new Markdown.
- Follow the source primary language unless the user explicitly requests another output language. Conversation, interface, and locale language are not override evidence.
- Exclude appendix content unless explicitly included.
- Source-back every number, conclusion, risk, and recommendation. Preserve every denominator, period, sample, scope, status, qualifier, and causal boundary. Mark unsupported gaps as `原文未提供` / `not provided in the source` or `推断` / `inference`.
- Rebuild the narrative around what readers must understand, trust, decide, or do; do not impose a fixed body template.
- Keep prompts, process notes, style names, placeholders, and internal method language out of the artifact.

## Runtime Sequence

### 1. Initialize And Gate

Initialize a task-specific working directory with `run_3080.py init`. For Feishu, immediately run `scripts/check_dependencies.py --mode feishu --json`; request one explicit approval for the complete emitted installation bundle and rerun after installation/reload. A document request is not installation or authentication approval.

Then fetch the source. Inventory embedded sheets, Base, images, charts, and whiteboards carrying P0/P1 evidence or chartable data. A loaded Skill description or plan is not a source read.

### 2. Freeze Source Grounding

Create these files in the working directory:

- raw `source_before` fetch result;
- normalized non-appendix `source_non_appendix.md`;
- `source_inventory.md` using [references/source-inventory-template.md](references/source-inventory-template.md);
- `claim_ledger.json` using [references/claim-ledger.schema.json](references/claim-ledger.schema.json).

Protect subject-predicate-object relations, scope, time/status, qualifiers, and exact value attachment for every non-appendix P0/P1 claim. Classify evidence strength and thin material with [references/source-faithful-expression.md](references/source-faithful-expression.md). Run `run_3080.py ground`; later changes to any frozen artifact invalidate downstream checkpoints.

### 3. Draft And Preflight

Ask at most three questions only when ambiguity can change the main judgment, metric meaning, risk boundary, reader, action, language, or protected source relation. Otherwise continue with explicit missing-source/inference labels.

Create the complete draft and `visual_spec.json` before drawing. Map every visual block to claim IDs, preserve all P0 claims, and use real quantitative encoding when supported. For Feishu, choose one allowed `beautiful-feishu-whiteboard` style, create editable native-shape SVG, and never use a bitmap or media image as the required whiteboard.

Run `run_3080.py preflight`. It executes the claim, language, expression, coverage, visual-spec, and whiteboard gates. Do not create the review draft until this checkpoint passes.

### 4. Create And Record The Review Draft

Create the complete new artifact immediately after preflight. For Feishu, insert `<whiteboard type="svg">`, capture the new document URL, native whiteboard block ID and token, query the live whiteboard, and save the raw generated-document snapshot plus live preview. Run `run_3080.py record-output`.

An SVG inserted through image/media upload is not a valid Feishu whiteboard. The runtime rejects a generated document without a native whiteboard marker, matching block ID, matching query token, and non-empty live preview.

### 5. Review The Recorded Artifact

Run `run_3080.py prepare-review` to create three role-specific, hash-locked packets. In `standard` and `strict`, execute Reader, Source, and Visualization reviews independently with three distinct execution IDs. In `fast`, execute the same three role-separated checks as `self_check`; never describe them as independent.

Aggregate only matching artifact hashes and review rounds. Any failed check, unsupported claim, missing coverage, blocker, or required fix fails the round. Revise the generated draft, rerun preflight, update the same output, and repeat all three reviews. For `standard` and `strict`, run Primary Blind Reader Replay after all three reviews pass. See [references/review-loop.md](references/review-loop.md) and [references/blind-reader-replay.md](references/blind-reader-replay.md).

Run `run_3080.py record-review`. Standard/strict cannot pass with self-review evidence.

### 6. Re-Fetch And Finalize

Re-fetch the source and generated output after review. Run `run_3080.py finalize` with the raw post-run source snapshot and final live-output evidence. It must verify:

- source-before and source-after hashes match;
- output is accessible and distinct from the source;
- reviewed local artifacts have not changed;
- selected review profile actually passed;
- Feishu contains the same native editable whiteboard and a current live preview.

Resume from the reported missing checkpoint instead of restarting the whole task. Do not deliver when finalization is blocked.

## Conditional References

- Format routing: [references/output-format-rules.md](references/output-format-rules.md)
- Evidence, metrics, causality, and risk: [references/evidence-and-risk-rules.md](references/evidence-and-risk-rules.md)
- Reader restructuring: [references/reader-optimization.md](references/reader-optimization.md)
- Visual selection and SVG: [references/visual-pattern-library.md](references/visual-pattern-library.md), [references/semantic-color-system.md](references/semantic-color-system.md), [references/whiteboard-patterns.md](references/whiteboard-patterns.md)
- Feishu creation and live verification: [references/feishu-doc-output.md](references/feishu-doc-output.md)
- Dependency approval and installation: [references/dependency-and-installation.md](references/dependency-and-installation.md)

Read only references whose condition is active.

## Delivery

Return briefly:

- generated output link or absolute path;
- source link or absolute path;
- `delivery_receipt.json` verdict and key checks;
- selected profile and independent/self-review status;
- any limitation or exact blocker.

If `lark-cli` returns `_notice.update`, mention `lark-cli update` only after completing the task.
