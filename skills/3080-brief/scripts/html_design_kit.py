#!/usr/bin/env python3
"""3080-owned HTML design planning, local assets, and progressive enhancement."""

import base64
import html
import json
import re
from pathlib import Path

from theme_registry import resolve_visual_theme, theme_palette


SKILL_DIR = Path(__file__).resolve().parents[1]
KIT_DIR = SKILL_DIR / "assets" / "html-kit"
FONT_DIR = KIT_DIR / "fonts"
FONT_CATALOG = KIT_DIR / "font-catalog.json"
ECHARTS_JS = KIT_DIR / "js" / "echarts.min.js"
MERMAID_JS = KIT_DIR / "js" / "mermaid.min.js"
LAYOUTS = {"editorial-research", "decision-dashboard", "technical-analysis", "narrative-longform", "product-brief"}
DENSITIES = {"compact", "balanced", "deep"}
CHART_TYPES = {
    "bar", "diverging_bar", "stacked_bar", "dot", "slope", "line", "scatter",
    "threshold", "range", "distribution", "matrix", "heatmap", "funnel",
}
DIAGRAM_TYPES = {"timeline", "flow", "sequence", "hierarchy", "network"}


def esc(value):
    return html.escape(str(value), quote=True)


def load_font_catalog():
    catalog = json.loads(FONT_CATALOG.read_text(encoding="utf-8"))
    return {item["family"]: item for item in catalog.get("families", [])}


def validate_design_plan(plan, visual_spec):
    errors = []
    if plan.get("schema_version") != 1:
        errors.append("HTML design plan schema_version must be 1")
    if plan.get("layout") not in LAYOUTS:
        errors.append("HTML design plan must select one supported layout")
    if plan.get("density") not in DENSITIES:
        errors.append("HTML design plan must select compact, balanced, or deep density")
    catalog = load_font_catalog()
    typography = plan.get("typography") or {}
    for role in ("display", "body", "mono"):
        family = typography.get(role)
        if family not in catalog:
            errors.append(f"HTML design plan {role} font is not in the bundled catalog: {family}")
    body_family = catalog.get(typography.get("body"), {})
    if body_family.get("category") not in {"sans", "serif"}:
        errors.append("HTML body font must use a bundled sans or serif family")
    mono_family = catalog.get(typography.get("mono"), {})
    if mono_family.get("category") != "mono":
        errors.append("HTML mono font must use a bundled mono family")
    picture = plan.get("one_picture") or {}
    if picture.get("renderer") not in {"auto", "echarts", "mermaid", "native-svg"}:
        errors.append("HTML one-picture renderer is unsupported")
    block_ids = {block.get("id") for block in visual_spec.get("blocks", [])}
    if picture.get("anchor_block_id") not in block_ids:
        errors.append("HTML design plan anchor_block_id is not present in visual_spec")
    anchor = next((block for block in visual_spec.get("blocks", []) if block.get("id") == picture.get("anchor_block_id")), None)
    if anchor and picture.get("renderer") == "echarts" and anchor.get("type") not in CHART_TYPES:
        errors.append("HTML design plan selected ECharts for a non-quantitative anchor block")
    if anchor and picture.get("renderer") == "mermaid" and anchor.get("type") not in DIAGRAM_TYPES:
        errors.append("HTML design plan selected Mermaid for a non-structural anchor block")
    if picture.get("support_position") not in {"right", "below"}:
        errors.append("HTML one-picture support_position must be right or below")
    support_count = max(0, len(visual_spec.get("blocks", [])) - 1)
    if picture.get("support_position") == "right" and support_count > 2:
        errors.append("HTML one-picture with more than two support blocks must use the below evidence band")
    if picture.get("fallback") != "native-svg":
        errors.append("HTML rich rendering requires the auditable native-svg fallback")
    if plan.get("asset_mode", "inline") != "inline":
        errors.append("HTML asset_mode must be inline for offline delivery")
    if plan.get("motion", "none") != "none":
        errors.append("HTML document rendering must disable motion")
    if len(str(plan.get("rationale", "")).strip()) < 20:
        errors.append("HTML design plan requires a content-fit rationale of at least 20 characters")
    return errors


def _font_properties(path):
    suffix = path.stem.rsplit("-", 1)[-1].casefold()
    weight = 700 if "bold" in suffix else 300 if "light" in suffix else 500 if "medium" in suffix else 400
    style = "italic" if "italic" in suffix else "normal"
    return weight, style


