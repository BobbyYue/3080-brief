#!/usr/bin/env python3
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ALLOWED = {"svg", "g", "defs", "marker", "rect", "circle", "ellipse", "line", "polyline", "text", "tspan", "path"}
FORBIDDEN_ATTRIBUTES = {"opacity", "fill-opacity", "stroke-opacity", "font-family", "style"}
SIMPLE_MARKER_PATH = re.compile(r"^[MmLlHhVvZz0-9.,+\-\s]+$")


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def main():
    parser = argparse.ArgumentParser(description="Validate editable Feishu whiteboard SVG constraints.")
    parser.add_argument("svg")
    args = parser.parse_args()
    path = Path(args.svg)
    errors = []
    warnings = []
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        print(f"FAIL\nERROR invalid SVG XML: {exc}")
        return 1
    if local_name(root.tag) != "svg":
        errors.append("root element must be <svg>")

    parent = {child: node for node in root.iter() for child in node}
    marker_ids = {node.attrib.get("id") for node in root.iter() if local_name(node.tag) == "marker" and node.attrib.get("id")}

    for node in root.iter():
        tag = local_name(node.tag)
        if tag not in ALLOWED:
            errors.append(f"unsupported SVG element <{tag}>")
            continue
        for attr, value in node.attrib.items():
            attr_name = local_name(attr)
            if attr_name in FORBIDDEN_ATTRIBUTES:
                errors.append(f"<{tag}> uses unsupported attribute {attr_name}")
            if attr_name in {"href", "xlink:href"}:
                errors.append(f"<{tag}> uses external/reference href")
            if attr_name == "transform" and re.search(r"matrix|skew", value, re.I):
                errors.append(f"<{tag}> uses unsupported transform {value}")
            if "url(" in value and attr_name not in {"marker-start", "marker-end"}:
                errors.append(f"<{tag}> uses unsupported paint/reference URL in {attr_name}")
            if attr_name in {"marker-start", "marker-end"}:
                match = re.fullmatch(r"url\(#([^)]+)\)", value.strip())
                if not match or match.group(1) not in marker_ids:
                    errors.append(f"<{tag}> references missing or invalid marker: {value}")
        if tag == "path":
            parent_tag = local_name(parent[node].tag) if node in parent else ""
            data = node.attrib.get("d", "")
            if parent_tag != "marker" or not SIMPLE_MARKER_PATH.fullmatch(data):
                errors.append("<path> is allowed only as a simple straight-line arrow shape inside <marker>")
        if tag == "polyline" and not (node.attrib.get("marker-end") or node.attrib.get("marker-start")):
            warnings.append("polyline without marker may be a hand-drawn arrowhead; inspect it")
        if tag in {"text", "tspan"}:
            size = node.attrib.get("font-size")
            if size:
                try:
                    if float(re.sub(r"[^0-9.]", "", size)) < 16:
                        warnings.append(f"text smaller than 16px: {''.join(node.itertext()).strip()[:40]}")
                except ValueError:
                    warnings.append(f"unreadable font-size value: {size}")

    if "viewBox" not in root.attrib:
        warnings.append("SVG has no viewBox")
    if not list(root):
        errors.append("SVG is empty")

    print("FAIL" if errors else "PASS")
    for error in sorted(set(errors)):
        print(f"ERROR {error}")
    for warning in sorted(set(warnings)):
        print(f"WARN {warning}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
