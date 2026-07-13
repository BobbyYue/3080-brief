# Clarification And Review Loop

Use this reference whenever a source has ambiguity, unclear data, undefined terms, conflicting claims, or when creating the final `3080-brief` output.

## Contents

- Clarification gate and ambiguity handling
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

## Three-Reviewer Subagent Protocol

Before final output, create three role-specific, hash-locked packets using [review-packet-template.md](review-packet-template.md) and `scripts/build_review_packet.py --role all`, then send them to three reviewer subagents at the same time. They must evaluate independently and must not see each other's comments before submitting their own verdicts.

The main agent must not expose, quote, summarize, hint at, or use any reviewer's comments in prompts to the other reviewers before all three reviews have been submitted.

The reviewers are auditors, not co-authors. They should identify problems and required fixes; the main agent owns the revision.

### Reviewer Roles

Use three independent reviewer roles:

1. **Reader Comprehension Reviewer**
   - Persona: mixed reader layer, including decision maker, cross-functional reader, domain reader, implementer, and capable novice.
   - Focus: whether the document can be understood, whether the one-sentence summary lets readers get the source document's core value within 30 seconds, whether the opening follows Pyramid Principle instead of a reusable template, whether the key-question table answers what readers most want to ask while reading, whether the body follows SUCCESs Framework and Stepwise Information Delivery, whether Novice Reverse Review catches jargon/background gaps, and whether reader questions are anticipated.

2. **Source Coverage And Grounding Reviewer**
   - Persona: source auditor.
   - Focus: whether the draft covers most of the source's valuable non-appendix information, whether key non-appendix sections are missing, whether data/conclusions/risks are source-backed, whether inferred content is labeled, and whether source appendix content was excluded unless the user explicitly requested it.

3. **Visualization And Expression Reviewer**
   - Persona: presentation and visualization reviewer.
   - Focus: whether the one-picture visual covers at least 80% of value-weighted non-appendix claims, whether visual forms match the content logic, whether Feishu/Lark style was selected from candidate styles instead of using a fixed default, whether chartable metrics are encoded visually instead of written as prose, whether image2/bitmap generation was used only for inspiration and not evidence, whether the board avoids text piles and empty pretty graphics, whether body-level expression forms help comprehension without defaulting to tables, and whether body/board semantic colors agree.

### Reviewer Inputs

All packets share user constraints, source inventory, claim ledger, TLDR, review round, and artifact hashes. Give each role only the additional evidence it needs:

- Reader Comprehension: full reader-facing draft or rendered document and document preview. Body summaries alone are insufficient to judge readability.
- Source Coverage And Grounding: complete non-appendix source outline, P0/P1 source excerpts with locations, claim ledger, and body claim mapping. The reviewer must fail when it cannot independently verify coverage or grounding.
- Visualization And Expression: `visual_spec.json`, value-weighted coverage result, whiteboard validation summary, selected style, local/live board previews, rendered document preview, and the ledger's semantic directions/display values. Do not paste full SVG/XML unless debugging a specific defect.

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
  - The one-sentence summary makes the source document's core value clear within 30 seconds.
  - The key-question table answers the questions readers most want to ask while reading and explains necessary terms/口径 without becoming a separate body section.
  - The key-question table uses output-language reader-facing headers: `问题 / 结论 / 为什么` for Chinese or `Question / Conclusion / Why` for English; it does not use method labels such as `读者最想问`, `理解口径`, or `必要术语/口径`.
  - The key-question table is visually readable; if any cell needs more than 3 visual lines, the row height/vertical spacing is increased, the row is split, or detail is moved into the body.
  - The body has no `先回答关键问题`, `Key Questions First`, `术语与口径`, `Glossary`, `30 秒判断`, `30 秒读法`, or `30-second read` section heading.
  - The body does not use a fixed section order when the source logic calls for another sequence.
  - Body first-level headings are short judgment-style titles that advance the narrative, not long paragraph sentences or functional labels.
  - The reader can understand within the first minute what problem is being solved.
  - The reader can simply restate the proposed solution.
  - The reader can remember one concrete case, scenario, or story when the source supports one.
  - The reader knows who should do what next when the source provides ownership or next steps.
  - Decision-relevant directional values remain understandable without color alone, and their color agrees with the accompanying sign, arrow, label, or wording.
  - Title, TLDR, question table, body, and visual consistently use the declared output language, apart from necessary source-native terms.
- Source Coverage And Grounding Reviewer:
  - Source coverage and grounding both pass against the independent source outline/excerpts and claim ledger.
  - Missing non-appendix source coverage is non-critical or intentionally placed outside the 80% board.
  - No source-backed risk, caveat, or key result is omitted from both board and body.
  - Appendix material is excluded from the draft and from missing-coverage objections unless the user explicitly requested it.
  - Source/output language and routing basis are independently verified; any language change includes the user's exact explicit override instruction.
