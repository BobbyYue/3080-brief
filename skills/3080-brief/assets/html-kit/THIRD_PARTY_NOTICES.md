# 3080 HTML Design Kit: Third-Party Notices

The HTML Design Kit bundles only redistributable runtime assets from the local
`html-report` installation. 3080 Brief owns the design contract, renderer,
validation, and documentation added around these assets.

## Apache ECharts

- Bundled file: `js/echarts.min.js`
- Version detected from the runtime: 5.5.1
- License: Apache License 2.0
- License text: `licenses/ECHARTS-LICENSE.txt`
- Upstream: <https://github.com/apache/echarts>

## Mermaid

- Bundled file: `js/mermaid.min.js`
- Version: pinned by SHA-256 in `asset-manifest.json`
- License: MIT
- License text: `licenses/MERMAID-LICENSE.txt`
- Upstream: <https://github.com/mermaid-js/mermaid>

## Fonts

Fonts under `fonts/` are distributed under the SIL Open Font License 1.1.
Family-specific OFL files are retained beside the font files. `IBMPlex-OFL.txt`
and `InstrumentSerif-OFL.txt` cover the two families whose source package did
not include a filename-matched notice.

Generated HTML embeds only the selected font files and runtime libraries. It
does not copy this complete asset directory into each output.
