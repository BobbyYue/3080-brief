#!/usr/bin/env python3
"""Validate the shared 3080 structured brief before any format renderer runs."""

import argparse
import json
import sys
from pathlib import Path

from brief_model import validate_document
from theme_registry import resolve_visual_theme


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config" / "3080-brief.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", help="Reviewed brief.json")
    parser.add_argument("visual_spec", help="Reviewed visual_spec.json")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    try:
        document = json.loads(Path(args.document).read_text(encoding="utf-8"))
        visual_spec = json.loads(Path(args.visual_spec).read_text(encoding="utf-8"))
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        resolve_visual_theme(visual_spec, config)
        warnings = validate_document(document, visual_spec, config)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("FAIL")
        print(f"ERROR {exc}")
        return 1
    print("PASS")
    for warning in warnings:
        print(f"WARN {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
