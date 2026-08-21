#!/usr/bin/env python3
"""Build an offline 3080 Brief HTML file from reviewed structured content."""

import argparse
import html
import json
import re
import sys
from pathlib import Path

from brief_model import BLOCK_TYPES, SEMANTIC_DIRECTIONS, subset_visual_spec, validate_document as validate_brief_document
from html_design_kit import (
    design_css,
    embedded_font_css,
    render_rich_visual,
    runtime_scripts,
    validate_design_plan,
)
from html_runtime_contract import (
    CONTRACT_VERSION,
    GENERATOR,
    GENERATOR_COMMENT,
    create_contract,
    load_json as load_contract_json,
    validate_contract,
    write_contract,
    write_receipt,
)
from render_visual_spec import render_svg
from theme_registry import resolve_visual_theme, theme_css


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config" / "3080-brief.json"
DEFAULT_CSS = SKILL_DIR / "assets" / "html" / "brief.css"


def esc(value):
    return html.escape(str(value), quote=True)


def rich_text(value):
    if isinstance(value, str):
        return esc(value)
    if not isinstance(value, list):
        raise ValueError("rich text must be a string or an array of spans")
    output = []
    for span in value:
        if not isinstance(span, dict) or "text" not in span:
            raise ValueError("each rich-text span requires text")
        content = esc(span["text"])
        direction = span.get("semantic_direction")
        if direction:
            if direction not in SEMANTIC_DIRECTIONS:
                raise ValueError(f"unknown semantic direction: {direction}")
            content = f'<span class="semantic-{direction}" data-semantic="{direction}">{content}</span>'
        if span.get("strong"):
            content = f"<strong>{content}</strong>"
        output.append(content)
    return "".join(output)


def plain_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(str(span.get("text", "")) for span in value if isinstance(span, dict))
    return str(value)


def validate_svg(svg_text, label):
    lowered = svg_text.casefold()
    lowered = lowered.replace('xmlns="http://www.w3.org/2000/svg"', "")
    forbidden = ("<script", "<foreignobject", "javascript:", "http://", "https://", "file://")
    if "<svg" not in lowered or "</svg>" not in lowered:
        raise ValueError(f"{label} is not a complete SVG")
    if any(token in lowered for token in forbidden):
        raise ValueError(f"{label} contains an external or executable SVG feature")
    return re.sub(r"<\?xml[^>]*>\s*", "", svg_text, count=1, flags=re.I)


def render_table(headers, rows, class_name=""):
    if not headers or not rows:
        raise ValueError("table requires headers and rows")
    header_html = "".join(f"<th scope=\"col\">{rich_text(cell)}</th>" for cell in headers)
    row_html = []
    for row in rows:
        if len(row) != len(headers):
            raise ValueError("table row width does not match headers")
        cells = "".join(
            f'<td data-label="{esc(plain_text(headers[index]))}">{rich_text(cell)}</td>'
            for index, cell in enumerate(row)
        )
        row_html.append(f"<tr>{cells}</tr>")
    class_attr = f' class="{esc(class_name)}"' if class_name else ""
    return f'<div class="table-wrap" data-geometry-scope="table"><table{class_attr}><thead><tr>{header_html}</tr></thead><tbody>{"".join(row_html)}</tbody></table></div>'


