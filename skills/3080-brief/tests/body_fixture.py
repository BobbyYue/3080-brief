"""Synthetic body contracts and judgments ONLY; no claim of reader/source quality."""
import json
from pathlib import Path
import body_completion as body


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return Path(path)


def make_body(base, candidate, source, *, ledger=None, outline=None, document=None):
    base = Path(base)
    request = base / "synthetic-body-request.md"
    request.write_text("SYNTHETIC TEST ONLY: explain the complete source, including its limits.")
    if ledger is None:
        ledger = save(base / "synthetic-body-ledger.json", {"claims": [{"id": "C01", "priority": "P0"}]})
    outline = outline or source
    claims = [c["id"] for c in body.load(ledger)["claims"] if not c.get("appendix") and c.get("priority") in {"P0", "P1"}]
    if document is None:
        document = {"title": "3080 Brief Synthetic structural fixture", "language": "en", "source": {"title": "Synthetic source"},
                    "opening": {"lines": ["A bounded finding.", "A source limit applies."]},
                    "questions": [{"question": q, "conclusion": "A bounded finding", "why": "Source limit"}
                                  for q in ("What changed?", "What is unknown?", "What follows?")],
                    "reading_path": {"contract_version": "1.0", "reader_decision": "Inspect a bounded finding",
                                     "section_questions": ["What does the source explain?"], "section_density": ["light"]},
                    "body": [{"heading": "Synthetic body explanation", "blocks": [{"type": "paragraph",
                        "text": "The inspected sample supplies this finding; other samples are not established by this evidence."}]}]}
        candidate.write_text(candidate.read_text() + "\n## Synthetic body explanation\n\n" + document["body"][0]["blocks"][0]["text"] + "\n")
    mapped = []
    for section in document["body"]:
        for block in section["blocks"]:
            if block.get("type") in {"paragraph", "callout", "bullets", "table"}:
                key = "B" + str(len(mapped) + 1)
                block["answers"] = [key]
                mapped.append({"id": key, "question": "What does this source finding mean?", "claim_ids": claims,
                               "answer_requires": ["SYNTHETIC FIXTURE: explanation and source limits"]})
    plan_input = save(base / "synthetic-body-plan-input.json", {"scope": "full", "requirements": mapped, "excluded_claims": []})
    lock = save(base / "synthetic-body-plan.lock.json", body.lock(plan_input, request, source, ledger, outline))
    document["body_plan"] = body.ref(lock)
    brief = save(base / "synthetic-brief.json", document)
    return brief, body.context(brief)


def structural_body(record, role):
    if role not in body.ROLES:
        return None
    result = body.template(record, role)
    data = body.current(record)
    contents = body.validate_plan(data["plan"])
    result["scope_check"].update(status="pass", request_quote=contents["user_request"],
        outline_quote=contents["source_outline"], reason="SYNTHETIC structural fixture, not an actual scope judgment.")
    for item in result["requirements"]:
        block = data["evidence"][item["id"]][0]
        item.update(status="pass", quotes=[{"block": block["block"], "quote": block["parts"][0]}],
                    reason="SYNTHETIC structural fixture, not a semantic sufficiency judgment.")
        if role == "source":
            item["source_quote"] = contents["source_snapshot"]
    for item in result["excluded_claims"]:
        item.update(status="pass", reason="SYNTHETIC structural fixture, not an exclusion approval.")
    return result
