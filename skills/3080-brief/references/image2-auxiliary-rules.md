# Image2 Auxiliary Rules

Use this reference only when considering image generation or bitmap visual exploration for `3080-brief`.

## Contents

- Auxiliary positioning and two-track model
- Image2 gate, privacy, and prompt rules
- Translation back to editable whiteboard
- Final-document and reviewer rules

## Positioning

Image2 is optional and auxiliary. It may be used for visual exploration, composition inspiration, moodboarding, or non-evidence illustration.

Image2 must not be used as the authoritative `3080-brief` whiteboard. Any source-critical data, conclusion, risk, chart, metric, formula, threshold, or recommendation must be rebuilt as editable Feishu whiteboard elements and grounded in the source.

Default: do not include image2 output in the final doc.

## Two-Track Model

Keep image2 in the exploration track, not the evidence-delivery track.

| Track | Purpose | Allowed output | Final evidence carrier |
| --- | --- | --- | --- |
| Visual exploration track | Explore composition, visual hierarchy, mood, metaphor, and layout options | Generated bitmap drafts, moodboards, layout references | None |
| Evidence delivery track | Communicate source-backed conclusion, data, risk, and next action | Editable Feishu whiteboard SVG plus body prose, bullets, callouts, tables, charts, timelines, or examples as appropriate | Native editable elements only |

The final 3080 whiteboard belongs to the evidence delivery track.

## Image2 Gate

Do not start with image2. First complete:

1. Source inventory.
2. Source-fit body narrative plus Novice Reverse Review notes.
3. Chartable-data inventory.
4. Required whiteboard information list.
5. Risk and next-action boundary.

Image2 may be used only when one of these is true:

- the visual structure is unclear and composition exploration would reduce iteration time;
- the source is mostly conceptual, strategic, or journey-oriented and needs a metaphor or spatial layout;
- the user explicitly asks for visual style exploration, cover image, illustration, or moodboard;
- the final image2 output will be translated back into editable Feishu whiteboard elements.

Do not use image2 when:

- the visual must carry core data, metrics, formulas, thresholds, axes, risks, or recommendations;
- the source contains chartable quantitative evidence that can be represented with native shapes;
- the generated bitmap would become the main 80% summary;
- the image could imply unsupported conclusions, precision, causality, or certainty;
- the output needs to be edited, audited, or updated by later readers.

## Prompt Rules

Image2 prompts must be de-evidenced. They may describe layout, visual hierarchy, mood, and abstract composition. They must not include source-critical numbers, final conclusions, exact chart labels, formulas, axes, risk statements, or recommendations.

Treat internal and confidential source material as unavailable to image generation. Never send source sentences, document links/tokens, internal project or customer names, account identifiers, code names, or real metrics. Replace them with abstract placeholders such as `System A`, `Segment B`, `Metric 1`, and `Risk Zone`. Image generation must not become an alternate data-exfiltration path.

Safe prompt pattern:

```text
Create a restrained whiteboard-style layout inspiration for a decision brief.
Use abstract blocks, chart-like spaces, directional flow, and clear visual hierarchy.
Do not include readable text, numbers, metrics, logos, final claims, or specific data.
This image is only for composition inspiration, not final evidence.
```

Unsafe prompt pattern:

```text
Draw a chart proving that metric X increased and recommend rollout based on that result.
```

## Translation Back To Editable Whiteboard

After image2 generation, extract only:

- section placement;
- reading path;
- visual weight;
- whitespace rhythm;
- chart placeholder locations;
- shape vocabulary;
- restrained color mood;
- possible metaphor or spatial grouping.

Do not copy or trust:

- generated text;
- generated numbers;
- pseudo charts;
- axes and scales;
- labels;
- source claims;
- risk statements;
- recommendations.

Rebuild the final whiteboard with native editable elements:

- `rect` for bars, matrices, lanes, bands, and cards;
- `circle` or `ellipse` for dot plots, markers, and bubbles;
- `line` or `polyline` for thresholds, trend sketches, reference lines, and flows;
- `text` for source-grounded labels and annotations;
- grouped native shapes for matrix, funnel, threshold, distribution, or calibration visuals.

## Final Doc Rules

Default: do not insert image2 output into the final Feishu doc.

Image2 may appear in the final doc only when:

- the user explicitly requests a cover image, illustration, or non-evidence visual; and
- the image does not carry source-critical evidence, numbers, charts, risks, or recommendations; and
- the editable 3080 whiteboard still exists immediately after the one-sentence summary.

If included, label its role in internal verification as "non-evidence illustration". Do not label it as the 80% whiteboard.

## Review Rules

The final output fails if:

- a generated bitmap image carries evidence, numbers, charts, risks, formulas, thresholds, or recommendations;
- the generated bitmap replaces the editable 3080 whiteboard;
- source-critical visual claims exist only in image2 and not in editable whiteboard/body structures;
- reviewers cannot trace visual claims back to source facts;
- the bitmap contains readable generated text that was not independently verified and rewritten as editable text.

Reviewer check:

```text
If image2 was used, confirm it only influenced composition/style. The final evidence must be rebuilt as source-grounded, editable Feishu whiteboard elements.
```

## Decision Rule

Use image2 only to answer: "What could this visual look like?"

Never use image2 to answer: "What does the source prove?"
