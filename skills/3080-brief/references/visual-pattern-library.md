# Visual Pattern Library

Use this reference when choosing the visual pattern for the opening whiteboard or body-level visual blocks.

This library synthesizes common practice from public visualization references such as FT Visual Vocabulary, From Data to Viz, Data Visualisation Catalogue, Data Viz Project, Vega-Lite examples, Observable Plot, Datawrapper, Flourish, and mature agent skill structures. Do not depend on those sources at runtime. Use this file as the local decision system.

## Contents

- Core selection principle and relationship tree
- Quantitative encoding gate and chart-first flow
- Executive and body-level pattern cards
- Visual encoding grammar and anti-pattern routing
- Advanced cross-dimension analysis
- Selection checklist

## Core Principle

Choose a pattern by the reader question and information relationship, not by visual appearance.

Before rendering, write `visual_spec.json` using `visual-spec.schema.json`. Every block must name the claim IDs it carries. Use `scripts/render_visual_spec.py` for supported native-shape quantitative blocks, then compose or refine the complete board with the selected Feishu palette.

The decision order is:

1. What should the reader understand, trust, decide, or do?
2. What information relationship proves that point?
3. Which visual encoding makes that relationship easier to see than prose?
4. What must stay on the board to preserve source value?
5. What should move to the body or generated appendix / 后置补充区?

## Visual Pattern Selection Tree

Use this tree before drawing.

| Reader question | Source information relationship | Prefer pattern family | Common chart or whiteboard form |
| --- | --- | --- | --- |
| What changed? | Baseline vs new state, before vs after | Change / Deviation | Before-after panel, slopegraph, delta card, migration flow |
| Why does it matter? | Value driver, business impact, experiment result | Evidence / Magnitude | Big-number evidence cards, bar comparison, value bridge |
| Where is the difference? | Segment, market, platform, channel, cohort | Comparison / Segmentation | Matrix, heatmap table, quadrant, grouped bars |
| How does it work? | Step, dependency, mechanism, causal chain | Flow / Process | Flowchart, swimlane, causal chain, funnel |
| What narrows or drops off? | Filtering, conversion, exclusion, prioritization | Funnel / Staged Filter | Funnel, staged filter, drop-off path |
| What is the system shape? | Layer, module, hierarchy, ownership | Hierarchy / Architecture | Layered stack, capability map, nested map |
| What should we prioritize? | Impact vs effort, risk vs value, urgency vs confidence | Prioritization / Trade-off | 2x2 matrix, weighted score table, priority lane |
| What is risky or uncertain? | Probability, impact, boundary, trigger, mitigation | Risk / Guardrail | Risk matrix, guardrail box, scope boundary map |
| What happens over time? | Trend, phase, rollout, milestone | Time / Roadmap | Timeline, phased roadmap, Gantt-lite, trend line |
| What composes the whole? | Share, mix, allocation, contribution | Part-to-whole / Composition | Stacked bar, treemap-lite, contribution bridge |
| What connects to what? | Network, handoff, data lineage, dependency | Relationship / Network | Node-link map, dependency map, lineage path |
| Where does it happen? | Region, market, location, surface, scenario | Spatial / Scenario Map | Region grid, scenario map, platform map |

If none of these relationships is present, use a structured table or callout instead of forcing a diagram.

## Quantitative Visual Encoding Gate

Use this gate before choosing any whiteboard layout.

The whiteboard must include at least one quantitative visual encoding beyond text cards when either condition is true:

- the source contains 3 or more quantitative claims; or
- the main conclusion depends on quantitative evidence, even if there are fewer than 3 numbers.

Acceptable quantitative encodings include:

- bar or dot plots for proportions, rates, counts, or ranked comparisons;
- slope charts or before/after bars for deltas;
- scatter, diagonal comparison, or calibration sketches for relationship and model-fit claims;
- threshold split charts for rule cutoffs, pass/fail boundaries, or trigger levels;
- matrices for cross-classification, over/under interpretation, risk/value trade-offs, or segment comparison;
- funnels for staged filtering, conversion, exclusion, or narrowing logic;
- distribution strips, bands, or range markers for spread, uncertainty, or confidence boundary.

