## User Supplements and Limits

This section is synced from `docs/user-supplements-template.md` into runtime rules. Keep it compact: detailed methods belong in `references/`.

### Priority And Trigger

- Conflict priority: source truth -> explicit user requirements -> reader comprehension -> 30-second judgment -> one-picture 80% understanding -> professional expression and visual polish.
- Aesthetics must serve facts, evidence, comprehension, coverage, and risk boundaries.
- Trigger aliases: `3080-brief`, `3080 brief`, `3080skill`, `读者视角总结`, `3080总结`, `3080summary`, `3080-onepager`.
- Do not trigger for pure source polishing, generic summary without 3080/reader/visual requirements, or style-only whiteboard exploration that does not create a summary document.

### Reader-First Thinking

- Before drafting, identify what the source is about, reader layers, what each reader must understand/trust/decide/do, and what the reader should remember.
- Use reader-reception logic instead of author-output logic: reorganize by reader cognition path, information needs, blind spots, and decision demands.
- Ask before drafting when ambiguity affects the main conclusion, metric meaning, denominator, period, sample, scope, risk boundary, target reader, or next action. Prioritize questions by conclusion -> data -> risk -> reader/scenario -> concept.
- Non-blocking gaps may proceed only when labeled `原文未提供` / `not provided in the source` or `推断` / `inference`.

### Source And Output Constraints

- Never modify the source, including title, comments, existing whiteboards, attachments, permissions, or directory structure.
- Output type follows input type unless the user explicitly specifies otherwise: Feishu/Lark -> new Feishu/Lark doc, Word/docx -> new Word/docx, Markdown -> new Markdown. Ask if the input type or same-format output support is unclear.
- Output-language precedence is: explicit user instruction naming an output language -> source primary language -> ask when source-language primacy is ambiguous. The language of the user's request, conversation, interface, locale, or surrounding context is never an override by itself.
- Record `Source language`, `Output language`, `Output-language basis`, and exact `Explicit language override evidence` in `source_inventory.md`. Only `source_primary_language` and `explicit_user_request` are valid bases; phrases such as `Chinese context` are invalid.
- Apply the selected output language consistently to title, TLDR, key-question table, body, and visual. Keep source wording for proper nouns, internal names, metrics, and necessary mixed-language terms; lightly clarify only when needed without changing meaning.
- Preflight and reviewers must FAIL when output language differs from source primary language without exact explicit user evidence, when conversation language is used as the basis, or when the rendered draft/visual conflicts with the declared output language.
- Source link is mandatory and uses compact, low-emphasis metadata near the top. Apply exact heading restrictions from `config/3080-brief.json`.
- Generated time, owner, summary version, whiteboard version, location, permission, and sharing settings stay default unless requested, source-provided, or operationally necessary.
- Exclude source appendix / 附录 / Appendix content from TLDR, whiteboard, body, and review coverage unless the user explicitly asks to include appendix material.
- Keep process rationale, prompts, style names, tool notes, and internal method language out of the generated artifact; machine-enforced phrases live in `config/3080-brief.json`.
- Data, conclusions, context, risks, and recommendations must be traceable to the source; wording may be rewritten, but meaning and numbers must not change. Inferences are allowed only when clearly labeled.
- If sample size, denominator, period, significance, confidence interval, or metric scope is present, preserve it; if a critical data issue is missing or conflicting, ask or avoid using that data as sole evidence for the core conclusion.

### Token And Runtime Discipline

- Normal runs read `runtime-core.md` and `user-supplements-rules.md` first; do not read this template during normal execution.
- Build `source_inventory.md` first and use it for drafting, visual planning, and reviewer packets.
- Reviewer subagents should receive role-specific packets, not one generic packet or full source/XML/SVG by default.
- Second and later review rounds should pass only blockers, revision summary/diff, changed excerpts, and necessary unchanged snippets.
- Keep core self-validation offline and Python-standard-library-only; an unavailable optional validator must be reported as `SKIP`, never as `PASS`.
- Before any Feishu/Lark fetch or write, run the Feishu dependency diagnostic. Missing `lark-cli`, the pinned whiteboard CLI, or `beautiful-feishu-whiteboard` is `BLOCKED` for Feishu output but must not prompt users during non-Feishu tasks.
- When installation is required, show the exact CLI package version or GitHub skill source/minimum version, install root, network/file/restart effects, and every command; request explicit user approval and do not install in the same turn. After approval, install CLIs into the isolated user cache and install the skill through the official Codex skill installer, verify their contracts, and rerun the diagnostic. Restart Codex after a new skill install before continuing.
- Installation approval is not Feishu configuration or authentication approval. If installation is declined or fails, keep Feishu output blocked and offer another format only as an explicit user choice.

