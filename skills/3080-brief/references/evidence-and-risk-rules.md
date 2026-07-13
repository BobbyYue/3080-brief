# Evidence And Risk Rules

Use this reference before writing claims, data interpretations, risks, or recommendations.

## Source Grounding

- Every metric, result, conclusion, risk, and next step must be traceable to the source.
- Exclude source appendix / 附录 / Appendix content from summary claims and coverage checks unless the user explicitly asks to include appendix material.
- If the source provides a number, preserve its sign, unit, scope, population, and p-value/confidence if available.
- If the source does not provide a value or threshold, write "原文未提供" / "not provided in the source".
- Do not calculate new business results unless the user explicitly asks and the source provides enough data.
- Do not turn a directional observation into a proven conclusion.
- Assign every valuable non-appendix claim a stable claim ID and P0/P1/P2 priority in `claim_ledger.json`; preserve its source location and inference state through the board, body, and reviewer packet.

## Claim Hierarchy

Separate evidence into three layers:

1. **Main claim**
   - The metric or conclusion the source uses to justify the decision.
   - Usually one primary metric, not a list of all positive numbers.

2. **Supporting evidence**
   - Ablations, budget buckets, regional splits, partial data, early reads, or secondary metrics.
   - Helpful, but not equal to the main claim.

3. **Confidence boundary**
   - Small sample, short period, low coverage, non-converged region, inconsistent segment, logging issue, production-scope mismatch.
   - Must be visible in the summary and whiteboard.

## Risk Treatment

Explain source-backed risks in the format that best fits the content: prose, bullets, callout, matrix, table, timeline, or visual boundary. Do not default to a risk table.

Rules:

- Use severity only when it is defensible from the source. Otherwise use "Needs observation".
- Do not invent thresholds. If the source says to monitor SWR but gives no threshold, write "monitor SWR; source does not provide threshold".
- For rollout documents, include rollback, reverse experiment, grey release, or monitoring only when source-backed.
- For analysis documents, distinguish "calibration signal" from "policy rule".

## Recommendation Rules

Good recommendations answer:

- What can be done now?
- What should not be generalized yet?
- What must be watched next?

For strategy rollout:

- Proceed / do not proceed / proceed with protection.
- Protection mechanism.
- Monitoring focus.
- Expansion condition.

For analytical calibration:

- Use as signal / do not use as final rule.
- Segment where the finding is strongest.
- Evidence gap before policy change.

## Conservative Language

Use:

- "原文显示..."
- "从原文可判断..."
- "该证据支持..."
- "仍需观察..."
- "directional, not final"
- "the source does not provide..."

Avoid:

- "显著证明" unless statistical significance is in the source.
- "完全解决" unless the source says so.
- "没有风险" unless the source explicitly supports it.

## Insight Strength Rules

Use these rules when turning chart/table observations into 3080 insights.

- A strong insight usually changes interpretation or action. It is stronger than a restatement of the biggest bar, highest value, or expected business common sense.
- For multi-dimensional data, first ask which dimension explains the largest value difference, then whether the next dimensions change traffic allocation or only describe the same pattern.
- Treat multi-way crosses as decomposition tools. State what each dimension contributes to the explanation: scenario split, allocation mechanism, outcome quality, coverage boundary, or validation need.
- If an observed pattern could reflect platform strategy, system mechanics, sample selection, or field coverage, do not collapse it into one causal explanation. Present the strongest supported reading and the competing explanations.
- For same-system vs cross-system observations, use directional language unless the source includes an experiment or randomized test. Good phrasing: "数据支持同体系组合存在结果优势的方向性判断，但不能单独证明系统主动优先分配."
- When comparing two mechanisms or ownership paths, control the visible scope: first hold the strongest segmentation dimension constant, then compare the mechanism layer, then compare the outcome layer. Otherwise the result may be polluted by upstream segment differences.

## Fact / Hypothesis / Action Split

For every important analytical claim, keep three layers explicit:

- Fact: directly observed from the source table/chart. Example: "在相同上游分组内，路径 A 的目标指标高于路径 B."
- Hypothesis: mechanism that may explain the fact. Example: "这可能说明系统分配、样本结构或策略偏好影响了结果质量."
- Action: what to do before using it as policy. Example: "需要补齐覆盖、校验口径，并通过实验或监控验证后，才能作为上线规则."

Do not let a whiteboard or summary skip from fact directly to policy. If evidence is directional, the action should be validation, monitoring, or feature construction, not immediate rule change.
