# Output Format Rules

Use this reference when deciding what kind of document to create.

## Core Rule

Match the output document type to the input document type unless the user explicitly specifies another output type.

The source document must remain unchanged in all cases.

## Format Mapping

| Input source | Default output | Required tool / workflow |
| --- | --- | --- |
| Feishu / Lark doc or wiki URL | New Feishu / Lark doc | `lark-doc` plus `lark-whiteboard` |
| Word `.docx` file | New Word `.docx` file | `documents:documents` workflow |
| Markdown file | New Markdown file | local file edit/create or `lark-markdown` when the target is Lark Markdown |
| Plain pasted text | Ask if output format matters; otherwise create a Markdown artifact unless user requests Feishu/Word | local file or requested target tool |
| Unsupported or ambiguous source type | Ask one clarification question | do not guess when final format matters |

If the user asks for a different output format, honor the explicit request when source truth and tool capability allow it.

## Language Routing

Use this precedence independently from document-format routing:

1. An explicit user instruction naming the desired output language.
2. Otherwise, the source document's primary language.
3. If source-language primacy is ambiguous, ask before drafting.

Do not infer output language from the language used to ask the question, prior conversation language, interface locale, user locale, or a phrase such as “Chinese context.” Record source language, output language, routing basis, and exact override evidence in `source_inventory.md`. Apply the resulting language to the title, TLDR, key-question table, body, and visual; retain source-native proper nouns and necessary terms when helpful.

## First-Screen Contract By Output Type

Every output type must preserve the 3080 first-screen contract:

1. Opening first-level heading first: `TLDR` by default, or a short source-language equivalent when the user explicitly prefers localized wording.
2. One-sentence summary immediately under the opening heading; it must let readers get the source document's core value within 30 seconds.
3. One-picture summary immediately after the one-sentence summary; it must cover at least 80% of value-weighted non-appendix claims.
4. One compact key-question table under the same opening section; it must answer the questions readers most want to ask while reading the document. Use `问题 / 结论 / 为什么` for Chinese and `Question / Conclusion / Why` for English; avoid method labels and cramped cells.
5. Source citation/reference near the top as low-emphasis metadata, not a standalone heading or section.

Implementation differs by output:

- Feishu / Lark output: insert the one-picture summary as editable Feishu whiteboard SVG.
- Word output: insert the one-picture summary as a rendered visual in the `.docx`; keep the source SVG or chart data as an auditable companion artifact when practical.
- Markdown output: embed or link the rendered visual and keep source SVG/chart data nearby.

The visual must remain source-grounded even when the output format cannot preserve Feishu-style editability.

## Tool Selection

- For Feishu / Lark sources and outputs, use `lark-doc`; use `lark-whiteboard` to query live previews.
- For Word `.docx` sources and outputs, use `documents:documents`; preserve professional document rendering and verify the generated file.
- For local files, create the new file beside the source or in the working output directory unless the user specifies a destination.
- Do not upload or convert formats solely for convenience. Convert only when the user requests it or the source format cannot support the required output.

## Verification By Output Type

- Feishu / Lark: verify created doc link, source unchanged, whiteboard block written, live preview inspected.
- Word `.docx`: verify the new `.docx` exists, opens/renders, source unchanged, one-picture summary is visible, and source citation/reference is included without a standalone source heading.
- Markdown: verify file exists, visual link/path works, source unchanged, and source citation/reference is included without a standalone source heading.

## Final Response

Report the generated output in the same format language:

- Feishu / Lark: generated doc link.
- Word / local file: generated file path.
- Markdown / local file: generated file path.

Always include source reference and verification notes. In the generated document, keep the source reference compact and low-emphasis; do not use headings such as `来源文档`, `原文链接`, or `Source Document`.