def embedded_font_css(plan):
    catalog = load_font_catalog()
    families = []
    for role in ("display", "body", "mono"):
        family = plan["typography"][role]
        if family not in families:
            families.append(family)
    declarations = []
    for family in families:
        entry = catalog[family]
        files = sorted(FONT_DIR.glob(f'{entry["prefix"]}-*.ttf'))
        if not files:
            raise ValueError(f"bundled font files are missing for {family}")
        for path in files:
            weight, style = _font_properties(path)
            payload = base64.b64encode(path.read_bytes()).decode("ascii")
            declarations.append(
                "@font-face {"
                f"font-family: '{family}'; font-style: {style}; font-weight: {weight}; font-display: swap;"
                f"src: url(data:font/ttf;base64,{payload}) format('truetype');"
                "}"
            )
    display = plan["typography"]["display"]
    body = plan["typography"]["body"]
    mono = plan["typography"]["mono"]
    declarations.append(
        ":root {"
        f"--font-display: '{display}', 'PingFang SC', 'Microsoft YaHei', sans-serif;"
        f"--font-body: '{body}', 'PingFang SC', 'Microsoft YaHei', sans-serif;"
        f"--font-mono: '{mono}', 'SFMono-Regular', Consolas, monospace;"
        "}"
    )
    return "\n".join(declarations)


def design_css(plan):
    measure = {"narrow": "700px", "medium": "780px", "wide": "900px"}.get(
        (plan.get("body") or {}).get("prose_measure", "medium"), "780px"
    )
    density_gap = {"compact": "48px", "balanced": "64px", "deep": "78px"}[plan["density"]]
    return f"""
html {{ font-family: var(--font-body); }}
body {{ font-family: var(--font-body); }}
h1, h2, h3, figcaption {{ font-family: var(--font-display); }}
code, pre, .metric-scope {{ font-family: var(--font-mono); }}
.page {{ --prose-measure: {measure}; --design-gap: {density_gap}; }}
.story-section > p, .story-section > ul, .story-section > .callout, .story-section > details {{ max-width: var(--prose-measure); }}
.rich-visual {{ display: none; gap: 26px; align-items: stretch; }}
.rich-visual[data-support-position="right"] {{ grid-template-columns: minmax(0, 2.15fr) minmax(220px, 0.85fr); }}
.rich-visual[data-support-position="below"] {{ grid-template-columns: 1fr; }}
.rich-visual[data-support-position="none"] {{ grid-template-columns: minmax(0, 1fr); }}
.rich-visual[data-support-position="below"] .rich-support {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
.js-rich-loading .rich-visual {{ display: grid; visibility: hidden; }}
.js-rich-ready .rich-visual {{ display: grid; visibility: visible; }}
.js-rich-ready .visual-fallback {{ display: none; }}
.rich-anchor, .rich-support-block {{ min-width: 0; }}
.rich-anchor {{ min-height: 320px; }}
.rich-support {{ display: flex; flex-direction: column; gap: 16px; border-left: 1px solid var(--rule); padding-left: 20px; }}
.rich-visual[data-support-position="below"] .rich-support {{ border-left: 0; border-top: 1px solid var(--rule); padding: 18px 0 0; }}
.rich-block-title {{ margin: 0 0 6px; font: 700 0.95rem/1.35 var(--font-display); }}
.metric-scope {{ margin: 0 0 10px; color: var(--muted); font-size: 0.78rem; line-height: 1.45; }}
.chart-runtime {{ width: 100%; height: 320px; }}
.rich-support-block .chart-runtime {{ height: 190px; }}
.mermaid {{ display: flex; min-height: 280px; align-items: center; justify-content: center; margin: 0; overflow: auto; background: transparent; }}
.rich-anchor[data-renderer="mermaid"] {{ min-height: 270px; }}
.rich-anchor[data-renderer="mermaid"] .mermaid {{ min-height: 235px; }}
.rich-support-block .mermaid {{ min-height: 170px; }}
.rich-annotation {{ border-top: 3px solid var(--accent); padding-top: 10px; }}
.rich-annotation ul {{ margin: 8px 0 0; padding: 0; list-style: none; }}
.rich-annotation li {{ display: flex; justify-content: space-between; gap: 12px; padding: 7px 12px 7px 0; border-bottom: 1px solid var(--rule); }}
.rich-annotation li > span {{ min-width: 0; overflow-wrap: anywhere; }}
.rich-annotation strong {{ min-width: 0; max-width: 50%; text-align: right; overflow-wrap: anywhere; }}
.rich-annotation strong:not([data-semantic]) {{ color: var(--ink); }}
.rich-note {{ margin: 8px 0 0; color: var(--muted); font-size: 0.78rem; line-height: 1.5; }}
html[data-html-layout="editorial-research"] .report-header {{ background: var(--ink); color: var(--surface); }}
html[data-html-layout="editorial-research"] .opening-unit {{ border-left: 0; border-top: 4px solid var(--accent); padding: 20px 0 0; }}
html[data-html-layout="editorial-research"] .story-section > h2 {{ font-size: 2.15rem; }}

html[data-html-layout="decision-dashboard"] .page {{ --content-width: 1120px; }}
html[data-html-layout="decision-dashboard"] .report-header {{ border-top-width: 12px; background: var(--surface); color: var(--ink); }}
html[data-html-layout="decision-dashboard"] .artifact-label {{ color: var(--accent); }}
html[data-html-layout="decision-dashboard"] .opening-unit {{ display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(220px, 0.6fr); column-gap: 22px; }}
html[data-html-layout="decision-dashboard"] .opening-unit p:first-child {{ grid-row: 1 / span 3; }}

html[data-html-layout="technical-analysis"] .report-header {{ border-top: 0; border-left: 10px solid var(--accent); background: var(--surface); color: var(--ink); }}
html[data-html-layout="technical-analysis"] h2 {{ border-bottom-style: dashed; }}
html[data-html-layout="technical-analysis"] .artifact-label {{ font-family: var(--font-mono); }}

html[data-html-layout="narrative-longform"] .page {{ --content-width: 940px; }}
html[data-html-layout="narrative-longform"] .report-header {{ padding-left: 0; padding-right: 0; border-top: 0; border-bottom: 1px solid var(--rule); background: transparent; color: var(--ink); }}
html[data-html-layout="narrative-longform"] .artifact-label {{ color: var(--accent); }}
html[data-html-layout="narrative-longform"] .report-title {{ max-width: 860px; font-size: 4rem; }}
html[data-html-layout="narrative-longform"] p, html[data-html-layout="narrative-longform"] li {{ font-size: 1.02rem; line-height: 1.78; }}

html[data-html-layout="product-brief"] .report-header {{ background: var(--accent); color: var(--surface); }}
html[data-html-layout="product-brief"] .artifact-label {{ color: var(--surface); opacity: 0.82; }}
html[data-html-layout="product-brief"] .story-section > h2 {{ border-left: 4px solid var(--accent); border-bottom: 0; padding: 3px 0 3px 14px; }}

html[data-density="compact"] .story-section {{ margin-bottom: 48px; }}
html[data-density="deep"] .story-section {{ margin-bottom: 78px; }}
@media (max-width: 760px) {{
  .rich-visual[data-support-position] {{ grid-template-columns: 1fr; }}
  .rich-support, .rich-visual[data-support-position="right"] .rich-support {{ border-left: 0; border-top: 1px solid var(--rule); padding: 18px 0 0; }}
  .rich-visual[data-support-position="below"] .rich-support {{ grid-template-columns: 1fr; }}
  html[data-html-layout="decision-dashboard"] .opening-unit {{ display: block; }}
}}
"""


