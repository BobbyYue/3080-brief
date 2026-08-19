#!/usr/bin/env python3
import argparse
import html
import json
import math
import re
from pathlib import Path

from theme_registry import resolve_visual_theme, theme_palette


SKILL_DIR = Path(__file__).resolve().parents[1]


def esc(value):
    return html.escape(str(value), quote=True)


def color(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value) else fallback


def blend(foreground, background, amount):
    amount = max(0.0, min(1.0, float(amount)))
    fg = tuple(int(foreground[index:index + 2], 16) for index in (1, 3, 5))
    bg = tuple(int(background[index:index + 2], 16) for index in (1, 3, 5))
    mixed = tuple(round(bg_value + (fg_value - bg_value) * amount) for fg_value, bg_value in zip(fg, bg))
    return "#" + "".join(f"{value:02X}" for value in mixed)


def text(x, y, value, size=20, weight=500, fill="#172033", anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(value)}</text>'


def wrapped_text(x, y, value, size=20, weight=500, fill="#172033", max_chars=18, line_height=None):
    """Render short SVG labels as separate native text nodes."""
    content = str(value or "").strip()
    if not content:
        return []
    line_height = line_height or round(size * 1.35)
    if len(content) <= max_chars:
        lines = [content]
    elif " " in content:
        lines = []
        current = ""
        for word in content.split():
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > max_chars:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
    else:
        lines = [content[index:index + max_chars] for index in range(0, len(content), max_chars)]
    return [text(x, y + index * line_height, line, size, weight, fill) for index, line in enumerate(lines)]


def semantic_color(node, block, palette, tint=False, fallback=None):
    direction = node.get("semantic_direction") or block.get("semantic_direction")
    mapping = palette["semantic"].get(direction, {})
    key = "svg_tint" if tint else "svg"
    return mapping.get(key, fallback or palette["primary"])


def block_height(block):
    block_type = block.get("type")
    if block_type == "annotation":
        return 220 if block.get("items") else 150
    compact = {"bar", "diverging_bar", "stacked_bar", "dot", "slope", "threshold", "range", "funnel", "timeline", "flow", "sequence"}
    return 250 if block_type in compact else 300


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


def render_diverging_bar(block, x, y, width, palette):
    items = block.get("items", [])[:6]
    values = [float(item.get("value", 0)) for item in items]
    extent = max([abs(value) for value in values] or [1]) or 1
    center = x + width * 0.56
    half = width * 0.36
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    output.append(f'<line x1="{center:.1f}" y1="{y + 38}" x2="{center:.1f}" y2="{y + 230}" stroke="{palette["rule"]}" stroke-width="2"/>')
    for index, item in enumerate(items):
        row_y = y + 48 + index * 32
        value = float(item.get("value", 0))
        bar_w = half * abs(value) / extent
        bar_x = center if value >= 0 else center - bar_w
        mark_color = semantic_color(item, block, palette)
        output.append(text(x, row_y + 18, item.get("label", ""), 17, 600, palette["text"]))
        output.append(f'<rect x="{bar_x:.1f}" y="{row_y}" width="{max(2, bar_w):.1f}" height="22" rx="3" fill="{mark_color}"/>')
        label_x = center + bar_w + 10 if value >= 0 else center - bar_w - 10
        anchor = "start" if value >= 0 else "end"
        output.append(text(label_x, row_y + 18, item.get("display", value), 17, 700, mark_color, anchor))
    return output


