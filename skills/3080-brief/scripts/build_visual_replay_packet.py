#!/usr/bin/env python3
"""Build an isolated, hash-locked packet for one-picture comprehension replay."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual-preview", required=True, type=Path)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reader-profile", required=True)
    parser.add_argument("--known-context", required=True)
    parser.add_argument("--reader-decision", required=True)
    args = parser.parse_args()

    preview = args.visual_preview.resolve()
    if not preview.is_file():
        raise SystemExit(f"visual preview is missing: {preview}")
    if preview.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        raise SystemExit("visual preview must be a rendered image")
    if args.round < 1:
        raise SystemExit("review round must be at least 1")

    artifact_id = hashlib.sha256(preview.read_bytes()).hexdigest()
    output_contract = {
        "reader_role": "visual_blind",
        "visual_artifact_id": artifact_id,
        "review_round": args.round,
        "main_judgment": "the overall conclusion understood from the image",
        "supporting_evidence": ["each concrete finding and its visible supporting comparison"],
        "next_action_or_boundary": "the visible action or decision-changing boundary",
        "reading_path": "the order in which the image was read",
        "unresolved_confusion": [],
    }
    packet = f"""# 3080 Visual Blind Replay

## Role

Target reader: {args.reader_profile}
Known context: {args.known_context}
Reader task: {args.reader_decision}
You have not seen the source document or the brief.

## Isolation

- Inspect only this rendered one-picture image: `{preview}`
- Visual artifact ID: `{artifact_id}`
- Review round: {args.round}
- Do not open nearby files or request the TLDR, body, source, alt text, visual spec, expected answer, coverage report, or reviewer comments.
- Describe only what the visible image communicates. Do not repair, grade, or rewrite it.

## Replay

Return the overall judgment and each concrete finding you understood with its visible evidence, including what is being compared. Also state the next action or decision-changing boundary, reading order, and unresolved confusion. Do not guess how many findings should exist.

Return JSON only in this shape:

```json
{json.dumps(output_contract, ensure_ascii=False, indent=2)}
```

Do not return claim IDs, PASS, or FAIL.
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(packet, encoding="utf-8")
    print(json.dumps({"status": "PASS", "visual_artifact_id": artifact_id, "packet": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
