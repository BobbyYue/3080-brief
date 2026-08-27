# HTML Output And Visualization

Read this reference only when HTML is the selected output. It defines the 3080-owned HTML Design Kit: content-fit layout planning, a complete local font catalog, ECharts quantitative rendering, Mermaid structural rendering, semantic HTML components, and an auditable native-SVG fallback. It does not invoke or require another report skill at runtime.

## Ownership Boundary

- 3080 owns source grounding, claim strength, reader narrative, TLDR, visual selection, review, and replay.
- The HTML renderer owns semantic markup, page hierarchy, content-fit typography/layout, progressive visual enhancement, and faithful rendering of the approved visual spec.
- Rendering must not add, delete, strengthen, translate, or reinterpret a claim.
- Use the source-language decision already recorded in `source_inventory.md`; request language is not an override.
- The HTML Design Kit is an output adapter, not a second author. It may change marks, spacing, grouping, and type treatment only when the same approved claim IDs, values, scope, and semantic direction remain visible.

## Output Package

Create one self-contained `.html` file by default. Embed only the selected local fonts and required runtime library into the artifact; never reference a CDN, remote font, local absolute path, or another skill at viewing time. The native SVG remains in the file as the no-script evidence fallback.

Build through the locked composer path. The contract binds the three reviewed inputs to the output; the receipt binds the finished bytes back to that contract:

```bash
scripts/validate_brief.py brief.json visual_spec.json
scripts/html_runtime_contract.py init --brief brief.json --visual-spec visual_spec.json --design-plan html_design.json --output-html output.html --contract output.contract.json
scripts/build_html_brief.py brief.json visual_spec.json output.html --design-plan html_design.json --contract output.contract.json --receipt output.build-receipt.json
scripts/preflight_check.py output.html --format html --source-inventory source_inventory.md --claim-ledger claim_ledger.json
scripts/validate_html_output.py output.html --visual-spec visual_spec.json --design-plan html_design.json --contract output.contract.json --build-receipt output.build-receipt.json
```

The final HTML must carry the current composer signature, runtime contract ID, and input hashes. A visually plausible hand-authored page, copied template, or modified post-build file fails validation. Do not repair the signature manually; rebuild from the reviewed inputs.

`html_design.json` follows `html-design.schema.json`. Select it from the source's document type, dominant relationship, reader, tone, and density after `brief.json` and `visual_spec.json` are stable. Do not choose a style before understanding the content, and do not use a silent default.

`brief.json` follows the shared `brief.schema.json` used by Feishu and HTML. Rich text may be a string or an array of spans:

```json
[
  {"text": "Result improved by "},
  {"text": "+12%", "semantic_direction": "favorable", "strong": true}
]
```

Allowed body blocks are `paragraph`, `bullets`, `callout`, `table`, `figure`, and `details`. Use `details` only for P2 implementation or methodology; P0/P1 conclusions, evidence, risk, and action stay visible.

## Bundled Material Library

The complete local inventory lives under `assets/html-kit/`:

- `font-catalog.json`: 29 font families / 54 font files, tagged for editorial, product, technical, data, longform, and expressive use;
- `js/echarts.min.js`: quantitative chart renderer, embedded only when a selected block needs it;
- `js/mermaid.min.js`: process, hierarchy, sequence, and dependency renderer, embedded only when needed;
- `asset-manifest.json` and `THIRD_PARTY_NOTICES.md`: hashes, versions, licenses, and redistribution notes.

This is a library, not a requirement to use everything. The output embeds the smallest selected subset. For Chinese or mixed-script documents, bundled Latin fonts must retain the configured CJK system fallback.

## HTML Design Plan

Select exactly one layout family and explain why it fits the source:

| Layout | Use when | Avoid when |
| --- | --- | --- |
| `editorial-research` | evidence, methods, policy, or formal analysis lead | repeated operational scanning is primary |
| `decision-dashboard` | several decision-bearing metrics must be compared quickly | the source is mainly narrative or qualitative |
| `technical-analysis` | implementation logic, code, systems, or precise mechanisms matter | the main reader should not meet implementation detail first |
| `narrative-longform` | a case, chronology, or argument develops through prose | the source is a compact scorecard |
| `product-brief` | problem, product change, user impact, and rollout form one concise story | the source is a dense research paper |

Choose display, body, and mono families from `font-catalog.json`. Body must use a readable sans or serif family; expressive display faces require a source-fit rationale and must never carry dense body text. Set density, prose measure, section treatment, one-picture anchor, renderer, and support position explicitly. Keep motion `none` and asset mode `inline`.

Separate hard floors from preferred reading defaults. Body text below the
configured 14px minimum, clipped content, inaccessible contrast, or unreadable
table geometry is a failure. The bundled 16px body size, long-form line height
of at least 1.5, controlled prose measure, and left alignment are preferred
starting points; a departure is a review signal and blocks only when the actual
render increases reading error or prevents the intended reader task.

These choices must materially change the report shell, not merely add CSS labels. The composer provides a strong title field, a readable prose measure, generous section rhythm, integrated figures, argument-bearing headings, and restrained callouts. Layout families may change header treatment, section rhythm, opening composition, and technical/editorial emphasis; they may not turn the body into a component gallery.

The renderer choice follows the relationship:

- quantitative comparison, trend, distribution, threshold, matrix, or funnel -> ECharts;
- process, sequence, hierarchy, or dependency -> Mermaid when the structure is the conclusion;
- mixed evidence -> one dominant ECharts/Mermaid anchor plus compact source-backed support annotations;
- no chartable or structural relationship -> native SVG / semantic HTML, not decorative charts.

Never choose ECharts or Mermaid only to make the page look richer. Never turn multiple unrelated facts into an equal-weight dashboard. The planned `anchor_block_id` must be the block that carries the document's main visual judgment.

Choose a right support rail when the rendered supports remain compact relative to the anchor; use the below evidence band when it creates a clearer reading order or avoids empty vertical space. Do not infer readability from block count alone. Geometry checks and visual replay decide whether the chosen placement works.

## First-Screen Contract

The first visible section is `TLDR` and contains, in order:

1. one Pyramid opening unit: one primary judgment and 1-3 support lines;
2. one `<figure class="one-picture">` rendered from the approved visual spec;
3. one 3-5 row key-question table using `Question / Conclusion / Why` or its configured Chinese equivalent;
4. one compact, low-emphasis source citation without a standalone source heading.

The one-picture figure uses one conclusion title, one dominant visual relationship, compact evidence annotations, and visible risk/action boundaries. It is not an equal-weight card wall. Runtime charts may improve the normal view, but the same values, labels, scope, risk, and action must remain available in the embedded native-SVG fallback without hover, animation, filtering, or expansion.

## Feishu / HTML Visual Parity

Feishu and HTML share the same approved `visual_spec.json`, selected theme, semantic colors, claim mappings, and deliberate `composition`. The output medium may change text wrapping or responsive behavior, but it must not change the visual argument or fall back to a separate HTML-only card layout.

Before HTML generation:

1. Select the relationship and composition using the Pattern Library; do not leave composition implicit.
2. Render the standalone SVG with `scripts/render_visual_spec.py` and inspect it at normal document width.
3. Reject title-only blocks, annotation blocks whose metric items are not visibly rendered, repeated full-width stage panels, and vertical canvases that make the first-screen visual feel sparse.
4. Build the HTML from the same reviewed spec, then compare the embedded SVG against the standalone preview.

After deterministic render checks, crop the one-picture figure at normal document width and run [Visual Blind Replay](visual-blind-replay.md). Then capture one full-page desktop screenshot, collect `window.__3080GeometryAudit`, validate it with `validate_html_geometry_report.py`, and run [Full-page Visual Replay](full-page-visual-replay.md). A validator PASS does not replace either comprehension gate.

`anchor_support` must render a visibly dominant first-row anchor, not equal full-width panels. Its support and caveat blocks flow into readable rows according to their actual count; block count is not a quality proxy. `comparison_grid` must render peer blocks on a shared grid. If the output DOM lacks the declared `data-layout` or block role groups, validation fails instead of accepting a composition label that did not affect layout.

For a process with 3-4 substantive stages, prefer `stage_story`: one compact context band, one connected stage row, and one evidence/risk/action strip. Do not render every stage as a separate full-width panel unless vertical order itself is the conclusion.

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

ECharts is the default rich renderer for supported quantitative blocks; Mermaid is the default rich renderer for supported structural blocks. Native SVG remains the audit and failure fallback. A rich render is invalid if it hides any source-backed block, replaces exact display values with ambiguous axes, drops metric scope, or loads only after an interaction.

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
- Keep four proximity levels visible: tight within one idea and between a visual
  and its label, normal between paragraphs, wider between subsections or evidence
  forms, and widest between major reader questions.
- Use callouts for a decision, risk, boundary, or action that interrupts the main flow; do not wrap every section in a card.
- Use micro visuals such as sparklines only beside an existing metric or table row, never as unsupported decoration.
- Keep tables full width when dense. Allow horizontal scrolling rather than compressing text into unreadable columns.
- Use native `<details>` only for lower-priority depth.

## Rendered Accessibility And Integrity Gate

Validate the rendered artifact:

- no clipped labels, blank SVG, overlap, unintended page overflow, or unreadably narrow table cells;
- body text remains at least 14px and captions at least 12px;
- long links wrap;
- figures preserve aspect ratio;
- semantic meaning survives grayscale and color-vision differences through redundant cues;
- every figure has alt text and every table has headers;
- the full page reads as one report: title hierarchy is clear, TLDR is a distinct opening unit, headings alone carry the argument, the one-picture summary is dominant, and the body is not a wall of repeated components;
- the runtime contract, generator signature, build receipt, geometry report, and full-page replay all bind to the same unchanged HTML artifact;

FAIL when the canonical composer/receipt chain is absent; no allowed content-fit theme or HTML design plan was selected; HTML and the visual disagree on theme; layout/font/density differs from the approved design plan; chartable evidence is rendered primarily as prose/cards; the visual form does not match the source relationship; the figure title is merely a topic label; scope is lost; missing data is shown as zero; critical information is interaction-only; semantic colors conflict; selected fonts/runtime assets are not embedded; an external resource is required; or the delivered render is clipped.

Also FAIL when the SVG omits any title, label, or display value declared in the approved visual spec; a block has only a title and empty space; the final composition differs from the spec; or the one-picture canvas falls outside the configured compact width/height range.