def _scope_text(block):
    scope = block.get("metric_scope") or {}
    ordered = [scope.get(key) for key in ("metric", "unit", "period", "denominator", "segment", "filter")]
    return " · ".join(str(value) for value in ordered if value not in (None, ""))


def _semantic_color(node, block, config, fallback):
    direction = node.get("semantic_direction") or block.get("semantic_direction") or "neutral"
    return config.get("semantic_colors", {}).get(direction, {}).get("svg", fallback)


def _display(item, value_key="value"):
    return str(item.get("display", item.get(value_key, "")))


def _numeric(value, fallback=0.0):
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value or "").replace(",", ""))
    return float(match.group(0)) if match else float(fallback)


def echarts_option(block, visual_spec, config, font_family="Instrument Sans"):
    theme = resolve_visual_theme(visual_spec, config)
    palette = theme_palette(theme)
    body_font = f"{font_family}, PingFang SC, Microsoft YaHei, sans-serif"
    common = {
        "animation": False,
        "textStyle": {"fontFamily": body_font, "fontSize": 12, "color": palette["text"]},
        "tooltip": {"show": False},
        "grid": {"left": 24, "right": 72, "top": 24, "bottom": 42, "containLabel": True},
    }
    items = block.get("items") or []
    block_type = block.get("type")
    colors = [_semantic_color(item, block, config, palette["primary"]) for item in items]

    if block_type in {"bar", "diverging_bar"}:
        common.update({
            "xAxis": {"type": "value", "axisLabel": {"fontSize": 12}, "axisLine": {"lineStyle": {"color": palette["rule"]}}, "splitLine": {"lineStyle": {"color": palette["rule"]}}},
            "yAxis": {"type": "category", "inverse": True, "data": [str(item.get("label", "")) for item in items], "axisLabel": {"fontSize": 12, "width": 150, "overflow": "break", "lineHeight": 16}, "axisTick": {"show": False}, "axisLine": {"show": False}},
            "series": [{"type": "bar", "barMaxWidth": 24, "data": [
                {"value": item.get("value", 0), "itemStyle": {"color": color}, "label": {"show": True, "position": "right" if item.get("value", 0) >= 0 else "left", "formatter": _display(item)}}
                for item, color in zip(items, colors)
            ]}],
        })
        return common
    if block_type == "stacked_bar":
        groups = list(dict.fromkeys(str(item.get("series", "")) for item in items if item.get("series")))
        if groups:
            labels = list(dict.fromkeys(str(item.get("label", "")) for item in items))
            item_map = {(str(item.get("series", "")), str(item.get("label", ""))): item for item in items}
            series = []
            for label in labels:
                sample = next((item for item in items if str(item.get("label", "")) == label), {})
                color = _semantic_color(sample, block, config, palette["primary"])
                data = []
                for group in groups:
                    item = item_map.get((group, label), {})
                    value = item.get("value", 0)
                    data.append({
                        "value": value,
                        "itemStyle": {"color": color},
                        "label": {"show": bool(item), "position": "inside", "formatter": _display(item) if item else ""},
                    })
                series.append({"name": label, "type": "bar", "stack": "total", "barMaxWidth": 42, "itemStyle": {"color": color}, "data": data})
            common.update({
                "grid": {"left": 18, "right": 24, "top": 18, "bottom": 42, "containLabel": True},
                "xAxis": {"type": "value", "min": block.get("minimum", 0), "max": block.get("maximum", 100), "axisLine": {"show": False}, "splitLine": {"show": False}, "axisLabel": {"formatter": "{value}%"}},
                "yAxis": {"type": "category", "inverse": True, "data": groups, "axisLine": {"show": False}, "axisTick": {"show": False}},
                "legend": {"bottom": 0},
                "series": series,
            })
        else:
            common.update({
                "xAxis": {"type": "value", "axisLine": {"show": False}, "splitLine": {"show": False}},
                "yAxis": {"type": "category", "data": [""], "axisLine": {"show": False}, "axisTick": {"show": False}},
                "legend": {"bottom": 0},
                "series": [
                    {"name": str(item.get("label", "")), "type": "bar", "stack": "total", "data": [{"value": item.get("value", 0), "itemStyle": {"color": color}, "label": {"show": True, "position": "inside", "formatter": _display(item)}}]}
                    for item, color in zip(items, colors)
                ],
            })
        return common
    if block_type == "dot":
        common.update({
            "xAxis": {"type": "value", "axisLabel": {"fontSize": 12}, "splitLine": {"lineStyle": {"color": palette["rule"]}}},
            "yAxis": {"type": "category", "inverse": True, "data": [str(item.get("label", "")) for item in items], "axisLabel": {"fontSize": 12, "width": 150, "overflow": "break", "lineHeight": 16}, "axisLine": {"show": False}, "axisTick": {"show": False}},
            "series": [{"type": "scatter", "symbolSize": 14, "data": [
                {"value": [item.get("value", 0), index], "itemStyle": {"color": color}, "label": {"show": True, "position": "right", "formatter": _display(item)}}
                for index, (item, color) in enumerate(zip(items, colors))
            ]}],
        })
        return common
    if block_type == "line":
        common.update({
            "xAxis": {"type": "category", "boundaryGap": False, "data": [str(item.get("label", "")) for item in items], "axisLabel": {"fontSize": 12, "width": 110, "overflow": "break", "lineHeight": 16}, "axisLine": {"lineStyle": {"color": palette["rule"]}}},
            "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": palette["rule"]}}},
            "series": [{"type": "line", "smooth": False, "symbolSize": 9, "lineStyle": {"width": 3, "color": palette["primary"]}, "itemStyle": {"color": palette["primary"]}, "data": [
                {"value": item.get("value", 0), "label": {"show": index in {0, len(items) - 1} or bool(item.get("annotate")), "position": "top", "formatter": _display(item)}}
                for index, item in enumerate(items)
            ]}],
        })
        return common
    if block_type == "slope":
        starts = block.get("start_label", "Before")
        ends = block.get("end_label", "After")
        common.update({
            "xAxis": {"type": "category", "data": [starts, ends], "axisLine": {"lineStyle": {"color": palette["rule"]}}},
            "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": palette["rule"]}}},
            "legend": {"bottom": 0},
            "series": [
                {"name": str(item.get("label", "")), "type": "line", "symbolSize": 9, "lineStyle": {"width": 3, "color": color}, "itemStyle": {"color": color}, "data": [
                    {"value": item.get("start", item.get("low", 0)), "label": {"show": True, "formatter": str(item.get("start_display", item.get("start", item.get("low", 0))))}},
                    {"value": item.get("end", item.get("high", 0)), "label": {"show": True, "formatter": str(item.get("end_display", item.get("end", item.get("high", 0))))}},
                ]}
                for item, color in zip(items, colors)
            ],
        })
        return common
    if block_type == "scatter":
        common.update({
            "xAxis": {"type": "value", "splitLine": {"lineStyle": {"color": palette["rule"]}}},
            "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": palette["rule"]}}},
            "series": [{"type": "scatter", "symbolSize": 14, "data": [
                {"name": str(item.get("label", "")), "value": [item.get("x", 0), item.get("y", 0)], "itemStyle": {"color": color}, "label": {"show": bool(item.get("label")), "position": "top", "formatter": str(item.get("label", ""))}}
                for item, color in zip(items, colors)
            ]}],
        })
        return common
    if block_type == "threshold":
        value = block.get("value", 0)
        threshold = block.get("threshold", 0)
        common.update({
            "grid": {"left": 24, "right": 78, "top": 42, "bottom": 28, "containLabel": True},
            "xAxis": {"type": "value", "min": block.get("minimum", 0), "max": block.get("maximum", 100), "splitLine": {"lineStyle": {"color": palette["rule"]}}},
            "yAxis": {"type": "category", "data": [str(block.get("value_label", "Current"))], "axisLine": {"show": False}, "axisTick": {"show": False}},
            "series": [{"type": "bar", "barWidth": 28, "data": [{"value": value, "itemStyle": {"color": _semantic_color(block, block, config, palette["primary"])}, "label": {"show": True, "position": "right", "formatter": str(block.get("display", value))}}], "markLine": {"silent": True, "symbol": "none", "label": {"show": True, "formatter": f'{block.get("threshold_label", "Threshold")} {threshold}'}, "lineStyle": {"color": config["semantic_colors"]["warning"]["svg"], "width": 2, "type": "dashed"}, "data": [{"xAxis": threshold}]}}],
        })
        return common
    if block_type in {"range", "distribution"}:
        if any("low" in item or "high" in item for item in items):
            range_marks = [
                {"value": [str(item.get("label", "")), item.get("high", item.get("low", 0))], "itemStyle": {"color": "transparent"}, "label": {"show": True, "position": "top", "formatter": _display(item)}}
                for item in items
            ]
            common.update({
                "xAxis": {"type": "category", "data": [str(item.get("label", "")) for item in items], "axisLabel": {"interval": 0, "fontSize": 12, "overflow": "break", "width": 110, "lineHeight": 16}},
                "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": palette["rule"]}}},
                "series": [
                    {"type": "candlestick", "data": [
                        {"value": [item.get("low", 0), item.get("low", 0), item.get("high", 0), item.get("high", 0)], "itemStyle": {"color": color, "color0": color, "borderColor": color, "borderColor0": color}}
                        for item, color in zip(items, colors)
                    ]},
                    {"type": "scatter", "symbolSize": 1, "data": range_marks},
                ],
            })
        else:
            common.update({
                "xAxis": {"type": "category", "data": [str(item.get("label", "")) for item in items]},
                "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": palette["rule"]}}},
                "series": [{"type": "bar", "data": [{"value": item.get("value", 0), "itemStyle": {"color": color}, "label": {"show": True, "position": "top", "formatter": _display(item)}} for item, color in zip(items, colors)]}],
            })
        return common
    if block_type in {"matrix", "heatmap"}:
        rows = [str(value) for value in block.get("rows", [])]
        columns = [str(value) for value in block.get("columns", [])]
        values = []
        numeric = []
        for cell in block.get("cells") or []:
            if str(cell.get("row")) not in rows or str(cell.get("column")) not in columns:
                continue
            display = str(cell.get("label", cell.get("value", "")))
            value = _numeric(cell.get("value", display), 0)
            numeric.append(value)
            entry = {
                "value": [columns.index(str(cell.get("column"))), rows.index(str(cell.get("row"))), value],
                "label": {"show": True, "formatter": display},
            }
            if block_type == "matrix":
                explicit_direction = cell.get("semantic_direction")
                entry["itemStyle"] = {
                    "color": _semantic_color(cell, {}, config, palette["background_alt"]) if explicit_direction else palette["background_alt"],
                    "borderColor": palette["rule"],
                    "borderWidth": 1,
                }
            values.append(entry)
        visual_map = {
            "show": True,
            "min": min(numeric or [0]),
            "max": max(numeric or [1]),
            "orient": "horizontal",
            "left": "center",
            "bottom": 0,
            "inRange": {"color": [palette["background_alt"], palette["primary"]]},
        } if block_type == "heatmap" else {"show": False}
        common.update({
            "grid": {"left": 18, "right": 28, "top": 18, "bottom": 48, "containLabel": True},
            "xAxis": {"type": "category", "data": columns, "splitArea": {"show": True}},
            "yAxis": {"type": "category", "data": rows, "splitArea": {"show": True}},
            "visualMap": visual_map,
            "series": [{"type": "heatmap", "data": values, "label": {"show": True}}],
        })
        return common
    if block_type == "funnel":
        common.pop("grid", None)
        common.update({
            "series": [{"type": "funnel", "left": "8%", "right": "8%", "top": 10, "bottom": 18, "sort": "descending", "gap": 3, "label": {"show": True, "position": "inside", "formatter": "{b}: {c}"}, "data": [
                {"name": str(item.get("label", "")), "value": item.get("value", 0), "itemStyle": {"color": color}}
                for item, color in zip(items, colors)
            ]}],
        })
        return common
    return None


