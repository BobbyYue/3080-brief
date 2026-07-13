# Review Packet Contract

Use `scripts/build_review_packet.py --role all` to build three independent packets from one artifact set. Do not manually reuse one generic packet for all roles.

## Shared Integrity

Every packet contains the review round, one artifact-set ID, SHA256 hashes, user constraints, source inventory, claim ledger, draft TLDR, a role-specific PASS gate, and a JSON-only output contract. The inventory must state source language, output language, language basis, and exact override evidence when applicable.

Launch all three reviewers before reading or using any result. Do not expose, quote, summarize, hint at, or use one reviewer's comments in another reviewer's prompt.

## Reader Packet

Provide the full reader-facing draft or rendered document, its preview/path when available, the TLDR, and the claim ledger. This reviewer evaluates real reading experience, including whether the title, TLDR, table, visual, and body consistently use the declared output language.

## Source Packet

Provide the complete non-appendix source outline, P0/P1 source excerpts with locations, claim ledger, body claim mapping, and a source link only when the reviewer can independently access it.

The source reviewer returns `FAIL` when the supplied evidence is insufficient to independently verify valuable-source coverage or grounding, or when output language differs from source primary language without an exact explicit user override. The language of the user's message is not override evidence. Do not rely only on the main agent's summary of the source.

## Visual Packet

Provide `visual_spec.json`, value-weighted coverage result, local/live whiteboard previews, rendered document preview, validation summary, selected style, and the ledger's semantic directions/display values. Check one semantic mapping across body and board plus redundant non-color cues. Do not paste full SVG/XML unless a specific rendering defect requires it.

## Output And Aggregation

Each reviewer returns JSON with its role key, artifact-set ID, round, PASS/FAIL checks, blockers, unsupported claims, missing coverage, and required fixes. Aggregate only after all three results arrive:

```bash
scripts/aggregate_reviews.py reader.json source.json visual.json --output review_result.json
```

Aggregation fails when roles are missing or duplicated, artifact IDs differ, rounds differ, any verdict is `FAIL`, or a blocking/unsupported claim remains.