def render_stacked_bar(block, x, y, width, palette):
    items = block.get("items", [])[:8]
    values = [max(0, float(item.get("value", 0))) for item in items]
    total = sum(values) or 1
    start = x + 40
    usable = width - 80
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    cursor = start
    for item, value in zip(items, values):
        segment_width = usable * value / total
        mark_color = semantic_color(item, block, palette)
        output.append(f'<rect x="{cursor:.1f}" y="{y + 70}" width="{segment_width:.1f}" height="46" fill="{mark_color}"/>')
        if segment_width >= 70:
            output.append(text(cursor + segment_width / 2, y + 99, item.get("display", item.get("value", "")), 16, 700, "#FFFFFF", "middle"))
        cursor += segment_width
    legend_x = start
    for index, item in enumerate(items):
        if index and index % 4 == 0:
            legend_x = start
        legend_y = y + 155 + (index // 4) * 34
        mark_color = semantic_color(item, block, palette)
        output.append(f'<circle cx="{legend_x + 7}" cy="{legend_y - 5}" r="7" fill="{mark_color}"/>')
        output.append(text(legend_x + 20, legend_y, item.get("label", ""), 15, 600, palette["text"]))
        legend_x += usable / 4
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
            f'<line x1="{x + 170}" y1="{row_y}" x2="{x + width - 70}" y2="{row_y}" stroke="{palette["rule"]}" stroke-width="2"/>',
            f'<circle cx="{dot_x:.1f}" cy="{row_y}" r="8" fill="{semantic_color(item, block, palette)}"/>',
            text(dot_x + 14, row_y + 7, item.get("display", value), 17, 700, semantic_color(item, block, palette)),
        ])
    return output


def render_slope(block, x, y, width, palette):
    items = block.get("items", [])[:5]
    pairs = [(float(item.get("start", item.get("low", 0))), float(item.get("end", item.get("high", 0)))) for item in items]
    values = [value for pair in pairs for value in pair]
    low = min(values) if values else 0
    high = max(values) if values else 1
    span = high - low or 1
    left = x + width * 0.28
    right = x + width * 0.78
    top = y + 45
    chart_height = 165
    scale_y = lambda value: top + chart_height - chart_height * (value - low) / span
    output = [
        text(x, y, block.get("title", ""), 24, 700, palette["text"]),
        text(left, y + 33, block.get("start_label", "Before"), 15, 700, palette["text"], "middle"),
        text(right, y + 33, block.get("end_label", "After"), 15, 700, palette["text"], "middle"),
    ]
    for item, (start_value, end_value) in zip(items, pairs):
        start_y = scale_y(start_value)
        end_y = scale_y(end_value)
        mark_color = semantic_color(item, block, palette)
        output.append(f'<line x1="{left:.1f}" y1="{start_y:.1f}" x2="{right:.1f}" y2="{end_y:.1f}" stroke="{mark_color}" stroke-width="4"/>')
        output.append(f'<circle cx="{left:.1f}" cy="{start_y:.1f}" r="7" fill="{mark_color}"/>')
        output.append(f'<circle cx="{right:.1f}" cy="{end_y:.1f}" r="7" fill="{mark_color}"/>')
        output.append(text(left - 14, start_y + 5, item.get("start_display", start_value), 15, 700, mark_color, "end"))
        output.append(text(right + 14, end_y + 5, item.get("end_display", end_value), 15, 700, mark_color))
        output.append(text(x, (start_y + end_y) / 2 + 5, item.get("label", ""), 15, 600, palette["text"]))
    return output


def render_line(block, x, y, width, palette):
    items = block.get("items", [])[:12]
    values = [float(item.get("value", 0)) for item in items]
    low = min(values) if values else 0
    high = max(values) if values else 1
    span = high - low or 1
    left = x + 70
    right = x + width - 45
    top = y + 45
    bottom = y + 230
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    output.extend([
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{palette["rule"]}" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="{palette["rule"]}" stroke-width="2"/>',
    ])
    points = []
    for index, (item, value) in enumerate(zip(items, values)):
        point_x = left + (right - left) * index / max(1, len(items) - 1)
        point_y = bottom - (bottom - top) * (value - low) / span
        points.append((point_x, point_y, item, value))
    if points:
        output.append(f'<polyline points="{" ".join(f"{px:.1f},{py:.1f}" for px, py, _, _ in points)}" fill="none" stroke="{semantic_color(block, block, palette)}" stroke-width="4"/>')
    for index, (point_x, point_y, item, value) in enumerate(points):
        mark_color = semantic_color(item, block, palette)
        output.append(f'<circle cx="{point_x:.1f}" cy="{point_y:.1f}" r="6" fill="{mark_color}"/>')
        output.append(text(point_x, bottom + 25, item.get("label", ""), 14, 600, palette["text"], "middle"))
        if index in {0, len(points) - 1} or item.get("annotate"):
            output.append(text(point_x, point_y - 12, item.get("display", value), 15, 700, mark_color, "middle"))
    return output