def mermaid_source(block, config):
    orientation = "TB" if block.get("type") == "hierarchy" else "LR"
    items = block.get("items") or []
    labels = [str(item.get("label") or item.get("display") or f"Step {index + 1}") for index, item in enumerate(items)]
    lines = [f"flowchart {orientation}"]
    for index, label in enumerate(labels):
        clean = re.sub(r"[\[\]{}()<>]", " ", label).strip()
        lines.append(f'  N{index}["{clean}"]')
        direction = (items[index].get("semantic_direction") or block.get("semantic_direction") or "").strip()
        semantic = config.get("semantic_colors", {}).get(direction)
        if semantic:
            lines.append(
                f'  style N{index} fill:{semantic["svg_tint"]},stroke:{semantic["svg"]},color:#1F2329'
            )
    links = block.get("links") or []
    if links:
        index_by_id = {str(item.get("id", index)): index for index, item in enumerate(items)}
        for link in links:
            if isinstance(link, dict):
                source = index_by_id.get(str(link.get("source")))
                target = index_by_id.get(str(link.get("target")))
            elif isinstance(link, list) and len(link) >= 2:
                source = index_by_id.get(str(link[0]))
                target = index_by_id.get(str(link[1]))
            else:
                continue
            if source is not None and target is not None:
                lines.append(f"  N{source} --> N{target}")
    elif len(labels) > 1:
        for index in range(len(labels) - 1):
            lines.append(f"  N{index} --> N{index + 1}")
    return "\n".join(lines) if labels else ""


