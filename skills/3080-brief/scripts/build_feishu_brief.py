#!/usr/bin/env python3
"""Build native Feishu XML from one reviewed 3080 structured document and visual spec."""

import argparse
import html
import json
import re
import sys
from pathlib import Path

from brief_model import SEMANTIC_DIRECTIONS, plain_text, subset_visual_spec, validate_document
from render_visual_spec import render_svg
from theme_registry import resolve_visual_theme


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config" / "3080-brief.json"


def esc(value):
    return html.escape(str(value), quote=True)


def rich_text(value, config):
    if isinstance(value, str):
        return esc(value)
    output = []
    for span in value:
        content = esc(span["text"])
        direction = span.get("semantic_direction")
        if direction:
            if direction not in SEMANTIC_DIRECTIONS:
                raise ValueError(f"unknown semantic direction: {direction}")
            content = f'<span text-color="{config["semantic_colors"][direction]["body"]}">{content}</span>'
        if span.get("strong"):
            content = f"<b>{content}</b>"
        output.append(content)
    return "".join(output)


def render_table(headers, rows, config, widths=None):
    widths = widths or [1] * len(headers)
    total = sum(widths)
    pixel_widths = [max(90, round(720 * width / total)) for width in widths]
    cols = "".join(f'<col width="{width}"/>' for width in pixel_widths)
    head = "".join(f'<th background-color="light-gray" vertical-align="top">{rich_text(cell, config)}</th>' for cell in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f'<td vertical-align="top">{rich_text(cell, config)}</td>' for cell in row) + "</tr>")
    return f"<table><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def svg_from_block(block, base_dir, visual_spec, config):
    if block.get("visual_block_ids"):
        subset = subset_visual_spec(visual_spec, block["visual_block_ids"], block["title"], block["alt_text"])
        return render_svg(subset, config, include_header=False)
    candidate = (base_dir / block["svg"]).resolve() if not Path(block["svg"]).is_absolute() else Path(block["svg"]).resolve()
    if not candidate.is_file() or candidate.suffix.casefold() != ".svg":
        raise ValueError(f"body figure SVG not found: {block['svg']}")
    svg = candidate.read_text(encoding="utf-8")
    if "<svg" not in svg or "</svg>" not in svg or re.search(r"<script|<foreignObject|javascript:|https?://|file://", svg, re.I):
        raise ValueError(f"body figure SVG is unsafe or incomplete: {candidate}")
    return re.sub(r"<\?xml[^>]*>\s*", "", svg, count=1, flags=re.I)


def render_blocks(blocks, config, base_dir, visual_spec, allow_details=True):
    output = []
    callout_colors = {
        "favorable": ("light-green", "green"), "unfavorable": ("light-red", "red"),
        "warning": ("light-orange", "orange"), "neutral": ("light-blue", "blue"),
        "unknown": ("light-gray", "gray"),
    }
    for block in blocks:
        block_type = block["type"]
        if block_type == "paragraph":
            output.append(f'<p>{rich_text(block.get("text", ""), config)}</p>')
        elif block_type == "bullets":
            output.append("<ul>" + "".join(f'<li>{rich_text(item, config)}</li>' for item in block.get("items") or []) + "</ul>")
        elif block_type == "callout":
            tone = block.get("tone", "neutral")
            background, border = callout_colors[tone]
            title = f'<p><b>{rich_text(block["title"], config)}</b></p>' if block.get("title") else ""
            output.append(f'<callout background-color="{background}" border-color="{border}">{title}<p>{rich_text(block.get("text", ""), config)}</p></callout>')
        elif block_type == "table":
            output.append(render_table(block["headers"], block["rows"], config, block.get("widths")))
        elif block_type == "figure":
            svg = svg_from_block(block, base_dir, visual_spec, config)
            output.append(f'<p><b>{rich_text(block["title"], config)}</b></p><whiteboard type="svg">{svg}</whiteboard>')
            caption = block.get("note") or block["alt_text"]
            output.append(f'<blockquote><p><i>{rich_text(caption, config)}</i></p></blockquote>')
        elif block_type == "details":
            if not allow_details or block.get("priority") != "P2":
                raise ValueError("details blocks are allowed only for P2 supporting depth")
            nested = block.get("blocks") or [{"type": "paragraph", "text": item} for item in block.get("paragraphs") or []]
            output.append(f'<blockquote><p><b>{rich_text(block.get("summary", ""), config)}</b></p>{render_blocks(nested, config, base_dir, visual_spec, False)}</blockquote>')
    return "".join(output)


def metric_scope_caption(visual_spec):
    scopes = []
    for block in visual_spec.get("blocks", []):
        scope = block.get("metric_scope") or {}
        parts = [str(scope[key]) for key in ("metric", "unit", "period", "denominator", "segment", "filter") if scope.get(key)]
        if parts:
            scopes.append(" · ".join(parts))
    unique = list(dict.fromkeys(scopes))
    return "；".join(unique[:2])


def build_xml(document, visual_spec, config, base_dir):
    warnings = validate_document(document, visual_spec, config)
    resolve_visual_theme(visual_spec, config)
    language = str(document["language"])
    is_zh = language.casefold().startswith("zh")
    headers = ["问题", "结论", "为什么"] if is_zh else ["Question", "Conclusion", "Why"]
    source_label = "来源" if is_zh else "Source"
    figure_label = "图解" if is_zh else "Figure"
    opening = "".join(f'<p>{rich_text(line, config)}</p>' for line in document["opening"]["lines"])
    main_svg = render_svg(visual_spec, config, include_header=True)
    scope = metric_scope_caption(visual_spec)
    visual_caption = visual_spec.get("alt_text") or visual_spec.get("reading_path", "")
    if scope:
        visual_caption = f"{visual_caption}（{scope}）" if is_zh else f"{visual_caption} ({scope})"
    questions = [[item["question"], item["conclusion"], item["why"]] for item in document["questions"]]
    source = document["source"]
    source_title = esc(source["title"])
    if source.get("url") and re.match(r"^https?://", source["url"], re.I):
        source_value = f'<a href="{esc(source["url"])}">{source_title}</a>'
    else:
        source_value = source_title
    body = []
    for section in document.get("body") or []:
        body.append(f'<h1>{rich_text(section["heading"], config)}</h1>{render_blocks(section["blocks"], config, base_dir, visual_spec)}')
    xml = (
        f'<title>{esc(document["title"])}</title><h1>TLDR</h1>'
        f'<callout>{opening}</callout>'
        f'<whiteboard type="svg">{main_svg}</whiteboard>'
        f'<blockquote><p><i>{figure_label}：{esc(visual_caption)}</i></p></blockquote>'
        f'{render_table(headers, questions, config, [26, 30, 44])}'
        f'<blockquote><p><i>{source_label}：{source_value}</i></p></blockquote>'
        f'{"".join(body)}'
    )
    return xml, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", help="Reviewed brief.json")
    parser.add_argument("visual_spec", help="Reviewed visual_spec.json")
    parser.add_argument("output", help="Output Feishu XML path")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    document_path = Path(args.document).resolve()
    document = json.loads(document_path.read_text(encoding="utf-8"))
    visual_spec = json.loads(Path(args.visual_spec).read_text(encoding="utf-8"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    try:
        xml, warnings = build_xml(document, visual_spec, config, document_path.parent)
    except ValueError as exc:
        print(f"FAIL\nERROR {exc}")
        return 1
    target = Path(args.output)
    if target.suffix.casefold() != ".xml":
        print("FAIL\nERROR output path must end in .xml")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(xml + "\n", encoding="utf-8")
    print(target)
    for warning in warnings:
        print(f"WARN {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
