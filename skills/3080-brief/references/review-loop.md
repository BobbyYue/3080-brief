# Clarification And Review Loop

Use this reference whenever a source has ambiguity, unclear data, undefined terms, conflicting claims, or when creating the final `3080-brief` output.

## Contents

- Clarification gate and ambiguity handling
- Review readiness before rendering and delegation
- Isolated Visual Blind Replay before audit
- Full-artifact Blind Reader Replay before audit
- Three independent reviewer roles and packets
- Role-specific PASS criteria
- Revision loop, review tiers, and final release rule

## Clarification Gate

Do not force an interpretation when the source is ambiguous. Before drafting, classify uncertainty into blocking questions and non-blocking assumptions.

### Blocking Questions

Ask the user before drafting when the uncertainty could change:

- The main conclusion or one-sentence summary.
- The business value, experiment result, or metric interpretation.
- The risk boundary, rollout recommendation, or next action.
- The target reader or usage scenario.
- The meaning of a core term, acronym, internal project name, or custom metric.
- The comparison basis, denominator, time window, sample scope, or data source behind a key number.
- Whether a claim is source-backed or only the author's opinion.

Use this concise format:

```text
我需要先确认 N 个问题，否则可能误读原文：

1. <问题>
   - 影响：<会改变哪部分输出>
   - 默认处理：如果不确认，我会 <写“原文未提供” / 标注为“推断” / 暂不使用该结论>
```

Ask at most 3 questions at a time. If there are more than 3, ask the questions that most affect the opening summary, whiteboard spine, and risk boundary.

### Question Categories

Classify questions before asking so the user sees why the clarification matters:

| Category | Ask when | Example |
| --- | --- | --- |
| Concept | A term, acronym, internal project name, or custom metric is unclear | "`MMP 大客`在本文里指客户类型还是投放链路？" |
| Data | Denominator, period, sample, scope, source, or number consistency is unclear | "`收益 +12%` 的统计周期和分母是什么？" |
| Reader / Scene | The target reader or presentation scenario changes the output structure | "这份 brief 是给管理层决策、评审会，还是执行团队同步？" |
| Conclusion | The source data does not obviously support the stated conclusion | "原文数据只说明相关性，是否可以写成策略有效？" |
| Risk | Benefits are stated but risk, boundary, or fallback is missing | "是否有灰度/回滚/兼容性边界需要纳入风险？" |

When multiple categories apply, ask the questions in this order: Conclusion -> Data -> Risk -> Reader / Scene -> Concept.

### Non-Blocking Assumptions

Continue without asking when the missing information does not change the main conclusion. Mark the boundary clearly:

- Use "原文未提供" / "not provided in the source" for missing facts.
- Use "推断" / "inference" for reasoning based on the source.
- Move uncertain detail out of the opening summary and into caveats or risk notes.
- Do not put uncertain or inferred data into the whiteboard unless clearly labeled.

### Ambiguity Checklist

Before drafting, check:

- Undefined terms, abbreviations, internal codes, or historical context.
- Numbers without denominator, period, sample, segment, source, or filter.
- Inconsistent numbers across sections, charts, or tables.
- Data and conclusion mismatch.
- Benefits without risks or risks without fallback.
- User instruction that conflicts with source content.
- Reader or presentation scenario not specified when it changes the structure.

If any item affects the main decision, ask first.

## Pre-Audit Visual Blind Replay

After deterministic render validation, follow [visual-blind-replay.md](visual-blind-replay.md) before building audit packets. The visual blind reader receives only the cropped one-picture render at normal document width. Do not provide surrounding TLDR/body text, source evidence, claim IDs, visual spec, alt text, expected answer, coverage, or prior feedback.

The main agent compares the replay with the hidden ledger/spec and validates the result with `scripts/validate_visual_replay.py`. If it fails, revise the picture and rerun deterministic visual gates plus Visual Blind Replay. Do not spend the three audit reviews on a picture that an isolated reader cannot understand. After PASS, do not expose the replay transcript or its revision rationale to any audit reviewer.

Fast mode may use the same criteria as a self-check and must disclose that independent Visual Blind Replay was skipped.

## Review Readiness Gate

Follow [execution-efficiency.md](execution-efficiency.md). Before delegation,
run `scripts/validate_review_readiness.py` against the final source snapshot,
inventory, ledger, P0/P1 outline and excerpts, draft components, validation
notes, and actual renders. Pass its unchanged receipt to
`scripts/build_review_packet.py`. Missing or stale evidence blocks audit.

After Visual Blind Replay passes, run [blind-reader-replay.md](blind-reader-replay.md)
on the full rendered candidate. Resolve blocking comprehension defects before
building audit packets.

