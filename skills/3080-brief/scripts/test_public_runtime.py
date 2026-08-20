#!/usr/bin/env python3
"""Smoke-test the public resumable runtime with a complete Standard HTML run."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
FIXTURES = SKILL / "evals" / "fixtures"


def run(*arguments, expect=0):
    result = subprocess.run(
        [sys.executable, *(str(item) for item in arguments)],
        text=True,
        capture_output=True,
    )
    if result.returncode != expect:
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        raise RuntimeError(
            f"command returned {result.returncode}, expected {expect}: {arguments}\n{output}"
        )
    return result


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory(prefix="3080-public-runtime-") as temporary:
        workspace = Path(temporary)
        run_dir = workspace / "run"
        output = workspace / "brief.html"
        run(
            SCRIPTS / "build_html_brief.py",
            FIXTURES / "html-brief.json",
            FIXTURES / "html-visual-spec.json",
            output,
            "--design-plan",
            FIXTURES / "html-design.json",
        )
        run(
            SCRIPTS / "run_3080.py",
            "init",
            run_dir,
            "--source-ref",
            FIXTURES / "source-zh.md",
            "--source-type",
            "markdown",
            "--output-type",
            "html",
            "--profile",
            "standard",
        )
        run(
            SCRIPTS / "run_3080.py",
            "ground",
            run_dir,
            "--source-before",
            FIXTURES / "source-zh.md",
            "--source-snapshot",
            FIXTURES / "source-zh.md",
            "--inventory",
            FIXTURES / "inventory-zh-source.md",
            "--claim-ledger",
            FIXTURES / "claim-ledger.json",
        )
        run(
            SCRIPTS / "run_3080.py",
            "preflight",
            run_dir,
            "--draft",
            FIXTURES / "html-brief.json",
            "--visual-spec",
            FIXTURES / "html-visual-spec.json",
            "--html-design",
            FIXTURES / "html-design.json",
        )
        run(
            SCRIPTS / "run_3080.py",
            "record-output",
            run_dir,
            "--output-ref",
            output,
            "--one-picture-preview",
            output,
        )

        visual_replay = workspace / "visual-replay.json"
        write_json(
            visual_replay,
            {
                "reader_role": "visual_blind",
                "visual_artifact_id": hashlib.sha256(output.read_bytes()).hexdigest(),
                "review_round": 1,
                "replay": {
                    "main_judgment": "分层证据更强，但未达到扩大范围阈值。",
                    "supporting_evidence": ["分层为 68，汇总为 42。"],
                    "next_action_or_boundary": "先验证稳定性。",
                    "reading_path": "先比较，再看阈值。",
                    "unresolved_confusion": [],
                },
                "evaluation": {
                    "verdict": "PASS",
                    "main_judgment_claim_ids": ["C01"],
                    "evidence_claim_ids": ["C02"],
                    "action_or_boundary_claim_ids": ["C04"],
                    "reading_path_clear": True,
                    "unresolved_confusion_blocks_decision": False,
                    "blocking_issues": [],
                    "required_fixes": [],
                },
            },
        )
        run(
            SCRIPTS / "run_3080.py",
            "record-visual-replay",
            run_dir,
            "--visual-replay-result",
            visual_replay,
        )
        run(
            SCRIPTS / "run_3080.py",
            "prepare-review",
            run_dir,
            "--document-preview",
            output,
        )
        state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
        artifact_set_id = state["review_preparation"]["artifact_set_id"]

        primary_reader = workspace / "primary-reader.json"
        write_json(
            primary_reader,
            {
                "reader_role": "primary",
                "artifact_set_id": artifact_set_id,
                "questions": [
                    {
                        "question": f"这个结论对问题 {index} 意味着什么？",
                        "answer": "先保留分层诊断，并验证稳定性。",
                        "inference_or_uncertainty": "none",
                    }
                    for index in range(1, 4)
                ],
            },
        )
        blocked = run(
            SCRIPTS / "run_3080.py",
            "record-reader",
            run_dir,
            "--blind-reader-result",
            primary_reader,
            expect=3,
        )
        if "audit_review" not in blocked.stderr:
            raise RuntimeError("Blind Reader Replay was not blocked before audit review PASS")

        review_paths = []
        for role in ("reader", "source", "visual"):
            review_path = workspace / f"{role}-review.json"
            write_json(
                review_path,
                {
                    "reviewer_role": role,
                    "artifact_set_id": artifact_set_id,
                    "review_round": 1,
                    "verdict": "PASS",
                    "checks": [
                        {"name": "runtime smoke", "result": "PASS", "reason": "synthetic fixture"}
                    ],
                    "blocking_issues": [],
                    "unsupported_claims": [],
                    "missing_coverage": [],
                    "required_fixes": [],
                },
            )
            review_paths.append(review_path)
        run(
            SCRIPTS / "run_3080.py",
            "record-review",
            run_dir,
            "--reader-review",
            review_paths[0],
            "--source-review",
            review_paths[1],
            "--visual-review",
            review_paths[2],
        )
        run(
            SCRIPTS / "run_3080.py",
            "record-reader",
            run_dir,
            "--blind-reader-result",
            primary_reader,
        )
        run(
            SCRIPTS / "run_3080.py",
            "finalize",
            run_dir,
            "--source-after",
            FIXTURES / "source-zh.md",
        )
        receipt = json.loads((run_dir / "delivery_receipt.json").read_text(encoding="utf-8"))
        for check in ("visual_blind_replay", "review", "blind_reader_replay"):
            if receipt.get("checks", {}).get(check) != "PASS":
                raise RuntimeError(f"delivery receipt did not pass {check}")

    print("PUBLIC HTML STANDARD STATE MACHINE PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
