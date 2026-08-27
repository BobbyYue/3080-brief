# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.8.0] - 2026-08-27

### Added

- Added four reader outcomes to the existing TLDR, heading readback, Blind Reader, and audit flow: readers must be able to access, find, understand, and use task-critical information.
- Added mutable-source metadata to the source inventory, including actual observation time and only source-visible publication, update, or version markers.
- Added a proximity-hierarchy gate to the existing full-page replay so labels, captions, sources, and major reader questions remain visibly grouped.

### Changed

- Treat sentence relationship load, paragraph topic drift, prose measure, and preferred typography values as contextual risk signals rather than automatic rewrite or release failures.
- Kept the existing three reviewers and repair limit; the new checks reuse current review packets and full-page replay without adding another agent pass or review round.

## [0.7.0] - 2026-08-21

### Added

- Added layer-hashed scoped revalidation for source, content, core visual, desktop layout, and mobile layout.
- Added `plan_review_scope.py` with `snapshot`, `plan`, and `verify` commands so later revisions preserve unaffected PASS results and stop when the required scope passes.
- Added regression coverage proving that mobile-only repairs require only target validation, mobile geometry, and mobile visual review, while source or content changes still restart the complete audit.

### Changed

- Replaced the global package-hash reset with change-impact review planning after the first complete audit.
- Removed the arbitrary limit on supporting blocks; one dominant anchor remains required, while support count now follows evidence value and rendered readability.
- Neutral categories now use distinct theme accents without implying favorable, unfavorable, warning, or unknown meaning.

### Fixed

- Made key-question and body tables readable at 390 px by rendering labeled vertical rows instead of hiding decision-critical columns behind horizontal interaction.
- Extended HTML geometry validation to key-question tables, table cells, and full-document horizontal overflow on desktop and mobile.
- Kept observed actor shares semantically neutral while applying favorable styling consistently to source-supported task-value increases.

## [0.6.0] - 2026-08-20

### Added

- Added a signed canonical HTML composer contract, input hashes, and a build receipt so hand-authored or post-build-modified HTML cannot reuse a passing review state.
- Added browser geometry evidence and an isolated Full-page Visual Replay covering title hierarchy, TLDR distinction, heading narrative, page rhythm, one-picture dominance, overlap, and clipping.
- Added an `HTMLPAGE-01` capability contract and regression coverage that locks full-page evidence into review readiness, reviewer packets, and final artifact verification.

### Changed

- Reworked the HTML shell into a report-level composition with a stronger title field, readable prose measure, deliberate section rhythm, integrated figures, and layout families that materially affect the page.
- Updated Standard and Strict flow documentation to run applicable visual replays and Blind Reader Replay before the final three-reviewer audit.
- Public CI now executes the canonical offline suite directly instead of maintaining a second runtime implementation.

### Removed

- Removed the obsolete public-only `run_3080.py` state-machine wrapper and its duplicate acceptance/runtime tests; canonical skill scripts are now the only behavior source.

## [0.5.0] - 2026-08-20

### Added

- Added a mandatory execution-efficiency contract that completes source and review inputs before rendering, keeps multiple briefs in isolated lanes, and reruns deterministic checks by change impact.
- Added a hash-bound review-readiness validator; incomplete or changed source, draft, render, or validation inputs now block independent review packet creation.

### Changed

- Moved full-artifact Blind Reader Replay before the final three-reviewer audit so known comprehension problems are resolved before an expensive audit batch.
- The normal path now uses one complete parallel audit batch per stable artifact. When it fails, all feedback is merged into one revision before the next hash-locked batch.

## [0.4.0] - 2026-08-20

### Added

- Added a mandatory reading-path contract to every generated brief, including the reader decision, the question each section answers, and a declared density level for each section.
- Added permanent regression cases for missing reading paths, incomplete section maps, and consecutive dense evidence blocks without an explanatory bridge.

### Changed

- HTML generation now carries the validated reading path into section attributes and stable light, balanced, or dense spacing classes.
- Brief and HTML validation now block evidence-first sections, incomplete reading paths, and unregistered dense-block sequences instead of treating layout as optional guidance.

## [0.3.0] - 2026-08-20

### Added

- Bundled an offline HTML Design Kit with local fonts, ECharts, Mermaid, semantic HTML, and a native-SVG fallback; self-contained HTML no longer depends on external runtime assets.
- Added an isolated one-picture Visual Blind Replay before audit review, including a hash-bound replay packet, validator, schema, and regression coverage.
- Added a public Standard-profile state-machine smoke test that exercises HTML generation, stage ordering, review, reader replay, and final delivery receipts.

