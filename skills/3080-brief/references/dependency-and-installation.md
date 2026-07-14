# Dependency Gate And Installation Approval

Read this file when a Feishu/Lark output needs `lark-cli`, the pinned whiteboard renderer, or `beautiful-feishu-whiteboard`, or when dependency diagnostics return `BLOCKED`, `SKIP`, or `FAIL`.

## Status Contract

- `PASS`: the CLI command or skill contract exists, its path and version were verified, and the applicable smoke/contract test passed.
- `SKIP`: an optional adapter is unavailable but the current non-Feishu task can continue.
- `BLOCKED`: the current Feishu task requires a missing/incompatible adapter or an approved installation.
- `FAIL`: an installed/core dependency is broken or below the required version.
- Never report `SKIP` or `BLOCKED` as `PASS`.

Run the core offline check for development and self-test:

```bash
python3 scripts/check_dependencies.py --mode core
```

Before fetching or writing a Feishu/Lark output, run:

```bash
python3 scripts/check_dependencies.py --mode feishu --json
```

## Approval Flow

When `installation_request.required` is true:

1. Show the user every missing dependency, exact npm package version or GitHub skill source/minimum version, every known install root/network/file/restart effect, and either the approval command or `host_install_prompt` from the diagnostic JSON.
2. Ask for explicit installation approval. A request for a Feishu document is not installation approval.
3. Do not call the installer in the same turn before approval.
4. If `host_registration_required` is true, do not run a local file installer. After approval, use the current host's native registry/import capability to install `host_install_prompt`; if no such capability is callable, present the prompt to the user and keep the task `BLOCKED`.
5. Otherwise, after approval, run only the diagnostic-provided `approval_commands`, which include `--user-approved`; do not add this flag without the user's explicit approval.
6. Treat `FILES INSTALLED AND VERIFIED` only as `PENDING_RUNTIME_RECHECK`, never as dependency `PASS`.
7. Tell the user to reload or restart the current agent. Then re-run `check_dependencies.py --mode feishu --json` from its normal registered runtime and continue only when every required CLI and skill returns `PASS`.

The installer uses an isolated user cache (`$BRIEF3080_TOOL_CACHE` or `${XDG_CACHE_HOME:-~/.cache}/3080-brief/tools`) and exact npm package versions. It must not add `node_modules` to the skill or repository.

Never infer a Skill registry from the directory that happens to execute the script: managed agents may run installation code from a disposable checkout. By default, request host-native installation of `https://github.com/zarazhangrui/beautiful-feishu-whiteboard` at ref `main`. Use the portable file installer only when the host explicitly provides a persistent registry through `--skill-install-root`, `--install-root`, or `BRIEF3080_SKILL_INSTALL_ROOT`. It validates archive paths plus `SKILL.md`, declared version `1.1.1` or newer, `CATALOG.md`, `RULES.md`, and `templates` before an atomic write, and never overwrites an existing destination.

If Node.js/npm is absent, show that prerequisite and request a separate platform-appropriate Node.js 20+ installation approval. Do not guess or silently run an OS package manager.

## Decline Or Failure

- If the user declines or has not reloaded the current agent after a new skill installation, keep the Feishu output `BLOCKED`; do not silently publish an unverified board.
- Offer Markdown/Word only as an explicit user choice, not an automatic fallback.
- If installation or smoke testing fails, report the exact failed command/status and keep the task `BLOCKED`.

## Installation Is Not Authentication

Installing `lark-cli` does not approve application configuration, scopes, or user login. After installation, follow `lark-shared` for `config init`, minimum-scope authorization, QR-code forwarding, and split-flow authentication. Never reuse installation approval as authentication approval.
