# Reading Layout Contract

This contract turns document layout into a required part of every 3080 Brief run. It applies to Feishu/Lark, Word, Markdown, and HTML because every renderer consumes the same reviewed `brief.json`.

## Required Plan

Before rendering, write `brief.json.reading_path` with:

- `contract_version`: exactly `1.0`;
- `reader_decision`: the judgment or decision the intended reader must be able to make;
- `section_questions`: exactly one concrete reader question for each body section, in body order;
- `section_density`: exactly one `light`, `balanced`, or `dense` value for each body section.

Do not add a body section that is absent from the plan. Do not use the plan to add facts, certainty, actions, or scope that the source does not support.

## Required Reading Path

- TLDR remains the first reading level: judgment, strongest support, one-picture summary, and key-question table.
- Each body section answers one planned reader question. Its heading states the useful result rather than the method used to obtain it.
- A section containing a table or figure starts with a paragraph, bullets, or a restrained callout that states the takeaway.
- Tables and figures are dense evidence. Two dense evidence blocks may not be adjacent; place a substantive explanatory bridge between them.
- Definitions, uncertainty, scope, and source notes remain adjacent to the claim or visual they qualify.
- `dense` sections receive more separation in HTML. Other native formats use their own heading and paragraph spacing while preserving the same structural path.
- Every renderer uses four distinguishable proximity relationships: tight within
  one idea or between an object and its label, normal between paragraphs, wider
  between subsections or evidence forms, and widest between major reader
  questions. A heading, caption, annotation, or source note must sit closer to
  the content it qualifies than to neighboring content.

## Runtime Gate

`scripts/validate_brief.py` calls the shared document validator before any renderer runs. It rejects a missing or stale `reading_path`, an incomplete section map, an unknown density, evidence before takeaway, and consecutive dense evidence without explanation. Existing rendered review verifies proximity and grouping; this adds no new review pass.

Failure is blocking. A renderer, output-format override, fast mode, or visual review cannot waive this contract. Fix the plan or document, rerun `validate_brief.py`, then rerun the target-format validator.

## Body Completeness

An outline is not an explanation. Before prose, save the unaltered user request,
non-appendix source snapshot, claim ledger and an independently source-derived
outline. Do not derive that outline from the author's narrowed body plan. Draft
`body-plan-input.json` using [body-completion.schema.json](body-completion.schema.json):

```json
{
  "scope": "full",
  "requirements": [{
    "id": "B1", "question": "What must this reader understand?",
    "claim_ids": ["C01"],
    "answer_requires": ["The source-supported explanation, conditions and limits needed to answer."]
  }],
  "excluded_claims": []
}
```

Every non-appendix P0/P1 claim must map to a requirement or an explicit
`excluded_claims` item `{ "claim_id": "C02", "reason": "..." }`. Exclusions require
confirmation from both existing Reader and Source reviewers. The scope check
must also find important source/request questions missing from the plan itself.

```bash
python3 scripts/body_completion.py lock --plan body-plan-input.json \
  --user-request user-request.md --source-snapshot source_non_appendix.md \
  --claim-ledger claim_ledger.json --source-outline source-outline.md \
  --output body-plan.lock.json
```

The command refuses overwrite and prints `{path, sha256}`. Put that exact object
in `brief.json.body_plan`. Use absolute task paths; package fixtures may use
package-root-relative references. A lock proves integrity, not when prose was
written or that an outline was independently derived. Preserve old locks and
review evidence; changed source/request/ledger/outline needs a new lock.

Write `answers: ["B1"]` on the visible body blocks that actually explain the
requirement. Paragraphs, bullets, callout text and table cells can supply evidence;
headings, figure labels, TLDR mappings and collapsed P2 details cannot. The
shared renderer validation rejects missing/empty bodies, empty explanation,
unknown/unanswered requirements, stale inputs and all evidence merely repeating
the TLDR. It uses no universal word count or section count. A thin source may
need only one concise explanatory paragraph. Paraphrase detection and sufficiency
remain semantic judgments, not code-proven outcomes.

Only an explicit request to omit the body permits `scope: "summary-only"` with
empty `requirements`, all P0/P1 claims explicitly excluded and
`summary_only_request_quote` copied verbatim from the bound request. Both existing
reviewers must approve that exact quote and exclusions. "Compact", a short source,
or Fast mode is not permission. A lock or render alone is not exception approval.

### Existing Pipeline Integration

- Render commands are unchanged; they validate `body_plan` through `brief_model`.
- Add `--brief-json brief.json` to `validate_review_readiness.py`,
  `build_review_packet.py`, `verify_reviewed_artifacts.py` and standard/draft
  `deliver.py`. Readiness additionally matches the locked source, ledger and outline.
- For CSS-controlled HTML, also pass `--body-visible-text desktop-visible.txt`
  consistently and `--delivery-artifact index.html`. Capture the actual visible
  text during the existing browser inspection. Its hash is bound to those exact
  HTML bytes, not treated as proof that a browser produced it. Checks require
  mapped answers in the snapshot AND eligible HTML text; scripts, hidden nodes,
  closed details and styles cannot substitute. Existing visual review confirms
  the real rendering. DOCX integrity is binary; answer presence uses native XML
  text without treating hidden runs as evidence.
- `body_completion.py check --brief-json brief.json --candidate index.html
  --body-visible-text desktop-visible.txt` reports structural completeness only.
- Reader and Source return the generated `body_completion` object in their
  existing review: `scope_check` with exact request/outline quotes and reason;
  one judgment per requirement with exact mapped block quotes and a reason
  addressing every `answer_requires` item; Source also supplies `source_quote`;
  both judge every exclusion. Use `pass`/`fail`, not blank attestations. Visual
  review is unchanged. Aggregation and delivery recheck original evidence.
- Fast uses the same fields as self-checks, never independent-review claims:
  add `--brief-json` and optional `--body-visible-text` to
  `editorial_gate.py prepare-fast/verify-fast` and `deliver.py fast`. The first
  `--text` is the exact delivery candidate; include the locked snapshot in
  `--source`. Preparation emits body evidence and initially failing templates.
- Scoped snapshots use `--brief-json` and optional `--body-visible-text`.
  Carry `body_completion`, `body_candidate` and, when used, `body_visible_text`
  from the editorial inputs into scoped receipt `editorial_inputs`. Snapshot
  and plan bind the body context; unchanged semantic judgments remain reusable.
  Body-plan/source/claim changes invalidate reuse. All three original role
  results remain necessary; a scope receipt cannot replace them with PASS text.

Missing or failed body judgments block acceptance on every route. A properly
captured negative judgment remains a semantic failure, not a transport retry;
the existing exhausted-review labeled-draft exit is preserved. Do not rewrite
old real review evidence to satisfy the new contract. Synthetic migration tests
verify plumbing, not literary quality, source truth or actual comprehension.
