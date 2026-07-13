# Feishu Whiteboard Implementation

Use this reference only after selecting the visual relationship and pattern in [visual-pattern-library.md](visual-pattern-library.md). This file owns Feishu style selection, native-shape SVG implementation, render/write workflow, and live-board QA; it does not duplicate the visual taxonomy.

## Contents

- Style selection and dependency override
- Composition and layout rules
- Native SVG contract
- Build, write, and verify workflow
- Live-board QA checklist

## Style Selection

Use `beautiful-feishu-whiteboard/CATALOG.md` to choose a candidate from source type, tone, reader scenario, information density, and explicit preference. In a 3080 run, choose automatically when the user did not express a style preference; do not pause only to ask for a vibe. Read:

- `beautiful-feishu-whiteboard/RULES.md`;
- `beautiful-feishu-whiteboard/CATALOG.md`;
- only the selected template's `design.md`.

Filter out the styles in `config/3080-brief.json`, the single machine-readable banned-style source. If the user requests one, say it is unavailable for this skill and select the closest allowed alternative.

For multiple style outputs, vary narrative skeleton, reading path, layout density, visual anchor, emphasis method, and color system. Palette-only reskins do not count as distinct styles.

When directional values or statuses appear, read `semantic-color-system.md`. The candidate style controls decorative/non-semantic colors only; canonical semantic colors in `config/3080-brief.json` override the style palette for evidence marks, status labels, risks, and direction cues.

## Composition Contract

Start from `claim_ledger.json` and `visual_spec.json`:

1. Confirm the visual pattern and reader question were selected in `visual-pattern-library.md`.
2. Map every board block to claim IDs.
3. Run `scripts/check_coverage.py`; do not draw before the claim spine reaches the configured threshold.
4. Run `scripts/validate_visual_spec.py visual_spec.json claim_ledger.json` to verify claim-to-block mapping and style eligibility.
5. Use `scripts/render_visual_spec.py` for supported bar, dot, threshold, matrix, timeline, or flow anchors when useful.
6. Compose the complete board with one dominant reading path.

Rules:

- One visual block supports one claim; titles state the conclusion.
- Let position, size, line, grouping, boundary, and color encode meaning.
- Use repeated cards only for true peer items.
- Put the strongest source-specific insight above expected or common-sense context.
- Use short phrases and manually wrap long labels; do not shrink text to fit.
- Keep big numbers separate from long labels.
- Leave generous internal and outer padding.
- Separate overview, business view, and professional detail. The opening board is the overview unless the user targets a technical review.
- Show source-backed risk or confidence boundaries when they can change interpretation or action.
- Do not print source links, prompts, style names, task notes, tool notes, or internal process language on the board.

## Native SVG Contract

Allowed editable vocabulary:

- `rect`, `circle`, `ellipse` for cards, bars, bands, matrices, dots, and bubbles;
- `line`, `polyline` for straight or right-angled connectors, thresholds, and reference lines;
- `text`, `tspan` for labels, although separate `<text>` nodes are safer for manual line breaks;
- `g`, `defs`, and `marker` for grouping and native connector arrowheads;
- one simple straight-line `<path>` inside a `<marker>` only.

Forbidden:

- structural, freeform, or curved path and polygon;
- gradient, filter, pattern, mask, clipPath, blur, image, external href/reference;
- opacity attributes, CSS `style`, `font-family`, matrix/skew transforms;
- hand-drawn arrowhead triangles or chevrons.

Use `marker-end` or `marker-start` on a line or connector. Do not draw a separate arrowhead. Use a solid lighter hex instead of opacity.

## Stable Layout Rules

- Use a logical SVG width around 1600-1700; let content determine height.
- Prefer left-to-right then top-to-bottom unless the selected pattern calls for another explicit path.
- Use font size at least 16px for load-bearing text.
- Avoid important small light text on dark fills because exported text color can differ from the live board.
- Add more vertical padding than local rendering appears to need; Feishu font metrics can expand.
- Keep labels away from canvas edges and connector paths.
- Treat `whiteboard-cli --check` warnings as evidence to inspect, not as an automatic visual verdict.

## Build And Write Workflow

1. Build `diagram.svg` from the approved visual spec.
2. Run static and renderer checks:

   ```bash
   scripts/validate_whiteboard.sh diagram.svg output_dir
   ```

3. View the rendered PNG and fix overflow, clipping, padding, overlap, unclear reading path, and misleading encoding with targeted SVG edits.
4. Wrap only after static validation:

   ```bash
   node scripts/wrap_svg_as_whiteboard.js diagram.svg whiteboard.xml
   ```

5. Write the SVG as an editable Feishu whiteboard.
6. Query the live board image and raw nodes. Inspect the live image for layout and raw nodes for stored text color.
7. Preserve preview and artifact hashes in the reviewer packet.

If live preview is stale, query raw nodes to confirm the write, then export again. Do not assume an old preview is the current board.

## Whiteboard QA Checklist

- [ ] Does the board communicate one coherent story rather than arranged paragraphs?
- [ ] Can a reader state the core conclusion without reading the body?
- [ ] Does every visual block map to claim IDs in `visual_spec.json`?
- [ ] Does value-weighted board coverage pass, with no omitted P0 claim?
- [ ] Does the visual form match the source relationship selected in the Pattern Library?
- [ ] When chartable data exists, is there a quantitative encoding beyond boxes and prose?
- [ ] Are observation, hypothesis, boundary, and action visibly distinct?
- [ ] Are risk and benefit both visible when both change the decision?
- [ ] Are chart titles conclusions rather than topic labels?
- [ ] Are all colors, arrows, shapes, and icons load-bearing?
- [ ] Do directional claims use the same semantic meaning/color as the document body, with a redundant non-color cue?
- [ ] Are long labels manually wrapped and text sizes readable?
- [ ] Is the local render free of clipping, overlap, overflow, and cramped spacing?
- [ ] Is the live Feishu preview also clean and current?
- [ ] Is the chosen style allowed and appropriate for the content density and tone?
- [ ] If image2 was used, is all final evidence rebuilt as editable native content?

## Known Rendering Caveats

- Image export can render text colors differently; verify stored colors through raw/live board data.
- Nested `tspan` can render unexpectedly in table-like headers; separate text nodes are safer.
- Intentional overlaps may be reported by the CLI; inspect visually.
- Live image export can lag behind an update.
