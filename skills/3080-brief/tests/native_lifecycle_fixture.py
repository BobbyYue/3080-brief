"""Derive native-bound process fixtures; never real semantic-review evidence."""
from pathlib import Path

from lifecycle_fixture import prepare_flow, save
import lifecycle_delivery
from execution_fixture import init_fixture, seed_fixture


def prepare_native_flow(lifecycle, base, artifact, native_result, reader_lock, rounds=1, verdict="pass", prior_verdicts=()):
    template = prepare_flow(lifecycle, base, artifact, native_result=native_result, rounds=rounds, verdict=verdict)
    root = template["root"] / "native-bound"
    root.mkdir()
    run, plan = root / "run", root / "plan.json"
    lifecycle_delivery.init_from_native(run, template["plan"], reader_lock, plan)
    init_fixture(run)
    lifecycle.record_unit(run, artifact, template["unit"])
    report = root / "report.json"
    measured = lifecycle.measure(run, artifact, report)
    record = lifecycle.load_json(template["record"])
    record["text_sha256"] = measured["text_sha256"]
    record["report_sha256"] = lifecycle.ref(report)["sha256"]
    record["dispositions"] = [{"signal_id": s["id"], "decision": "retain", "reason": "Synthetic process fixture"}
        for m in measured["metrics"].values() for s in m["signals"]]
    assessment = save(root / "assessment.json", record)
    lifecycle.register_candidate(run, artifact, artifact, report, assessment)
    for number in range(1, rounds + 1):
        lifecycle.start_review(run, artifact)
        result = native_result if number == rounds else template["root"] / ("review-" + str(number) + ".json")
        current_verdict = prior_verdicts[number - 1] if number <= len(prior_verdicts) else verdict
        if current_verdict != verdict:
            result = save(root / ("prior-" + str(number) + ".json"), {"status": current_verdict, "issues": []})
        lifecycle.finish_review(run, result, current_verdict,
            issues=[] if current_verdict == "pass" else [{"impact": "Synthetic unresolved reader issue"}])
        seed_fixture(run, result)
    with lifecycle.session(run) as state:
        source = Path(state["sources"][0]["path"])
    return {**template, "run": run, "plan": plan, "source": source, "report": report, "record": assessment, "root": root}