def _annotation_html(block):
    items = block.get("items") or []
    rows = []
    for item in items:
        label = esc(item.get("label", ""))
        display = esc(item.get("display", item.get("value", "")))
        direction = str(item.get("semantic_direction") or block.get("semantic_direction") or "").strip()
        semantic_class = f' class="semantic-{esc(direction)}" data-semantic="{esc(direction)}"' if direction in {"favorable", "unfavorable", "warning", "neutral", "unknown"} else ""
        rows.append(f"<li><span>{label}</span><strong{semantic_class}>{display}</strong></li>")
    note = f'<p class="rich-note">{esc(block["note"])}</p>' if block.get("note") else ""
    return f'<div class="rich-annotation"><p class="rich-block-title">{esc(block.get("title", ""))}</p><ul>{"".join(rows)}</ul>{note}</div>'


def render_rich_visual(visual_spec, fallback_svg, design_plan, config, figure_id, full_picture=False):
    blocks = list(visual_spec.get("blocks") or [])
    if not blocks or design_plan["one_picture"]["renderer"] == "native-svg":
        return f'<div class="visual-fallback visual-canvas">{fallback_svg}</div>', []
    anchor_id = design_plan["one_picture"].get("anchor_block_id")
    anchor = next((block for block in blocks if block.get("id") == anchor_id), blocks[0])
    ordered = [anchor] + [block for block in blocks if block is not anchor]
    runtime_items = []
    panels = []
    selected_renderer = design_plan["one_picture"].get("renderer", "auto")
    for index, block in enumerate(ordered):
        block_type = block.get("type")
        renderer = selected_renderer if index == 0 and selected_renderer != "auto" else "auto"
        if renderer == "auto":
            renderer = "echarts" if block_type in CHART_TYPES else "mermaid" if block_type in DIAGRAM_TYPES else "annotation"
        panel_class = "rich-anchor" if index == 0 else "rich-support-block"
        scope = _scope_text(block)
        scope_html = f'<p class="metric-scope">{esc(scope)}</p>' if scope else ""
        if renderer == "echarts" and block_type in CHART_TYPES:
            option = echarts_option(block, visual_spec, config, design_plan["typography"]["body"])
            if option is not None:
                dom_id = f"{figure_id}-chart-{index}"
                runtime_items.append({"kind": "echarts", "dom_id": dom_id, "option": option, "figure_id": figure_id})
                note = f'<p class="rich-note">{esc(block["note"])}</p>' if block.get("note") else ""
                panels.append(
                    f'<div class="{panel_class}" data-visual-block="{esc(block.get("id", ""))}" data-renderer="echarts">'
                    f'<p class="rich-block-title">{esc(block.get("title", ""))}</p>{scope_html}'
                    f'<div id="{esc(dom_id)}" class="chart-runtime" role="img" aria-label="{esc(block.get("alt_text", block.get("title", "")))}"></div>{note}</div>'
                )
                continue
        if renderer == "mermaid" and block_type in DIAGRAM_TYPES:
            source = mermaid_source(block, config)
            if source:
                runtime_items.append({"kind": "mermaid", "figure_id": figure_id})
                panels.append(
                    f'<div class="{panel_class}" data-visual-block="{esc(block.get("id", ""))}" data-renderer="mermaid">'
                    f'<p class="rich-block-title">{esc(block.get("title", ""))}</p>{scope_html}'
                    f'<pre class="mermaid" aria-label="{esc(block.get("alt_text", block.get("title", "")))}">{esc(source)}</pre></div>'
                )
                continue
        panels.append(f'<div class="{panel_class}" data-visual-block="{esc(block.get("id", ""))}" data-renderer="html">{_annotation_html(block)}</div>')
    anchor_panel = panels[0]
    support_panels = "".join(panels[1:])
    support_position = design_plan["one_picture"]["support_position"] if support_panels else "none"
    support_html = f'<div class="rich-support">{support_panels}</div>' if support_panels else ""
    rich = (
        f'<div id="{esc(figure_id)}" class="rich-visual" data-rich-visual="true" '
        f'data-support-position="{esc(support_position)}" '
        f'data-full-picture="{str(bool(full_picture)).lower()}">{anchor_panel}'
        f'{support_html}</div>'
    )
    fallback = f'<div class="visual-fallback visual-canvas">{fallback_svg}</div>'
    return rich + fallback, runtime_items