def render_scatter(block, x, y, width, palette):
    items = block.get("items", [])[:30]
    xs = [float(item.get("x", 0)) for item in items]
    ys = [float(item.get("y", 0)) for item in items]
    xmin, xmax = (min(xs), max(xs)) if xs else (0, 1)
    ymin, ymax = (min(ys), max(ys)) if ys else (0, 1)
    xspan = xmax - xmin or 1
    yspan = ymax - ymin or 1
    left = x + 70
    right = x + width - 45
    top = y + 45
    bottom = y + 250
    output = [
        text(x, y, block.get("title", ""), 24, 700, palette["text"]),
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{palette["rule"]}" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="{palette["rule"]}" stroke-width="2"/>',
    ]
    if block.get("reference_line") == "diagonal":
        output.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{top}" stroke="{palette["rule"]}" stroke-width="2" stroke-dasharray="8 7"/>')
    for item in items:
        item_x = float(item.get("x", 0))
        item_y = float(item.get("y", 0))
        point_x = left + (right - left) * (item_x - xmin) / xspan
        point_y = bottom - (bottom - top) * (item_y - ymin) / yspan
        mark_color = semantic_color(item, block, palette)
        output.append(f'<circle cx="{point_x:.1f}" cy="{point_y:.1f}" r="8" fill="{mark_color}"/>')
        if item.get("label"):
            output.append(text(point_x + 10, point_y - 9, item["label"], 13, 600, palette["text"]))
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
        f'<rect x="{start}" y="{y + 65}" width="{max(0, threshold_x - start):.1f}" height="28" rx="4" fill="{palette["background_alt"]}"/>',
        f'<rect x="{threshold_x:.1f}" y="{y + 65}" width="{max(0, end - threshold_x):.1f}" height="28" rx="4" fill="{palette["accent"]}"/>',
        f'<line x1="{threshold_x:.1f}" y1="{y + 45}" x2="{threshold_x:.1f}" y2="{y + 115}" stroke="{palette["text"]}" stroke-width="3"/>',
        f'<circle cx="{value_x:.1f}" cy="{y + 79}" r="11" fill="{semantic_color(block, block, palette)}"/>',
        text(threshold_x, y + 135, f'{block.get("threshold_label", "Threshold")} {threshold:g}', 17, 600, palette["text"], "middle"),
        text(value_x, y + 165, f'{block.get("value_label", "Value")} {value:g}', 17, 700, semantic_color(block, block, palette), "middle"),
    ]
    if block.get("note"):
        output.append(text(x + 40, y + 205, block["note"], 17, 500, palette["text"]))
    return output


def render_range(block, x, y, width, palette):
    items = block.get("items", [])[:6]
    values = [float(item.get(key, 0)) for item in items for key in ("low", "high")]
    low = min(values) if values else 0
    high = max(values) if values else 1
    span = high - low or 1
    start = x + 170
    end = x + width - 70
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    for index, item in enumerate(items):
        row_y = y + 52 + index * 34
        item_low = float(item.get("low", 0))
        item_high = float(item.get("high", item_low))
        low_x = start + (end - start) * (item_low - low) / span
        high_x = start + (end - start) * (item_high - low) / span
        mark_color = semantic_color(item, block, palette)
        output.append(text(x, row_y + 6, item.get("label", ""), 16, 600, palette["text"]))
        output.append(f'<line x1="{start}" y1="{row_y}" x2="{end}" y2="{row_y}" stroke="{palette["rule"]}" stroke-width="2"/>')
        output.append(f'<line x1="{low_x:.1f}" y1="{row_y}" x2="{high_x:.1f}" y2="{row_y}" stroke="{mark_color}" stroke-width="10" stroke-linecap="round"/>')
        output.append(f'<circle cx="{low_x:.1f}" cy="{row_y}" r="6" fill="{mark_color}"/>')
        output.append(f'<circle cx="{high_x:.1f}" cy="{row_y}" r="6" fill="{mark_color}"/>')
        output.append(text(high_x + 12, row_y + 6, item.get("display", f"{item_low:g}-{item_high:g}"), 15, 700, mark_color))
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
            output.append(f'<rect x="{cell_x:.1f}" y="{cell_y:.1f}" width="{cell_w - 6:.1f}" height="{cell_h - 6}" rx="4" fill="{fill}" stroke="{palette["rule"]}"/>')
            output.append(text(cell_x + (cell_w - 6) / 2, cell_y + 28, cell.get("label", ""), 15, 700, label_color, "middle"))
    return output