Fallback rule:

- Use a process diagram, evidence-card board, or text-heavy decision spine only when the source lacks chartable data or the available data cannot be extracted reliably.
- If chart data exists in embedded sheets, charts, images, or whiteboards and affects the conclusion, inspect or query it before drawing.
- If extraction is incomplete, do not draw precise quantitative charts. Use a boundary visual, direction marker, or caveat band and label the limitation.

## Data Relationship To Default Visual

Use this mapping to avoid defaulting to boxes and prose.

| Source relationship | Default visual | Notes |
| --- | --- | --- |
| Proportion, rate, share, success/failure ratio | Horizontal bar, dot plot, stacked bar | Best for showing difference size quickly. |
| Before vs after, baseline vs new | Slope chart, delta bar, paired dots | Make the change magnitude visible. |
| Threshold, cutoff, trigger, rule boundary | Threshold split chart, band with marker, pass/fail lane | Show which side of the boundary matters. |
| Formula, calibration, model fit, expected vs observed | Calibration sketch, diagonal scatter, reference-line plot | Show benchmark/reference line and observed direction without inventing points. |
| Over/under, high/low, true/false interpretation | 2x2 matrix, diagonal comparison, quadrant | Good for decision interpretation and category meaning. |
| Segment, cohort, market, platform comparison | Matrix, heatmap table, grouped bars, bubble comparison | Encode size/value/risk separately when source supports it. |
| Funnel, exclusion, filtering, stage drop-off | Funnel, staged filter path, drop-off bars | Use when the logic narrows scope. |
| Distribution, variance, uncertainty, confidence | Distribution strip, range band, confidence boundary | Prefer over a paragraph of caveats. |
| Ranking or priority | Ordered bar, priority lane, ranked dots | Put the decision-changing rank first. |
| Time trend or rollout phase | Line, timeline, phase band | Separate trend evidence from execution plan. |

## Chart-First Whiteboard Flow

When chartable data exists, use this order:

1. List all chartable source facts and their scope: metric, denominator, period, segment, filter, and source.
2. Pick the one quantitative relationship that most directly supports the main conclusion.
3. Draw that relationship as the visual anchor of the whiteboard.
4. Add short annotations for caveat, metric scope, and next action.
5. Add supporting flow or evidence cards only after the quantitative anchor is clear.

Do not start with a flow diagram and add numbers afterward unless the source's main point is truly a process rather than a data-supported judgment.

## Pattern Card Format

Every reusable pattern should be described in this shape.

```text
Pattern name:
Use when:
Reader question:
Required source facts:
Visual form:
Encoding rules:
Must preserve:
Move to body:
Avoid:
Feishu SVG notes:
Quality check:
```

## Executive 3080 Patterns

These are the default candidates for the opening one-picture summary.

### 1. Decision Spine

- Use when: the source argues for a decision, approval, launch, rollout, or strategy direction.
- Reader question: "What should we do, and why is it safe enough?"
- Required source facts: main conclusion, value/result, key evidence, risk or observation boundary, next action.
- Visual form: top conclusion band -> evidence row -> risk/next-action guardrail.
- Encoding rules: use position for logic order, larger cards for stronger evidence, semantic color for benefit/risk/baseline.
- Must preserve: decision, reason, source-backed evidence, explicit risk boundary.
- Move to body: detailed methodology, implementation tasks, secondary metrics.
- Avoid: a decorative dashboard where all cards have equal weight.
- Feishu SVG notes: use one top band, 2-3 evidence cards, one right or bottom guardrail box.
- Quality check: a manager can restate the decision and caveat in 30 seconds.

### 2. Old Problem To New Strategy

