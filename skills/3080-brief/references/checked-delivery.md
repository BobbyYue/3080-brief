# Checked Delivery

For a host integration, use [host_delivery.py](../scripts/host_delivery.py) to
invoke this checked path and validate current context, state and exact returned
bytes before exposure. See [host-integration.md](host-integration.md) for the
caller responsibilities, environment limits and separate judgment calibration.
The consumer is implemented; actual third-party UI integration still needs its
own acceptance test. No platform is certified merely by installation.

For the standard independent-audit path, add `--delivery-artifact FINAL_FILE`
to `validate_review_readiness.py`, `build_review_packet.py`, and final delivery.
This can be the rendered local HTML/Markdown/XML or native file accompanied by
the existing extracted draft and render evidence. Reviewers inspect the bound
file and its correspondence with those views; hashing alone cannot prove it.

Replace the final `verify_reviewed_artifacts.py` invocation with
`deliver.py` using the same arguments, including `--delivery-artifact` and
required `--lifecycle-run RUN`. Follow [writing-lifecycle.md](writing-lifecycle.md)
from before drafting; the same run binds the original final review result.
Initialize [managed execution](writing-execution.md) before units, prepare
all native packets with `--lifecycle-run RUN`, and use its actual dispatcher.
The final verifier matches each consumed role file, not an unrelated hash field.
It calls the existing verifier, then the lifecycle verifier, and returns the exact file bytes, not a newly
generated summary. Missing original reviews, a different file, stale evidence,
preparation success and self-check masquerading as independent review block it.

For scoped repairs, add `--delivery-artifact FINAL_FILE` when creating the
before and after snapshots and include that same file in a content or render
layer. Keep original review files immutable; the plan retains the paths/hashes
of reviews it reuses and revalidates their actual results. Final visible-content
changes trigger content review even if a caller labels them layout-only; when
content extraction cannot establish equivalence, do not assume layout-only.
Emit a native scoped result using `plan_review_scope.py verify --plan PLAN.json
--receipt CHECKS.json --output SCOPED_RESULT.json`, register that result in the
same lifecycle run, then use `deliver.py scoped --plan PLAN.json --receipt
SCOPED_RESULT.json --lifecycle-run RUN`.
This calls the existing scoped verifier without restarting the full audit;
its review method remains `scoped-revalidation`.
Reused results must be captured originals. Changed layout requires an actual
visual role result in `review_results`, bound to the scope plan; a scalar PASS
cannot substitute for a new review. Unchanged publication checks reuse all
valid role returns without another audit.

The envelope exposes state, review method, local file hash and base64 `payload`.
For agent tool calls, add `--output NEW_ENVELOPE.json` to keep the document bytes
out of model context; stdout then contains only status, path and hash. This
creates a private file exclusively, never overwriting a source or earlier result.
Consumers must verify process success, state and payload hash, and use those
bytes directly. It covers the main local file, not a portable resource archive.
Preserve relative assets and existing native/live visual checks.

Native Feishu/Word order: create a new authorized pending-review preview first,
inspect its real layout/live board, then run final native review and checked
delivery against that version. Reuse the existing preview path and keep the
source unchanged; do not require final acceptance before the preview it needs.

Use `deliver.py draft` with the full native-verifier arguments and required
`--lifecycle-run RUN` only after three completed batches with a currently failed final review and unresolved
issues. Its envelope is labeled draft, requires a warning and a user question,
and never authorizes publication. If the final failed batch was scoped, use
`deliver.py draft scoped` with its same plan, emitted failed result and lifecycle
run. A past passing version does not prevent a currently failed draft exit.

For explicit-user-choice Fast, use `deliver.py fast` with native repeatable
`--text/--source/--renders`, `--result FAST_RESULT.json`, `--delivery-artifact
FINAL_FILE`, `--lifecycle-run RUN` and `--explicit-fast-choice`. It performs native
self-check and the same lifecycle/source checks, returning `self-checked` with
`review_method=self-check`. Register that exact native Fast result in the run;
native `verify-fast` alone is not a final exit. Disclose omitted independent
reviews/replays. Never promote self-check, draft or prepared/built/schema-only states
to independent acceptance. Do not launch another audit solely for an envelope.

This wrapper performs no network writes and authorizes no publication. Feishu
still needs authorized creation, exact live readback and rendered-board checks.
Installing it does not force a host to call it. The host must gate its verified
output UI on the wrapper and retain original reviewer returns separately from
author edits. Hashes do not authenticate an independent review or prove semantic
quality. Reuse existing relevance, syntax, caveat and progression checks, the
same reviewers and the same retry limits; do not add style-only review rounds.