def render_heatmap(block, x, y, width, palette):
    rows = block.get("rows", [])[:6]
    columns = block.get("columns", [])[:6]
    cells = {(cell.get("row"), cell.get("column")): cell for cell in block.get("cells", [])}
    numeric_values = [float(cell["value"]) for cell in cells.values() if isinstance(cell.get("value"), (int, float))]
    value_low = min(numeric_values) if numeric_values else 0
    value_high = max(numeric_values) if numeric_values else 1
    span = value_high - value_low or 1
    left = x + 150
    top = y + 55
    cell_w = (width - 180) / max(1, len(columns))
    cell_h = min(42, 205 / max(1, len(rows)))
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    for col_index, column in enumerate(columns):
        output.append(text(left + col_index * cell_w + cell_w / 2, top - 13, column, 14, 700, palette["text"], "middle"))
    for row_index, row in enumerate(rows):
        output.append(text(x, top + row_index * cell_h + cell_h * 0.65, row, 14, 600, palette["text"]))
        for col_index, column in enumerate(columns):
            cell = cells.get((row, column))
            cell_x = left + col_index * cell_w
            cell_y = top + row_index * cell_h
            if not cell:
                fill = palette["semantic"].get("unknown", {}).get("svg_tint", palette["background_alt"])
                label = "N/A"
                label_color = palette["semantic"].get("unknown", {}).get("svg", palette["text"])
            else:
                direction = cell.get("semantic_direction")
                if direction:
                    fill = semantic_color(cell, block, palette, tint=True, fallback=palette["background_alt"])
                    label_color = semantic_color(cell, block, palette, fallback=palette["text"])
                else:
                    value = float(cell.get("value", value_low)) if isinstance(cell.get("value"), (int, float)) else value_low
                    opacity = 0.12 + 0.50 * (value - value_low) / span
                    fill = blend(palette["primary"], palette["background"], opacity)
                    label_color = palette["text"]
                label = cell.get("label", cell.get("value", "N/A"))
            output.append(f'<rect x="{cell_x:.1f}" y="{cell_y:.1f}" width="{cell_w - 5:.1f}" height="{cell_h - 5:.1f}" rx="3" fill="{fill}" stroke="{palette["rule"]}"/>')
            output.append(text(cell_x + (cell_w - 5) / 2, cell_y + cell_h * 0.65, label, 13, 700, label_color, "middle"))
    return output


def render_funnel(block, x, y, width, palette):
    items = block.get("items", [])[:6]
    values = [max(0, float(item.get("value", 0))) for item in items]
    maximum = max(values) if values else 1
    center = x + width * 0.58
    max_width = width * 0.58
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    for index, (item, value) in enumerate(zip(items, values)):
        row_y = y + 42 + index * 34
        bar_width = max(34, max_width * value / (maximum or 1))
        mark_color = semantic_color(item, block, palette)
        output.append(text(x, row_y + 21, item.get("label", ""), 16, 600, palette["text"]))
        output.append(f'<rect x="{center - bar_width / 2:.1f}" y="{row_y}" width="{bar_width:.1f}" height="27" rx="3" fill="{mark_color}"/>')
        output.append(text(center, row_y + 20, item.get("display", value), 15, 700, "#FFFFFF", "middle"))
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
        label = item.get("label", "")
        if len(str(label)) <= 18:
            output.append(text(cx, cy + 62, label, 16, 700, palette["text"], "middle"))
        else:
            # Long labels are left-aligned in two or more native text rows to avoid
            # shrinking the entire visual or clipping at panel edges.
            output.extend(wrapped_text(cx - gap * 0.36, cy + 58, label, 15, 700, palette["text"], max_chars=max(10, int(gap / 12))))
        if index < len(items) - 1:
            output.append(f'<line x1="{cx + 30:.1f}" y1="{cy}" x2="{cx + gap - 30:.1f}" y2="{cy}" stroke="{mark_color}" stroke-width="3" marker-end="url(#arrow)"/>')
    return output


