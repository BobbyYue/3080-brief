# Efficient Execution Contract

Use this contract on every 3080 Brief task. It changes work order and retry
scope without weakening source, visual, audit, replay, or delivery gates.

## Batch Scope First

For multiple independent briefs, identify all sources, readers, formats,
languages, publication targets, and shared constraints once. Then keep one
isolated lane per brief with separate source snapshots, ledgers, designs,
artifact hashes, reviews, and receipts. Run non-conflicting lanes concurrently;
serialize writes to the same destination.

## Evidence Ready Before Rendering

Finish the non-appendix source snapshot, inventory, P0/P1 excerpts, claim
ledger, protected relations, evidence ceilings, missing-input decisions, and
reviewer inputs before rendering. Run `scripts/validate_review_readiness.py`
after the final candidate and renders pass deterministic checks. A blocked
receipt stops audit; do not use reviewers to discover an incomplete packet.

## One Full Audit On The Normal Path

Use deterministic gates, Visual Blind Replay, and full-artifact Blind Reader
Replay to stabilize comprehension before the expensive three-reviewer audit.
The normal path launches one complete Reader/Source/Visual batch per artifact.
An additional complete batch is allowed only after a prior complete batch
failed and the scoped plan shows that source or content changed.

Wait for every audit result before editing. Merge and deduplicate all required
fixes and make one coherent revision. Preserve each role's result separately;
a PASS remains reusable when its review layer has not changed.

## Change-Impact Reruns

Before the first audit, rerun only checks affected by a change. After any
review result exists, follow [scoped-revalidation.md](scoped-revalidation.md)
and generate a machine-readable scope with `scripts/plan_review_scope.py`.

| Change | Required rerun |
| --- | --- |
| Source, metric, certainty, risk, or action | ledger, source expression, coverage, mapped visuals, readiness |
| TLDR, heading, prose, term, or order | expression, brief, reading path, document render, reader replay |
| Visual data, label, layout, or color | coverage, visual spec, visual render, Visual Blind Replay, document render |
| HTML/Feishu renderer, asset, link, or fallback | target validator, affected renders, readiness |
| Publication placement only | action preflight and live-target verification |

Use the union for cross-category changes. Do not treat the final HTML hash as a
global reset: compare source, content, core visual, desktop layout, and mobile
layout independently. Source/content changes require a full audit; a layout-only
change requires only target validation, affected geometry, and affected visual
review. Publication-only placement does not regenerate unchanged content.

## Stop Conditions

Stop as soon as the generated scope receipt passes. Do not add another replay
or audit for reassurance. Allow at most two targeted repair rounds after the
first complete audit; then deliver the current version with unresolved issues
and ask whether to continue. Missing source, intent, permission, or external
state stops immediately.
