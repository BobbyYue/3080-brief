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
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--claim-ledger", required=True)
    parser.add_argument("--tldr", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--draft", default="")
    parser.add_argument("--visual-spec", default="")
    parser.add_argument("--whiteboard-preview", default="")
    parser.add_argument("--document-preview", default="")
    args = parser.parse_args()

    reviewed = json.loads(Path(args.review_result).read_text(encoding="utf-8"))
    hashes = {
        "inventory": digest(args.inventory),
        "claim_ledger": digest(args.claim_ledger),
        "tldr": digest(args.tldr),
        "body": digest(args.body),
        "draft": digest(args.draft),
        "visual_spec": digest(args.visual_spec),
        "whiteboard_preview": digest(args.whiteboard_preview),
        "document_preview": digest(args.document_preview),
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