def render_annotation(block, x, y, width, palette):
    output = [text(x, y, block.get("title", ""), 24, 700, palette["text"])]
    items = block.get("items", [])[:4]
    if items:
        gap = 16
        card_width = (width - gap * (len(items) - 1)) / len(items)
        for index, item in enumerate(items):
            card_x = x + index * (card_width + gap)
            tint = semantic_color(item, block, palette, tint=True, fallback=palette["background_alt"])
            mark_color = semantic_color(item, block, palette, fallback=palette["text"])
            output.append(f'<rect x="{card_x:.1f}" y="{y + 42}" width="{card_width:.1f}" height="105" rx="6" fill="{tint}" stroke="{palette["rule"]}"/>')
            display = item.get("display", item.get("value", ""))
            output.append(text(card_x + 18, y + 82, display, 28, 800, mark_color))
            output.extend(wrapped_text(card_x + 18, y + 116, item.get("label", ""), 16, 600, palette["text"], max_chars=max(10, int(card_width / 12))))
        if block.get("note"):
            output.extend(wrapped_text(x, y + 180, block["note"], 16, 500, palette["text"], max_chars=max(24, int(width / 13))))
    elif block.get("note"):
        output.extend(wrapped_text(x, y + 48, block["note"], 18, 500, palette["text"], max_chars=max(24, int(width / 13))))
    return output


def panel_fill(block, palette):
    role = block.get("visual_role", "support")
    if role == "anchor":
        return palette["surface"]
    direction = "warning" if role == "caveat" else "unknown"
    return palette["semantic"].get(direction, {}).get("svg_tint", palette["surface"])