- Use when: the source describes a strategy upgrade, rule change, policy change, model change, or ranking/filtering change.
- Reader question: "What was wrong before, what changed, and why is the new path better?"
- Required source facts: old problem, new strategy, mechanism, evidence/result, rollout/risk boundary.
- Visual form: left-right migration flow with an evidence bridge.
- Encoding rules: gray for old baseline, green/blue for new strategy, arrows only for real transformation or dependency.
- Must preserve: old pain, new rule, why the change matters, evidence, risk.
- Move to body: edge cases, full metric table, low-level implementation.
- Avoid: pure before/after text cards without mechanism or evidence.
- Feishu SVG notes: three zones work well: "旧问题" -> "策略迁移" -> "新策略 / 结果".
- Quality check: the reader sees both the change itself and the reason it improves the situation.

### 3. Experiment Judgment

- Use when: the source reports A/B test, gray release, model experiment, product experiment, or measurement comparison.
- Reader question: "Did the experiment prove enough to act?"
- Required source facts: hypothesis, design/scope, result, interpretation, confidence or limitation, decision.
- Visual form: hypothesis -> test path -> result cards -> confidence boundary -> action.
- Encoding rules: separate result from interpretation; visually mark sample, period, significance, or "原文未提供".
- Must preserve: experiment design, main result, confidence boundary, decision.
- Move to body: metric definitions, full cohorts, secondary slices.
- Avoid: declaring success from one number without sample, period, denominator, or risk.
- Feishu SVG notes: show "验证链路" as a short flow and "结果判断" as a separate card.
- Quality check: the reader can distinguish "observed result" from "decision recommendation".

### 4. Current-State Inventory

- Use when: the source inventories status across regions, platforms, teams, modules, clients, or policies.
- Reader question: "Where are we now, what gaps remain, and what should move first?"
- Required source facts: scope, dimensions, status categories, gaps, priority, next action.
- Visual form: segmented status matrix or map.
- Encoding rules: use columns for stable dimensions, rows for reader-relevant layers, color for status only.
- Must preserve: scope, status categories, gaps, priority signal.
- Move to body: full item list and owner detail.
- Avoid: one huge table where every cell has equal visual weight.
- Feishu SVG notes: include a compact legend; keep status labels consistent.
- Quality check: the reader can locate "done / in progress / blocked / next" without reading paragraphs.

### 5. Problem Diagnosis

- Use when: the source investigates a performance issue, anomaly, funnel drop, quality problem, or operational failure.
- Reader question: "What caused the problem, how do we know, and how should we fix it?"
- Required source facts: symptom, affected scope, evidence, likely cause, fix path, uncertainty.
- Visual form: symptom -> evidence -> cause -> fix path, or fishbone-lite.
- Encoding rules: separate confirmed facts from inferred causes; use dashed lines for hypotheses.
- Must preserve: symptom, evidence, affected scope, causal confidence, fix path.
- Move to body: raw logs, full diagnosis tree, alternative hypotheses.
- Avoid: jumping directly from symptom to solution.
- Feishu SVG notes: place the symptom on the left and the fix path on the right; put uncertainty near the causal link.
- Quality check: the reader can see why the proposed fix follows from the evidence.

### 6. Rollout Roadmap

- Use when: the source describes phased delivery, launch plan, migration, dependency plan, or adoption route.
- Reader question: "What happens when, what depends on what, and where are the checkpoints?"
- Required source facts: phases, milestones, dependency, owner/action, risk, checkpoint.
- Visual form: timeline, swimlane, staged roadmap.
- Encoding rules: position encodes time; lanes encode teams/surfaces; markers encode decision checkpoints.
- Must preserve: phases, dependencies, risks, decision gates.
- Move to body: detailed task list, meeting cadence, owner roster.
- Avoid: decorative timelines without go/no-go checkpoints.
- Feishu SVG notes: avoid dense Gantt charts; use 3-5 phases.
- Quality check: the reader knows the next checkpoint and what could block it.

### 7. Data Insight And Segmentation

