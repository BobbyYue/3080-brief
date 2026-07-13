# Three Reviewer Result Example

Runtime reviewers return JSON, not prose reports. Each role evaluates one artifact-set ID and review round independently.

```json
{
  "reviewer_role": "source",
  "artifact_set_id": "same-hash-derived-id-for-all-three-reviewers",
  "review_round": 1,
  "verdict": "FAIL",
  "checks": [
    {
      "name": "P0/P1 source coverage",
      "result": "FAIL",
      "reason": "A source-backed compatibility boundary is missing from both the board and body."
    }
  ],
  "blocking_issues": ["The compatibility boundary can change the rollout decision."],
  "unsupported_claims": [],
  "missing_coverage": ["Add the missing P0 risk claim and its source location."],
  "required_fixes": ["Map the risk to a board block or explain why it cannot fit, then preserve it in the body."]
}
```

The main agent waits for all three JSON results, runs `scripts/aggregate_reviews.py`, revises any failure, rebuilds packets with a new artifact-set ID, and reruns all three reviewers.
