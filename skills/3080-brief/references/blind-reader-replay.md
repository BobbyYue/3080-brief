# Blind Reader Replay

Use Blind Reader Replay to test what readers actually understand, not what an auditor predicts they should understand. Blind readers are test participants, not reviewers: they replay their understanding and expose questions; they do not grade themselves or edit the draft.

## Entry Gate

Run Blind Reader Replay only after the deterministic preflight passes and all three audit reviewers return `PASS` for the same artifact-set ID. Start with the Primary Blind Reader alone against that reviewer-approved rendered artifact. Launch the Technical and Decision blind readers in parallel only when an escalation condition is met. Do not run blind readers in parallel with the audit reviewers by default.

If any replay exposes a blocking comprehension failure, revise the artifact and restart from deterministic preflight and all three audit reviewers. Run Blind Reader Replay again only after the revised artifact passes all three audit reviewers.

## Isolation

- Give each blind reader only its role definition and the rendered reader-facing artifact for the current artifact-set ID.
- Do not provide the source, claim ledger, source inventory, visual spec, expected answer, reviewer packet, or any reviewer/blind-reader opinion.
- Do not answer clarification questions during the replay. Record unresolved questions as test output.
- Run every selected blind-reader role independently. When escalation is required, launch the Technical and Decision roles in parallel; do not reveal the Primary replay, another role's replay, or any reviewer opinion to them.
- Keep the role labels inside the validation process; do not add audience labels such as `给管理者` or `给 RD` to the generated document.

## Roles

### Primary Blind Reader

**Role definition:** 理解业务、产品和常见指标，不了解技术实现，无决策能力。

阅读文档后，根据具体内容自行提出并回答最关心的三个问题。

### Technical / Development / RD

**Role definition:** 具备相关领域的专业知识和通用技术能力，注重底层逻辑和可行性。

阅读文档后，根据具体内容自行提出并回答最关心的三个问题。

### Direction / Priority / Resource / Risk Decision Maker

**Role definition:** 阅读时间有限，不具备项目隐含背景，不希望先阅读实施细节，注重收益和成功的可复制性。

## Dynamic-Question Contract

- Each role must independently derive and answer exactly three questions from the specific document.
- Do not provide preset question categories, example questions, fixed dimensions, sentence stems, or an expected answer.
- Questions must reflect what this role genuinely cares about in this document, not a generic checklist.
- Prefer source-specific objects, changes, metrics, scenarios, or decisions in the wording when the document makes them available.
- A question may identify missing information. Answer `文档未说明` / `not stated in the document` instead of inventing context.
- Do not force the three roles to ask different questions. Natural overlap is useful evidence of shared reader priority.

## Escalation Gate

After the Primary replay returns, launch both the Technical and Decision blind readers when any one condition is true:

- The document itself addresses multiple functions.
- The Primary reader cannot correctly replay a P0 core conclusion.
- The Primary reader cannot identify the next action.
- The Primary reader cannot judge whether the document's conclusion is high-value or low-value.
- The Primary reader cannot judge whether the document's conclusion is feasible or infeasible.
- The conclusion affects resources, risk, or broad rollout.

Escalation is not itself a document failure. Evaluate the additional independent replays before deciding whether the issue is a comprehension defect, a source-information gap, or an appropriate role boundary. The Technical and Decision readers must receive only their role definitions and the same reviewer-approved artifact; do not include the Primary reader's replay or the condition that triggered escalation.

## Replay Output

Return the role, artifact-set ID, and three question-answer pairs. For each answer, distinguish document-stated understanding from reader inference and state any material uncertainty. Do not return `PASS` or `FAIL`.

```json
{
  "reader_role": "primary | technical | decision",
  "artifact_set_id": "sha256-derived ID",
  "questions": [
    {
      "question": "document-specific question",
      "answer": "reader's own-word replay",
      "inference_or_uncertainty": "none, inference, or unresolved gap"
    }
  ]
}
```

## Evaluation

After all replays arrive, the main agent compares them with the hidden P0/P1 claim ledger and user intent. A replay exposes a blocking comprehension failure when it reverses or misses a decision-changing P0 claim, invents a material causal/quantitative/action claim, cannot identify the document's central value, or reveals that a required action/boundary is materially ambiguous.

Revise only the document defects revealed by the replay. Do not add unsupported information, satisfy every reader preference, or expand the brief merely because a secondary detail was not recalled. After a blocking replay-driven revision, re-run preflight and all three audit reviewers. Once they all pass, restart with the Primary Blind Reader; apply the escalation gate again rather than automatically launching all three roles.