### Changed

- Expanded the shared visual specification and HTML renderer so Feishu and HTML use the same composition, theme, semantic colors, visible values, metric scope, and evidence mapping.
- Enforced the runtime order `visual replay → three audit reviewers → Blind Reader Replay`; the public runner now blocks reader replay before audit PASS and records Fast-mode omissions explicitly.
- Added content-fit HTML layout, typography, density, renderer, anchor, and fallback planning with deterministic validation.
- Extended acceptance receipts to require Visual Blind Replay and Blind Reader Replay PASS for Standard host certification.

### Fixed

- Replaced sparse or text-heavy HTML one-picture layouts with richer quantitative and structural encodings when the source supports them.
- Aligned the public resumable runner with the current validator CLIs, HTML design plan, one-picture preview, reviewer packet hashes, and conditional reader escalation.

## [0.2.2] - 2026-08-19

### Fixed

- Enforced source-language parity across the title, TLDR, table, body, and one-picture visual unless the user explicitly requests a different language.

## [0.2.1] - 2026-08-19

### Fixed

- Aligned HTML one-picture output with the Feishu visual contract: both now require one explicit composition, render every declared label/value, reject title-only or overly tall sparse visuals, and use a compact stage-story layout for multi-stage processes.

## [0.2.0] - 2026-08-18

### Added

- Added a source-linked Claude Code article example with a 30-second judgment, one-picture summary, key-question table, storyline, and evidence boundary.
- Added an explicit original-article versus 3080-output comparison built from a real webpage screenshot.

### Changed

- Reworked the runtime into a resumable, fail-closed state machine: source grounding, preflight, review-draft creation, review, and final delivery are ordered checkpoints, and success requires a machine-generated PASS delivery receipt.
- Added source-before/source-after hash verification, live Feishu document and whiteboard evidence, native-whiteboard enforcement, and automatic invalidation when frozen artifacts change.
- Added distinct reviewer execution IDs; Standard/Strict reject three reports from one execution context, while explicitly selected Fast retains three structured role-separated self-checks.
- Added source-relation, evidence-ceiling, thin-source, and contextual expression checks without introducing blanket style bans.
- Added a simulated end-to-end state-machine test covering native whiteboard delivery, plus failure cases for image substitution and non-independent review.
- Added executable host-capability gates for `lark-doc` and `lark-whiteboard`; loading Skill specifications no longer counts as Feishu runtime readiness, and a run cannot complete without a real new-document link.
- Replaced the Codex-only installation flow with agent-agnostic GitHub, manual-folder, and upload instructions for Agent Skills-compatible clients.
- Replaced the Codex-only `beautiful-feishu-whiteboard` dependency installer with a verified GitHub archive installer for hosts that explicitly expose a persistent Skill registry.
- Stopped inferring a host Skill registry from the script path; managed agents now request native registration unless a persistent registry root is explicitly provided, and file installation remains pending until a runtime recheck passes.
- Added an installation-time approval bundle so one explicit user approval covers every displayed missing Feishu dependency and companion-Skill registration action, without repeated per-item prompts.
- Made the English README fully English, including its language link and natural-language trigger example.
- Reorganized both READMEs around value, real output, and a two-step quick start; moved detailed installation and dependency guidance into expandable sections.
- Expanded repository wording for discovery through AI Agent Skill, executive summary, decision brief, visual summary, one-pager, and document summarization use cases.

### Removed

- Removed the ambiguous synthetic evaluation graphic from both READMEs and deleted its unused asset.

## [0.1.0] - 2026-07-13

### Added

- Unified brand subtitle: `30-second judgment, 80% in one picture`.
- Reader-first 3080 brief workflow with a three-unit TLDR contract.
- Value-weighted source claim ledger and 80% visual coverage gate.
- Feishu/Lark, Word, and Markdown output routing.
- Deterministic preflight, three-role review packets, and blind-reader replay protocol.
- Balanced trigger evaluation fixtures and offline self-test.
- Approval-gated dependency diagnostics for Feishu CLIs and `beautiful-feishu-whiteboard`.
- Bilingual project documentation and GitHub community files.

### Changed

- Defined “一句话” as one primary judgment sentence plus 1–3 evidence/action/boundary support lines, and connected that contract to Markdown/XML preflight fixtures.
- Replaced three mandatory runtime documents with one compact `SKILL.md` execution kernel and conditional reference routing.
- Added a 12-capability single-owner contract plus CI-enforced 15KB/200-line context budget.
- Retired the duplicated `runtime-core` and user-supplement synchronization chain after migrating their unique rules.