- Visualization And Expression Reviewer:
  - Value-weighted one-picture coverage is at least the configured threshold, based on valuable non-appendix claims rather than decorative density.
  - Visualization readability and style-content fit both pass.
  - If the source contains 3 or more quantitative claims, or the main conclusion depends on quantitative evidence, quantitative visual encoding passes.
  - If image2 or generated bitmap imagery was used, it influenced only composition/style and did not carry evidence, numbers, charts, risks, formulas, thresholds, or recommendations.
  - The whiteboard uses visual structure rather than rearranged text.
  - The whiteboard is not primarily boxes and prose when chartable metrics are available.
  - Body-level expression forms are chosen for comprehension; tables are not used as the default container for most content.
  - Classified directional values/statuses use the canonical configured semantic meaning in both body and whiteboard; candidate style colors do not override it.
  - Mathematical sign is not treated as business meaning, and color remains redundant with text, sign, arrow, shape, or position.
  - Whiteboard labels and annotations use the declared output language consistently with the body.

The Visualization And Expression Reviewer must return `FAIL` if chartable metrics are available but the whiteboard is primarily boxes plus prose, unless the draft explicitly explains that the data could not be extracted reliably or that the source lacks enough chartable data.

The Visualization And Expression Reviewer must return `FAIL` if a generated bitmap image carries source-critical evidence, numbers, charts, risks, formulas, thresholds, or recommendations, or if it replaces the editable 3080 whiteboard.

The Visualization And Expression Reviewer must return `FAIL` when a decision-relevant value classified in the claim ledger is unstyled in the body, has a conflicting semantic color on the whiteboard, or depends on color alone. Use `neutral` or `unknown` when the source does not support a favorable/unfavorable interpretation.

The final draft passes only when all three reviewers return `PASS`.

If one or more reviewers fail, the main agent must merge required fixes across all reviewers, deduplicate conflicts, revise the draft, and re-run all three reviewers. Do not only re-run the reviewer that failed; fixes in one area can break another.

### Revision Loop

Use this loop:

1. Draft v1.
2. Build three role-specific, hash-locked reviewer packets.
3. Three reviewers evaluate independently in parallel from their role-specific evidence.
4. Do not aggregate, summarize, or share any review until all three reports are complete.
5. Run `scripts/aggregate_reviews.py` to verify roles, artifact-set ID, round, verdicts, and blockers; then aggregate the three reports.
6. If all three return `PASS`, proceed to Blind Reader Replay using `blind-reader-replay.md`.
7. If any reviewer returns `FAIL`, revise the required failing areas.
8. For follow-up rounds, send only previous blocking issues, revision diff/summary, changed excerpts, and unchanged packet sections needed to verify the fix.
9. Re-run all three reviewers.
10. Repeat up to 3 rounds.

If any reviewer still fails after 3 rounds, or if a blocker depends on missing user/source information, stop and ask the user for the required clarification instead of publishing a final version.

Use this wording:

```text
当前无法达到 3080-brief 质量标准，原因是：
- ...

需要补充：
- ...
```

## Review Tier

Use the review tier that matches the task risk:

- **Full Review**: default for strategy, experiment result, data analysis, management-facing, policy/rule change, or any doc with material business/risk implications. Run all three reviewers with full scoring and required fixes.
- **Light Review**: allowed for low-risk internal summaries or quick drafts when the source is short and factual. Still run all three reviewers independently, but each returns only `Verdict`, `Top Issues`, and `Required Fixes`. Any `FAIL` still blocks final output.
- **Skip Review**: allowed only when the user explicitly asks for fastest possible output or says to skip review. Run a lightweight self-check against the same PASS criteria and disclose that reviewer validation was skipped.

Never use review tiering to bypass source grounding, clarification of blocking ambiguity, the new-doc-only rule, or Blind Reader Replay. If review is explicitly skipped, disclose that replay cannot be treated as reviewer-approved validation.

## Post-Review Reader Replay

Audit review and Blind Reader Replay are sequential quality gates, not parallel substitutes. After all three audit reviewers pass the same artifact set, follow [blind-reader-replay.md](blind-reader-replay.md): run Primary first, conditionally escalate to Technical and Decision, and restart preflight plus all three reviewers after any blocking replay-driven revision.

## Final Output Rule

Do not present a generated doc as final until either:

- All three reviewers return `PASS` and the required Blind Reader Replay completes without a blocking comprehension failure, or
- The user explicitly asks to publish despite known unresolved issues.

If the user asks to skip review, still run a lightweight self-check against the same PASS criteria and disclose the skipped-review risk.