- Use when: the source analyzes channel, market, cohort, attribution, ranking, conversion, ROI, or user segment differences.
- Reader question: "Which segment changes the decision?"
- Required source facts: segmentation dimension, metric, contrast, anomaly, possible mechanism, action.
- Visual form: matrix, quadrant, grouped comparison, bubble comparison, heatmap table.
- Encoding rules: position shows category/priority, size shows volume, color/intensity shows value or risk.
- Must preserve: which segment matters, how much, why it matters, action implication.
- Move to body: full data table, minor segments, detailed query notes.
- Avoid: numeric inventory with no decision implication.
- Feishu SVG notes: use bubble size sparingly and label the encoding.
- Quality check: the reader can identify the important segment without scanning every number.

### 8. Risk And Guardrail

- Use when: the source contains trade-offs, compatibility risk, compliance risk, uncertainty, quality concern, or monitoring plan.
- Reader question: "What could go wrong, how large is it, and how will we know?"
- Required source facts: risk type, probability or likelihood, impact, trigger signal, mitigation/fallback, owner or checkpoint.
- Visual form: risk matrix, guardrail panel, impact path.
- Encoding rules: red/orange marks risk, gray marks unknown, green marks mitigation; do not overstate unsupported probability.
- Must preserve: risk, impact scope, trigger, mitigation, unknowns.
- Move to body: full risk register and detailed owner actions.
- Avoid: hiding risk in prose after visualizing only benefits.
- Feishu SVG notes: risk matrix should be small and readable; do not use tiny text.
- Quality check: the reader can say what to monitor after approving the plan.

### 9. System Layer And Capability Map

- Use when: the source explains architecture, capability coverage, data flow, platform modules, or infrastructure.
- Reader question: "What are the layers, which layer changed, and what business effect does it create?"
- Required source facts: layers/modules, dependencies, changed component, capability/result, risk or limitation.
- Visual form: layered stack, capability map, data lineage path.
- Encoding rules: vertical position encodes layer, arrows encode data/control flow, highlight only changed components.
- Must preserve: changed layer, dependency, impact, boundary.
- Move to body: low-level API, schema, event tracking, compatibility detail.
- Avoid: architecture diagrams that require domain expertise to understand the conclusion.
- Feishu SVG notes: add plain-language layer labels and a small "business meaning" note.
- Quality check: a cross-functional reader can understand the business implication without reading technical specs.

### 10. Narrative Evidence Board

- Use when: the source is mostly qualitative, strategic, or decision-discussion oriented and lacks chartable data.
- Reader question: "What is the argument, and what evidence supports it?"
- Required source facts: conclusion, 3-5 evidence points, counterpoint/risk, action.
- Visual form: argument map or evidence ladder.
- Encoding rules: group evidence by claim; use weight or position for evidence strength; mark weak/unsupported evidence.
- Must preserve: claim, evidence, counterpoint or risk.
- Move to body: detailed discussion notes and secondary arguments.
- Avoid: making qualitative content look quantitatively proven.
- Feishu SVG notes: use evidence cards connected to one central conclusion, not a random card wall.
- Quality check: the reader can trace every conclusion to at least one source-backed evidence block.

## Body-Level Visual Patterns

Use these outside the opening whiteboard to carry supporting details without overloading the board.

| Body need | Candidate form | Use when | Avoid |
| --- | --- | --- | --- |
| Explain terminology | Short definition, glossary block, or table | jargon blocks comprehension | long prose definitions |
| Compare options | Prose comparison, decision matrix, or chart | multiple choices or trade-offs exist | paragraphs that hide criteria |
| Preserve evidence | Evidence paragraph, callout, chart, or table | many facts support one conclusion | putting all facts on the board |
| Show risk detail | Risk paragraph, guardrail callout, matrix, or timeline | monitoring plan matters | risk footnotes |
| Show phased action | Stage list, mini roadmap, or timeline | next steps have order | unordered action bullets |
| Explain metric scope | Short note, metric definition block, or table | denominator, period, filter matter | mixing incompatible numbers |
| Show before/after details | Narrative delta, chart, or table | source has old/new values | vague "improved" wording |
| Separate reader layers | Executive / business / technical sections | different roles need different depth | one universal dense section |

