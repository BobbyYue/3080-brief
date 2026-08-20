# Full-page Visual Replay

Use this gate for HTML after the one-picture Visual Blind Replay and before Blind Reader Replay.

## Isolation

Give the reviewer only one full-page desktop screenshot. Do not provide the source, brief JSON, visual spec, design plan, implementation notes, prior reviews, or author explanation. This is a visual reading test, not a source audit.

## Replay task

From the screenshot alone:

1. Write the visible heading path in reading order.
2. State the judgment available from the first screen.
3. Describe the page rhythm and identify any dense or fragmented regions.
4. Check every gate in `full-page-replay.schema.json`.

PASS only when the document reads as one report rather than a stack of components, the TLDR is visibly distinct, the one-picture summary is dominant, headings carry the story, and no content overlaps or clips.

Before this replay, collect `window.__3080GeometryAudit` from the same rendered HTML and validate it with `validate_html_geometry_report.py`. Do not substitute the geometry report for visual judgment: one checks measurable collisions, the other checks hierarchy and reading rhythm.

Mobile and print variants are outside this gate.
