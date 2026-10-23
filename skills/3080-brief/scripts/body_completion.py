#!/usr/bin/env python3
"""Body integrity and existing-review evidence, not a semantic completeness oracle."""
import argparse
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES = {"reader", "source"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def object_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def resolve(path):
    path = Path(path)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("body evidence relative path escapes package")
    return path


def ref(path):
    # Caller/CLI paths are cwd-relative; only stored references use package roots.
    path = Path(path).resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def read_ref(entry, *, decode=True):
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
        raise ValueError("missing body evidence path and SHA256")
    path = resolve(entry["path"])
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
        raise ValueError("stale body evidence: " + str(path))
    if not raw.strip():
        raise ValueError("empty body evidence: " + str(path))
    return raw.decode("utf-8") if decode else raw


def text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(span.get("text", "") for span in value if isinstance(span, dict))
    return ""


def normalized(value):
    # Ignore formatting punctuation/spacing, not words, quantities or order.
    return "".join(c.casefold() for c in text(value) if c.isalnum())


def nonempty(value):
    return isinstance(value, str) and bool(normalized(value))


def unique_strings(values, label, *, empty=False):
    if (not isinstance(values, list) or (not values and not empty)
            or any(not nonempty(v) for v in values) or len(set(values)) != len(values)):
        raise ValueError(label + " requires unique nonempty strings")
    return values


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get("version") != 1 or plan.get("state") != "locked":
        raise ValueError("body_plan requires a version 1 locked plan")
    inputs = plan.get("inputs", {})
    contents = {key: read_ref(inputs.get(key)) for key in
                ("user_request", "source_snapshot", "claim_ledger", "source_outline")}
    claims = json.loads(contents["claim_ledger"]).get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("body plan claim ledger has no claims")
    unique_strings([c.get("id") for c in claims], "claim IDs")
    known = {c["id"] for c in claims if not c.get("appendix", False)}
    required = {c["id"] for c in claims if c["id"] in known and c.get("priority") in {"P0", "P1"}}
    if not required:
        raise ValueError("body plan requires non-appendix P0/P1 claims")
    requirements = plan.get("requirements")
    scope = plan.get("scope")
    if scope not in {"full", "summary-only"} or not isinstance(requirements, list):
        raise ValueError("body plan requires scope full or summary-only and requirements")
    unique_strings([r.get("id") for r in requirements], "body requirement IDs", empty=scope == "summary-only")
    mapped = set()
    for requirement in requirements:
        if not nonempty(requirement.get("question")):
            raise ValueError("body requirement needs a reader question")
        mapped.update(unique_strings(requirement.get("claim_ids"), "body requirement claim_ids"))
        unique_strings(requirement.get("answer_requires"), "body requirement answer_requires")
    exclusions = plan.get("excluded_claims")
    if not isinstance(exclusions, list):
        raise ValueError("body plan requires explicit excluded_claims, even when empty")
    excluded = set(unique_strings([e.get("claim_id") for e in exclusions], "excluded claims", empty=True))
    if any(not nonempty(e.get("reason")) for e in exclusions):
        raise ValueError("excluded claims require reasons for Reader and Source review")
    if mapped & excluded or not (mapped | excluded) <= known or not required <= mapped | excluded:
        raise ValueError("body plan must account for every P0/P1 claim without stale, appendix or conflicting mappings")
    if scope == "summary-only":
        quote = plan.get("summary_only_request_quote")
        if requirements or not nonempty(quote) or quote not in contents["user_request"]:
            raise ValueError("summary-only needs an exact request quote, no body requirements, and explicit exclusions")
    elif plan.get("summary_only_request_quote"):
        raise ValueError("full body plan cannot carry a summary-only exception")
    return contents


def lock(plan_path, user_request, source_snapshot, claim_ledger, source_outline):
    plan = load(plan_path)
    allowed = {"scope", "requirements", "excluded_claims", "summary_only_request_quote"}
    if not isinstance(plan, dict) or set(plan) - allowed:
        raise ValueError("body plan input has unsupported fields")
    locked = {**plan, "version": 1, "state": "locked", "inputs": {
        "user_request": ref(user_request), "source_snapshot": ref(source_snapshot),
        "claim_ledger": ref(claim_ledger), "source_outline": ref(source_outline)}}
    validate_plan(locked)
    return locked


def block_parts(block):
    kind = block.get("type")
    if kind in {"paragraph", "callout"}:
        return [text(block.get("text"))]
    if kind == "bullets":
        return [text(item) for item in block.get("items", [])]
    if kind == "table":
        return [text(cell) for row in block.get("rows", []) for cell in row]
    return []  # Headings, figure labels and hidden P2 details cannot answer obligations.


def inspect(document):
    plan_ref = document.get("body_plan")
    plan = json.loads(read_ref(plan_ref))
    validate_plan(plan)
    body = document.get("body")
    if not isinstance(body, list) or (not body and plan["scope"] == "full"):
        raise ValueError("body completion requires a nonempty full body")
    requirements = {r["id"]: r for r in plan["requirements"]}
    evidence = {key: [] for key in requirements}
    tldr = [text(line) for line in document.get("opening", {}).get("lines", [])]
    tldr += [text(q.get(k)) for q in document.get("questions", []) for k in ("question", "conclusion", "why")]
    summary = normalized(" ".join(tldr))
    blocks = []
    for si, section in enumerate(body):
        if not isinstance(section, dict) or not section.get("blocks"):
            raise ValueError("body section cannot be an empty heading")
        for bi, block in enumerate(section["blocks"]):
            parts = block_parts(block)
            if block.get("type") in {"paragraph", "callout", "bullets", "table"} and (
                    not parts or any(not nonempty(p) for p in parts)):
                raise ValueError("body explanation cannot contain empty text")
            answers = unique_strings(block.get("answers", []), "body block answers", empty=True)
            if set(answers) - set(requirements):
                raise ValueError("body answers map to unknown requirements")
            if answers and not parts:
                raise ValueError("body answers require visible explanation, not headings, figures or details")
            item = {"block": f"body/{si}/blocks/{bi}", "heading": text(section.get("heading")),
                    "parts": parts, "answers": answers}
            if answers:
                blocks.append(item)
            for answer in answers:
                evidence[answer].append(item)
    for key, items in evidence.items():
        if not items:
            raise ValueError("unresolved body requirement: " + key)
    if requirements and all(normalized(part) in summary for item in blocks for part in item["parts"]):
        raise ValueError("body evidence merely repeats TLDR; explanation is unresolved")
    return {"plan": plan, "plan_ref": plan_ref, "evidence": evidence, "blocks": blocks}


def context(brief_json, **expected):
    document = load(brief_json)
    from brief_model import validate_document
    validate_document(document)
    data = inspect(document)
    for name, path in expected.items():
        if path and ref(path) != {**data["plan"]["inputs"][name],
                                "path": str(resolve(data["plan"]["inputs"][name]["path"]))}:
            raise ValueError("body plan binds a different " + name)
    return {"brief": ref(brief_json), "evidence_sha256": object_sha(data)}


def current(context_record):
    document = json.loads(read_ref(context_record.get("brief")))
    from brief_model import validate_document
    validate_document(document)
    data = inspect(document)
    if object_sha(data) != context_record.get("evidence_sha256"):
        raise ValueError("body evidence changed after preparation")
    return data


def visible_ref(snapshot, candidate):
    return {**ref(snapshot), "candidate_sha256": ref(candidate)["sha256"]} if snapshot else None


def candidate_text(candidate, visible_text=None):
    import reader_value
    path = Path(candidate)
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        return "\n".join("".join(t.text or "" for run in p.findall(".//w:r", ns)
                                  if run.find("w:rPr/w:vanish", ns) is None
                                  for t in run.findall("w:t", ns)) for p in root.findall(".//w:p", ns))
    if path.suffix.lower() in {".html", ".htm"}:
        # CSS visibility needs an independently inspected rendered snapshot.
        # Keep this local: general editorial extraction has its own contract.
        try:
            reader_value.read_text(path)
        except ValueError:
            if not visible_text:
                raise ValueError("HTML CSS visibility requires --body-visible-text from the rendered candidate")
        class BodyText(reader_value.VisibleText):
            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if (tag == "details" and "open" not in values or "inert" in values or
                        re.search(r"opacity\s*:\s*0(?:\D|$)|visibility\s*:\s*collapse|clip(?:-path)?\s*:", values.get("style", ""), re.I)):
                    attrs = [*attrs, ("hidden", "")]
                super().handle_starttag(tag, attrs)
        parser = BodyText()
        parser.feed(path.read_text(encoding="utf-8"))
        return " ".join(parser.parts)
    return reader_value.read_text(path)


def candidate_errors(data, candidate, visible_text=None):
    """Check visible answer presence in order; native visual review still checks layout."""
    texts = [candidate_text(candidate, visible_text)]
    if visible_text:
        if visible_text.get("candidate_sha256") != ref(candidate)["sha256"]:
            return ["rendered body text belongs to another candidate"]
        texts.append(read_ref(visible_text))
    return [error for raw in texts for error in presence_errors(data, raw)]


def presence_errors(data, raw):
    visible = normalized(raw)
    position, heading = 0, None
    for block in data["blocks"]:
        if block["heading"] != heading:
            heading = block["heading"]
            found = visible.find(normalized(heading), position)
            if found < 0:
                return ["body heading missing from the candidate: " + block["block"]]
            position = found + len(normalized(heading))
        for part in block["parts"]:
            found = visible.find(normalized(part), position)
            if found < 0:
                return ["mapped body answer missing from the candidate: " + block["block"]]
            position = found + len(normalized(part))
    return []


def template(context_record, role):
    data = current(context_record)
    result = {"version": 1, "evidence_sha256": context_record["evidence_sha256"],
              "scope_check": {"status": "fail", "request_quote": "", "outline_quote": "", "reason": ""},
              "requirements": [{"id": key, "status": "fail", "quotes": [], "reason": "",
                                **({"source_quote": ""} if role == "source" else {})}
                               for key in data["evidence"]],
              "excluded_claims": [{"claim_id": e["claim_id"], "status": "fail", "reason": ""}
                                  for e in data["plan"]["excluded_claims"]]}
    return result


def review_errors(review, bundle):
    role = review.get("reviewer_role")
    if role not in ROLES:
        return []
    errors = []
    try:
        record = bundle["body_completion"]
        data = current(record)
        result = review.get("body_completion")
        if not isinstance(result, dict) or result.get("version") != 1 or result.get("evidence_sha256") != record["evidence_sha256"]:
            return [role + " missing or stale body_completion judgments"]
        contents = validate_plan(data["plan"])
        scope = result.get("scope_check", {})
        for key, source in (("request_quote", "user_request"), ("outline_quote", "source_outline")):
            quote = scope.get(key)
            if not nonempty(quote) or quote not in contents[source]:
                errors.append(role + " body scope check needs an exact " + key)
        if scope.get("status") not in {"pass", "fail"} or not nonempty(scope.get("reason")):
            errors.append(role + " body scope judgment is missing or unexplained")
        elif scope["status"] == "fail":
            errors.append("body completion unresolved scope: " + role)
        if data["plan"]["scope"] == "summary-only" and scope.get("request_quote") != data["plan"]["summary_only_request_quote"]:
            errors.append(role + " did not check the exact summary-only request exception")
        items = result.get("requirements", [])
        ids = unique_strings([item.get("id") for item in items], "review requirement IDs", empty=True)
        if set(ids) != set(data["evidence"]):
            errors.append(role + " must judge every body requirement exactly once")
        for item in items:
            allowed = {b["block"]: b for b in data["evidence"].get(item["id"], [])}
            if item.get("status") not in {"pass", "fail"} or not nonempty(item.get("reason")):
                errors.append(role + " body answer judgment is missing or unexplained: " + item["id"])
            elif item["status"] == "fail":
                errors.append("body completion unresolved answer: " + role + " " + item["id"])
            quotes = item.get("quotes")
            if not isinstance(quotes, list) or not quotes:
                errors.append(role + " body judgment requires quotes from mapped visible blocks")
            else:
                for quote in quotes:
                    block = allowed.get(quote.get("block"), {})
                    if not nonempty(quote.get("quote")) or not any(quote["quote"] in p for p in block.get("parts", [])):
                        errors.append(role + " body quote is not in the mapped answer")
            if role == "source" and (not nonempty(item.get("source_quote")) or item["source_quote"] not in contents["source_snapshot"]):
                errors.append("source body judgment requires a source snapshot quote")
        excluded = result.get("excluded_claims", [])
        ids = unique_strings([item.get("claim_id") for item in excluded], "review exclusion IDs", empty=True)
        if set(ids) != {item["claim_id"] for item in data["plan"]["excluded_claims"]}:
            errors.append(role + " must confirm every excluded claim")
        for item in excluded:
            if item.get("status") not in {"pass", "fail"} or not nonempty(item.get("reason")):
                errors.append(role + " body exclusion judgment is missing or unexplained")
            elif item["status"] == "fail":
                errors.append("body completion unresolved exclusion: " + role)
        candidate = bundle.get("delivery_artifact") or bundle.get("body_candidate")
        if not candidate:
            errors.append("body review lacks its candidate binding")
        else:
            read_ref(candidate, decode=False)
            errors.extend(candidate_errors(data, resolve(candidate["path"]), bundle.get("body_visible_text")))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append("invalid body completion evidence: " + str(exc))
    return errors


def packet(context_record, role):
    data = current(context_record)
    contents = validate_plan(data["plan"])
    return ("\n## Body Completion Evidence\n\n"
            "Judge explanation, not outline presence or length. Check every answer_requires item against the "
            "mapped visible answer; reject a one-line appendix, TLDR paraphrase, or narrowed plan that omits "
            "material source/request questions. Confirm exclusions individually. Thin sources may need only "
            "a concise explanation; never pad. Summary-only requires explicit permission to omit the body, "
            "not 'compact' or Fast. Check the delivered candidate agrees with these answers.\n\n"
            "### Unaltered User Request\n\n" + contents["user_request"] +
            "\n### Independent Source Outline\n\n" + contents["source_outline"] +
            "\n### Locked Plan and Automatically Extracted Answers\n\n```json\n" +
            json.dumps({"plan": data["plan"], "blocks": data["blocks"]}, ensure_ascii=False, indent=2) +
            "\n```\nReturn `body_completion` in the existing response. Quotes must be exact; reasons must "
            "explain sufficiency, source limits and scope, not assert PASS. Structural integrity does not "
            "prove semantic completeness.\n\n```json\n" +
            json.dumps(template(context_record, role), ensure_ascii=False, indent=2) + "\n```\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    locking = sub.add_parser("lock", help="Lock before drafting; never overwrite an earlier lock")
    for name in ("plan", "user-request", "source-snapshot", "claim-ledger", "source-outline", "output"):
        locking.add_argument("--" + name, required=True)
    check = sub.add_parser("check", help="Check structure only; not review acceptance")
    check.add_argument("--brief-json", required=True)
    check.add_argument("--candidate")
    check.add_argument("--body-visible-text", help="Rendered visible text snapshot for CSS-controlled HTML")
    args = parser.parse_args()
    try:
        if args.action == "lock":
            result = lock(args.plan, args.user_request, args.source_snapshot, args.claim_ledger, args.source_outline)
            with Path(args.output).open("x", encoding="utf-8") as handle:
                json.dump(result, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            print(json.dumps(ref(args.output)))
        else:
            record = context(args.brief_json)
            errors = candidate_errors(current(record), args.candidate,
                visible_ref(args.body_visible_text, args.candidate)) if args.candidate else []
            if errors:
                raise ValueError("; ".join(errors))
            print(json.dumps({"status": "structurally-complete", "semantic_confidence": "not-assessed",
                              "body_completion": record}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print("FAIL body completion: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
