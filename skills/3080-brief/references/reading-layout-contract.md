# Reading Layout Contract

This contract turns document layout into a required part of every 3080 Brief run. It applies to Feishu/Lark, Word, Markdown, and HTML because every renderer consumes the same reviewed `brief.json`.

## Required Plan

Before rendering, write `brief.json.reading_path` with:

- `contract_version`: exactly `1.0`;
- `reader_decision`: the judgment or decision the intended reader must be able to make;
- `section_questions`: exactly one concrete reader question for each body section, in body order;
- `section_density`: exactly one `light`, `balanced`, or `dense` value for each body section.

Do not add a body section that is absent from the plan. Do not use the plan to add facts, certainty, actions, or scope that the source does not support.

## Required Reading Path

- TLDR remains the first reading level: judgment, strongest support, one-picture summary, and key-question table.
- Each body section answers one planned reader question. Its heading states the useful result rather than the method used to obtain it.
- A section containing a table or figure starts with a paragraph, bullets, or a restrained callout that states the takeaway.
- Tables and figures are dense evidence. Two dense evidence blocks may not be adjacent; place a substantive explanatory bridge between them.
- Definitions, uncertainty, scope, and source notes remain adjacent to the claim or visual they qualify.
- `dense` sections receive more separation in HTML. Other native formats use their own heading and paragraph spacing while preserving the same structural path.

## Runtime Gate

`scripts/validate_brief.py` calls the shared document validator before any renderer runs. It rejects a missing or stale `reading_path`, an incomplete section map, an unknown density, evidence before takeaway, and consecutive dense evidence without explanation.

Failure is blocking. A renderer, output-format override, fast mode, or visual review cannot waive this contract. Fix the plan or document, rerun `validate_brief.py`, then rerun the target-format validator.
