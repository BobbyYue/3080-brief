# Reader Optimization

Use this reference when writing the summary doc or improving an existing generated summary from a reader and decision perspective.

## Contents

- Reader-first principle and layered workflow
- Common narrative mistakes and corrections
- TLDR and source-fit document shape
- Reader-facing and high-signal opening rules
- Data-analysis and Pyramid opening patterns

## Goal

The reader should understand the decision in 30 seconds, then have enough evidence to trust or challenge it. Do not merely compress the source. Rebuild the source into a reader-layered decision narrative.

## First Principle

Abandon the author's "what do I want to say" mindset. Use the receiver's "what does each reader layer need to understand, trust, decide, or do" mindset.

Traditional narrative is author-to-reader broadcasting. `3080-brief` narrative follows the cognitive path of different reader roles: their information habits, knowledge gaps, hidden assumptions, decision needs, and likely objections. The goal is to remove information gaps and break the knowledge curse at the root.

The output is not a shorter version of the source. It is a source-grounded synthesis that reorganizes the source into a clear, evidence-backed, professional, useful narrative.

## Reader-Layered Narrative Workflow

Before drafting, build a reader map:

1. **Reader layers**
   - Decision maker: needs conclusion, business value, risk boundary, and next action.
   - Cross-functional reader: needs context, why it matters, dependencies, and impact.
   - Domain reader: needs logic, evidence, metric definitions, and confidence.
   - Implementer: needs actionable constraints, rollout details, and edge cases when relevant.
   - Skeptical reviewer: needs source evidence, causal boundary, missing data, and assumptions.

2. **Reader questions**
   - What happened?
   - Why should this reader care?
   - What should they believe, decide, or do?
   - What evidence earns trust?
   - What could be misunderstood?
   - What is still uncertain?

3. **Narrative order**
   - Start with the conclusion and decision implication.
   - Add the minimum context needed to remove knowledge gaps.
   - Present the strongest evidence for the main claim.
   - Surface risk and confidence boundary before next steps.
   - Move implementation or detailed context after the decision spine unless the target reader is an implementer.

4. **Knowledge-curse check**
   - If a term, metric, mechanism, or dependency is obvious only to the author, translate or define it.
   - If the source jumps from data to conclusion, add the missing reasoning step and mark it as inference when needed.
   - If a section only reflects source chronology, reorder it by reader questions.

## Common Reader-Narrative Mistakes And Corrections

Use [expression-anti-patterns.md](expression-anti-patterns.md) when the draft or reviewer signals technical-detail-first narration, hidden jargon, one-depth-for-all readers, vague claims, source chronology, or hidden risk. Keep this file focused on the positive reader workflow and use the anti-pattern reference for symptom/correction pairs.

## Recommended Document Shape

1. **Opening title**
   - Use one first-level heading for the opening one-sentence, one-picture, and key-question table section.
   - Default title: `TLDR`.
   - Use a short source-language equivalent only when the user explicitly prefers localized wording.

2. **One-sentence summary**
   - Put this in the first callout.
   - Treat it as a Pyramid Principle opening, not a literal single sentence.
   - Its job is to let readers get the source document's core value within 30 seconds.
   - Make clear what value the source creates for the reader, why it matters, and what decision/action/understanding it enables.
   - Start with the highest-level reader judgment, then add 1-3 stepwise supporting lines.
   - Choose the top judgment from the source type, but keep the Pyramid Principle structure across all source types.
   - Put risk or confidence boundary here only when it changes the recommended action. Otherwise move it to the risk, caveat, or observation-action section.
   - Prefer 2-4 short lines or bullets when one long sentence would increase reading cost. Each line should contain one information unit and be short enough to avoid awkward wrapping in the target document.

3. **One-picture summary**
   - Put the whiteboard immediately after the first callout.
   - It should let readers absorb at least 80% of value-weighted non-appendix claims in one visual.
   - It should be useful even if the reader skips the rest of the doc.

4. **Key-question table**
   - Put one compact table inside the opening `TLDR` section.
   - Use it to answer the 3-5 questions readers would most want to ask while reading the document.
   - Prefer questions that unlock comprehension, trust, or action; explain only the terms, metrics, or口径 needed to understand those answers.
   - Use output-language reader-facing headers: `问题 / 结论 / 为什么` for Chinese or `Question / Conclusion / Why` for English; adapt only when the source type clearly calls for more concrete wording.
   - Keep the table concise. If any cell needs more than 3 visual lines, increase row height/vertical spacing, split the row, or move detail into the body.
   - Apply table-header and section-heading restrictions from config/preflight.

