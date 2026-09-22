# Source-Faithful Expression

Read this reference only after the first reader-structured draft exists, or when source sufficiency, claim strength, templated language, or false-positive risk needs attention. Do not use it to choose the body structure.

## Execution Order

1. Protect source relationships.
2. Respect material sufficiency and source identity.
3. Keep output assertion at or below the evidence ceiling.
4. Make the minimum effective expression edit.
5. Preserve valid professional language and useful imperfection.
6. Validate both what should change and what should remain.

## Protect Relationships, Not Isolated Words

For every non-appendix P0/P1 claim, record at least one protected relation in `claim_ledger.json`:

- `subject`: who or what the source discusses;
- `predicate`: what happened, was observed, is proposed, or remains unknown;
- `object`: the affected object, metric, state, or decision;
- `scope`: population, segment, platform, geography, sample, denominator, or other applicability boundary;
- `time_status`: period plus status such as planned, testing, launched, observed, or completed;
- `qualifiers`: confidence, significance, uncertainty, dependency, exception, or causal boundary;
- `values`: exact numbers and the objects they modify.

Never change subject ownership, action direction, completion state, comparison basis, causality, scope, or numeric attachment for smoother prose. Co-occurrence is not an implementation or causal relation.

## Do Not Make Thin Material Look Rich

Classify source sufficiency before drafting:

- `sufficient / proceed`: the source can support the intended brief.
- `thin / shorten`: preserve the core value but reduce length, detail, and certainty.
- `thin / clarify`: ask when the missing material can change the main judgment, metric meaning, risk, or action.
- `blocked / clarify`: do not draft a final brief until the blocking source issue is resolved.

Never fill a thin source with external facts, invented examples, personal experience, emotion, or false precision. External research is out of scope unless the user explicitly requests it.

For `thin / shorten`, preserve a normalized non-appendix source snapshot and pass the configured expansion guardrail. The guardrail is a release ceiling, not a target: write only what the source can support. `thin / clarify` cannot produce a final draft before clarification.

Classify each material claim as `source_fact`, `source_author_claim`, `source_self_report`, `agent_inference`, or `unknown`. Keep `agent_inference` visibly labeled and below a source-backed assertion.

## Match Assertion To Evidence

Use the same ordered scale for `evidence_ceiling` and `output_assertion`:

`unknown < reported < observed < suggestive < supported < demonstrated < causal`

The output assertion must never exceed the source evidence ceiling. Examples:

- `reported`: “the source states / the team reports”; do not convert to an independently verified fact.
- `observed`: describe the measured state or difference without inventing mechanism.
- `suggestive`: use “suggests / may indicate”; keep alternatives visible.
- `supported`: use “supports” only when the source supplies material evidence and boundaries.
- `demonstrated`: require a source-backed test or result that warrants the stronger wording.
- `causal`: require an explicit causal design or source conclusion with the relevant controls and caveats.

Preserve legitimate hedging, passive voice, technical terms, and neutral tone when they carry precision. Natural expression does not mean casual expression.

## Make The Minimum Effective Edit

Apply [writing-craft.md](writing-craft.md) within this pass: supported details,
purposeful progression and natural reading flow. Version 2 reader-value records
require three anchored `expression.craft_checks` and `meaning.detail_support`.
Retain the three mandatory TLDR units, source-only scope and existing reviewers.
No invented story, hidden conclusion, sentence quota or extra style-only round.

Make the required units complementary: the takeaway gives the judgment, the picture exposes the relationship, and the question table answers likely follow-ups. Preserve useful repetition, every P0 and the weighted-coverage denominator. Do not achieve brevity by hiding decisive evidence or shrinking labels.

Keep interpretation-changing caveats beside claims; defer lookup-only detail and omit generic disclaimers. Examples and transitions can reduce reader effort without adding new facts. Any review request to add content must name the concrete misunderstanding prevented; completeness alone is insufficient.

The existing reader/source/visual responses must complete their `reader_value` fields. `build_review_packet.py` creates `reader-value-inputs.json`; pass it to `aggregate_reviews.py --reader-value-inputs`. Missing, stale, unanchored or unresolved evidence blocks aggregation and final artifact verification. This uses the same three roles and existing retry limits. Fast mode must use the same axes in its disclosed self-check, never claim independent review.

For explicitly requested Fast mode, run `editorial_gate.py prepare-fast --text FINAL_TEXT --source SOURCE --renders PREVIEW --output CHECK_DIR` (repeat file flags as needed). Complete its three role-specific records yourself, without launching reviewers. Run `aggregate_reviews.py CHECK_DIR/reader.json CHECK_DIR/source.json CHECK_DIR/visual.json --reader-value-inputs CHECK_DIR/reader-value-inputs.json --self-check --output RESULT.json`, then `editorial_gate.py verify-fast` with the same current file flags and `--result RESULT.json`. Missing/failed/stale records block this path too. It verifies editorial self-checks only; preserve all existing Fast hard gates and disclose skipped independent review.

For scoped updates, `plan_review_scope.py verify` also requires `editorial_inputs` and `reader_value` in the existing receipt, bound to its `plan_id`. Use `reader_value.template` with expression/selection/meaning/unit_roles/presentation. Input entries use path and SHA256 and must match the after-snapshot content/source/render layers. Reuse unchanged semantic explanations after verifying their layer hashes; inspect changed rendering afresh. This adds no reviewer or retry round and cannot be bypassed with bare PASS flags.

Edit only after the source-grounded reader narrative is complete.

