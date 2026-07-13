# Feishu Doc Output

Use this reference when creating or updating Feishu/Lark docs.

## Contents

- Required Feishu skills and new-doc contract
- Body visualization and XML shape
- Whiteboard insertion, live preview, and generated-doc updates

## Required Skills

Use:

- `lark-doc` for source fetch and doc create/update.
- `lark-whiteboard` for querying live whiteboard previews.
- `beautiful-feishu-whiteboard` for SVG whiteboard style and validation rules.

Before creating/updating docs, read the relevant lark references:

- `lark-shared/SKILL.md`
- `lark-doc/references/lark-doc-xml.md`
- `lark-doc/references/lark-doc-create.md` for new docs
- `lark-doc/references/lark-doc-update.md` for updating generated docs
- `lark-doc/references/style/lark-doc-create-workflow.md`
- `lark-doc/references/style/lark-doc-update-workflow.md` when editing an existing generated doc

## New Doc Contract

- Create a new doc unless the user explicitly asks to update an already generated summary doc.
- Never edit the source doc.
- Do not include source appendix / 附录 / Appendix content in the generated summary unless the user explicitly requests it.
- Use XML by default.
- Include one `<title>`.
- Put `<h1>TLDR</h1>` first by default, or a short source-language equivalent only when the user explicitly prefers localized wording.
- Put `<callout>` immediately after that heading for the one-sentence summary; it must let readers get the source document's core value within 30 seconds.
- Put `<whiteboard type="svg">...</whiteboard>` immediately after the first callout; it must cover at least 80% of value-weighted non-appendix claims in one visual.
- Build `claim_ledger.json` and `visual_spec.json` first. Every board block must map to claim IDs; run `scripts/check_coverage.py` before insertion.
- Put one compact key-question table immediately after the whiteboard. Use output-language headers (`问题 / 结论 / 为什么` for Chinese; `Question / Conclusion / Why` for English); make dense rows taller, split them, or move detail into the body.
- Add the source link near the top as compact, low-emphasis citation metadata.
- Choose body-level prose, bullets, callouts, tables, charts, timelines, examples, or short stories when they improve comprehension beyond the opening whiteboard.
- Use short judgment-style body headings that form a logical narrative path.
- For decision-relevant directional values/statuses, read `semantic-color-system.md`, classify meaning in the claim ledger, and use `<span text-color="...">` for the compact value/label. Keep signs/arrows/wording as redundant cues.
- Use the same configured semantic meaning in the body and whiteboard; the selected whiteboard style may not remap favorable, unfavorable, warning, neutral, or unknown colors.
- Apply exact heading, audience-label, placeholder, and meta-language restrictions from `config/3080-brief.json` through preflight.
- Do not use generated bitmap images as the authoritative 3080 whiteboard. The required one-picture summary must be editable Feishu whiteboard content.
- If image2 output is included by explicit user request, treat it only as non-evidence cover/illustration and keep it separate from the required source-grounded whiteboard.

## Body Visualization Rules

Use visual expression in the document body when it helps readers understand faster.

- Pick the format from the relationship being explained; tables are optional, not preferred.
- Start important body sections with short explanatory prose before dense structured objects.
- Use callouts, tables, charts, timelines, bullets, or examples only when they reduce reader effort.
- Preserve source value: if an important detail is omitted from the whiteboard, place it in the closest relevant body section with the simplest effective format.
- Color only decision-bearing values or short status labels, never whole paragraphs. Verify the rendered color instead of trusting XML alone.

## Recommended XML Shape

```xml
<title>3080 Brief｜Source Title</title>
<h1>TLDR</h1>
<callout emoji="💡">
  <p>30 秒内能理解的原文核心价值...</p>
  <p>支撑该价值判断的关键事实、影响或动作...</p>
  <p>必要的不确定性、观察条件或下一步...</p>
</callout>
<whiteboard type="svg">
  ...svg...
</whiteboard>
<table>
  <tr>
    <th>问题</th>
    <th>结论</th>
    <th>为什么</th>
  </tr>
  <tr>
    <td>这件事本质变了什么？</td>
    <td>...</td>
    <td>...</td>
  </tr>
</table>
<blockquote>
  <p><i>来源：<a href="SOURCE_URL">SOURCE_TITLE</a></i></p>
</blockquote>
<h1>根据原文内容生成的判断型短标题</h1>
<p>先用短段落说明本节要解决的问题或判断，再按内容需要选择分点、callout、表格、图表、时间线或案例。</p>
<h1>根据原文内容生成的下一段判断型短标题</h1>
<p>继续按照 SUCCESs Framework + Stepwise Information Delivery 推进叙事。</p>
```

Generate body headings from the source narrative instead of using a fixed heading list.

Validate the generated document with `scripts/preflight_check.py DRAFT --source-inventory source_inventory.md`; exact restrictions and the Language Gate live in config/preflight.

## Whiteboard Insert Workflow

1. Build `claim_ledger.json` and `visual_spec.json`; render supported chart blocks with `scripts/render_visual_spec.py` when useful.
2. Build or refine `diagram.svg` with the selected content-fit palette.
3. Run:
   ```bash
   scripts/validate_whiteboard.sh diagram.svg output_dir
   ```
4. Wrap:
   ```bash
   node scripts/wrap_svg_as_whiteboard.js diagram.svg whiteboard.xml
   ```
5. Create or update doc with `--content @whiteboard.xml` as appropriate.
6. Capture the returned whiteboard token.
7. Query live preview:
   ```bash
   lark-cli whiteboard +query --whiteboard-token TOKEN --output_as image --output output/live_preview --overwrite --as user
   ```
8. Inspect the live preview and preserve its hash in the reviewer artifact set.

## Updating Generated Docs

If optimizing an already generated `3080-brief` doc:

- Fetch with `--detail with-ids`.
- Locate the existing whiteboard block id.
- Use `block_replace` to replace only that whiteboard unless the user asked for broader edits.
- Re-fetch after replacement because block ids can change.
