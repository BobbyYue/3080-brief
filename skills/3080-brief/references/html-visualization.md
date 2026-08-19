# HTML Output And Visualization

Read this reference only when HTML is the selected output. It defines an original, self-contained HTML renderer for 3080 Brief; it does not depend on another report skill.

## Ownership Boundary

- 3080 owns source grounding, claim strength, reader narrative, TLDR, visual selection, review, and replay.
- The HTML renderer owns semantic markup, page hierarchy, responsive layout, print behavior, and faithful rendering of the approved visual spec.
- Rendering must not add, delete, strengthen, translate, or reinterpret a claim.
- Use the source-language decision already recorded in `source_inventory.md`; request language is not an override.

## Output Package

Create one self-contained `.html` file by default. Use system fonts and inline CSS/SVG so downloaded users do not need a network connection, font package, CDN, or another skill.

Build from two reviewed inputs:

```bash
scripts/validate_brief.py brief.json visual_spec.json
scripts/build_html_brief.py brief.json visual_spec.json output.html
scripts/preflight_check.py output.html --format html --source-inventory source_inventory.md --claim-ledger claim_ledger.json
scripts/validate_html_output.py output.html --visual-spec visual_spec.json
```

`brief.json` follows the shared `brief.schema.json` used by Feishu and HTML. Rich text may be a string or an array of spans:

```json
[
  {"text": "Result improved by "},
  {"text": "+12%", "semantic_direction": "favorable", "strong": true}
]
```

Allowed body blocks are `paragraph`, `bullets`, `callout`, `table`, `figure`, and `details`. Use `details` only for P2 implementation or methodology; P0/P1 conclusions, evidence, risk, and action stay visible.

## First-Screen Contract

The first visible section is `TLDR` and contains, in order:

1. one Pyramid opening unit: one primary judgment and 1-3 support lines;
2. one `<figure class="one-picture">` rendered from the approved visual spec;
3. one 3-5 row key-question table using `Question / Conclusion / Why` or its configured Chinese equivalent;
4. one compact, low-emphasis source citation without a standalone source heading.

The one-picture figure uses one conclusion title, one dominant visual relationship, compact evidence annotations, and visible risk/action boundaries. It is not a dashboard or equal-weight card wall. Critical information must remain available without hover, animation, filtering, or expansion.

## Visual Selection

Use `visual-pattern-library.md` and `theme-selection.md` before this file. Select exactly one allowed Beautiful Feishu Whiteboard theme and record it in `visual_spec.style` with a content-based `style_rationale`. The bundled renderer adapts that same theme to HTML page tokens; it must not silently choose a default, print the style name, or override semantic evidence colors.

For HTML rendering, prefer:

| Relationship | Preferred mark |
| --- | --- |
| category comparison or rank | bar, diverging bar, dot |
| old/new or baseline/result | slope, paired dot, delta bar |
| time trend | line with visible endpoint/event annotations |
| expected/observed or correlation | scatter with source-backed pairs and a labeled reference line |
| cutoff or allowed range | threshold or range band |
| segment cross-comparison | heatmap or matrix with explicit N/A cells |
| staged conversion or exclusion | funnel with source-backed stage values |
| process, state, or dependency | flow, sequence, timeline, or hierarchy only when structure is the conclusion |

Do not generate scatter points from a regression equation, convert missing heatmap cells to zero, imply a funnel when stages are not sequential, or use area/size when the source does not support magnitude.

Avoid radar and gauge charts. Use pie/donut only for a complete 100% composition with no more than four categories. Use Sankey, treemap, maps, and network diagrams only when complete source relationships make their encoding necessary; they are not default 3080 forms.

## Figure Contract

Every figure must include:

- a short judgment title stating what the reader should notice;
- visible labels for decision-bearing values;
- metric scope when present: period, denominator, unit, segment, and filter;
- a concise interpretation or boundary annotation when the chart is not self-explanatory;
- source note or claim mapping in the audit artifacts;
- useful alt text that states the conclusion and key relationship.

Tooltips may repeat precise values but never carry the only copy of a conclusion, caveat, or action. Animation is off for document output.

## Semantic Color And Page Tokens

Use `semantic-color-system.md` as the source of truth. HTML variables map to the configured semantic colors:

- `--favorable`, `--unfavorable`, `--warning`, `--neutral`, `--unknown` carry evidence meaning;
- `--accent` is non-semantic emphasis only;
- `--ink`, `--muted`, `--rule`, `--surface`, and `--background` organize the page.

The selected theme supplies non-semantic page tokens such as background, surface, ink contrast, rules, spacing, border weight, radius, and figure accents. The bundled registry is an MIT-attributed adaptation of `beautiful-feishu-whiteboard`; it is included with the skill so HTML output remains self-contained and portable.

Color is redundant with sign, wording, symbol, shape, or position. Never color whole paragraphs. The same claim cannot change semantic color across TLDR, figure, table, and body.

## Body Composition

- Keep a readable single-column measure for prose.
- Let first-level headings advance the argument; do not introduce a fixed body template.
- Start a dense section with a short explanatory paragraph before a chart, table, or detail block.
- Use callouts for a decision, risk, boundary, or action that interrupts the main flow; do not wrap every section in a card.
- Use micro visuals such as sparklines only beside an existing metric or table row, never as unsupported decoration.
- Keep tables full width when dense. On narrow screens, allow horizontal scrolling rather than compressing text into unreadable columns.
- Use native `<details>` only for lower-priority depth. Print styles must expand or preserve that content when it is part of the delivered artifact.

## Responsive, Print, And Accessibility Gate

Validate at desktop and mobile widths and in print:

- no clipped labels, blank SVG, overlap, horizontal page overflow, or unreadably narrow table cells;
- grids collapse to one column on mobile;
- body text remains at least 14px and captions at least 12px;
- long links wrap;
- figures preserve aspect ratio;
- semantic meaning survives grayscale and color-vision differences through redundant cues;
- every figure has alt text and every table has headers;
- interactive or navigational controls disappear in print without removing evidence.

FAIL when no allowed content-fit theme was selected, HTML and the visual disagree on theme, chartable evidence is rendered primarily as prose/cards, the visual form does not match the source relationship, the figure title is merely a topic label, scope is lost, missing data is shown as zero, critical information is interaction-only, semantic colors conflict, or mobile/print output is clipped.
