# Visual Blind Replay

Use this gate to test whether the one-picture summary communicates by itself. It is separate from the Visualization Reviewer: that reviewer sees the visual spec and evidence map, while the visual blind reader must not.

## Position In The Flow

In Standard and Strict modes, run Visual Blind Replay after deterministic render validation and before building the three audit-review packets. This catches a weak visual argument before the expensive audit loop. Fast mode may replace it with a disclosed self-check, but must not claim independent visual comprehension validation.

If the replay fails, revise the visual hierarchy, relationship, encoding, labels, or evidence selection; rerun deterministic visual gates and Visual Blind Replay. Do not start the three audit reviewers until it passes.

## Isolation

- Give the reader only the cropped one-picture render at normal document width and a role definition: a cross-functional reader who understands ordinary business/product metrics but has not seen the source or brief.
- Do not provide TLDR text, body, source, claim ledger, `visual_spec.json`, `html_design.json`, alt text, expected answer, coverage report, reviewer packet, nearby files, or prior comments.
- The image must include exactly what a normal reader sees inside the figure: visible figure title, marks, labels, annotations, and source/boundary note. Do not add explanatory text for the replay.
- Use `scripts/build_visual_replay_packet.py` so the image hash and isolation contract are fixed before delegation.

## Blind Reader Output

The reader returns JSON only and does not grade the visual:

```json
{
  "reader_role": "visual_blind",
  "visual_artifact_id": "sha256 of the supplied image",
  "review_round": 1,
  "main_judgment": "the one conclusion understood from the image",
  "supporting_evidence": ["visible evidence 1", "visible evidence 2"],
  "next_action_or_boundary": "what the reader thinks should happen next, or the decision-changing boundary",
  "reading_path": "the order in which the image was read",
  "unresolved_confusion": []
}
```

Do not include claim IDs, hidden expected answers, `PASS`, or `FAIL` in the blind reader prompt or response.

## Main-Agent Evaluation

After the replay returns, compare it with the hidden claim ledger and visual spec. Record the raw replay plus an evaluation conforming to [visual-replay.schema.json](visual-replay.schema.json), then run:

```bash
scripts/validate_visual_replay.py visual_replay.json --visual-preview ONE_PICTURE.png --claim-ledger claim_ledger.json --visual-spec visual_spec.json
```

PASS requires all of the following:

- the replay identifies a mapped P0 main judgment carried by the anchor;
- visible evidence correctly supports that judgment rather than listing unrelated facts;
- a mapped action or decision-changing boundary is understood when the visual contains one;
- the reader can describe a coherent reading path without relying on hidden prose;
- no material direction, actor, object, number, or scope is reversed or invented;
- any unresolved confusion is recorded, and none would change the intended decision.

FAIL when the reader can only inventory panels, reads the figure as a table of facts, cannot connect evidence to the conclusion, misses the action/boundary, or needs the surrounding TLDR/body to explain the picture. Classify fixes as hierarchy, relationship, encoding, evidence selection, wording, or legibility. Do not add unsupported content merely to make the picture feel complete.