5. **Source citation**
   - Include the original link near the top as compact low-emphasis metadata.
   - Prefer quote-style or small/gray text when supported.
   - Apply source-heading restrictions from config/preflight.

6. **Source-fit body**
   - There is no fixed body structure or section order.
   - Choose the narrative sequence from the source content using SUCCESs Framework and Stepwise Information Delivery.
   - Each section should have one job and should start with the point before details.
   - Use examples, scenarios, or short stories when they make the source more concrete and memorable.
   - Choose prose, bullets, callouts, tables, charts, timelines, or other forms based on what the content needs.

7. **Novice Reverse Review pass**
   - Run this as a method check after the body structure exists.
   - Check whether a capable newcomer can understand the terms, background, hidden assumptions, and why the sections appear in this order.
   - Add explanations only where they reduce confusion.

## Reader-Facing Rules

- Lead with the answer and organize by reader cognition.
- Make body first-level headings form the narrative path through short judgment-style titles; apply exact heading and audience-label restrictions from config/preflight.
- Use stepwise layered delivery: top layer for judgment, middle layer for evidence, lower layer for details.
- Prefer short explanatory paragraphs, clear section openings, and one strong whiteboard. Use tables only when the relationship is easier to understand as a table.
- Use decision-grade statements that connect source evidence to judgment, uncertainty, and action.
- Proactively explain jargon, background, and hidden assumptions that cross-functional or novice readers may not know.
- Disclose source-backed risks and unknowns before next steps.
- Keep implementation details only when needed to support the decision.
- Follow the source language unless the user requests otherwise.

## High-Signal Opening Rules

Use these rules when the first 30-second callout or the opening whiteboard feels too generic.

- State the source-specific difference that changes interpretation, action, or validation rather than a generic category truth.
- Convert "many fields" into a decomposition of differences. Good 3080 openings explain the analytical role of each dimension: e.g. one dimension separates scenarios, another explains allocation or mechanism, and another identifies outcome quality or ownership.
- When a section has a layer-by-layer logic, make the opening follow the same progression. Start from the broad segmentation, then the allocation mechanism, then the competitive outcome, then the usable modeling signal.
- Put the method in the headline only when the method itself is the product; otherwise state what it revealed.
- The final landing should not repeat earlier bullets. It should synthesize them into a more abstract decision sentence, such as "the value of the multi-way cross is to split mixed differences into separately explainable and actionable signals."

## Data Analysis Writing Pattern

For analytical documents with charts, tables, and cross dimensions:

1. Start each subsection with the conclusion, not the table readout.
2. Use decision-changing numbers to prove the conclusion and connect each number to its scope and interpretation.
3. Separate "what is observed" from "why it may happen" and "what should be validated."
4. Highlight surprising or non-common-sense insight first, then add expected/common-sense findings as supporting context.
5. When a chart only shows data and the original text lacks analysis, add a short synthesis: main pattern, exception, likely mechanism, and confidence boundary.

## Pyramid Opening Patterns

Use the source type to choose the highest-level reader judgment, then deliver support step by step.

| Source type | Highest-level reader judgment | Stepwise support |
| --- | --- | --- |
| Data analysis | the non-obvious insight readers should remember | evidence, likely explanation, validation action |
| Experiment review | whether the experiment supports proceed, stop, or observe | core result, confidence boundary, action |
| Product planning | the product direction or plan judgment | sequence, dependency, decision needed |
| Strategy proposal | the strategic change and why it matters | value, rollout path, guardrail |
| Current-state inventory | the current map and priority judgment | key difference, gap, priority item |
| Problem diagnosis | the root issue and impact judgment | evidence, affected scope, repair action |
| Risk review | the risk posture and response judgment | impact, trigger signal, mitigation or observation |
| Technical design | the capability change and usable value | constraint, integration point, rollout condition |

Chinese Pyramid example:

> 本方案把 X 从旧判断 A 升级为新判断 B；实验显示核心指标 Y +x%，支持 Z 决策；但 R 风险仍需上线后观察。

Can be split into a callout:

> X 应从旧判断 A 升级为新判断 B。  
> 原文中的核心指标 Y +x%，足以支持 Z 决策。  
> 先灰度推进，同时把 R 风险纳入上线后观察。

English Pyramid example:

> This work shifts X from old rule A to new rule B; the source shows Y improved by x%, supporting Z; however, R remains a confidence boundary to monitor.

## Expression Failure Routing

See [expression-anti-patterns.md](expression-anti-patterns.md) for vague openings, fixed templates, inflated certainty, and their corrections. Exact discouraged phrases are maintained in config and surfaced by preflight warnings.
