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

Edit only after the source-grounded reader narrative is complete.

1. Identify the concrete reading problem: ambiguity, repetition, vague abstraction, mechanical sequence, unsupported certainty, or missing actor.
2. Change the smallest span that resolves that problem.
3. Recheck the protected relation and assertion ceiling.
4. Stop when the passage is clear, professional, and source-fit.

Do not force first person, slang, rhetorical questions, emotion, deliberate mistakes, varied punctuation, or a personal voice. Do not rewrite a clear passage merely because it contains one listed pattern.

## Prevent False Positives

Treat expression patterns as clusters, not banned words. A style warning is actionable only when multiple signals create real reader friction in context. Keep the original when a phrase:

- is a defined technical, legal, academic, metric, or product term;
- accurately marks uncertainty, source identity, or causal limits;
- is the clearest label for a real structure or process;
- matches the source language and document genre;
- does not obstruct the reader's understanding.

Deterministic checks distinguish:

- **Hard failure**: fabricated or unsupported content, relation drift, assertion above evidence, source-language error, appendix leakage, or missing mandatory contract fields.
- **Warning**: clustered vague language, mechanical transitions, inflated rhetoric, repetitive sentence framing, or other scene-dependent expression risk.

Warnings require contextual judgment and do not block release by themselves.

## Bidirectional Validation

Maintain three evaluation classes:

- `should_fix`: clustered expression problems that reduce clarity or credibility.
- `should_not_fix`: legitimate professional prose, uncertainty, passive voice, terminology, punctuation, and concise structure.
- `relation_preservation`: cases where subject, action, object, scope, state, number attachment, or causal strength must not change.

Run the fidelity pass before the expression pass. A more natural draft fails when it loses or strengthens source meaning. Reviewers must be able to explain both why a change is necessary and why untouched professional language was correctly preserved.

## Explicit Rejections

Do not optimize for AI-detector scores. Do not fabricate specificity. Do not apply global bans on adverbs, passive voice, punctuation, headings, or individual words. Do not imitate a named person's voice. Do not import a long-form publishing, persona-cloning, or external-research pipeline into a source-summary task.