def render_panel(block, x, y, width, height, palette, renderers):
    output = [f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{panel_fill(block, palette)}" stroke="{palette["rule"]}"/>']
    renderer = renderers.get(block.get("type"), render_annotation)
    output.extend(renderer(block, x + 28, y + 40, width - 56, palette))
    return output


def render_stage_story(blocks, start_y, palette, renderers):
    """Render a multi-stage process as one compact story, not stacked full-width cards."""
    stage_types = {"flow", "sequence", "timeline"}
    stages = [block for block in blocks if block.get("type") in stage_types]
    stage_ids = {id(block) for block in stages}
    context = [block for block in blocks if id(block) not in stage_ids and block.get("visual_role") == "anchor"]
    remainder = [block for block in blocks if id(block) not in stage_ids and id(block) not in {id(item) for item in context}]
    output = []
    y = start_y
    if context:
        block = context[0]
        height = block_height(block)
        output.extend(render_panel(block, 60, y, 1480, height, palette, renderers))
        y += height + 28

    count = max(1, len(stages))
    gap = 24
    card_width = (1480 - gap * (count - 1)) / count
    card_height = 350
    center_y = y + card_height / 2
    for index in range(count - 1):
        x1 = 60 + (index + 1) * card_width + index * gap
        x2 = x1 + gap - 5
        output.append(f'<line x1="{x1:.1f}" y1="{center_y:.1f}" x2="{x2:.1f}" y2="{center_y:.1f}" stroke="{palette["primary"]}" stroke-width="3" marker-end="url(#arrow)"/>')
    for stage_index, block in enumerate(stages):
        card_x = 60 + stage_index * (card_width + gap)
        output.append(f'<rect x="{card_x:.1f}" y="{y}" width="{card_width:.1f}" height="{card_height}" rx="8" fill="{panel_fill(block, palette)}" stroke="{palette["rule"]}"/>')
        output.extend(wrapped_text(card_x + 22, y + 40, block.get("title", ""), 22, 750, palette["text"], max_chars=max(10, int(card_width / 13))))
        items = block.get("items", [])[:4]
        item_gap = min(78, 245 / max(1, len(items)))
        for item_index, item in enumerate(items):
            item_y = y + 105 + item_index * item_gap
            mark_color = semantic_color(item, block, palette)
            output.append(f'<circle cx="{card_x + 35:.1f}" cy="{item_y:.1f}" r="15" fill="{mark_color}"/>')
            output.append(text(card_x + 35, item_y + 6, item_index + 1, 16, 800, "#FFFFFF", "middle"))
            if item_index < len(items) - 1:
                output.append(f'<line x1="{card_x + 35:.1f}" y1="{item_y + 18:.1f}" x2="{card_x + 35:.1f}" y2="{item_y + item_gap - 18:.1f}" stroke="{mark_color}" stroke-width="2"/>')
            output.extend(wrapped_text(card_x + 62, item_y + 5, item.get("label", ""), 17, 650, palette["text"], max_chars=max(10, int((card_width - 82) / 11))))
        if block.get("note"):
            output.extend(wrapped_text(card_x + 22, y + card_height - 35, block["note"], 14, 500, palette["text"], max_chars=max(10, int(card_width / 11))))
    y += card_height + 28

    for block in remainder:
        height = block_height(block)
        output.extend(render_panel(block, 60, y, 1480, height, palette, renderers))
        y += height + 28
    return output, y


def render_svg(spec, config, include_header=True):
    theme = resolve_visual_theme(spec, config)
    palette = theme_palette(theme)
    palette["risk"] = config.get("semantic_colors", {}).get("unfavorable", {}).get("svg", "#C94B4B")
    palette["semantic"] = config.get("semantic_colors", {})
    blocks = spec.get("blocks", [])
    width = 1600
    header_height = 170 if include_header else 55
    composition = spec.get("composition", "vertical_story")
    stage_count = sum(block.get("type") in {"flow", "sequence", "timeline"} for block in blocks)
    if composition == "stage_story" and 3 <= stage_count <= 4:
        estimated_content_height = header_height + 350 + sum(block_height(block) + 28 for block in blocks if block.get("type") not in {"flow", "sequence", "timeline"}) + 60
    else:
        estimated_content_height = header_height + sum(block_height(block) for block in blocks) + max(0, len(blocks) - 1) * 28 + 60
    max_aspect = float(config.get("whiteboard_render", {}).get("max_viewbox_aspect_ratio", 1.7))
    height = max(estimated_content_height, math.ceil(width / max_aspect))
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" data-composition="{esc(composition)}">',
        '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0 0 L10 4 L0 8 z"/></marker></defs>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{palette["background"]}"/>',
    ]
    if include_header:
        output.extend([
            text(70, 72, spec.get("title", "3080 Visual"), 38, 800, palette["text"]),
            text(70, 112, spec.get("reading_path", ""), 19, 500, palette["text"]),
        ])
    y = 165 if include_header else 50
    renderers = {
        "bar": render_bar,
        "diverging_bar": render_diverging_bar,
        "stacked_bar": render_stacked_bar,
        "dot": render_dot,
        "slope": render_slope,
        "line": render_line,
        "scatter": render_scatter,
        "threshold": render_threshold,
        "range": render_range,
        "distribution": render_range,
        "matrix": render_matrix,
        "heatmap": render_heatmap,
        "funnel": render_funnel,
        "timeline": render_sequence,
        "flow": render_sequence,
        "sequence": render_sequence,
        "hierarchy": render_sequence,
        "network": render_sequence,
        "annotation": render_annotation,
    }
    if composition == "stage_story" and 3 <= stage_count <= 4:
        story_output, y = render_stage_story(blocks, y - 36, palette, renderers)
        output.extend(story_output)
    else:
        for block in blocks:
            height_item = block_height(block)
            output.extend(render_panel(block, 60, y - 36, 1480, height_item, palette, renderers))
            y += height_item + 28
    output.append("</svg>")
    return "\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Render a 3080 visual_spec.json to editable native-shape SVG.")
    parser.add_argument("spec")
    parser.add_argument("output")
    parser.add_argument("--config", default=str(SKILL_DIR / "config" / "3080-brief.json"))
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_svg(spec, config), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