def runtime_scripts(runtime_items, visual_spec, config):
    kinds = {item["kind"] for item in runtime_items}
    scripts = []
    if "echarts" in kinds:
        if not ECHARTS_JS.is_file():
            raise ValueError("bundled ECharts runtime is missing")
        payload = ECHARTS_JS.read_text(encoding="utf-8").replace("</script>", "<\\/script>")
        scripts.append(f'<script data-3080-runtime="echarts">{payload}</script>')
    if "mermaid" in kinds:
        if not MERMAID_JS.is_file():
            raise ValueError("bundled Mermaid runtime is missing")
        payload = MERMAID_JS.read_text(encoding="utf-8").replace("</script>", "<\\/script>")
        scripts.append(f'<script data-3080-runtime="mermaid">{payload}</script>')
    charts = [{"dom_id": item["dom_id"], "option": item["option"]} for item in runtime_items if item["kind"] == "echarts"]
    figures = sorted({item["figure_id"] for item in runtime_items})
    theme = resolve_visual_theme(visual_spec, config)
    palette = theme_palette(theme)
    chart_json = json.dumps(charts, ensure_ascii=False).replace("<", "\\u003c")
    figure_json = json.dumps(figures, ensure_ascii=False).replace("<", "\\u003c")
    mermaid_init = ""
    if "mermaid" in kinds:
        variables = {
            "primaryColor": palette["background_alt"],
            "primaryTextColor": palette["text"],
            "primaryBorderColor": palette["primary"],
            "lineColor": palette["primary"],
            "secondaryColor": palette["surface"],
            "tertiaryColor": palette["background"],
            "fontFamily": "var(--font-body)",
        }
        variables_json = json.dumps(variables, ensure_ascii=False).replace("<", "\\u003c")
        mermaid_init = f"mermaid.initialize({{startOnLoad:false,securityLevel:'strict',theme:'base',themeVariables:{variables_json}}});await mermaid.run({{nodes:document.querySelectorAll('.mermaid')}});"
    bootstrap = f"""<script data-3080-bootstrap="true">
(async function(){{
  try {{
    for (const id of {figure_json}) {{
      const node = document.getElementById(id);
      if (node) node.parentElement.classList.add('js-rich-loading');
    }}
    const charts = {chart_json};
    const instances = [];
    for (const item of charts) {{
      const node = document.getElementById(item.dom_id);
      if (!node) throw new Error('missing chart node');
      const chart = echarts.init(node, null, {{renderer:'svg'}});
      chart.setOption(item.option, {{notMerge:true}});
      instances.push(chart);
    }}
    {mermaid_init}
    for (const id of {figure_json}) {{
      const node = document.getElementById(id);
      if (node) {{
        node.parentElement.classList.remove('js-rich-loading');
        node.parentElement.classList.add('js-rich-ready');
      }}
    }}
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
    await new Promise(function(resolve){{ requestAnimationFrame(function(){{ requestAnimationFrame(resolve); }}); }});
    const geometryIssues = [];
    const rounded = function(value){{ return Math.round(value * 10) / 10; }};
    const outside = function(child, parent, tolerance){{
      return child.left < parent.left - tolerance || child.right > parent.right + tolerance ||
        child.top < parent.top - tolerance || child.bottom > parent.bottom + tolerance;
    }};
    for (const scope of document.querySelectorAll('[data-geometry-scope], .body-figure')) {{
      const scopeRect = scope.getBoundingClientRect();
      for (const node of scope.querySelectorAll('svg text, .rich-block-title, .metric-scope, .rich-note')) {{
        const rect = node.getBoundingClientRect();
        if (rect.width && rect.height && outside(rect, scopeRect, 3)) {{
          geometryIssues.push({{type:'out-of-scope', text:(node.textContent || '').trim().slice(0,80)}});
        }}
        if (node.matches('svg text') && rect.height > 0 && rect.height < 11.5) {{
          geometryIssues.push({{type:'small-load-bearing-text', text:(node.textContent || '').trim().slice(0,80), height:rounded(rect.height)}});
        }}
      }}
      for (const svg of scope.querySelectorAll('svg')) {{
        const labels = Array.from(svg.querySelectorAll('text')).map(function(node){{
          return {{node:node, rect:node.getBoundingClientRect(), text:(node.textContent || '').trim()}};
        }}).filter(function(item){{ return item.text && item.rect.width && item.rect.height; }});
        for (let i = 0; i < labels.length; i += 1) {{
          for (let j = i + 1; j < labels.length; j += 1) {{
            const a = labels[i].rect;
            const b = labels[j].rect;
            const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            if (overlapX > 2 && overlapY > 2) {{
              geometryIssues.push({{type:'text-overlap', first:labels[i].text.slice(0,60), second:labels[j].text.slice(0,60), overlap:[rounded(overlapX),rounded(overlapY)]}});
            }}
          }}
        }}
      }}
    }}
    for (const node of document.querySelectorAll('.report-header, .report-title, .opening-unit, .one-picture, .story-section, .rich-anchor, .rich-support-block')) {{
      const style = getComputedStyle(node);
      if (node.scrollWidth > node.clientWidth + 2 && !['auto','scroll'].includes(style.overflowX)) {{
        geometryIssues.push({{type:'horizontal-overflow', element:node.className || node.tagName, overflow:node.scrollWidth-node.clientWidth}});
      }}
    }}
    window.__3080GeometryAudit = {{
      schema_version: 1,
      contract_id: document.documentElement.dataset.contractId || '',
      viewport: {{width: window.innerWidth, height: window.innerHeight}},
      status: geometryIssues.length ? 'FAIL' : 'PASS',
      issues: geometryIssues,
      checked_scopes: document.querySelectorAll('[data-geometry-scope], .body-figure').length
    }};
    document.documentElement.setAttribute('data-geometry-status', window.__3080GeometryAudit.status.toLowerCase());
    window.addEventListener('resize', function(){{ for (const chart of instances) chart.resize(); }});
  }} catch (error) {{
    for (const node of document.querySelectorAll('.js-rich-loading')) node.classList.remove('js-rich-loading');
    document.documentElement.setAttribute('data-rich-render-error', 'true');
  }}
}})();
</script>"""
    scripts.append(bootstrap)
    return "\n".join(scripts)