def resolve_svg(block, base_dir, visual_spec, config):
    if block.get("visual_block_ids"):
        subset = subset_visual_spec(visual_spec, block["visual_block_ids"], block.get("title", ""), block.get("alt_text", ""))
        return validate_svg(render_svg(subset, config, include_header=False), "rendered body figure"), subset
    raw_path = block.get("svg")
    if not raw_path:
        raise ValueError("figure block requires svg")
    candidate = (base_dir / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
    if not candidate.is_file() or candidate.suffix.casefold() != ".svg":
        raise ValueError(f"figure SVG not found: {raw_path}")
    return validate_svg(candidate.read_text(encoding="utf-8"), str(candidate)), None


def render_blocks(
    blocks,
    base_dir,
    visual_spec,
    config,
    allow_details=True,
    design_plan=None,
    runtime_items=None,
    figure_counter=None,
):
    runtime_items = runtime_items if runtime_items is not None else []
    figure_counter = figure_counter if figure_counter is not None else [0]
    output = []
    for block in blocks:
        block_type = block.get("type")
        if block_type not in BLOCK_TYPES:
            raise ValueError(f"unsupported HTML body block: {block_type}")
        if block_type == "paragraph":
            output.append(f'<p>{rich_text(block.get("text", ""))}</p>')
        elif block_type == "bullets":
            items = block.get("items") or []
            output.append("<ul>" + "".join(f"<li>{rich_text(item)}</li>" for item in items) + "</ul>")
        elif block_type == "callout":
            tone = block.get("tone", "neutral")
            if tone not in SEMANTIC_DIRECTIONS:
                raise ValueError(f"unknown callout tone: {tone}")
            title = f'<p class="callout-title">{rich_text(block["title"])}</p>' if block.get("title") else ""
            output.append(f'<aside class="callout" data-tone="{tone}">{title}<p>{rich_text(block.get("text", ""))}</p></aside>')
        elif block_type == "table":
            output.append(render_table(block.get("headers") or [], block.get("rows") or [], "body-table"))
        elif block_type == "figure":
            svg, figure_spec = resolve_svg(block, base_dir, visual_spec, config)
            title = rich_text(block.get("title", ""))
            alt_text = esc(block.get("alt_text", ""))
            if not title or not alt_text:
                raise ValueError("body figure requires a judgment title and alt_text")
            note = f'<p class="figure-note">{rich_text(block["note"])}</p>' if block.get("note") else ""
            figure_counter[0] += 1
            figure_id = f"body-visual-{figure_counter[0]}"
            if design_plan and figure_spec:
                visual_markup, visual_runtime = render_rich_visual(
                    figure_spec,
                    svg,
                    design_plan,
                    config,
                    figure_id,
                    full_picture=False,
                )
                runtime_items.extend(visual_runtime)
            else:
                visual_markup = f'<div class="visual-canvas">{svg}</div>'
            output.append(
                f'<figure class="body-figure" aria-label="{alt_text}"><figcaption>{title}</figcaption>'
                f'{visual_markup}{note}</figure>'
            )
        elif block_type == "details":
            if not allow_details or block.get("priority") != "P2":
                raise ValueError("details blocks are allowed only for P2 supporting depth")
            detail_blocks = block.get("blocks") or [
                {"type": "paragraph", "text": paragraph} for paragraph in block.get("paragraphs", [])
            ]
            nested = render_blocks(
                detail_blocks,
                base_dir,
                visual_spec,
                config,
                allow_details=False,
                design_plan=design_plan,
                runtime_items=runtime_items,
                figure_counter=figure_counter,
            )
            output.append(
                f'<details data-priority="P2"><summary>{rich_text(block.get("summary", ""))}</summary>'
                f'<div class="details-body">{nested}</div></details>'
            )
    return "".join(output)


def semantic_css(config):
    declarations = []
    for direction, mapping in config.get("semantic_colors", {}).items():
        if direction not in SEMANTIC_DIRECTIONS:
            continue
        declarations.append(f"--{direction}: {mapping['svg']};")
        declarations.append(f"--{direction}-tint: {mapping['svg_tint']};")
    return ":root { " + " ".join(declarations) + " }"


def build_html(document, visual_spec, config, css, base_dir, design_plan, runtime_contract):
    warnings = validate_brief_document(document, visual_spec, config)
    theme = resolve_visual_theme(visual_spec, config)
    svg = validate_svg(render_svg(visual_spec, config, include_header=False), "rendered one-picture visual")
    design_errors = validate_design_plan(design_plan, visual_spec)
    if design_errors:
        raise ValueError("; ".join(design_errors))
    css = f"{css}\n{embedded_font_css(design_plan)}\n{design_css(design_plan)}"
    runtime_items = []
    figure_counter = [0]
    language = str(document["language"])
    is_zh = language.casefold().startswith("zh")
    headers = ["问题", "结论", "为什么"] if is_zh else ["Question", "Conclusion", "Why"]
    source_label = "来源" if is_zh else "Source"
    source = document["source"]
    source_title = esc(source["title"])
    source_url = source.get("url", "")
    if source_url and re.match(r"^https?://", source_url, re.I):
        source_html = f'<a href="{esc(source_url)}" rel="noopener">{source_title}</a>'
    else:
        source_html = f"<span>{source_title}</span>"
    opening = "".join(f"<p>{rich_text(line)}</p>" for line in document["opening"]["lines"])
    question_rows = [[item["question"], item["conclusion"], item["why"]] for item in document["questions"]]
    question_table = render_table(headers, question_rows, "key-questions")
    body = []
    section_density = (document.get("reading_path") or {}).get("section_density") or []
    section_questions = (document.get("reading_path") or {}).get("section_questions") or []
    for section_index, section in enumerate(document.get("body") or []):
        density = section_density[section_index]
        reader_question = section_questions[section_index]
        body.append(
            f'<section class="story-section story-section--{esc(density)}" '
            f'data-reading-density="{esc(density)}" data-reader-question="{esc(reader_question)}">'
            f'<h2>{rich_text(section["heading"])}</h2>'
            f'{render_blocks(section["blocks"], base_dir, visual_spec, config, design_plan=design_plan, runtime_items=runtime_items, figure_counter=figure_counter)}</section>'
        )
    visual_title = rich_text(visual_spec.get("title", ""))
    visual_alt = esc(visual_spec.get("alt_text") or f'{visual_spec.get("title", "")}: {visual_spec.get("reading_path", "")}')
    coverage = esc(visual_spec.get("coverage_percent", ""))
    source_note = visual_spec.get("source_note")
    visual_note = f'<p class="figure-note">{rich_text(source_note)}</p>' if source_note else ""
    visual_markup, visual_runtime = render_rich_visual(
        visual_spec,
        svg,
        design_plan,
        config,
        "one-picture-visual",
        full_picture=True,
    )
    runtime_items.extend(visual_runtime)
    body_plan = design_plan.get("body") or {}
    html_attributes = (
        f' data-html-layout="{esc(design_plan["layout"])}"'
        f' data-density="{esc(design_plan["density"])}"'
        f' data-font-display="{esc(design_plan["typography"]["display"])}"'
        f' data-font-body="{esc(design_plan["typography"]["body"])}"'
        f' data-prose-measure="{esc(body_plan.get("prose_measure", "medium"))}"'
        f' data-section-treatment="{esc(body_plan.get("section_treatment", "ruled"))}"'
        f' data-figure-treatment="{esc(body_plan.get("figure_treatment", "integrated"))}"'
        f' data-generator="{GENERATOR}"'
        f' data-contract-version="{CONTRACT_VERSION}"'
        f' data-contract-id="{esc(runtime_contract["contract_id"])}"'
        f' data-brief-sha256="{esc(runtime_contract["inputs"]["brief"]["sha256"])}"'
        f' data-visual-spec-sha256="{esc(runtime_contract["inputs"]["visual_spec"]["sha256"])}"'
        f' data-html-design-sha256="{esc(runtime_contract["inputs"]["html_design"]["sha256"])}"'
    )
    scripts = runtime_scripts(runtime_items, visual_spec, config)
    visible_title = re.sub(r"^3080\s+Brief\s*[｜|]\s*", "", str(document["title"]), flags=re.I).strip()
    visible_title = visible_title or str(document["title"])
    output = f'''{GENERATOR_COMMENT}
<!doctype html>
<html lang="{esc(language)}" data-theme="{esc(theme['slug'])}"{html_attributes}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="{GENERATOR}">
  <title>{esc(document["title"])}</title>
  <style>{css}\n{theme_css(theme)}\n{semantic_css(config)}</style>
</head>
<body>
  <main class="page">
    <header class="report-header">
      <p class="artifact-label">3080 Brief</p>
      <h1 class="report-title">{esc(visible_title)}</h1>
    </header>
    <section class="tldr" data-section="tldr">
      <h2 class="tldr-heading">TLDR</h2>
      <div class="opening-unit" data-opening-lines="{len(document["opening"]["lines"])}">{opening}</div>
      <figure class="one-picture" data-coverage="{coverage}" data-geometry-scope="one-picture" aria-label="{visual_alt}">
        <figcaption>{visual_title}</figcaption>
        {visual_markup}
        {visual_note}
      </figure>
      {question_table}
      <p class="source-citation">{source_label}: {source_html}</p>
    </section>
    {''.join(body)}
    <footer class="artifact-footer">3080 Brief</footer>
  </main>
  {scripts}
</body>
</html>
'''
    return output, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", help="HTML brief content JSON")
    parser.add_argument("visual_spec", help="Reviewed 3080 visual_spec.json")
    parser.add_argument("output", help="Output .html path")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--css", default=str(DEFAULT_CSS))
    parser.add_argument("--design-plan", required=True, help="Reviewed HTML design plan JSON")
    parser.add_argument("--contract", default="", help="Locked HTML runtime contract JSON")
    parser.add_argument("--receipt", default="", help="Build receipt path; defaults beside the HTML")
    args = parser.parse_args()

    document_path = Path(args.document).resolve()
    document = json.loads(document_path.read_text(encoding="utf-8"))
    visual_spec = json.loads(Path(args.visual_spec).read_text(encoding="utf-8"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    css = Path(args.css).read_text(encoding="utf-8")
    design_plan_path = Path(args.design_plan).resolve()
    design_plan = json.loads(design_plan_path.read_text(encoding="utf-8"))
    target = Path(args.output).resolve()
    if target.suffix.casefold() != ".html":
        print("FAIL\nERROR output path must end in .html")
        return 1
    contract_path = Path(args.contract).resolve() if args.contract else Path(str(target) + ".contract.json")
    receipt_path = Path(args.receipt).resolve() if args.receipt else Path(str(target) + ".build-receipt.json")
    visual_spec_path = Path(args.visual_spec).resolve()
    try:
        if contract_path.is_file():
            runtime_contract = load_contract_json(contract_path, "HTML runtime contract")
            contract_errors = validate_contract(
                runtime_contract,
                document_path,
                visual_spec_path,
                design_plan_path,
                target,
            )
            if contract_errors:
                raise ValueError("; ".join(contract_errors))
        else:
            runtime_contract = create_contract(
                document_path,
                visual_spec_path,
                design_plan_path,
                target,
            )
            write_contract(contract_path, runtime_contract)
        output_html, warnings = build_html(
            document,
            visual_spec,
            config,
            css,
            document_path.parent,
            design_plan,
            runtime_contract,
        )
    except ValueError as exc:
        print(f"FAIL\nERROR {exc}")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(output_html, encoding="utf-8")
    write_receipt(receipt_path, runtime_contract, target, warnings)
    print(target)
    print(f"CONTRACT {contract_path}")
    print(f"RECEIPT {receipt_path}")
    for warning in warnings:
        print(f"WARN {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
