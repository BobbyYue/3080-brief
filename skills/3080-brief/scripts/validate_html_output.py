#!/usr/bin/env python3
"""Validate the structural, offline, and accessibility contract of 3080 HTML output."""

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from html_design_kit import CHART_TYPES, DIAGRAM_TYPES, validate_design_plan
from theme_registry import resolve_visual_theme


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config" / "3080-brief.json"
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def classes(attributes):
    attrs = dict(attributes)
    return set(attrs.get("class", "").split())


class BriefParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.title_parts = []
        self.heading_parts = []
        self.current_heading = None
        self.headings = []
        self.opening_depth = 0
        self.opening_paragraphs = 0
        self.one_picture_depth = 0
        self.one_picture_count = 0
        self.one_picture_attrs = {}
        self.one_picture_svg = 0
        self.one_picture_svg_depth = 0
        self.one_picture_svg_attrs = {}
        self.one_picture_svg_text = []
        self.one_picture_layouts = set()
        self.one_picture_roles = {"anchor": 0, "support": 0, "caveat": 0}
        self.one_picture_caption_parts = []
        self.in_caption = False
        self.key_table_depth = 0
        self.key_table_count = 0
        self.key_table_rows = 0
        self.current_headers = []
        self.current_header_parts = None
        self.source_citations = 0
        self.figures = []
        self.details_priorities = []
        self.scripts = 0
        self.authorized_scripts = 0
        self.runtime_kinds = set()
        self.external_resources = []
        self.theme_slug = ""
        self.html_layout = ""
        self.html_density = ""
        self.html_fonts = {}
        self.rich_visuals = 0
        self.rich_block_ids = set()
        self.story_sections = 0
        self.story_sections_with_reading_path = 0

    def handle_starttag(self, tag, attrs_list):
        attrs = dict(attrs_list)
        class_set = classes(attrs_list)
        if tag == "html":
            self.theme_slug = attrs.get("data-theme", "")
            self.html_layout = attrs.get("data-html-layout", "")
            self.html_density = attrs.get("data-density", "")
            self.html_fonts = {
                "display": attrs.get("data-font-display", ""),
                "body": attrs.get("data-font-body", ""),
            }
        if tag == "section" and "story-section" in class_set:
            self.story_sections += 1
            if (
                attrs.get("data-reading-density") in {"light", "balanced", "dense"}
                and attrs.get("data-reader-question", "").strip()
            ):
                self.story_sections_with_reading_path += 1
        if tag not in VOID_TAGS:
            self.stack.append(tag)
        if tag == "script":
            self.scripts += 1
            runtime = attrs.get("data-3080-runtime", "")
            if runtime in {"echarts", "mermaid"}:
                self.authorized_scripts += 1
                self.runtime_kinds.add(runtime)
            elif attrs.get("data-3080-bootstrap") == "true":
                self.authorized_scripts += 1
        if attrs.get("data-rich-visual") == "true":
            self.rich_visuals += 1
        if attrs.get("data-visual-block"):
            self.rich_block_ids.add(attrs["data-visual-block"])
        if tag in {"script", "img", "link", "iframe", "source", "video", "audio"}:
            location = attrs.get("src") or attrs.get("href") or ""
            if re.match(r"^(?:https?:|file:|//)", location, re.I):
                self.external_resources.append(location)
        if tag == "title":
            self.title_parts = []
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.current_heading = tag
            self.heading_parts = []
        if "opening-unit" in class_set:
            self.opening_depth = len(self.stack)
        if self.opening_depth and tag == "p":
            self.opening_paragraphs += 1
        if tag == "figure":
            figure = {"classes": class_set, "aria_label": attrs.get("aria-label", ""), "svg": 0, "caption": False}
            self.figures.append(figure)
            if "one-picture" in class_set:
                self.one_picture_count += 1
                self.one_picture_depth = len(self.stack)
                self.one_picture_attrs = attrs
        if tag == "figcaption":
            self.in_caption = True
            if self.figures:
                self.figures[-1]["caption"] = True
        if tag == "svg" and self.figures:
            self.figures[-1]["svg"] += 1
            if self.one_picture_depth:
                self.one_picture_svg += 1
                self.one_picture_svg_depth = len(self.stack)
                self.one_picture_svg_attrs = attrs
        if self.one_picture_svg_depth:
            if attrs.get("data-layout"):
                self.one_picture_layouts.add(attrs["data-layout"])
            role = attrs.get("data-visual-role")
            if role in self.one_picture_roles:
                self.one_picture_roles[role] += 1
        if tag == "table" and "key-questions" in class_set:
            self.key_table_count += 1
            self.key_table_depth = len(self.stack)
        if self.key_table_depth and tag == "tr":
            self.key_table_rows += 1
        if self.key_table_depth and tag == "th":
            self.current_header_parts = []
        if "source-citation" in class_set:
            self.source_citations += 1
        if tag == "details":
            self.details_priorities.append(attrs.get("data-priority", ""))

    def handle_endtag(self, tag):
        if tag == "title":
            pass
        if self.current_heading == tag:
            self.headings.append((tag, " ".join("".join(self.heading_parts).split())))
            self.current_heading = None
            self.heading_parts = []
        if tag == "figcaption":
            self.in_caption = False
        if tag == "th" and self.current_header_parts is not None:
            self.current_headers.append(" ".join("".join(self.current_header_parts).split()))
            self.current_header_parts = None
        if self.stack:
            depth = len(self.stack)
            if self.opening_depth == depth:
                self.opening_depth = 0
            if self.one_picture_depth == depth:
                self.one_picture_depth = 0
            if self.one_picture_svg_depth == depth:
                self.one_picture_svg_depth = 0
            if self.key_table_depth == depth:
                self.key_table_depth = 0
            self.stack.pop()

    def handle_data(self, data):
        if self.stack and self.stack[-1] == "title":
            self.title_parts.append(data)
        if self.current_heading:
            self.heading_parts.append(data)
        if self.in_caption and self.one_picture_depth:
            self.one_picture_caption_parts.append(data)
        if self.one_picture_svg_depth:
            self.one_picture_svg_text.append(data)
        if self.current_header_parts is not None:
            self.current_header_parts.append(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html")
    parser.add_argument("--visual-spec", default="")
    parser.add_argument("--design-plan", default="")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()

    text = Path(args.html).read_text(encoding="utf-8")
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    spec = json.loads(Path(args.visual_spec).read_text(encoding="utf-8")) if args.visual_spec else None
    design_plan = json.loads(Path(args.design_plan).read_text(encoding="utf-8")) if args.design_plan else None
    parsed = BriefParser()
    parsed.feed(text)
    errors = []

    title = " ".join("".join(parsed.title_parts).split())
    if not title.casefold().startswith("3080 brief"):
        errors.append("HTML <title> must start with 3080 Brief")
    if not parsed.headings or parsed.headings[0] != ("h1", "TLDR"):
        errors.append("the first visible heading must be H1 TLDR")
    if not 2 <= parsed.opening_paragraphs <= 4:
        errors.append("opening unit must contain one judgment plus 1-3 support paragraphs")
    if parsed.one_picture_count != 1:
        errors.append("TLDR must contain exactly one one-picture figure")
    if parsed.one_picture_svg != 1:
        errors.append("one-picture figure must contain exactly one inline SVG")
    if config.get("html_render", {}).get("visual_spec_required_for_validation") and not spec:
        errors.append("HTML one-picture validation requires the approved visual spec")
    if not parsed.one_picture_attrs.get("aria-label"):
        errors.append("one-picture figure requires conclusion-bearing aria-label")
    caption = " ".join("".join(parsed.one_picture_caption_parts).split())
    if len(caption) < 4:
        errors.append("one-picture figure requires a visible judgment title")
    minimum_coverage = float(config.get("coverage", {}).get("minimum_percent", 80))
    try:
        coverage = float(parsed.one_picture_attrs.get("data-coverage", 0))
    except ValueError:
        coverage = 0
    if coverage < minimum_coverage:
        errors.append(f"one-picture figure must declare at least {minimum_coverage:g}% coverage")
    view_box = parsed.one_picture_svg_attrs.get("viewbox", "").replace(",", " ").split()
    try:
        svg_width = float(view_box[2])
        svg_height = float(view_box[3])
        ratio = svg_width / svg_height
    except (IndexError, TypeError, ValueError, ZeroDivisionError):
        ratio = 0
        errors.append("one-picture SVG requires a valid non-zero viewBox")
    html_render = config.get("html_render", {})
    minimum_ratio = float(html_render.get("one_picture_min_width_height_ratio", 1.2))
    maximum_ratio = float(html_render.get("one_picture_max_width_height_ratio", 2.0))
    if ratio and not minimum_ratio <= ratio <= maximum_ratio:
        errors.append(
            f"one-picture SVG width/height ratio {ratio:.2f} is outside the compact HTML range "
            f"{minimum_ratio:.2f}-{maximum_ratio:.2f}"
        )
    if parsed.key_table_count != 1:
        errors.append("TLDR must contain exactly one key-question table")
    question_rows = max(0, parsed.key_table_rows - 1)
    if not config["tldr"]["questions_min"] <= question_rows <= config["tldr"]["questions_max"]:
        errors.append("key-question table must contain 3-5 question rows")
    expected_headers = {
        tuple(config["tldr"]["default_table_headers"]),
        tuple(config["tldr"]["english_table_headers"]),
    }
    if tuple(parsed.current_headers) not in expected_headers:
        errors.append("key-question table headers must be Question/Conclusion/Why or the configured Chinese equivalent")
    if parsed.source_citations != 1:
        errors.append("TLDR requires one compact source citation")
    if parsed.story_sections != parsed.story_sections_with_reading_path:
        errors.append("every HTML story section must carry its validated reading-path density and reader question")
    if parsed.scripts != parsed.authorized_scripts:
        errors.append("HTML output contains an unauthorized executable script")
    if parsed.external_resources:
        errors.append("HTML output contains external runtime resources: " + ", ".join(parsed.external_resources))
    for index, figure in enumerate(parsed.figures, 1):
        if not figure["aria_label"]:
            errors.append(f"figure {index} is missing aria-label")
        if not figure["caption"]:
            errors.append(f"figure {index} is missing figcaption")
        if figure["svg"] != 1:
            errors.append(f"figure {index} must contain exactly one inline SVG")
    if any(priority != "P2" for priority in parsed.details_priorities):
        errors.append("collapsed details may contain P2 supporting depth only")
    for required_css in ("overflow: auto", "--favorable", "--unfavorable", "--accent-2", "--section-gap"):
        if required_css not in text:
            errors.append(f"HTML output is missing required responsive/semantic CSS: {required_css}")
    if spec:
        try:
            theme = resolve_visual_theme(spec, config)
        except ValueError as exc:
            errors.append(str(exc))
            theme = None
        if theme and parsed.theme_slug != theme["slug"]:
            errors.append("rendered HTML theme differs from visual spec style")
        expected_alt = spec.get("alt_text", "")
        if expected_alt and parsed.one_picture_attrs.get("aria-label") != expected_alt:
            errors.append("rendered one-picture aria-label differs from visual spec")
        expected_coverage = float(spec.get("coverage_percent", 0))
        if expected_coverage and coverage != expected_coverage:
            errors.append("rendered one-picture coverage differs from visual spec")
        rendered_svg_text = " ".join("".join(parsed.one_picture_svg_text).split())
        rendered_svg_compact = re.sub(r"\s+", "", rendered_svg_text)
        rendered_composition = parsed.one_picture_svg_attrs.get("data-composition", "")
        if rendered_composition != spec.get("composition", ""):
            errors.append("rendered one-picture composition differs from visual spec")
        if rendered_composition in {"anchor_support", "comparison_grid"}:
            if rendered_composition not in parsed.one_picture_layouts:
                errors.append(f"rendered one-picture does not implement the declared {rendered_composition} layout")
            for role in ("anchor", "support", "caveat"):
                expected = sum(block.get("visual_role") == role for block in spec.get("blocks", []))
                actual = parsed.one_picture_roles[role]
                if actual != expected:
                    errors.append(f"rendered one-picture {role} role count differs from visual spec")
        for block in spec.get("blocks", []):
            required_tokens = [block.get("title", "")]
            if block.get("note"):
                required_tokens.append(block["note"])
            for item in block.get("items") or []:
                required_tokens.append(item.get("label", ""))
                display = item.get("display", item.get("value", ""))
                if display not in (None, ""):
                    required_tokens.append(str(display))
            for token in required_tokens:
                normalized = " ".join(str(token).split())
                if normalized and re.sub(r"\s+", "", normalized) not in rendered_svg_compact:
                    errors.append(f"one-picture SVG omitted visible visual-spec payload: {normalized}")
    if design_plan:
        if not spec:
            errors.append("HTML design-plan validation requires the approved visual spec")
        else:
            errors.extend(validate_design_plan(design_plan, spec))
            if parsed.html_layout != design_plan.get("layout"):
                errors.append("rendered HTML layout differs from the approved design plan")
            if parsed.html_density != design_plan.get("density"):
                errors.append("rendered HTML density differs from the approved design plan")
            typography = design_plan.get("typography") or {}
            for role in ("display", "body"):
                if parsed.html_fonts.get(role) != typography.get(role):
                    errors.append(f"rendered HTML {role} font differs from the approved design plan")
            if "@font-face" not in text or "data:font/ttf;base64," not in text:
                errors.append("rich HTML output must embed its selected local fonts")
            renderer = (design_plan.get("one_picture") or {}).get("renderer")
            if renderer != "native-svg" and any(block.get("type") in CHART_TYPES | DIAGRAM_TYPES for block in spec.get("blocks", [])):
                if parsed.rich_visuals < 1:
                    errors.append("rich HTML output omitted the planned one-picture runtime composition")
                expected_ids = {block.get("id") for block in spec.get("blocks", [])}
                if not expected_ids <= parsed.rich_block_ids:
                    errors.append("rich HTML output omitted one or more visual-spec blocks")
            anchor_id = (design_plan.get("one_picture") or {}).get("anchor_block_id")
            anchor = next((block for block in spec.get("blocks", []) if block.get("id") == anchor_id), None)
            if anchor and renderer in {"auto", "echarts"} and anchor.get("type") in CHART_TYPES and "echarts" not in parsed.runtime_kinds:
                errors.append("rich HTML output omitted the bundled ECharts runtime for its anchor chart")
            if anchor and renderer in {"auto", "mermaid"} and anchor.get("type") in DIAGRAM_TYPES and "mermaid" not in parsed.runtime_kinds:
                errors.append("rich HTML output omitted the bundled Mermaid runtime for its anchor diagram")
    elif parsed.runtime_kinds or parsed.rich_visuals:
        errors.append("rich HTML runtime output requires an approved design plan")

    print("FAIL" if errors else "PASS")
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