For HTML, first run [full-page-visual-replay.md](full-page-visual-replay.md) on a
source-isolated full-page screenshot and validate the geometry report. Both
files are hash-locked by readiness and the final review packet. This gate sits
between the one-picture replay and Blind Reader Replay.

## Three-Reviewer Subagent Protocol

After readiness and both replay gates pass, create three role-specific,
hash-locked packets using [review-packet-template.md](review-packet-template.md)
and `scripts/build_review_packet.py --role all`, then send them to three reviewer
subagents at the same time. The normal path uses one complete audit batch.

The main agent must not expose, quote, summarize, hint at, or use any reviewer's comments in prompts to the other reviewers before all three reviews have been submitted.

The reviewers are auditors, not co-authors. They should identify problems and required fixes; the main agent owns the revision.

### Reviewer Roles

Use three independent reviewer roles:

1. **Reader Comprehension Reviewer**
   - Persona: mixed reader layer, including decision maker, cross-functional reader, domain reader, implementer, and capable novice.
   - Focus: whether the document can be understood; whether the first opening line contains exactly one highest-level judgment; whether its 1–3 support lines contain only evidence, action, or boundary rather than a second peer conclusion; whether the opening works within 30 seconds and follows Pyramid Principle instead of a reusable template; whether value-bearing titles, headings, and leads identify their actual object and supported action, change, or result; whether the key-question table answers what readers most want to ask; whether the body follows SUCCESs Framework and Stepwise Information Delivery; whether Novice Reverse Review catches jargon/background gaps; and whether expression edits are minimal and contextual rather than driven by blanket word, punctuation, voice, or sentence bans.

2. **Source Coverage And Grounding Reviewer**
   - Persona: source auditor.
   - Focus: whether the draft covers most of the source's valuable non-appendix information, whether key non-appendix sections are missing, whether data/conclusions/risks are source-backed, whether every P0/P1 protected relation and numeric attachment is preserved, whether output assertion stays below its evidence ceiling, whether inferred content is labeled, whether thin material was shortened or clarified instead of padded, and whether source appendix content was excluded unless the user explicitly requested it.

3. **Visualization And Expression Reviewer**
   - Persona: presentation and visualization reviewer.
   - Focus: whether the one-picture visual visibly covers at least 80% of value-weighted non-appendix claims, whether visual forms match the content logic, whether the declared composition creates real hierarchy, whether values on one axis share a valid scope, whether decision-bearing entities and values are actually visible, whether Feishu/Lark style was selected from candidate styles instead of using a fixed default, whether chartable metrics are encoded visually instead of written as prose, whether image2/bitmap generation was used only for inspiration and not evidence, whether the board avoids text piles and empty pretty graphics, whether body-level expression forms help comprehension without defaulting to tables, and whether body/board semantic colors agree. This audit does not replace the earlier isolated visual replay.

### Reviewer Inputs

All packets share user constraints, source inventory, claim ledger, TLDR, review round, and artifact hashes. Give each role only the additional evidence it needs:

- Reader Comprehension: full reader-facing draft or rendered document and document preview. Body summaries alone are insufficient to judge readability.
- Source Coverage And Grounding: complete non-appendix source outline, P0/P1 source excerpts with locations, claim ledger, and body claim mapping. The reviewer must fail when it cannot independently verify coverage or grounding.
- Visualization And Expression: `visual_spec.json`, value-weighted coverage result, validation summary, selected style, local/live previews, rendered document preview, and the ledger's semantic directions/display values. For HTML, add `html_design.json`, selected local assets, runtime/fallback status, full-page screenshot, validated geometry report, and full-page replay record. Do not paste full SVG/XML unless debugging a specific defect. Do not provide replay transcripts, expected answers, failure reasons, or prior revision rationale.

Independence means reviewers do not see each other's opinions; it does not require identical evidence packets.

### Reviewer Output Format

Require each reviewer to return JSON only:

```json
{
  "reviewer_role": "reader | source | visual",
  "artifact_set_id": "sha256-derived ID from the packet",
  "review_round": 1,
  "verdict": "PASS | FAIL",
  "checks": [{"name": "role gate", "result": "PASS | FAIL", "reason": "evidence"}],
  "blocking_issues": [],
  "unsupported_claims": [],
  "missing_coverage": [],
  "required_fixes": []
}
```

Use role-specific binary gates instead of asking every reviewer to score every dimension. This reduces token use and avoids false precision while preserving strict failure behavior.

### PASS Criteria

Each reviewer can pass only when the items relevant to its role satisfy the standard.

Global pass conditions for every reviewer:

