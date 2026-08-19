#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "3080-brief.json"


def main():
    parser = argparse.ArgumentParser(description="Aggregate three independent 3080 reviewer JSON results.")
    parser.add_argument("reviews", nargs="+", help="Three reviewer JSON files")
    parser.add_argument("--output", default="")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()

    expected_roles = set(json.loads(Path(args.config).read_text(encoding="utf-8"))["review_roles"])
    reviews = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.reviews]
    roles = [review.get("reviewer_role") for review in reviews]
    issues = []
    if len(reviews) != len(expected_roles) or set(roles) != expected_roles or len(set(roles)) != len(expected_roles):
        issues.append(f"expected exactly reader/source/visual reviews, got {roles}")
    artifact_ids = {review.get("artifact_set_id") for review in reviews}
    rounds = {review.get("review_round") for review in reviews}
    if None in artifact_ids or len(artifact_ids) != 1:
        issues.append("reviewers did not evaluate the same artifact_set_id")
    if None in rounds or len(rounds) != 1:
        issues.append("reviewers did not evaluate the same review round")

    failed = [review.get("reviewer_role") for review in reviews if review.get("verdict") != "PASS"]
    blockers = []
    for review in reviews:
        blockers.extend(review.get("blocking_issues", []))
        blockers.extend(review.get("unsupported_claims", []))
    verdict = "PASS" if not issues and not failed and not blockers else "FAIL"
    result = {
        "verdict": verdict,
        "artifact_set_id": next(iter(artifact_ids)) if len(artifact_ids) == 1 else None,
        "review_round": next(iter(rounds)) if len(rounds) == 1 else None,
        "roles": roles,
        "failed_roles": failed,
        "integrity_issues": issues,
        "blocking_issues": blockers,
        "required_fixes": {
            review.get("reviewer_role", "unknown"): review.get("required_fixes", []) for review in reviews
        },
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
