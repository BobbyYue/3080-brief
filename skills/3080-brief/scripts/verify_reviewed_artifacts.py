#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
from pathlib import Path


def digest(path):
    if not path:
        return None
    candidate = Path(path)
    return hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None


def main():
    parser = argparse.ArgumentParser(description="Verify final 3080 artifacts match the reviewer-approved artifact set.")
    parser.add_argument("--review-result", required=True)
    parser.add_argument("--source-snapshot", default="")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--claim-ledger", required=True)
    parser.add_argument("--tldr", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--draft", default="")
    parser.add_argument("--visual-spec", default="")
    parser.add_argument("--html-design-plan", default="")
    parser.add_argument("--validation-notes", default="")
    parser.add_argument("--whiteboard-preview", default="")
    parser.add_argument("--document-preview", default="")
    parser.add_argument("--full-page-preview", default="")
    parser.add_argument("--geometry-report", default="")
    parser.add_argument("--full-page-replay", default="")
    parser.add_argument("--source-outline", required=True)
    parser.add_argument("--source-excerpts", required=True)
    parser.add_argument("--readiness-receipt", required=True)
    args = parser.parse_args()

    reviewed = json.loads(Path(args.review_result).read_text(encoding="utf-8"))
    hashes = {
        "source_snapshot": digest(args.source_snapshot),
        "inventory": digest(args.inventory),
        "claim_ledger": digest(args.claim_ledger),
        "tldr": digest(args.tldr),
        "body": digest(args.body),
        "draft": digest(args.draft),
        "visual_spec": digest(args.visual_spec),
        "html_design_plan": digest(args.html_design_plan),
        "validation_notes": digest(args.validation_notes),
        "whiteboard_preview": digest(args.whiteboard_preview),
        "document_preview": digest(args.document_preview),
        "full_page_preview": digest(args.full_page_preview),
        "geometry_report": digest(args.geometry_report),
        "full_page_replay": digest(args.full_page_replay),
        "source_outline": digest(args.source_outline),
        "source_excerpts": digest(args.source_excerpts),
        "readiness_receipt": digest(args.readiness_receipt),
    }
    hashes = {key: value for key, value in hashes.items() if value}
    artifact_set_id = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode("utf-8")).hexdigest()
    expected = reviewed.get("artifact_set_id")
    if reviewed.get("verdict") != "PASS":
        print("FAIL review result is not PASS")
        return 1
    if artifact_set_id != expected:
        print(f"FAIL artifact set changed after review: expected {expected}, got {artifact_set_id}")
        return 1
    print(f"PASS artifact_set_id={artifact_set_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