1. Scan the stable draft for empty abstraction, template-driven structure, purposeless repetition, rhetorical overstatement, audience/channel mismatch, and visual packaging without reader value. This is expression review, not AI-authorship detection.
2. In existing validation notes, record completion (including no issues found). For a detected signal record `location + quote -> reader impact -> confirmed/dismissed/unresolved -> smallest fix -> protected meaning`. An explicit user style mismatch can justify a local edit; "AI-like" alone cannot.
3. Merge confirmed issues and revise the smallest spans once before independent review. If specificity requires missing evidence, retain the uncertainty, shorten, or clarify; never fabricate a benefit.
4. Recheck protected relations, assertion ceilings, voice and intended action. Stop when the passage is clear, professional, and source-fit.

Do not force first person, slang, rhetorical questions, emotion, deliberate mistakes, varied punctuation, or a personal voice. Do not rewrite a clear passage merely because it contains one listed pattern.

Preserve the mandatory one-sentence judgment, one-picture summary and key-question
table. They serve different reading tasks; repeating a conclusion across them
is not automatically redundant. Generic headings need changing only when they
hide the real section question or duplicate another label without a distinct
job. Repeated layouts, three peer blocks, a numbered procedure and professional
terms can all be appropriate. Judge actual reading effort, not form counts.

Reuse the Reader reviewer for abstraction, repetition, structure and register;
Source for rhetorical overstatement and preserved meaning; Visualization for
empty packaging and reading obstacles. Each expression issue must quote or
locate the element, name its reader impact and give the smallest fix plus meaning
to protect in existing check reasons/issues. Pure style preference cannot fail
publication or trigger another round. Material reader or fidelity failures use
existing gates and retry limits. A changed artifact follows scoped revalidation;
never reuse a pass for a changed layer. No new reviewer or extra retry budget.

## Make Value Expressions Concrete

Apply this rule to a title, subtitle, section heading, opening judgment, or product/value line that tells the reader why something matters.

1. Use the existing object-action/result map and protected relations to identify the specific object and supported fact, question, change, condition, tradeoff, or impact. A result is optional when the source gives none.
2. Express the relationship that matters to the reader with the fewest necessary words. A single fact may stay a single fact. Use parallel clauses only for a real comparison on shared dimensions; do not invent an opposite, a winner, or a causal mechanism. Neither a one-sentence limit nor a memorable slogan is a goal.
3. Remove method labels, process narration, and generic benefit words only when they add no necessary meaning. A line that says only `更清晰`, `更高效`, `赋能`, or `不用猜` must be rewritten when the source provides the actual object and result.
4. Keep a method name, technical term, scope, evidence boundary, or uncertainty when it is the decision object or needed to interpret the result. Do not invent an outcome, user effect, magnitude, or certainty to make the line sound concrete.
5. Layer supporting evidence and explanation after the lead, but keep any qualifier that changes its interpretation in the lead or immediately adjacent. Preserve subject, direction, comparison basis, scope, time, and uncertainty; do not turn a local observation into a general law. The visual must express the same supported relationship and boundaries.
6. Read the lead with its adjacent qualifiers, without the full body. The target reader should be able to restate what happened, the relationship, and when it applies. Verify that restatement against the source in the existing reader/source reviews. Stop when it is accurate and easy to understand; rhythm, symmetry, and word count alone do not justify another revision.

For example, `本轮灰度中，审核从五步减为三步，错误率未见明显变化` may become `本轮灰度减少了审核步骤，尚未观察到错误率明显变化`, with the counts in the support. It cannot become `流程越简单，质量越稳定`. A and B having different strengths supports a tradeoff, not an invented recommendation.

## Prevent False Positives

Treat expression and readability patterns as signals, not banned forms. Sentence
or paragraph length, topic shifts, relationship load, and typography metrics are
actionable only when the target reader's actual task is impaired in context.
Keep the original when a phrase or passage:

- is a defined technical, legal, academic, metric, or product term;
- accurately marks uncertainty, source identity, or causal limits;
- is the clearest label for a real structure or process;
- matches the source language and document genre;
- does not obstruct the reader's understanding.

Deterministic checks distinguish:

- **Hard failure**: fabricated or unsupported content, relation drift, assertion above evidence, source-language error, appendix leakage, or missing mandatory contract fields.
- **Warning**: clustered vague language, mechanical transitions, inflated rhetoric, repetitive sentence framing, overloaded relationships, paragraph topic drift, or another scene-dependent readability risk.

Warnings require contextual judgment and do not block release by themselves.

## Bidirectional Validation

Maintain three evaluation classes:

- `should_fix`: clustered expression problems that reduce clarity or credibility.
- `should_not_fix`: legitimate professional prose, uncertainty, passive voice, terminology, punctuation, and concise structure.
- `relation_preservation`: cases where subject, action, object, scope, state, number attachment, or causal strength must not change.

Run the fidelity pass before the expression pass. A more natural draft fails when it loses or strengthens source meaning. Reviewers must be able to explain both why a change is necessary and why untouched professional language was correctly preserved.

For generation regression, use `semantic_cases` in `evals/expression_cases.json`. Give a fresh producer only the instructions, request, and source; keep expected behaviors for a separate reviewer. Existing script checks cover structure and signals, not semantic correctness. Reuse the reader/source review rather than adding a publication round.

## Explicit Rejections

Do not optimize for AI-detector scores. Do not fabricate specificity. Do not apply global bans on adverbs, passive voice, punctuation, headings, or individual words. Do not imitate a named person's voice. Do not import a long-form publishing, persona-cloning, or external-research pipeline into a source-summary task.
