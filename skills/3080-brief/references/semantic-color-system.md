# Semantic Color System

Read this reference when the source or draft contains directional metrics, signed deltas, status judgments, gains/losses, risks, exceptions, or confidence states. It is the single semantic-color contract for both the document body and the opening whiteboard.

## Classify Meaning Before Color

Never infer business meaning from the mathematical sign alone. Classify each decision-relevant value or state in `claim_ledger.json`:

- `favorable`: supports the desired outcome or materially improves the decision state.
- `unfavorable`: harms the desired outcome or shows a material negative result.
- `warning`: deviation, over/under-shoot, elevated uncertainty, or a condition needing attention without a fully negative judgment.
- `neutral`: descriptive comparison, baseline, reference value, or direction with no positive/negative interpretation.
- `unknown`: insufficient evidence to assign a direction safely.

Examples of the distinction:

- Revenue `+8%` may be favorable; cost `+8%` may be unfavorable.
- Error rate `-5%` may be favorable; coverage `-5%` may be unfavorable.
- Over-attribution and under-attribution may both be warning/unfavorable depending on the source's decision boundary.

For each decision-relevant directional claim, add `semantic_direction` and exact `display_values` to the claim ledger. Use `neutral` or `unknown` rather than guessing.

## Canonical Mapping

Use `config/3080-brief.json > semantic_colors` as the machine-readable source of truth:

| Meaning | Body | Whiteboard | Required redundant cue |
| --- | --- | --- | --- |
| favorable | green | canonical favorable SVG color | `+/-`, `up/down`, or explicit favorable wording |
| unfavorable | red | canonical unfavorable SVG color | sign/arrow plus explicit adverse wording |
| warning | orange | canonical warning SVG color | deviation/caution wording or boundary marker |
| neutral | blue or default text | canonical neutral SVG color | baseline/reference label |
| unknown | gray | canonical unknown SVG color | uncertainty or `source not provided` label |

Color is never the only carrier. Preserve signs, arrows, labels, position, or shape so color-blind and monochrome readers retain the meaning.

## Body Rules

- Color only decision-bearing values, short status labels, and compact evidence phrases. Do not color whole paragraphs.
- In Feishu XML, use named colors from config, for example `<span text-color="green"><b>+12%</b></span>`.
- Keep the same direction mapped to the same color throughout TLDR, tables, callouts, body prose, and chart annotations.
- Use bold sparingly with color for the most important values; color alone is enough for secondary values.
- For Word or another format, use the closest accessible equivalent and preserve redundant text/sign cues.

## Whiteboard Rules

- Candidate styles may control background, typography, decorative accents, and non-semantic structure only.
- Semantic marks must use the canonical SVG colors from config: data marks, risk bands, direction labels, threshold exceptions, and status indicators.
- Use the lighter canonical tint for large fills and the strong color for dots, lines, labels, or borders.
- If one block contains mixed directions, assign semantics at item/cell level rather than coloring the entire block.
- Do not recolor a favorable body value as warning or neutral on the board. If the board intentionally presents a different concept, change the label and claim mapping so the distinction is explicit.

## Release Gate

Before review:

1. Confirm every decision-relevant directional metric has an explicit semantic classification.
2. Confirm mathematical sign was not used as a proxy for business meaning.
3. Confirm body and board use the same semantic mapping for the same claim/value.
4. Confirm color is redundant with sign, label, arrow, shape, or position.
5. Confirm the rendered document and live board preserve the intended colors.

FAIL when a classified decision-relevant value is unstyled in the body, uses a conflicting semantic color on the board, or depends on color alone.
