"""Package-local delivery adapter; the shared module owns lifecycle validation."""
import importlib
import argparse
import json
from pathlib import Path

import checked_delivery as delivery
import reader_answers


def native_plan_fields(plan):
    return {"task": plan["reader"]["decision"],
            "reader": {"knowledge": plan["reader"]["known_context"], "need": plan["reader"]["decision"]},
            "required_answers": [{"id": item["id"], "question": item["question"],
                "expected": item["expected_information"], "source_location": item["source_location"]}
                for item in plan["answers"]]}


def init_from_native(run, context_plan, reader_lock, bound_plan, source_paths=()):
    """Derive task/reader/answers from their existing owner, not a second checklist."""
    module = importlib.import_module("writing_lifecycle")
    lock, original = reader_answers.open_lock(reader_lock)
    plan = json.loads(Path(context_plan).read_text(encoding="utf-8"))
    plan.update(native_plan_fields(original))
    plan["native_context"] = {"reader_plan_lock": module.ref(reader_lock)}
    module.write_json(bound_plan, plan, exclusive=True)
    return module.init_run(run, bound_plan, "functional", [lock["source"]["path"], *source_paths])


def reader_lock_from_readiness(path):
    ready = reader_answers.load(path)
    receipt = reader_answers.load(ready["reader_answers"]["path"])
    return reader_answers.load(receipt["manifest_path"])["lock_path"]


def verify_native_context(module, run, artifact, sources, reader_lock):
    with module.session(run) as state:
        native_hashes = {delivery.digest(Path(path).read_bytes()) for path in sources if path}
        if not native_hashes or not native_hashes <= {item["sha256"] for item in state["sources"]}:
            raise delivery.DeliveryBlocked("Lifecycle sources do not match the native source snapshots")
        plan = state["plan"]
        linked = plan.get("native_context", {}).get("reader_plan_lock")
        if reader_lock or linked:
            actual_lock = reader_lock or linked["path"]
            if linked != module.ref(actual_lock):
                raise delivery.DeliveryBlocked("Lifecycle must link the original reader-answer plan")
            lock, original = reader_answers.open_lock(actual_lock)
            if lock["source"]["sha256"] not in native_hashes:
                raise delivery.DeliveryBlocked("Reader plan and native review use different sources")
            if any(plan.get(key) != value for key, value in native_plan_fields(original).items()):
                raise delivery.DeliveryBlocked("Task, reader or answers drifted from the native plan")
        allowed = {".html": {"html"}, ".htm": {"html"}, ".docx": {"word"},
                   ".pdf": {"pdf"}, ".pptx": {"slides"}, ".md": {"markdown", "md", "text"},
                   ".txt": {"text", "markdown"}, ".xml": {"feishu", "xml"}}
        if Path(artifact).suffix.lower() in allowed and plan["format"] not in allowed[Path(artifact).suffix.lower()]:
            raise delivery.DeliveryBlocked("Lifecycle output format differs from the actual artifact")


def state_path(run):
    if Path(run).is_symlink():
        raise delivery.DeliveryBlocked("Lifecycle run must not be a symlink")
    run = Path(run).resolve()
    if not run.is_dir() or not (run / "lifecycle.json").is_file():
        raise delivery.DeliveryBlocked("A writing run directory with lifecycle.json is required")
    return run / "lifecycle.json"


def verify(run, artifact, evidence, native, *, draft=False, sources=(), reader_lock=None):
    state = state_path(run)
    try:
        module = importlib.import_module("writing_lifecycle")
    except ImportError as exc:
        raise delivery.DeliveryBlocked("The package-local lifecycle verifier is unavailable") from exc
    if Path(getattr(module, "__file__", "")).resolve() != Path(__file__).with_name("writing_lifecycle.py").resolve():
        raise delivery.DeliveryBlocked("Lifecycle verification must use this package's module")
    try:
        result = module.verify_delivery(state.parent, artifact, "functional", review_evidence=evidence, draft=draft)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise delivery.DeliveryBlocked("Writing lifecycle validation failed") from exc
    expected_status = "review-incomplete-draft" if draft else "pass"
    if not isinstance(result, dict) or result.get("status") != expected_status:
        raise delivery.DeliveryBlocked("Lifecycle result is not final for this delivery mode")
    if result.get("artifact_sha256") != native.get("artifact_sha256"):
        raise delivery.DeliveryBlocked("Native review and lifecycle checked different artifact bytes")
    if sources or reader_lock:
        try:
            verify_native_context(module, state.parent, artifact, sources, reader_lock)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise delivery.DeliveryBlocked("Native task/source binding failed") from exc
    evidence_paths = result.get("evidence_paths")
    if not isinstance(evidence_paths, list) or not evidence_paths:
        raise delivery.DeliveryBlocked("Lifecycle result must identify its evidence")
    verified = delivery.snapshots([state, *evidence_paths])
    for path, digest in native.get("verified_inputs", {}).items():
        if path in verified and verified[path] != digest:
            raise delivery.DeliveryBlocked("Native review and lifecycle consumed different inputs")
        verified[path] = digest
    issues = list(result.get("issues", []))
    for issue in native.get("issues", []):
        if issue not in issues:
            issues.append(issue)
    import writing_execution
    try:
        managed = writing_execution.accept_native(run, artifact, evidence,
            {**native, "status": expected_status}, method=native.get("review_method", "independent"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise delivery.DeliveryBlocked("Managed execution evidence is incomplete or changed") from exc
    captured = managed.get("review", {}).get("evidence_paths", [])
    verified.update(delivery.snapshots(captured))
    return {**native, "status": expected_status, "issues": issues, "verified_inputs": verified,
            "managed_execution": managed,
            "lifecycle": {"status": expected_status, "profile": "functional", "rounds": result.get("rounds"),
                          "evidence_paths": evidence_paths}}


def main():
    parser = argparse.ArgumentParser(description="Initialize a functional run from the existing locked reader-answer plan")
    parser.add_argument("run")
    parser.add_argument("--plan", required=True, help="Context/genre/format/reading-path plan; task/reader/answers are derived")
    parser.add_argument("--reader-plan-lock", required=True)
    parser.add_argument("--bound-plan", required=True, help="New derived plan file, never overwrites")
    parser.add_argument("--source", action="append", default=[], help="Additional captured native source/excerpt inputs")
    args = parser.parse_args()
    try:
        result = init_from_native(args.run, args.plan, args.reader_plan_lock, args.bound_plan, args.source)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        return delivery.blocked()


if __name__ == "__main__":
    raise SystemExit(main())