- No blocking issue remains.
- No unsupported claim or invented data remains.
- No internal writing rationale, method note, or source-justification meta-statement appears in the generated doc, including phrases such as `原文正文数据支持这个顺序` or `the source supports this order`.
- Artifact-set ID and review round match the packet.
- Key conclusions, metrics, risks, and next steps are traceable to source or explicitly marked as inference.
- Source appendix / 附录 / Appendix content is not included or counted as missing coverage unless the user explicitly requested appendix inclusion.
- The source link is present as compact low-emphasis citation/reference metadata, with no standalone `来源文档`, `原文链接`, `Source Document`, or equivalent heading.
- Output language matches the source primary language unless the user explicitly requested another language; request/conversation language alone is not an override.

Role-specific pass conditions:

- Reader Comprehension Reviewer:
  - 30-second judgment, Pyramid opening, body logic, Novice Reverse Review, and real rendered readability all pass.
  - Reader confusion risks are non-blocking or resolved.
  - A reader can understand the opening without reading implementation details.
  - The opening `TLDR` section contains the one-sentence summary, one-picture summary, and one compact key-question table.
  - The one-sentence judgment makes the source document's core value clear within 30 seconds; its support lines add only evidence, action, or boundary and do not introduce a second peer conclusion.
  - The key-question table answers the questions readers most want to ask while reading and explains necessary terms/口径 without becoming a separate body section.
  - The key-question table uses output-language reader-facing headers: `问题 / 结论 / 为什么` for Chinese or `Question / Conclusion / Why` for English; it does not use method labels such as `读者最想问`, `理解口径`, or `必要术语/口径`.
  - The key-question table is visually readable; if any cell needs more than 3 visual lines, the row height/vertical spacing is increased, the row is split, or detail is moved into the body.
  - The body has no `先回答关键问题`, `Key Questions First`, `术语与口径`, `Glossary`, `30 秒判断`, `30 秒读法`, or `30-second read` section heading.
  - The body does not use a fixed section order when the source logic calls for another sequence.
  - Body first-level headings are short judgment-style titles that advance the narrative, not long paragraph sentences or functional labels.
  - Every value-bearing title, heading, and lead names the actual object plus a supported action, change, or result; method labels, process descriptions, generic benefit words, and negative problem statements do not stand in for that value.
  - The reader can understand within the first minute what problem is being solved.
  - The reader can simply restate the proposed solution.
  - The reader can remember one concrete case, scenario, or story when the source supports one.
  - The reader knows who should do what next when the source provides ownership or next steps.
  - Decision-relevant directional values remain understandable without color alone, and their color agrees with the accompanying sign, arrow, label, or wording.
  - Title, TLDR, question table, body, and visual consistently use the declared output language, apart from necessary source-native terms.
- Source Coverage And Grounding Reviewer:
  - Source coverage and grounding both pass against the independent source outline/excerpts and claim ledger.
  - Every non-appendix P0/P1 claim preserves subject, predicate, object, scope, time/status, qualifiers, and values attached to their source objects.
  - `source_fact`, `source_author_claim`, `source_self_report`, `agent_inference`, and `unknown` remain distinct; output assertion does not exceed evidence ceiling.
  - Thin material is shortened or clarified; no external fact, invented example, personal experience, emotion, or false precision is used to make it appear richer.
  - Missing non-appendix source coverage is non-critical or intentionally placed outside the 80% board.
  - No source-backed risk, caveat, or key result is omitted from both board and body.
  - Appendix material is excluded from the draft and from missing-coverage objections unless the user explicitly requested it.
  - Source/output language and routing basis are independently verified; any language change includes the user's exact explicit override instruction.
- Visualization And Expression Reviewer:
  - Value-weighted one-picture coverage is at least the configured threshold after independently checking each claim's `visual_required_tokens` against the preview; declared percentages and block mappings are insufficient.
  - Visualization readability and style-content fit both pass.
  - If the source contains 3 or more quantitative claims, or the main conclusion depends on quantitative evidence, quantitative visual encoding passes.
  - If image2 or generated bitmap imagery was used, it influenced only composition/style and did not carry evidence, numbers, charts, risks, formulas, thresholds, or recommendations.
  - The whiteboard uses visual structure rather than rearranged text.
  - The whiteboard is not primarily boxes and prose when chartable metrics are available.
  - Body-level expression forms are chosen for comprehension; tables are not used as the default container for most content.
  - Classified directional values/statuses use the canonical configured semantic meaning in both body and whiteboard; candidate style colors do not override it.
  - Mathematical sign is not treated as business meaning, and color remains redundant with text, sign, arrow, shape, or position.
  - Whiteboard labels and annotations use the declared output language consistently with the body.
  - The preview visibly carries the conclusion and decision path instead of relying on hidden alt text or the visual spec; the independent Visual Blind Replay is verified separately before this audit.
  - `anchor_support` has one visibly dominant anchor plus smaller supports whose count is justified by evidence value and rendered readability; `comparison_grid` keeps peers directly comparable rather than stacking equal-weight panels.
  - Values sharing an axis have the same metric, unit, period, and denominator; visual titles stay at or below mapped evidence ceilings.
  - For HTML, the chosen layout and bundled typography fit the source; ECharts/Mermaid is used when it lowers understanding cost, no external runtime is required, and the complete native-SVG fallback remains available.

