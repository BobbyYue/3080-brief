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
failed for that artifact hash.

Wait for every audit result before editing. Merge and deduplicate all required
fixes, make one coherent revision, rerun affected pre-audit checks and replays,
then build the next hash-locked batch. Never fix one reviewer result while the
others are still running.

## Change-Impact Reruns

Before audit, rerun only checks affected by a change:

| Change | Required rerun |
| --- | --- |
| Source, metric, certainty, risk, or action | ledger, source expression, coverage, mapped visuals, readiness |
| TLDR, heading, prose, term, or order | expression, brief, reading path, document render, reader replay |
| Visual data, label, layout, or color | coverage, visual spec, visual render, Visual Blind Replay, document render |
| HTML/Feishu renderer, asset, link, or fallback | target validator, affected renders, readiness |
| Publication placement only | action preflight and live-target verification |

Use the union for cross-category changes. Record `change -> affected checks ->
result`. Any reader-facing change after a passing audit creates a new artifact
set and requires the audit contract again; publication-only placement does not
regenerate unchanged content.

## Stop Conditions

The three-round audit limit is an emergency bound. Stop and ask for input when
the blocker is missing source evidence, ambiguous intent, permission, or an
external-system state. Do not consume another generation, render, or reviewer
round when no document edit can resolve the blocker.
