# Writing Lifecycle

Use one run directory for one task, with `lifecycle.json` as its state. All
commands below use this package's standard-library `scripts/writing_lifecycle.py`
and `config/writing-quality.json`; no other skill supplies the verifier.
Keep evidence files immutable, including failed results and measurements.
The full plan/unit/measurement/geometry/assessment protocol is in
[writing-quality-records.md](writing-quality-records.md); this page covers only
3080 routing and checked exports. Use the run's selected `task-packet.json`
while writing rather than loading both profiles or the engine into context.

## Record The Work

Before prose, initialize `functional` with the captured source and the actual
reader task, requirement authority, required answers, reading path, language,
output format and source gaps. This complements the existing source ledger and
opening-answer plan; it does not replace them.

```bash
python3 scripts/lifecycle_delivery.py RUN --plan CONTEXT_PLAN.json --reader-plan-lock READER_PLAN_LOCK.json --bound-plan NEW_BOUND_PLAN.json
python3 scripts/writing_lifecycle.py unit RUN --text UNIT.md --record UNIT_RECORD.json
python3 scripts/writing_lifecycle.py measure RUN --text FINAL_TEXT.md --output METRICS.json
python3 scripts/writing_lifecycle.py candidate RUN --artifact FINAL_FILE --text FINAL_TEXT.md --report METRICS.json --record ASSESSMENT.json
python3 scripts/writing_lifecycle.py review-start RUN --artifact FINAL_FILE
# Run the existing native review, then register its unedited result:
python3 scripts/writing_lifecycle.py review-finish RUN --result RESULT.json --verdict pass
```

Remeasure repaired text rather than editing a report to claim removal. For
assessment, fill the generated `REPORT.assessment.json` template, preserving
its real `text_sha256` and `report_sha256` bindings. For
rendered formats, record actual target-page inspection; optional `--geometry`
uses captured raw geometry, not an estimate from text length. Measurements,
contextual judgments and real reader outcomes remain different evidence.

The initializer reuses the existing locked required-answer plan and captured
source. Supply only genre/purpose/authority/format/material/reading-path context;
task, reader and required answers are derived from their original owner. The
optional repeatable `--source` captures additional native source/excerpt inputs.
The derived file links that lock; it is not a second editable checklist. Full export
checks that reference and exact mapped fields against the lock already bound
by readiness. All exports compare native source hashes with registered sources
and check recognizable output formats. Scoped/Fast paths without an original
answer plan still bind their native sources and exact result; an inherited plan
link remains checked. These are identity/field checks, not automatic proof that
two plans or a draft are semantically equivalent.

Use `review-finish ... --verdict fail` for a failed native result, retaining
unresolved reader impact in its issue list. The API's `issues` argument can
record that impact when a native result's issue fields differ. A parallel
Reader/Source/Visualization batch counts once, not once per reviewer. Revisions
keep the same run and cumulative three-batch limit. Preserve original results,
all opening/one-picture/HTML replays, and the existing three roles. No extra
review role or style-only reassurance batch is introduced.

## Native Preview Before Acceptance

For Feishu/Word, first generate a new pending-review document or preview at the
already-authorized target using the existing creation/preview workflow. Inspect
its actual pages/live board, bind the corresponding native file/extracted text
and render evidence, then complete native review and checked delivery. A preview
is not checked acceptance or authorization to publish to a broader audience.
Keep the source document unchanged. Do not wait for final acceptance before
making the preview needed for that acceptance, or add another reviewer or
confirmation round. Existing permission handling still applies if that target
has not been authorized. Later visible changes rerun only affected checks.

## Checked Exits

Full delivery uses the existing native verifier arguments plus
`--delivery-artifact FINAL_FILE --lifecycle-run RUN`. Native final verification
must pass first; lifecycle verification then checks the same file with profile
`functional` and `review_evidence=[RESULT.json]` before any payload is released.
Missing records, wrong profile, old bytes, changed evidence or a different
native result block delivery.

For scoped revalidation, emit a native result after the existing checks pass:

```bash
python3 scripts/plan_review_scope.py verify --plan PLAN.json --receipt CHECKS.json --output SCOPED_RESULT.json
python3 scripts/writing_lifecycle.py review-finish RUN --result SCOPED_RESULT.json --verdict pass
python3 scripts/deliver.py scoped --plan PLAN.json --receipt SCOPED_RESULT.json --lifecycle-run RUN --output NEW_ENVELOPE.json
```

Start this review batch in the same run before doing its scoped checks. The
emitted result preserves the receipt and records actual pass/fail status
and issues after native verification runs; failure still returns nonzero.
Never hand-add PASS as evidence. The final adapter rechecks that exact scoped
result and binds it as `review_evidence`. Unaffected
original reviews remain reusable under the existing scope rules.

After exactly three completed batches, if the current final batch failed with unresolved issues, use
`deliver.py draft` with the full native-verifier arguments and
`--lifecycle-run RUN`. This checks native failed-review provenance and version
bindings without claiming semantic acceptance, then calls the lifecycle API
with `draft=True`. Output has `delivery_state=draft`, unresolved `issues`,
required user notice/question and `external_action_authorized=false`. Do not
publish it; present the limits and ask whether to continue. Fewer rounds, an
unfinished batch, a different result/file or a passing current result cannot
use this fallback. Earlier versions may have passed; that neither hides the
current regression nor prevents showing its labeled draft. Do not reset the run.

If the last failed batch was scoped, register its emitted failed native result
with `review-finish ... --verdict fail`, then use `deliver.py draft scoped --plan
PLAN.json --receipt SCOPED_RESULT.json --lifecycle-run RUN`. It preserves failed
checks instead of treating them as passes, while still requiring current plan,
artifact/layer/evidence bindings and the same cumulative three-round record.

## Limits And Integration

`verify_reviewed_artifacts.py` is explicitly a low-level native binding check;
its local success is not complete lifecycle acceptance. `deliver.py` has no
optional flag that skips the lifecycle check. It snapshots the run state and
registered evidence alongside the native artifacts to detect changes during
delivery. Its envelope preserves lifecycle rounds/evidence references.

Fast remains available only at the user's explicit request. Prepare and verify
the existing three self-check records, retain all existing Fast hard gates, then:

```bash
python3 scripts/deliver.py fast --text FINAL_FILE --source SOURCE --renders PREVIEW --result FAST_RESULT.json --delivery-artifact FINAL_FILE --lifecycle-run RUN --explicit-fast-choice --output NEW_ENVELOPE.json
```

Repeat text/source/render flags as in native `verify-fast`; the exact artifact
must be a reviewed text input. Register the unchanged self-check result in the
same functional run. This export rechecks native self-checks, source binding and
all lifecycle stages/measurements. It returns `delivery_state=self-checked` and
`review_method=self-check`, never independent acceptance. The choice flag records
the caller's assertion, not independent proof of user consent; use it only after
an explicit user choice and disclose skipped independent reviews/replays.
`editorial_gate.py verify-fast` alone remains a local editorial check, not final
delivery. Lifecycle bookkeeping cannot authenticate reviewer identity,
prove semantic quality, prove generation chronology or force a host to use an
export. External publication still needs authorization and live readback.

Adapter integration note: historical scoped receipts contain no top-level
`status/verdict`. Register the emitted pass/fail `SCOPED_RESULT.json`, not
the old `CHECKS.json`, because functional `finish_review` reads that field.
