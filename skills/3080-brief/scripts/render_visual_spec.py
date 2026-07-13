#!/usr/bin/env python3
import argparse
import html
import json
import math
import re
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


def esc(value):
    return html.escape(str(value), quote=True)


def color(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value) else fallback


def text(x, y, value, size=20, weight=500, fill="#172033", anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(value)}</text>'


def semantic_color(node, block, palette, tint=False, fallback=None):
    direction = node.get("semantic_direction") or block.get("semantic_direction")
    mapping = palette["semantic"].get(direction, {})
    key = "svg_tint" if tint else "svg"
    return mapping.get(key, fallback or palette["primary"])


def block_height(block):
    return 250 if block.get("type") in {"bar", "dot", "threshold", "timeline", "flow"} else 300


def render_bar(block, x, y, width, palette):
    items = block.get("items", [])[:6]
    values = [float(item.get("value", 0)) for item in items]
    maximum = max(values) if values else 1
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    for index, item in enumerate(items):
        row_y = y + 45 + index * 32
        value = float(item.get("value", 0))
        bar_w = max(2, (width - 220) * value / maximum) if maximum else 2
        output.append(text(x, row_y + 18, item.get("label", ""), 17, 600, palette["text"]))
        mark_color = semantic_color(item, block, palette)
        output.append(f'<rect x="{x + 150}" y="{row_y}" width="{bar_w:.1f}" height="22" rx="3" fill="{mark_color}"/>')
        output.append(text(x + 160 + bar_w, row_y + 18, item.get("display", value), 17, 700, mark_color))
    return output


def render_dot(block, x, y, width, palette):
    items = block.get("items", [])[:6]
    values = [float(item.get("value", 0)) for item in items]
    low = min(values) if values else 0
    high = max(values) if values else 1
    span = high - low or 1
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    for index, item in enumerate(items):
        row_y = y + 50 + index * 32
        value = float(item.get("value", 0))
        dot_x = x + 170 + (width - 260) * (value - low) / span
        output.extend([
            text(x, row_y + 7, item.get("label", ""), 17, 600, palette["text"]),
            f'<line x1="{x + 170}" y1="{row_y}" x2="{x + width - 70}" y2="{row_y}" stroke="#D6DAE3" stroke-width="2"/>',
            f'<circle cx="{dot_x:.1f}" cy="{row_y}" r="8" fill="{semantic_color(item, block, palette)}"/>',
            text(dot_x + 14, row_y + 7, item.get("display", value), 17, 700, semantic_color(item, block, palette)),
        ])
    return output


def render_threshold(block, x, y, width, palette):
    minimum = float(block.get("minimum", 0))
    maximum = float(block.get("maximum", 100))
    threshold = float(block.get("threshold", minimum))
    value = float(block.get("value", minimum))
    span = maximum - minimum or 1
    start = x + 40
    end = x + width - 40
    threshold_x = start + (end - start) * (threshold - minimum) / span
    value_x = start + (end - start) * (value - minimum) / span
    output = [
        text(x, y, block.get("title", ""), 24, 700, palette["text"]),
        f'<rect x="{start}" y="{y + 65}" width="{max(0, threshold_x - start):.1f}" height="28" rx="4" fill="#E9EDF4"/>',
        f'<rect x="{threshold_x:.1f}" y="{y + 65}" width="{max(0, end - threshold_x):.1f}" height="28" rx="4" fill="{palette["accent"]}"/>',
        f'<line x1="{threshold_x:.1f}" y1="{y + 45}" x2="{threshold_x:.1f}" y2="{y + 115}" stroke="{palette["text"]}" stroke-width="3"/>',
        f'<circle cx="{value_x:.1f}" cy="{y + 79}" r="11" fill="{semantic_color(block, block, palette)}"/>',
        text(threshold_x, y + 135, f'{block.get("threshold_label", "Threshold")} {threshold:g}', 17, 600, palette["text"], "middle"),
        text(value_x, y + 165, f'{block.get("value_label", "Value")} {value:g}', 17, 700, semantic_color(block, block, palette), "middle"),
    ]
    if block.get("note"):
        output.append(text(x + 40, y + 205, block["note"], 17, 500, palette["text"]))
    return output


