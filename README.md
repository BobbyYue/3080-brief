# 3080 Brief

**30-second judgment, 80% in one picture**

[![CI](https://github.com/BobbyYue/3080-brief/actions/workflows/ci.yml/badge.svg)](https://github.com/BobbyYue/3080-brief/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Source-grounded decision briefs that help readers understand the conclusion quickly and see the argument as one auditable visual.

[Chinese (Simplified)](README.zh-CN.md)

`3080-brief` turns a source document into a new, reader-first brief without modifying the source. The result is organized around four reader-facing elements:

1. one primary judgment sentence followed by 1–3 short evidence, action, or boundary support lines;
2. one clear storyline that helps readers untangle the source's logic;
3. one auditable visual covering at least 80% of value-weighted, non-appendix claims;
4. one key-question table answering what readers are most likely to ask.

## Why use it

- Reader-first: reorganizes the source around what readers need to understand, trust, decide, or do.
- Core-value extraction: separates decision-critical conclusions, evidence, risks, and actions from background noise and implementation detail.
- Clear storyline: turns fragmented or technical source logic into a coherent argument whose headings make the reasoning easy to scan.
- Fast understanding: combines a 30-second judgment, one-picture summary, and key-question table so readers can grasp the main line quickly.
- Reliable delivery: keeps claims traceable, preserves the source, matches the output format, and applies deterministic review gates.

## Install

`3080-brief` follows the open [Agent Skills](https://agentskills.io/) folder format. It can be used by any agent that supports this format; the install command, skills directory, and reload behavior vary by client. See the official [client showcase](https://agentskills.io/clients) for client-specific documentation.

### Option 1: ask your agent

Send this instruction to an agent that can install skills from GitHub:

```text
Install the Agent Skill from https://github.com/BobbyYue/3080-brief,
using the complete subdirectory skills/3080-brief and register it in your Skill registry.
Then run its Feishu dependency check, show me one complete plan for every missing dependency,
and ask once whether to install all of them. If I approve, install every listed item without
separate per-item approvals, including registering beautiful-feishu-whiteboard as an independent
Skill. If I decline, keep 3080-brief installed but leave Feishu output blocked.
```

### Option 2: install the folder manually

```bash
git clone --depth 1 https://github.com/BobbyYue/3080-brief.git
cp -R ./3080-brief/skills/3080-brief "<YOUR_AGENT_SKILLS_DIR>/3080-brief"
```

Windows PowerShell:

```powershell
git clone --depth 1 https://github.com/BobbyYue/3080-brief.git
Copy-Item -Recurse ./3080-brief/skills/3080-brief "<YOUR_AGENT_SKILLS_DIR>/3080-brief"
```

Replace `<YOUR_AGENT_SKILLS_DIR>` with the user-level or project-level skills directory documented by your agent. Copy the **entire** `skills/3080-brief` folder—not only `SKILL.md`—because the skill also uses its `scripts/`, `references/`, `config/`, and `evals/` resources. Reload or restart the agent if its documentation requires it.

### Option 3: upload in a web or desktop client

Download the [latest release](https://github.com/BobbyYue/3080-brief/releases/latest), extract it, and upload `skills/3080-brief` through the client's Skill import UI. Do not upload the repository root unless the client explicitly supports repository subpaths.

After any installation method, the agent should run the dependency check and use one bundled approval before declaring Feishu output ready.

### Verify the installation

Confirm that the installed skill root contains `SKILL.md`, then ask:

```text
Use $3080-brief to turn this document into a reader-first decision brief.
```

If an agent does not natively support Agent Skills, provide the complete skill folder as project context and instruct it to follow `SKILL.md`. Core instructions remain usable, but automatic discovery, conditional resource loading, script execution, and dependency approval depend on the host agent.

## Try it

Explicit invocation:

```text
Use $3080-brief to turn this document into a reader-first decision brief.
Keep the source unchanged and create the output in the same format.
```

Natural-language invocation:

```text
Create a new reader-first brief from this proposal: make the conclusion clear
in 30 seconds, cover the core information in one picture, and use one table
to answer readers' most important questions.
```

It should not trigger for source editing in place, generic summaries without the reader/visual contract, or standalone whiteboard styling.

## Requirements

Core validation is offline and uses Python 3.9+ with no third-party Python packages.

Feishu/Lark output additionally requires:

- Node.js 20+;
- `@larksuite/cli` / `lark-cli` 1.0.60+;
- `@larksuite/whiteboard-cli` exactly 0.2.11 in the isolated 3080 tool cache;
- [`beautiful-feishu-whiteboard`](https://github.com/zarazhangrui/beautiful-feishu-whiteboard) 1.1.1+;
- Feishu/Lark authentication and the required document permissions.

Missing Feishu dependencies block only the Feishu path. The skill displays the exact source, version, known network/file effects, and either an approval command or a host-native registration request. It does not silently install dependencies.

The installation-time dependency check produces one approval bundle covering every listed missing Feishu dependency. One explicit yes authorizes all displayed CLI commands and the independent registration of [`beautiful-feishu-whiteboard`](https://github.com/zarazhangrui/beautiful-feishu-whiteboard); it must not trigger repeated per-item approvals. A decline keeps the core Skill available and Feishu output blocked.

`3080-brief` never guesses a Skill registry from its execution directory because managed agents may run scripts from a disposable checkout. If the host does not expose a verified registry root, it uses that agent's native installer/import UI. An archive copy remains pending—not `PASS`—until the agent reloads and the dependency check succeeds from its normal runtime. For hosts that explicitly expose a persistent registry, set `BRIEF3080_SKILL_INSTALL_ROOT`.

Node.js installation without a known platform command, plus Feishu/Lark login and permission grants, remain separate because their undisclosed system or account effects cannot be covered safely by the bundle approval.

## Development verification

Run the complete offline test suite:

```bash
bash skills/3080-brief/scripts/self_test.sh
```

Check the single-owner capability ledger and runtime context budget directly:

```bash
python3 skills/3080-brief/scripts/check_context_budget.py skills/3080-brief --json
```

Check the current Feishu dependency state without installing anything:

```bash
python3 skills/3080-brief/scripts/check_dependencies.py --mode feishu --json
```

## Repository layout

```text
skills/3080-brief/   installable Agent Skill
.github/workflows/   offline CI
```

User-facing project documentation stays at the repository root; runtime instructions stay inside the installable skill.

## Privacy and limitations

- Never publish source document tokens, tenant identifiers, credentials, or real internal metrics in issues or examples.
- Feishu installation approval is separate from Feishu authentication approval.
- Independent reviewer and blind-reader claims are made only when those capabilities actually ran.
- The repository does not include with-skill/without-skill benchmark claims.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please report security-sensitive findings through the private process in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
