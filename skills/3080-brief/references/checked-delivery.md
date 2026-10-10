# Checked Delivery

For the standard independent-audit path, add `--delivery-artifact FINAL_FILE`
to `validate_review_readiness.py`, `build_review_packet.py`, and final delivery.
This can be the rendered local HTML/Markdown/XML or native file accompanied by
the existing extracted draft and render evidence. Reviewers inspect the bound
file and its correspondence with those views; hashing alone cannot prove it.

Replace the final `verify_reviewed_artifacts.py` invocation with
`deliver.py` using the same arguments, including `--delivery-artifact`.
It calls the existing verifier and returns the exact file bytes, not a newly
generated summary. Missing original reviews, a different file, stale evidence,
preparation success and self-check masquerading as independent review block it.

For scoped repairs, add `--delivery-artifact FINAL_FILE` when creating the
before and after snapshots and include that same file in a content or render
layer. Keep original review files immutable; the plan retains the paths/hashes
of reviews it reuses and revalidates their actual results. Final visible-content
changes trigger content review even if a caller labels them layout-only; when
content extraction cannot establish equivalence, do not assume layout-only.
Use `deliver.py scoped --plan PLAN.json --receipt CHECKS.json`.
This calls the existing scoped verifier without restarting the full audit;
its review method remains `scoped-revalidation`.

The envelope exposes state, review method, local file hash and base64 `payload`.
For agent tool calls, add `--output NEW_ENVELOPE.json` to keep the document bytes
out of model context; stdout then contains only status, path and hash. This
creates a private file exclusively, never overwriting a source or earlier result.
Consumers must verify process success, state and payload hash, and use those
bytes directly. It covers the main local file, not a portable resource archive.
Preserve relative assets and existing native/live visual checks.

Fast self-check and repair-exhausted draft presentation retain their existing
explicit-user-choice and warning policies. Do not route them through the
independent path or launch another full audit merely to obtain its envelope.
Until a corresponding caller is integrated, report those paths as not covered
by this checked-delivery wrapper, not as independently reviewed. Never use a
prepared/built/schema-only state as evidence of completion.

This wrapper performs no network writes and authorizes no publication. Feishu
still needs authorized creation, exact live readback and rendered-board checks.
Installing it does not force a host to call it. The host must gate its verified
output UI on the wrapper and retain original reviewer returns separately from
author edits. Hashes do not authenticate an independent review or prove semantic
quality. Reuse existing relevance, syntax, caveat and progression checks, the
same reviewers and the same retry limits; do not add style-only review rounds.
