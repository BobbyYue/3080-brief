# Expression Anti-Patterns

Read this reference only when drafting starts to look templated or vague, Novice Reverse Review finds comprehension friction, preflight emits expression warnings, or a reviewer fails narrative/readability/visual-expression gates. Exact prohibited headings, meta-statements, placeholders, audience labels, and discouraged phrases live in `config/3080-brief.json`; do not duplicate those lists here.

## Contents

- Opening and TLDR table anti-patterns
- Body narrative and evidence-language anti-patterns
- Visual-expression anti-patterns
- Meta/delivery anti-patterns and review routing

## Opening Anti-Patterns

### Fixed Label Template

Symptom: every source becomes the same sequence of conclusion, evidence, and next step, regardless of whether the source is analysis, planning, design, status, or risk review.

Correction: keep Pyramid Principle constant but let the source type determine the top judgment and supporting sequence. Omit a support line when it does not help the reader trust or use the judgment.

### Literal One-Sentence Constraint

Symptom: the opening becomes one long sentence with several clauses and high scanning cost.

Correction: use 2-4 short lines by default, one information unit per line. Treat “one sentence” as one Pyramid opening unit, not one grammatical sentence.

### Obvious Or Vague Conclusion

Symptom: the opening says only that something changed, matters, improved, or needs observation.

Correction: state the source-specific difference, consequence, evidence boundary, or decision that changes reader understanding. Replace vague benefit language with a concrete source-backed scenario or metric when available.

### Method Name As Headline

Symptom: a methodology label is presented as the reader-facing insight.

Correction: state what the method revealed. Name the method only when it is itself the product or decision object.

## TLDR Table Anti-Patterns

### Writer-Centric Headers

Symptom: headers describe the summarization method rather than the reader’s question and answer.

Correction: default to `问题 / 结论 / 为什么` or the configured source-language equivalent. Put only terminology needed to understand an answer inside the relevant cell.

### Table As A Glossary Dump

Symptom: the table becomes a dense terminology inventory or duplicates the body.

Correction: keep 3-5 questions that unlock comprehension, trust, or action. Move long explanation to the nearest body section.

### Cramped Cells

Symptom: one cell contains several paragraphs or more than about three visual lines.

Correction: increase row height, split the question, shorten the answer, or move detail into prose.

## Body Narrative Anti-Patterns

### Functional Or Author-Centric Headings

Symptom: headings name document mechanics, audience, remaining information, or reading time instead of advancing the argument.

Correction: write short judgment-style headings. Reading only the headings should reveal the reasoning path.

### Source Chronology Replay

Symptom: the brief follows the original outline even when readers need value, problem, evidence, and boundary in another order.

Correction: organize by the reader’s cognitive and decision path while preserving source truth.

### Technical Detail Before Reader Value

Symptom: parameters, architecture, or implementation appear before the reader knows what problem or decision they support.

Correction: lead with the source-fit judgment, then reveal the minimum context and evidence needed to trust it. Technical detail can lead only when implementers are the explicit target.

### One Depth For Every Reader

Symptom: decision context, business implications, evidence details, and implementation constraints are mixed at one level.

Correction: make the top layer independently complete, then reveal professional detail stepwise where it changes trust or action.

### Table-First Body

Symptom: most sections are tables even when prose, a chart, a timeline, or a concrete example would be easier to understand.

Correction: choose the expression form from the relationship. Start important dense sections with a short explanatory paragraph.

### Hidden Risk Or Unsupported Story

Symptom: benefits are memorable but risk, uncertainty, denominator, sample, or causal boundary is absent; alternatively, a story is added that the source does not support.

Correction: preserve decision-changing boundaries and use examples only when traceable to the source. Label inference explicitly.

## Evidence Language Anti-Patterns

### Numeric Roster

Symptom: numbers are listed without showing which one supports which judgment.

Correction: use only decision-changing numbers and connect each to a claim, scope, and interpretation.

### Causal Overreach

Symptom: correlation, directional evidence, or an observational split is written as proof of mechanism or policy effect.

Correction: separate fact, hypothesis, and action. Use validation or monitoring as the action when causality is unproven.

### Inflated Certainty

Symptom: words such as “significant,” “proven,” “fully solved,” or “no risk” exceed the source evidence.

Correction: preserve statistical and confidence qualifiers and use conservative source-grounded language.

## Visual Anti-Patterns

### Styled Text Pile

Symptom: prose is rearranged into cards with decorative arrows, but position, size, line, or grouping carries no additional meaning.

Correction: encode the source relationship as comparison, flow, hierarchy, threshold, matrix, funnel, timeline, distribution, or boundary.

### Pretty But Empty

Symptom: the board is polished but drops key evidence, logic, risk, or action.

Correction: map every board block to claim IDs and pass value-weighted coverage before release.

### One Form For Everything

Symptom: every claim becomes the same card, or multiple requested styles differ only by palette.

Correction: vary visual skeleton and encoding according to relationship and emphasis. Repeated forms are valid only for true peer items.

### Text-Only Quantitative Board

Symptom: chartable values are written as large numbers inside boxes.

Correction: use at least one truthful quantitative encoding when the conclusion depends on numbers or the configured quantitative gate applies.

### Risk-Free Benefit Story

Symptom: gain is visually dominant while source-backed risk or confidence boundary is hidden in small text.

Correction: give decision-changing risk a visible boundary, lane, trigger, band, or matrix position.

## Meta And Delivery Anti-Patterns

### Process Language In The Artifact

Symptom: the document or board explains how it was summarized, which style was chosen, why sections were ordered, or which tool produced it.

Correction: show the claim and evidence directly. Keep prompts, style names, source-processing notes, and tool rationale outside the artifact.

### Source Reference Competes With Content

Symptom: source metadata becomes a standalone high-emphasis section.

Correction: keep one compact, low-emphasis citation near the top in the output format’s supported reference style.

## Review Routing

- Exact phrase, heading, placeholder, and audience-label violations: `config/3080-brief.json` plus `scripts/preflight_check.py`.
- Reader comprehension, Pyramid opening, body logic, and jargon problems: Reader Comprehension reviewer.
- Unsupported claims and missing source boundaries: Source Coverage And Grounding reviewer.
- Text piles, wrong visual form, weak coverage, or style-only reskins: Visualization And Expression reviewer.
