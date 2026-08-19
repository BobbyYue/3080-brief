#!/usr/bin/env python3
"""Resolve Beautiful Feishu Whiteboard theme adaptations for 3080 renderers."""

import json
import re
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = SKILL_DIR / "assets" / "themes" / "beautiful-feishu-themes.json"


def canonical(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


def load_registry(path=DEFAULT_REGISTRY):
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    themes = registry.get("themes") or []
    if not themes:
        raise ValueError("theme registry contains no themes")
    return registry


def resolve_theme(style, config, path=DEFAULT_REGISTRY):
    if not style:
        raise ValueError("visual spec must select one Beautiful Feishu Whiteboard theme")
    banned = {canonical(item) for item in config.get("banned_whiteboard_styles", [])}
    if canonical(style) in banned:
        raise ValueError(f"theme is banned by 3080 policy: {style}")
    registry = load_registry(path)
    matches = [theme for theme in registry["themes"] if canonical(style) in {canonical(theme["name"]), canonical(theme["slug"])}]
    if len(matches) != 1:
        raise ValueError(f"unknown Beautiful Feishu Whiteboard theme: {style}")
    return matches[0]


def resolve_visual_theme(visual_spec, config, path=DEFAULT_REGISTRY):
    theme = resolve_theme(visual_spec.get("style"), config, path)
    if len(str(visual_spec.get("style_rationale", "")).strip()) < 8:
        raise ValueError("visual spec style_rationale must explain content fit")
    return theme


def theme_palette(theme):
    tokens = theme["tokens"]
    return {
        "primary": tokens["visual_primary"],
        "accent": tokens["visual_accent"],
        "background": tokens["background"],
        "background_alt": tokens["surface_subtle"],
        "surface": tokens["surface"],
        "text": tokens["ink"],
        "rule": tokens["rule"],
    }


def theme_css(theme):
    tokens = theme["tokens"]
    declarations = {
        "background": tokens["background"],
        "surface": tokens["surface"],
        "surface-subtle": tokens["surface_subtle"],
        "ink": tokens["ink"],
        "muted": tokens["muted"],
        "rule": tokens["rule"],
        "accent": tokens["accent"],
        "accent-2": tokens["accent2"],
        "radius": f'{tokens["radius"]}px',
        "rule-width": f'{tokens["border_width"]}px',
        "content-width": f'{tokens["content_width"]}px',
        "section-gap": f'{tokens["section_gap"]}px',
    }
    return ":root { " + " ".join(f"--{key}: {value};" for key, value in declarations.items()) + " }"
