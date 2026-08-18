# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
