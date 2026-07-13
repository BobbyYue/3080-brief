# Contributing

Thanks for helping improve `3080-brief`.

## Before opening a change

- Use an issue for behavior changes, new output formats, or changes to the source-grounding contract.
- Never attach confidential source documents, document tokens, tenant identifiers, credentials, or real internal metrics.
- Keep repository documentation outside `skills/3080-brief/`; the installable skill must contain runtime-essential files only.

## Local validation

Run the complete offline suite from the repository root:

```bash
bash skills/3080-brief/scripts/self_test.sh
```

The suite must remain Python-standard-library-only. Optional Feishu adapters may be absent in CI and must be reported as `SKIP`, not `PASS`.

Keep `SKILL.md` within the budget declared in `evals/capability_contract.json`. Add or move detail through conditional references instead of introducing another mandatory runtime file. Every P0 behavior change must update its capability owner or enforcement artifacts.

When changing triggers, update `evals/trigger_cases.json` without weakening the balanced 10-positive/10-negative contract. When changing output behavior, add or update a synthetic fixture.

## Pull requests

- Explain the reader problem and the behavior change.
- List the validation commands you ran.
- Call out changes to dependencies, network access, permissions, or user approval flows.
- Keep generated or local state such as `.sync-state/`, caches, and credentials out of the commit.