The Visualization And Expression Reviewer must return `FAIL` if chartable metrics are available but the whiteboard is primarily boxes plus prose, unless the draft explicitly explains that the data could not be extracted reliably or that the source lacks enough chartable data.

The Visualization And Expression Reviewer must return `FAIL` if a generated bitmap image carries source-critical evidence, numbers, charts, risks, formulas, thresholds, or recommendations, or if it replaces the editable 3080 whiteboard.

The Visualization And Expression Reviewer must return `FAIL` when a decision-relevant value classified in the claim ledger is unstyled in the body, has a conflicting semantic color on the whiteboard, or depends on color alone. Use `neutral` or `unknown` when the source does not support a favorable/unfavorable interpretation.

The first complete candidate passes its initial audit only when all three reviewers return `PASS`.

If one or more reviewers fail, wait for all reports, merge and deduplicate every
required fix, and make one coherent revision. Then use
[scoped-revalidation.md](scoped-revalidation.md) to decide which prior PASS
results remain valid. Do not restart all three roles merely because the package
hash changed.

### Revision Loop

Use this loop:

1. Complete source, claim, excerpt, and reviewer-input readiness.
2. Draft and render; pass deterministic gates.
3. Run Visual Blind Replay; for HTML, run geometry validation and Full-page Visual Replay; then run full-artifact Blind Reader Replay.
4. Fix blocking replay issues and rerun only affected pre-audit gates.
5. Run `validate_review_readiness.py` and lock its passing receipt.
6. Build one three-role packet set and launch all reviewers concurrently.
7. Wait for all reports, then aggregate matching roles, round, and hashes.
8. Snapshot the reviewed source, content, visual, desktop, and mobile layers.
9. If any role fails, revise once and generate a scoped rerun plan from the
   before/after manifests.
10. Run only the checks and roles required by that plan. When its receipt
    verifies, stop and proceed to creation; do not start a reassurance round.

After two targeted repair rounds, deliver the current version with unresolved
issues and ask whether to continue. A blocker caused by missing source, user
intent, permission, or external state stops immediately.

Use this wording:

```text
当前无法达到 3080-brief 质量标准，原因是：
- ...

需要补充：
- ...
```

## Runtime Profiles

- **Standard (default)**: run every deterministic hard gate, one expression scan, applicable one-picture/full-page visual replays, Primary Blind Reader Replay, then one complete three-reviewer audit batch. Escalate readers and repeat audit only under configured conditions.
- **Strict**: use when explicitly requested or when conclusions affect material resources, policy/rules, causal claims, risk, or broad rollout. Before reviewer packets are built, replay every non-appendix P0/P1 protected relation against its source excerpt and confirm output assertion does not exceed evidence ceiling. Then run the independent Visual Blind Replay, Standard audit, and configured reader escalation.
- **Fast**: use only when the user explicitly prioritizes speed or asks to skip independent review. Still run every deterministic hard gate and one expression scan. Replace Visual Blind Replay and the three independent reviewers with lightweight self-checks, skip Blind Reader Replay, and disclose all omissions. Never describe Fast output as independently reviewed.

No profile may bypass source grounding, blocking clarification, relation/claim-strength gates, source language, appendix exclusion, the new-doc-only rule, TLDR structure, visual coverage, or format validation.

## Pre-Audit Reader Replay

Blind Reader Replay is a pre-audit comprehension gate, not a substitute for the
final audit. Run Primary first and escalate only when configured. Audit starts
after the selected replays pass.

## Final Output Rule

Do not present a generated doc as final until either:

- the first candidate passes the complete audit, or a later candidate has a verified scoped-revalidation receipt that preserves unaffected PASS results and passes every affected check;
- The user explicitly asks to publish despite known unresolved issues.

Fast output follows the explicit exception above. Standard and Strict require
the complete initial audit or a valid scoped receipt; a changed package hash
alone does not invalidate unrelated evidence.
