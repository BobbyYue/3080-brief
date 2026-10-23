# Direct Expression

Lead with the source-supported answer. Compare a corrective sentence with an
equally accurate direct alternative, not only with deletion. Necessary
prohibitions, refusals, negative findings and uncertainty remain explicit.
"不是……而是……", "不能", "不按" and English equivalents are attention signals,
not banned words or automatic rewrite rules.

## Use The Existing Workflow

1. **Before prose:** add `expression_plan` to the existing required-answer plan.
   Select leading answer IDs, an opening move with its reason, and placements
   for essential limits. `reader_answers.py lock` requires it;
   `lifecycle_delivery.py` derives the same plan rather than accepting a second
   author-edited copy. See [required answers](required-reader-answers.md).
2. **While writing:** prepare the comparison for each complete unit with
   `direct_expression.py prepare --text UNIT --stage during --output REVIEW`.
   Fill that record as `expression_review` in the existing unit checkpoint.
   The lifecycle requires current text, a direct alternative or a justified
   protected original, and contextual keep/revise decisions.
3. **After writing:** the existing Reader independently completes
   `reader_value.checks.expression.direct_expression` for the full candidate,
   without the author's keep rationales. Inspect the title, takeaway, picture
   labels, question table and body together. Existing aggregation and delivery
   reject missing, stale or unresolved records. Source review still owns
   fidelity; Visualization still owns rendered reading. No fourth reviewer,
   additional round or visible checklist is added.

Use the script-generated templates for exact fields. Standard and Strict use
the existing independent Reader; explicit Fast uses the same record as a
disclosed self-check. Scoped updates retain unaffected review evidence and
check current expression through the existing editorial receipt. A pending
or revise decision cannot become PASS by changing only a status label.

## Compare Meaning And Reading Effort

- Identify the answer and any actual misconception. A real reader concern can
  justify correction; generic fear of misunderstanding is insufficient.
- Preserve subject, polarity, scope, conditions, confidence, responsibility,
  action and attribution. "No evidence of improvement" differs from "evidence
  of no improvement." A direct sentence can itself be negative.
- Explain the alternative's concrete benefit or retain the already-clear
  original. Alternatives are private comparison evidence, not extra versions
  the user must choose between.
- Review repeated warnings and labels as a group, including their placement.
  Each local caveat may have a reason while their accumulation still obscures
  the result. Conversely, overview/detail repetition may support separate
  entry points and the distinct jobs of the three required TLDR units.
- Keep interpretation-changing conditions beside their claims. A common scope
  can sit at a section entrance if relevant readers still encounter it; only
  background that does not change local decisions belongs in method notes.

Counts select candidates for inspection, not pass/fail thresholds. Identical
sentences share one comparison with all occurrence positions; the existing
final Reader owns cross-unit burden. The scanner does not establish semantic
quality. Reviewers must add missed wording and evaluate whole-text effort.
All-keep is acceptable when the comparisons support it.

For 3080, direct-expression records use the exact delivered candidate's reading
surface once, preferring its already-bound rendered text for HTML. Supporting
TLDR/body excerpts and visual specifications remain evidence, not extra visible
occurrences. Reuse the existing render snapshot; no new screenshot pass is added.
Actual repeated labels across the takeaway, visual and body remain in scope.

## Synthetic Examples

The following invented cases illustrate choices, not fixed replacements.

| Original | Candidate or decision | Meaning to protect |
| --- | --- | --- |
| 这次调整不是增加审批，而是把现有审批移到提交前。 | 这次调整把现有审批移到提交前，审批数量不变。 | The timing changes; the number does not. Keep correction if added approval is the reader's actual concern. |
| 不能省略的工作：核对分母。不能省略的工作：标注时间范围。 | 核对分母，并标注时间范围。 | Both required actions remain. Useful section-entry reminders may still recur. |
| 不按工单数量判断效果，而看问题是否解决。 | 以问题是否解决判断效果，工单数量不作为效果依据。 | Preserve the excluded criterion; do not invent another reporting requirement. |
| 禁止将未脱敏日志发到外部群。 | Keep the prohibition. | A vague reminder about safety weakens the restriction. |
| 本轮未发现错误率下降，样本不足以排除小幅变化。 | Keep the finding and limit. | "质量稳定" or "方案无效" would add unsupported certainty. |
| This is not proof of a rollout benefit, but a pilot result. | The result covers this pilot; rollout benefits remain untested. | Use only when both scope and untested status are source-supported. |

## Upgrade And Verification

Reader-value records are version 5. Old records without direct comparisons and
old functional plans/units without expression evidence need regeneration, not
automatic PASS backfill. Ongoing runs retain their original engine evidence;
an engine change blocks silent resume. Keep failed records and cumulative retry
budgets during any explicitly reviewed migration.

Use synthetic regression cases to verify record enforcement. A passing unit
test is not evidence that a real reader preferred a rewrite. The independent
review checks proposed alternatives; the Source role checks whether any actual
edit preserves evidence. This feature applies to the cooperating workflow and
does not automatically rewrite previously published articles.