### TLDR Contract

- Title format: `3080 Brief｜原文标题`.
- `TLDR` is the first top-level section unless the user explicitly requests an equivalent localized title.
- `TLDR` contains exactly three content units: one-sentence summary, one-picture summary, and one key-question table.
- Treat the one-sentence summary as one Pyramid Principle opening unit. Use 2-4 short lines by default, one information unit per line, with structure adapted to the source type.
- Adapt the top judgment to source type: insight for data analysis, plan for product planning, go/no-go for experiment review, strategic change for proposals, current priority for status inventory, root cause for diagnosis, risk posture for risk reviews.
- The one-sentence summary should help readers form a judgment within 30 seconds: core conclusion, key evidence/value, and what to do/observe/validate/stop next. Put non-actionable caveats in the body unless they change the next action.
- The key-question table answers 3-5 reader questions and stays inside `TLDR`. Use `问题 / 结论 / 为什么` for Chinese and `Question / Conclusion / Why` for English; exact expression warnings and restrictions come from config/preflight.
- If a table cell visually exceeds about 3 lines, increase row height/spacing, split the row, or move detail into the body.

### Body Narrative

- 3080-brief is not compression; it rebuilds the source into a clear, evidence-backed, professional, useful reader narrative.
- The body has no fixed section order or mandatory modules. Choose structure from source logic, SUCCESs, Stepwise Information Delivery, and reader decision path.
- Body headings advance the narrative and remain scannable as a reasoning path; exact prohibited headings and audience labels live in config/preflight.
- Keep the key-question bridge inside the TLDR table; merge terminology into the answer where it helps comprehension.
- Choose prose, bullets, callouts, tables, charts, timelines, examples, or stories according to what reduces reader effort.
- When decision-relevant directional values/statuses appear, classify their business meaning before styling. Do not infer favorable/unfavorable from the mathematical sign alone. Color compact values or labels, not whole paragraphs, and retain signs/arrows/explicit wording as redundant cues.

### Visual And Whiteboard Rules

- The one-picture summary should cover at least 80% of value-weighted non-appendix claims: core conclusion, logic, evidence, and risk boundary. It does not need to cover execution details, appendix, or process discussion.
- Define the 80% target with a value-weighted claim ledger: P0 claims can change decision/trust/risk/action, P1 claims materially support them, and P2 claims are useful detail. Map every board block to claim IDs and do not silently omit P0.
- Visualization serves narrative and evidence; detailed visual failure patterns live in `references/expression-anti-patterns.md`.
- First inventory chartable data and relationships. If the source has 3+ quantitative claims or the main conclusion depends on quantitative evidence, the whiteboard must use at least one quantitative visual encoding beyond text cards.
- If key data lives in Sheet/chart/image/embedded objects and affects the conclusion, try to inspect it. If it cannot be reliably extracted, use a boundary/directional visual and state the limitation instead of pretending precision.
- Feishu/Lark output must use editable Feishu whiteboard elements. Word/docx and Markdown output must keep the one-picture summary visible and auditable, with SVG/chart data retained when practical.
- `image2` is optional inspiration only. It may influence composition, hierarchy, mood, or cover/illustration ideas, but must not carry evidence, numbers, formulas, chart labels, thresholds, risks, conclusions, or recommendations. The final 80% visual must be rebuilt as source-grounded editable whiteboard or auditable chart content.
- Never send internal source text, document links/tokens, real metrics, project/customer names, account identifiers, or code names to image generation. Use abstract placeholders only.
- Choose whiteboard style automatically from `beautiful-feishu-whiteboard/CATALOG.md` based on source type, tone, audience, information density, and user preference. Read only the selected `design.md`.
- Filter banned `beautiful-feishu-whiteboard` styles from `config/3080-brief.json`, the machine-readable source of truth. If requested, state that the style is unavailable for this skill and choose the closest allowed alternative.
- For multiple style outputs, each board must differ in narrative skeleton, reading path, layout density, color system, or emphasis method, not only palette.
- Use one semantic mapping across body and whiteboard for favorable, unfavorable, warning, neutral, and unknown states. The selected board style may change decorative colors but must not remap semantic colors; exact values live in `config/3080-brief.json`.
- Before finalizing, check overlap, clipping, text overflow, crowded spacing, and whether a reader can understand the core conclusion from the visual alone.

### Evidence, Risk, And Review