## Advanced Cross-Dimension Analysis

Use this for channel mix, attribution, ranking, segmentation, funnel, experiment-split, or other multi-dimensional analysis:

1. **Segment value scenarios**: show which dimension separates high-value and low-value situations. Use position or marker size instead of a plain list.
2. **Show allocation mechanism**: hold the strongest segmentation dimension constant, then encode how the next layer changes traffic or ownership direction.
3. **Separate volume from quality**: use different channels such as marker size for volume and position or explicit labels for value/quality only when the source supports both.
4. **Preserve causal boundary**: use directional language and a visible validation boundary unless randomized evidence proves causality.
5. **Synthesize action**: end with which dimensions should be crossed, which coverage gap matters, and what validation is required before policy use.

## Visual Encoding Grammar

Use these encodings deliberately.

| Encoding | Use for | Do not use for |
| --- | --- | --- |
| Position | priority, sequence, hierarchy, comparison axis | decoration |
| Size / area | magnitude, volume, importance | unsupported emphasis |
| Color hue | semantic category: benefit, risk, baseline, unknown | arbitrary variety |
| Color intensity | severity, confidence, status strength | making text harder to read |
| Line / arrow | dependency, flow, causality, handoff | visual noise between unrelated cards |
| Grouping | same family, same layer, same audience | hiding unrelated items together |
| Boundary box | scope, guardrail, risk boundary, decision boundary | framing every section equally |
| Icon | quick semantic cue for risk, decision, data, rollout | replacing necessary text |
| Annotation | caveat, source scope, interpretation | repeating the title |

If an encoding does not carry meaning, remove it.

## Anti-Pattern Library

Use [expression-anti-patterns.md](expression-anti-patterns.md) for card walls, decorative flows, empty polish, text posters, numeric rosters, text-only quantitative boards, hidden risk, form-first chart selection, and static-board misuse. Keep this library focused on selecting and encoding the right visual relationship.

## External Reference Lessons

Use these lessons as design constraints, not as citations in generated docs.

| Reference family | Lesson to absorb | 3080 usage |
| --- | --- | --- |
| FT Visual Vocabulary | classify by communication intent | choose pattern family from reader question |
| From Data to Viz | start from data shape and warn against caveats | check whether source data supports the chosen form |
| Data Visualisation Catalogue / Data Viz Project | maintain a broad but organized chart vocabulary | expand options beyond cards and flows |
| Vega-Lite examples | separate data, mark, encoding, and transform | specify what position, color, size, and grouping mean |
| Observable Plot | compose marks instead of worshiping chart names | combine simple shapes only when each mark carries meaning |
| Datawrapper | title, annotation, source scope, and caveat make charts trustworthy | write conclusion titles and visible metric notes |
| Flourish | story progression improves retention | convert long logic into visible stages, not visual effects |
| Agent skill repositories | examples, references, and validation artifacts make skills reusable | keep this library as a reference, add examples when repeated failures appear |

## Pattern Selection Checklist

- [ ] The visual pattern answers a reader question, not an author section title.
- [ ] The source information relationship matches the selected pattern family.
- [ ] If the source has chartable metrics, at least one quantitative visual encoding appears on the opening board.
- [ ] If no quantitative visual is used, the source lacks chartable data or extraction limitations are explicitly stated.
- [ ] The pattern preserves conclusion, key evidence, risk boundary, and next action when source-backed.
- [ ] Visual encodings are meaningful and explained when not obvious.
- [ ] The opening board does not require interaction, hover, or animation.
- [ ] The body carries important details intentionally excluded from the board.
- [ ] The chosen form is simpler than prose for the target reader.
- [ ] The pattern avoids universal card walls, decorative arrows, text posters, and unsupported metric displays.
