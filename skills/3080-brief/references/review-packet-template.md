# Review Packet Contract

Run `scripts/validate_review_readiness.py` first, then pass its unchanged receipt
to `scripts/build_review_packet.py --role all` to build three independent
packets from one artifact set. Do not manually reuse one generic packet.

## Shared Integrity

Every packet contains the review round, one artifact-set ID, SHA256 hashes for the normalized non-appendix source snapshot and derived artifacts, user constraints, source inventory, claim ledger, draft TLDR, a role-specific PASS gate, and a JSON-only output contract. The inventory must state source language, output language, language basis, and exact override evidence when applicable.

Launch all three reviewers before reading or using any result. Do not expose, quote, summarize, hint at, or use one reviewer's comments in another reviewer's prompt.

## Reader Packet

Provide the full reader-facing draft or rendered document, its preview/path when available, the TLDR, and the claim ledger. This reviewer evaluates real reading experience, including whether the title, TLDR, table, visual, and body consistently use the declared output language. It checks contextual clarity, not isolated word or punctuation bans, and fails rewrites that add personality at the cost of professional precision.

## Source Packet

Provide the complete non-appendix source outline, P0/P1 source excerpts with locations, claim ledger, body claim mapping, and a source link only when the reviewer can independently access it. The ledger must include material sufficiency, source identity, evidence ceiling, output assertion, and protected relations for every non-appendix P0/P1 claim.

The source reviewer returns `FAIL` when the supplied evidence is insufficient to independently verify valuable-source coverage or grounding, a protected relation or numeric attachment drifts, an assertion exceeds its evidence ceiling, thin material is padded, or output language differs from source primary language without an exact explicit user override. The language of the user's message is not override evidence. Do not rely only on the main agent's summary of the source.

## Visual Packet

Provide `visual_spec.json`, value-weighted coverage result, local/live previews, rendered document preview, hash-locked validation notes, selected style, and the ledger's semantic directions, display values, and `visual_required_tokens`. For HTML, also provide and hash-lock `html_design.json`, the full-page screenshot, geometry report, and full-page replay record; validation notes must name the composer contract/receipt, selected fonts/runtime assets, offline status, rich-render success, and native-SVG fallback. Recompute visible coverage from the preview, verify real composition hierarchy and common scope on each quantitative axis, then check one semantic mapping across body and board plus redundant non-color cues. Do not trust a declared percentage or paste full SVG/XML unless a specific rendering defect requires it.

Visual Blind Replay is a separate earlier gate. Do not give this reviewer the replay transcript, its failure reason, expected answer, or revision rationale; those would bias the audit.

## Output And Aggregation

Each reviewer returns JSON conforming to `independent-review.schema.json`, with its role key, artifact-set ID, round, PASS/FAIL checks, blockers, unsupported claims, missing coverage, and required fixes. The simplified `evals/review.schema.json` is not the independent-review contract. Aggregate only after all three results arrive:

```bash
scripts/aggregate_reviews.py reader.json source.json visual.json --output review_result.json
```

Aggregation fails when roles are missing or duplicated, artifact IDs differ, rounds differ, any verdict is `FAIL`, or a blocking/unsupported claim remains.
