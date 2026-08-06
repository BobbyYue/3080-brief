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
    parser.add_argument("--mode", choices=("independent", "self_check"), default="independent")
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
    modes = [review.get("review_mode") for review in reviews]
    if any(mode != args.mode for mode in modes):
        issues.append(f"expected review mode {args.mode}, got {modes}")
    run_ids = [review.get("reviewer_run_id") for review in reviews]
    if any(not isinstance(run_id, str) or not run_id.strip() for run_id in run_ids):
        issues.append("every review must include a non-empty reviewer_run_id")
    if args.mode == "independent" and len(set(run_ids)) != len(expected_roles):
        issues.append("independent reviews must use three distinct reviewer_run_id values")

    failed = [review.get("reviewer_role") for review in reviews if review.get("verdict") != "PASS"]
    blockers = []
    for review in reviews:
        blockers.extend(review.get("blocking_issues", []))
        blockers.extend(review.get("unsupported_claims", []))
        blockers.extend(review.get("missing_coverage", []))
        blockers.extend(review.get("required_fixes", []))
        checks = review.get("checks")
        if not isinstance(checks, list) or not checks:
            issues.append(f"{review.get('reviewer_role', 'unknown')} review has no structured checks")
        elif any(check.get("result") != "PASS" for check in checks if isinstance(check, dict)):
            issues.append(f"{review.get('reviewer_role', 'unknown')} review contains a failed check")
    verdict = "PASS" if not issues and not failed and not blockers else "FAIL"
    result = {
        "verdict": verdict,
        "artifact_set_id": next(iter(artifact_ids)) if len(artifact_ids) == 1 else None,
        "review_round": next(iter(rounds)) if len(rounds) == 1 else None,
        "review_mode": args.mode,
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
