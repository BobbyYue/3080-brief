"""Bind standalone opening comprehension to the final 3080 review path."""
from pathlib import Path
import reader_answers as answers
import validate_visual_replay


def validate(receipt_path, draft, source, ledger):
    errors = answers.validate_receipt(receipt_path, draft)
    if errors:
        return errors
    try:
        receipt = answers.load(receipt_path)
        manifest = answers.load(receipt["manifest_path"])
        lock, plan = answers.open_lock(manifest["lock_path"])
        if lock["source"]["sha256"] != answers.digest(source):
            errors.append("opening answers use a different source snapshot")
        if any(s["mode"] == "full" for s in plan["surfaces"]):
            errors.append("3080 opening comprehension cannot use the full document")
        required = {c["id"] for c in answers.load(ledger)["claims"]
                    if c.get("priority") == "P0" and not c.get("appendix")}
        covered = {cid for answer in plan["answers"] for cid in answer.get("claim_ids", [])}
        if required - covered:
            errors.append("opening answer plan misses core claims: " + ", ".join(sorted(required - covered)))
    except (KeyError, ValueError, TypeError, OSError) as exc:
        errors.append(str(exc))
    return errors


def validate_readiness_binding(readiness, draft, source, ledger, visual_spec=None, preview=None):
    evidence = readiness.get("reader_answers", {})
    try:
        if answers.digest(evidence["path"]) != evidence["sha256"]:
            return ["reader answer receipt changed after readiness validation"]
        errors = validate(evidence["path"], draft, source, ledger)
        if visual_spec:
            visual = readiness.get("visual_replay_evidence", {})
            if answers.digest(visual["path"]) != visual["sha256"]:
                return errors + ["visual replay changed after readiness"]
            status, issues = validate_visual_replay.validate(answers.load(visual["path"]), preview,
                                                            answers.load(ledger), answers.load(visual_spec))
            errors.extend(issues)
            if status != "PASS" and not issues:
                errors.append("visual comprehension did not pass")
        return errors
    except (KeyError, OSError, TypeError) as exc:
        return ["required opening answer receipt is missing: " + str(exc)]