def render_matrix(block, x, y, width, palette):
    rows = block.get("rows", [])[:4]
    columns = block.get("columns", [])[:4]
    cells = {(cell.get("row"), cell.get("column")): cell for cell in block.get("cells", [])}
    left = x + 150
    top = y + 55
    cell_w = (width - 180) / max(1, len(columns))
    cell_h = 48
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    for col_index, column in enumerate(columns):
        output.append(text(left + col_index * cell_w + cell_w / 2, top - 14, column, 16, 700, palette["text"], "middle"))
    for row_index, row in enumerate(rows):
        output.append(text(x, top + row_index * cell_h + 30, row, 16, 600, palette["text"]))
        for col_index, column in enumerate(columns):
            cell = cells.get((row, column), {})
            fill = semantic_color(cell, block, palette, tint=True, fallback=color(cell.get("fill"), palette["background_alt"]))
            label_color = semantic_color(cell, block, palette, fallback=palette["text"]) if cell.get("semantic_direction") or block.get("semantic_direction") else palette["text"]
            cell_x = left + col_index * cell_w
            cell_y = top + row_index * cell_h
            output.append(f'<rect x="{cell_x:.1f}" y="{cell_y:.1f}" width="{cell_w - 6:.1f}" height="{cell_h - 6}" rx="4" fill="{fill}" stroke="#D6DAE3"/>')
            output.append(text(cell_x + (cell_w - 6) / 2, cell_y + 28, cell.get("label", ""), 15, 700, label_color, "middle"))
    return output


def render_sequence(block, x, y, width, palette):
    items = block.get("items", [])[:6]
    count = max(1, len(items))
    gap = width / count
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    cy = y + 105
    for index, item in enumerate(items):
        cx = x + gap * index + gap / 2
        mark_color = semantic_color(item, block, palette)
        output.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="25" fill="{mark_color}"/>')
        output.append(text(cx, cy + 7, index + 1, 17, 700, "#FFFFFF", "middle"))
        output.append(text(cx, cy + 62, item.get("label", ""), 16, 700, palette["text"], "middle"))
        if index < len(items) - 1:
            output.append(f'<line x1="{cx + 30:.1f}" y1="{cy}" x2="{cx + gap - 30:.1f}" y2="{cy}" stroke="{mark_color}" stroke-width="3" marker-end="url(#arrow)"/>')
    return output


def main():
    parser = argparse.ArgumentParser(description="Render a 3080 visual_spec.json to editable native-shape SVG.")
    parser.add_argument("spec")
    parser.add_argument("output")
    parser.add_argument("--config", default=str(SKILL_DIR / "config" / "3080-brief.json"))
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    palette_input = spec.get("palette", {})
    palette = {
        "primary": color(palette_input.get("primary"), "#0055A4"),
        "accent": color(palette_input.get("accent"), "#DCF4A2"),
        "risk": color(palette_input.get("risk"), "#C94B4B"),
        "background": color(palette_input.get("background"), "#FFFFFF"),
        "background_alt": "#F4F6F9",
        "text": color(palette_input.get("text"), "#172033"),
        "semantic": config.get("semantic_colors", {}),
    }
    blocks = spec.get("blocks", [])
    width = 1600
    heights = [block_height(block) for block in blocks]
    height = 170 + sum(heights) + max(0, len(blocks) - 1) * 28 + 60
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0 0 L10 4 L0 8 z"/></marker></defs>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{palette["background"]}"/>',
        text(70, 72, spec.get("title", "3080 Visual"), 38, 800, palette["text"]),
        text(70, 112, spec.get("reading_path", ""), 19, 500, palette["text"]),
    ]
    y = 165
    renderers = {
        "bar": render_bar,
        "dot": render_dot,
        "threshold": render_threshold,
        "matrix": render_matrix,
        "timeline": render_sequence,
        "flow": render_sequence,
    }
    for block, height_item in zip(blocks, heights):
        output.append(f'<rect x="60" y="{y - 36}" width="1480" height="{height_item}" rx="8" fill="#FFFFFF" stroke="#D6DAE3"/>')
        renderer = renderers.get(block.get("type"))
        if renderer:
            output.extend(renderer(block, 95, y, 1410, palette))
        else:
            output.append(text(95, y, block.get("title", ""), 24, 700, palette["text"]))
            output.append(text(95, y + 48, block.get("note", ""), 18, 500, palette["text"]))
        y += height_item + 28
    output.append("</svg>")
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