- The body expands what TLDR/whiteboard cannot carry: explanation, evidence, metric口径, risks, boundaries, and action, based on source need rather than a fixed format.
- If the source lacks business value or risk information, an inference may be included only when explicitly labeled.
- Three independent reviewer subagents are required before final release unless the user explicitly asks to skip/fast-track and accepts the risk.
- Reviewer roles: Reader Comprehension, Source Coverage And Grounding, Visualization And Expression.
- The main agent must not expose, quote, summarize, hint at, or use any reviewer comment in prompts to other reviewers before all three reports are submitted.
- Any `FAIL`, blocking issue, unsupported claim, or failed role gate must be fixed; then rerun all three reviewers, up to 3 rounds. If still blocked because source/user information is missing, stop and ask.
- Full Review is default for complex, high-risk, experiment/data, strategy, or management-facing documents. Light Review is allowed for low-risk short documents but still requires three independent PASS/FAIL verdicts.
- Visualization reviewer must FAIL if chartable metrics exist but the whiteboard is mainly boxes/prose without quantitative visual encoding, unless the draft explains that data cannot be reliably extracted or is not chartable.
- Visualization reviewer must FAIL if image2/bitmap output carries source-critical evidence, numbers, charts, risks, formulas, thresholds, or recommendations.
- Reviewer must FAIL when a classified decision-relevant value is unstyled in the body, conflicts with the whiteboard's semantic color, or relies on color alone.
- Reviewer packets must be role-specific and hash-locked: Reader gets the full readable draft, Source gets non-appendix outline plus P0/P1 excerpts, and Visualization gets preview plus visual spec/coverage/validation. All three must review the same artifact-set ID and round.
- Do not claim independent review when subagent capability is unavailable; disclose and escalate that limitation.
- After all three audit reviewers pass the same artifact set, run Blind Reader Replay sequentially, not in parallel with audit review. Start with the Primary role: `理解业务、产品和常见指标，不了解技术实现，无决策能力`.
- Each selected blind reader sees only the rendered reader-facing artifact, independently derives and answers exactly three document-specific questions, and must not receive source materials, expected answers, reviewer output, or another blind reader's replay.
- Launch Technical (`具备相关领域的专业知识和通用技术能力，注重底层逻辑和可行性`) and Decision (`阅读时间有限，不具备项目隐含背景，不希望先阅读实施细节，注重收益和成功的可复制性`) blind readers in parallel only when any escalation condition applies: multi-functional audience; Primary cannot replay the P0 conclusion, next action, value, or feasibility; or the conclusion affects resources, risk, or broad rollout.
- Blind readers do not grade PASS/FAIL. If replay exposes a blocking comprehension defect, revise and restart preflight plus all three audit reviewers before rerunning Primary Blind Reader Replay.

### Quality Bar

- First principle: let target readers make the intended understanding, judgment, or action at minimum cognitive cost.
- Good output is reader-first, purpose-first, conclusion-first, source-grounded, and structurally easier to navigate.
- A usable brief lets readers see the core conclusion/data within 30 seconds, follow the logic without jargon friction, remember at least one concrete case or scene, and know who should do what next.
- Use `references/expression-anti-patterns.md` for opening, heading, narrative, evidence-language, table, and visual failure patterns only when drafting/review signals require it.
- Use Novice Reverse Review as an independent check for terms, background, hidden assumptions, and likely reader questions; it should improve clarity without forcing audience labels into section headings.

### Reference Routing

- For detailed visualization patterns, read `references/visual-pattern-library.md`.
- For Feishu SVG/whiteboard build and style details, read `references/whiteboard-patterns.md`.
- For image2 boundaries, read `references/image2-auxiliary-rules.md`.
- For evidence/data/risk handling, read `references/evidence-and-risk-rules.md`.
- For reader narrative and common mistakes, read `references/reader-optimization.md`.
- For semantic wording, heading, table, narrative, and visual-expression failures, read `references/expression-anti-patterns.md` conditionally.
- For directional metrics, signed deltas, gains/losses, risk/exception states, or status judgments, read `references/semantic-color-system.md`.
- For full reviewer protocol/scoring, read `references/review-loop.md`.
- For post-review reader roles, isolation, escalation, output, and evaluation, read `references/blind-reader-replay.md`.
- For machine-readable thresholds, aliases, banned styles, and forbidden headings, read `config/3080-brief.json`.

### Examples To Learn From

- [待补充] 优秀原文链接：
- [待补充] 优秀新文档链接：
- [待补充] 优秀画板链接或截图路径：
- [待补充] 具体要学习的点：

### Open Questions

- Only ask when the answer can materially change the main conclusion, evidence interpretation, risk boundary, reader decision, or next action. Do not ask for author/reader roles or visual vibe when they can be inferred safely from the source and request.


