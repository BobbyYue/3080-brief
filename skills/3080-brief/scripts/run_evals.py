#!/usr/bin/env python3
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
FIXTURES = SKILL / "evals" / "fixtures"


def run(*args, expect=0, env=None):
    result = subprocess.run(args, text=True, capture_output=True, env=env)
    if result.returncode != expect:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"command returned {result.returncode}, expected {expect}: {' '.join(map(str, args))}")
    return result


def main():
    for script in SCRIPTS.glob("*.py"):
        py_compile.compile(str(script), doraise=True)
    config = json.loads((SKILL / "config" / "3080-brief.json").read_text(encoding="utf-8"))
    execution = config.get("execution", {})
    if execution.get("required_entrypoint") != "scripts/run_3080.py":
        raise SystemExit("stateful runtime entrypoint is missing")
    if execution.get("required_stages") != ["grounded", "preflight", "review_draft", "review", "finalized"]:
        raise SystemExit("stateful runtime stage contract is incomplete")
    dependency_config = json.loads((SKILL / "config" / "dependencies.json").read_text(encoding="utf-8"))
    bundle_contract = dependency_config.get("installation_bundle", {})
    if bundle_contract.get("approval_mode") != "single_explicit_approval":
        raise SystemExit("dependency config must require one explicit bundled approval")
    json.loads((SKILL / "references" / "claim-ledger.schema.json").read_text(encoding="utf-8"))
    json.loads((SKILL / "references" / "visual-spec.schema.json").read_text(encoding="utf-8"))
    json.loads((SKILL / "evals" / "agent_acceptance.json").read_text(encoding="utf-8"))
    expression_suite = json.loads((SKILL / "evals" / "expression_cases.json").read_text(encoding="utf-8"))
    inventory_zh = FIXTURES / "inventory-zh-source.md"

    run(sys.executable, str(SCRIPTS / "validate_skill.py"), str(SKILL))
    run(sys.executable, str(SCRIPTS / "check_context_budget.py"), str(SKILL))
    run(sys.executable, str(SCRIPTS / "check_dependencies.py"), "--mode", "core")
    run(sys.executable, str(SCRIPTS / "validate_claim_ledger.py"), str(FIXTURES / "claim-ledger.json"))

    run(sys.executable, str(SCRIPTS / "preflight_check.py"), str(FIXTURES / "valid-brief.md"), "--source-inventory", str(inventory_zh))
    run(sys.executable, str(SCRIPTS / "preflight_check.py"), str(FIXTURES / "valid-brief.xml"), "--format", "xml", "--source-inventory", str(inventory_zh))
    run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "valid-brief.xml"),
        "--format", "xml",
        "--output-type", "feishu",
        "--source-inventory", str(inventory_zh),
    )
    image_substitution = run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "valid-brief.md"),
        "--output-type", "feishu",
        "--source-inventory", str(inventory_zh),
        expect=1,
    )
    if "ordinary Markdown images are not editable whiteboards" not in image_substitution.stdout:
        raise SystemExit("Feishu preflight accepted a normal image as the required editable whiteboard")
    run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "valid-brief.xml"),
        "--format", "xml",
        "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
        "--source-inventory", str(inventory_zh),
    )
    run(sys.executable, str(SCRIPTS / "preflight_check.py"), str(FIXTURES / "invalid-missing-tldr.md"), "--source-inventory", str(inventory_zh), expect=1)
    two_openings = run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "invalid-opening-two-blocks.md"),
        "--source-inventory", str(inventory_zh),
        expect=1,
    )
    if "exactly one opening callout block" not in two_openings.stdout:
        raise SystemExit("preflight did not reject two peer opening blocks")
    too_many_support = run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "invalid-opening-too-many-support-lines.md"),
        "--source-inventory", str(inventory_zh),
        expect=1,
    )
    if "1-3 support lines" not in too_many_support.stdout:
        raise SystemExit("preflight did not reject an oversized opening support block")
    no_xml_support = run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "invalid-opening-no-support.xml"),
        "--format", "xml",
        "--source-inventory", str(inventory_zh),
        expect=1,
    )
    if "1-3 support lines" not in no_xml_support.stdout:
        raise SystemExit("preflight did not reject an XML opening with no support line")
    fixed_labels = run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "invalid-opening-fixed-labels.md"),
        "--source-inventory", str(inventory_zh),
        expect=1,
    )
    if "fixed label template" not in fixed_labels.stdout:
        raise SystemExit("preflight did not reject a fixed conclusion/evidence/action opening template")
    run(sys.executable, str(SCRIPTS / "preflight_check.py"), str(FIXTURES / "invalid-audience-heading.md"), "--source-inventory", str(inventory_zh), expect=1)
    expression_cases = expression_suite.get("cases", [])
    if {case.get("class") for case in expression_cases} != {"should_fix", "should_not_fix", "relation_preservation", "thin_source"}:
        raise SystemExit("expression evaluation must cover should_fix, should_not_fix, relation_preservation, and thin_source")
    case_ids = [case.get("id") for case in expression_cases]
    if len(case_ids) != len(set(case_ids)) or any(not case_id for case_id in case_ids):
        raise SystemExit("expression case IDs must be present and unique")
    for case in expression_cases:
        fixture = SKILL / "evals" / case["fixture"]
        if case["class"] in {"should_fix", "should_not_fix"}:
            result = run(
                sys.executable,
                str(SCRIPTS / "check_expression_quality.py"),
                str(fixture),
                "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
                "--language", case["language"],
                "--json",
            )
            report = json.loads(result.stdout)
            warning_ids = {warning["id"] for warning in report.get("warnings", [])}
            expected_warning_ids = set(case.get("expected_warning_ids", []))
            if warning_ids != expected_warning_ids:
                raise SystemExit(
                    f"expression case {case['id']} warnings differ: expected {sorted(expected_warning_ids)}, got {sorted(warning_ids)}"
                )
        elif case["class"] == "relation_preservation":
            result = run(
                sys.executable,
                str(SCRIPTS / "validate_claim_ledger.py"),
                str(fixture),
                expect=1,
            )
            if case["expected_error"] not in result.stdout:
                raise SystemExit(f"relation-preservation case {case['id']} did not expose the expected error")
            integrated = run(
                sys.executable,
                str(SCRIPTS / "check_expression_quality.py"),
                str(FIXTURES / "expression-should-not-fix-zh.md"),
                "--claim-ledger", str(fixture),
                "--language", "zh",
                expect=1,
            )
            if case["expected_error"] not in integrated.stdout:
                raise SystemExit(f"expression gate did not propagate relation failure for {case['id']}")
        else:
            expected_code = 0 if case["should_pass"] else 1
            result = run(
                sys.executable,
                str(SCRIPTS / "check_expression_quality.py"),
                str(fixture),
                "--claim-ledger", str(SKILL / "evals" / case["claim_ledger"]),
                "--non-appendix-source", str(SKILL / "evals" / case["source_fixture"]),
                "--language", "en",
                expect=expected_code,
            )
            if not case["should_pass"] and case["expected_error"] not in result.stdout:
                raise SystemExit(f"thin-source case {case['id']} did not expose the expected expansion error")

    run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "valid-brief-en.md"),
        "--source-inventory", str(FIXTURES / "inventory-en-source.md"),
    )
    invalid_context = run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "valid-brief.md"),
        "--source-inventory", str(FIXTURES / "inventory-en-invalid-context-zh.md"),
        expect=1,
    )
    if "invalid output-language basis" not in invalid_context.stdout:
        raise SystemExit("preflight accepted conversation language as an output-language override")
    mismatch = run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "valid-brief.md"),
        "--source-inventory", str(FIXTURES / "inventory-en-source.md"),
        expect=1,
    )
    if "draft language conflicts with declared output language" not in mismatch.stdout:
        raise SystemExit("preflight did not reject a Chinese draft for an English output decision")
    run(
        sys.executable,
        str(SCRIPTS / "preflight_check.py"),
        str(FIXTURES / "valid-brief.md"),
        "--source-inventory", str(FIXTURES / "inventory-en-explicit-zh.md"),
    )
    run(sys.executable, str(SCRIPTS / "check_coverage.py"), str(FIXTURES / "claim-ledger.json"))
    run(sys.executable, str(SCRIPTS / "validate_visual_spec.py"), str(FIXTURES / "visual-spec.json"), str(FIXTURES / "claim-ledger.json"))

    with tempfile.TemporaryDirectory(prefix="3080-brief-eval-") as tmp:
        tmp_path = Path(tmp)
        svg = tmp_path / "synthetic-board.svg"
        run(sys.executable, str(SCRIPTS / "render_visual_spec.py"), str(FIXTURES / "visual-spec.json"), str(svg))
        svg_text = svg.read_text(encoding="utf-8")
        for semantic_color in ("#1456F0", "#2EA121", "#DE7802"):
            if semantic_color not in svg_text:
                raise SystemExit(f"rendered visual omitted semantic color {semantic_color}")
        run(sys.executable, str(SCRIPTS / "validate_whiteboard_svg.py"), str(svg))
        wide_svg = run(
            sys.executable,
            str(SCRIPTS / "validate_whiteboard_svg.py"),
            str(FIXTURES / "invalid-wide-whiteboard.svg"),
            expect=1,
        )
        if "too wide for reliable preview" not in wide_svg.stdout:
            raise SystemExit("whiteboard validation did not reject a clipping-prone wide canvas")

        invalid_semantic_xml = tmp_path / "invalid-semantic.xml"
        valid_xml = (FIXTURES / "valid-brief.xml").read_text(encoding="utf-8")
        invalid_semantic_xml.write_text(
            valid_xml.replace('<span text-color="green"><b>+26pp</b></span>', '<span text-color="red"><b>+26pp</b></span>'),
            encoding="utf-8",
        )
        semantic_failure = run(
            sys.executable,
            str(SCRIPTS / "preflight_check.py"),
            str(invalid_semantic_xml),
            "--format", "xml",
            "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
            "--source-inventory", str(inventory_zh),
            expect=1,
        )
        if "conflicting semantic color" not in semantic_failure.stdout:
            raise SystemExit("preflight did not reject conflicting body semantic color")

        packets = tmp_path / "packets"
        run(
            sys.executable,
            str(SCRIPTS / "build_review_packet.py"),
            "--role", "all",
            "--source-snapshot", str(FIXTURES / "source-data-analysis.md"),
            "--inventory", str(SKILL / "references" / "source-inventory-template.md"),
            "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
            "--tldr", str(FIXTURES / "valid-brief.md"),
            "--body", str(FIXTURES / "valid-brief.md"),
            "--draft", str(FIXTURES / "valid-brief.md"),
            "--source-outline", "Synthetic non-appendix outline",
            "--source-excerpts", "Synthetic P0/P1 excerpts",
            "--visual-spec", str(FIXTURES / "visual-spec.json"),
            "--whiteboard-preview", str(svg),
            "--output", str(packets),
        )
        packet_texts = [(packets / f"review_packet_{role}.md").read_text(encoding="utf-8") for role in ("reader", "source", "visual")]
        if len(set(packet_texts)) != 3:
            raise SystemExit("role-specific review packets are not distinct")
        artifact_set_id = packet_texts[0].split("Artifact set ID: `", 1)[1].split("`", 1)[0]
        dynamic_reviews = []
        for role in ("reader", "source", "visual"):
            review_path = tmp_path / f"{role}.json"
            review_path.write_text(json.dumps({
                "reviewer_role": role,
                "review_mode": "independent",
                "reviewer_run_id": f"dynamic-{role}-run",
                "artifact_set_id": artifact_set_id,
                "review_round": 1,
                "verdict": "PASS",
                "checks": [{"name": f"{role} gates", "result": "PASS", "reason": "fixture"}],
                "blocking_issues": [],
                "unsupported_claims": [],
                "missing_coverage": [],
                "required_fixes": [],
            }), encoding="utf-8")
            dynamic_reviews.append(review_path)
        review_result = tmp_path / "review-result.json"
        run(sys.executable, str(SCRIPTS / "aggregate_reviews.py"), *(str(path) for path in dynamic_reviews), "--output", str(review_result))
        run(
            sys.executable,
            str(SCRIPTS / "verify_reviewed_artifacts.py"),
            "--review-result", str(review_result),
            "--source-snapshot", str(FIXTURES / "source-data-analysis.md"),
            "--inventory", str(SKILL / "references" / "source-inventory-template.md"),
            "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
            "--tldr", str(FIXTURES / "valid-brief.md"),
            "--body", str(FIXTURES / "valid-brief.md"),
            "--draft", str(FIXTURES / "valid-brief.md"),
            "--visual-spec", str(FIXTURES / "visual-spec.json"),
            "--whiteboard-preview", str(svg),
        )

        duplicate_id_reviews = []
        for role in ("reader", "source", "visual"):
            review_path = tmp_path / f"duplicate-{role}.json"
            review_path.write_text(json.dumps({
                "reviewer_role": role,
                "review_mode": "independent",
                "reviewer_run_id": "same-reviewer-run",
                "artifact_set_id": artifact_set_id,
                "review_round": 1,
                "verdict": "PASS",
                "checks": [{"name": f"{role} gates", "result": "PASS", "reason": "fixture"}],
                "blocking_issues": [],
                "unsupported_claims": [],
                "missing_coverage": [],
                "required_fixes": [],
            }), encoding="utf-8")
            duplicate_id_reviews.append(review_path)
        duplicate_ids = run(
            sys.executable,
            str(SCRIPTS / "aggregate_reviews.py"),
            *(str(item) for item in duplicate_id_reviews),
            "--mode", "independent",
            expect=1,
        )
        if "three distinct reviewer_run_id" not in duplicate_ids.stdout:
            raise SystemExit("review aggregation accepted three reviews from one execution context")

        run_dir = tmp_path / "stateful-run"
        run(
            sys.executable,
            str(SCRIPTS / "run_3080.py"),
            "init", str(run_dir),
            "--source-ref", "https://example.invalid/source",
            "--source-type", "feishu",
            "--output-type", "feishu",
            "--profile", "standard",
        )
        run(
            sys.executable,
            str(SCRIPTS / "run_3080.py"),
            "ground", str(run_dir),
            "--source-before", str(FIXTURES / "source-data-analysis.md"),
            "--source-snapshot", str(FIXTURES / "source-data-analysis.md"),
            "--inventory", str(inventory_zh),
            "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
        )
        run(
            sys.executable,
            str(SCRIPTS / "run_3080.py"),
            "preflight", str(run_dir),
            "--draft", str(FIXTURES / "valid-brief.xml"),
            "--visual-spec", str(FIXTURES / "visual-spec.json"),
            "--whiteboard-svg", str(svg),
        )
        live_document = tmp_path / "live-document.json"
        live_document.write_text(json.dumps({
            "document_token": "doc-output-1",
            "blocks": [{"block_type": "whiteboard", "block_id": "wb-block-1"}],
        }), encoding="utf-8")
        whiteboard_query = tmp_path / "whiteboard-query.json"
        whiteboard_query.write_text(json.dumps({
            "whiteboard_token": "wb-token-1",
            "status": "PASS",
        }), encoding="utf-8")
        run(
            sys.executable,
            str(SCRIPTS / "run_3080.py"),
            "record-output", str(run_dir),
            "--output-ref", "https://example.invalid/generated-doc",
            "--document-snapshot", str(live_document),
            "--whiteboard-query", str(whiteboard_query),
            "--whiteboard-preview", str(svg),
            "--whiteboard-token", "wb-token-1",
            "--whiteboard-block-id", "wb-block-1",
        )
        run(
            sys.executable,
            str(SCRIPTS / "run_3080.py"),
            "prepare-review", str(run_dir),
            "--document-preview", str(svg),
        )
        run_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
        state_artifact_id = run_state["review_preparation"]["artifact_set_id"]
        stateful_reviews = []
        for role in ("reader", "source", "visual"):
            review_path = tmp_path / f"stateful-{role}.json"
            review_path.write_text(json.dumps({
                "reviewer_role": role,
                "review_mode": "independent",
                "reviewer_run_id": f"stateful-{role}-run",
                "artifact_set_id": state_artifact_id,
                "review_round": 1,
                "verdict": "PASS",
                "checks": [{"name": f"{role} gates", "result": "PASS", "reason": "fixture"}],
                "blocking_issues": [],
                "unsupported_claims": [],
                "missing_coverage": [],
                "required_fixes": [],
            }), encoding="utf-8")
            stateful_reviews.append(review_path)
        blind_reader = tmp_path / "blind-reader.json"
        blind_reader.write_text(json.dumps({
            "reader_role": "primary",
            "artifact_set_id": state_artifact_id,
            "questions": [
                {"question": "核心判断是什么？", "answer": "需要分层判断。", "inference_or_uncertainty": "none"},
                {"question": "为什么？", "answer": "汇总会掩盖差异。", "inference_or_uncertainty": "none"},
                {"question": "下一步是什么？", "answer": "先验证稳定性。", "inference_or_uncertainty": "none"}
            ]
        }), encoding="utf-8")
        run(
            sys.executable,
            str(SCRIPTS / "run_3080.py"),
            "record-review", str(run_dir),
            "--reader-review", str(stateful_reviews[0]),
            "--source-review", str(stateful_reviews[1]),
            "--visual-review", str(stateful_reviews[2]),
            "--blind-reader-result", str(blind_reader),
        )
        changed_source = tmp_path / "source-after-changed.md"
        changed_source.write_text(
            (FIXTURES / "source-data-analysis.md").read_text(encoding="utf-8") + "\nChanged after generation.\n",
            encoding="utf-8",
        )
        source_change = run(
            sys.executable,
            str(SCRIPTS / "run_3080.py"),
            "finalize", str(run_dir),
            "--source-after", str(changed_source),
            "--final-document-snapshot", str(live_document),
            "--whiteboard-query", str(whiteboard_query),
            "--whiteboard-preview", str(svg),
            expect=3,
        )
        if "source changed during generation" not in source_change.stderr:
            raise SystemExit("stateful runtime did not block a changed source")
        run(
            sys.executable,
            str(SCRIPTS / "run_3080.py"),
            "finalize", str(run_dir),
            "--source-after", str(FIXTURES / "source-data-analysis.md"),
            "--final-document-snapshot", str(live_document),
            "--whiteboard-query", str(whiteboard_query),
            "--whiteboard-preview", str(svg),
        )
        delivery = json.loads((run_dir / "delivery_receipt.json").read_text(encoding="utf-8"))
        if delivery.get("verdict") != "PASS" or delivery.get("checks", {}).get("native_editable_whiteboard") != "PASS":
            raise SystemExit("stateful runtime did not issue a complete Feishu delivery receipt")
        thin_receipt = tmp_path / "thin-delivery-receipt.json"
        thin_delivery = dict(delivery)
        thin_delivery["run_id"] = "synthetic-thin-run"
        thin_receipt.write_text(json.dumps(thin_delivery), encoding="utf-8")
        markdown_receipt = tmp_path / "markdown-delivery-receipt.json"
        markdown_delivery = dict(delivery)
        markdown_delivery["run_id"] = "synthetic-markdown-run"
        markdown_delivery["output_type"] = "markdown"
        markdown_delivery["generated_output"] = str(FIXTURES / "valid-brief.md")
        markdown_delivery["checks"] = dict(delivery["checks"])
        markdown_delivery["checks"]["native_editable_whiteboard"] = "NOT_APPLICABLE"
        markdown_receipt.write_text(json.dumps(markdown_delivery), encoding="utf-8")
        acceptance_result = tmp_path / "agent-acceptance-result.json"
        acceptance_result.write_text(json.dumps({
            "host": "synthetic-host",
            "agent_version": "test-only",
            "model": "test-only",
            "executed_at": "2026-01-01T00:00:00Z",
            "cases": [
                {"id": "data-analysis-feishu", "status": "PASS", "delivery_receipt": str(run_dir / "delivery_receipt.json")},
                {"id": "thin-source-feishu", "status": "PASS", "delivery_receipt": str(thin_receipt)},
                {"id": "format-following-markdown", "status": "PASS", "delivery_receipt": str(markdown_receipt)}
            ]
        }), encoding="utf-8")
        run(
            sys.executable,
            str(SCRIPTS / "validate_agent_acceptance.py"),
            str(acceptance_result),
        )

    with tempfile.TemporaryDirectory(prefix="3080-brief-dependencies-") as tmp:
        tmp_path = Path(tmp)
        empty_cache = tmp_path / "empty-cache"
        isolated_env = os.environ.copy()
        isolated_env.pop("LARK_CLI", None)
        isolated_env.pop("WHITEBOARD_CLI", None)
        isolated_env.pop("BEAUTIFUL_FEISHU_WHITEBOARD_SKILL", None)
        isolated_env.pop("BRIEF3080_SKILL_INSTALL_ROOT", None)
        isolated_env.pop("BRIEF3080_SKILL_ROOTS", None)
        isolated_env.pop("BRIEF3080_HOST_CAPABILITIES", None)
        isolated_env.pop("NODE", None)
        missing = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(empty_cache),
            expect=3,
            env=isolated_env,
        )
        missing_report = json.loads(missing.stdout)
        if missing_report.get("overall_status") != "BLOCKED":
            raise SystemExit("missing Feishu dependencies were not reported as BLOCKED")
        request = missing_report.get("installation_request", {})
        if not request.get("required") or not request.get("requires_user_approval"):
            raise SystemExit("missing Feishu dependencies did not produce an installation approval request")
        requested_dependencies = {
            item.get("tool") or item.get("skill") or item.get("capability")
            for item in request.get("installations", [])
        }
        if requested_dependencies != {
            "lark-cli", "whiteboard-cli", "beautiful-feishu-whiteboard", "lark-doc", "lark-whiteboard"
        }:
            raise SystemExit("installation request does not cover the Feishu CLIs, style Skill, and executable host workflows")
        bundle = request.get("approval_bundle", {})
        if bundle.get("approval_mode") != "single_explicit_approval":
            raise SystemExit("missing dependencies did not produce one bundled approval")
        if set(bundle.get("single_approval_covers", [])) != requested_dependencies:
            raise SystemExit("single approval does not cover every listed missing dependency")
        if bundle.get("approval_scope") != "all_missing_feishu_dependencies" or "all missing" not in bundle.get("approval_prompt", "").casefold():
            raise SystemExit("bundle approval prompt does not clearly ask once for all missing dependencies")
        if "non-Feishu" not in bundle.get("on_decline", "") or "BLOCKED" not in bundle.get("on_decline", ""):
            raise SystemExit("bundle decline behavior must preserve the core Skill and block only Feishu output")
        excluded_text = " ".join(bundle.get("excludes", [])).casefold()
        if "node.js" not in excluded_text or "authentication" not in excluded_text:
            raise SystemExit("bundle must exclude undisclosed Node.js installation and account authorization")
        requested_skill = next(item for item in request["installations"] if item.get("skill") == "beautiful-feishu-whiteboard")
        if requested_skill.get("install_root") is not None or requested_skill.get("command") is not None:
            raise SystemExit("dependency diagnostic guessed a Skill registry without an explicit host root")
        if not requested_skill.get("requires_host_registration") or not request.get("host_registration_required"):
            raise SystemExit("missing host registry did not request native independent-Skill registration")
        if "zarazhangrui/beautiful-feishu-whiteboard" not in requested_skill.get("host_install_prompt", ""):
            raise SystemExit("host registration request omitted the verified whiteboard Skill source")
        requested_capabilities = {
            item.get("capability"): item
            for item in request["installations"]
            if item.get("capability")
        }
        if set(requested_capabilities) != {"lark-doc", "lark-whiteboard"}:
            raise SystemExit("dependency diagnostic omitted required host capabilities")
        if any("specification alone does not count" not in item.get("host_install_prompt", "") for item in requested_capabilities.values()):
            raise SystemExit("host-capability plan did not distinguish Skill text from executable readiness")
        if len(request.get("approval_commands", [])) != 1:
            raise SystemExit("unresolved host Skill registration must not emit a local file-install command")
        human_missing = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--isolated",
            "--tool-cache", str(empty_cache),
            expect=3,
            env=isolated_env,
        )
        if "ONE APPROVAL FOR ALL LISTED DEPENDENCIES" not in human_missing.stdout:
            raise SystemExit("human dependency plan did not present one bundled approval")

        explicit_root = tmp_path / "explicit-host-registry"
        explicit_env = isolated_env.copy()
        explicit_env["BRIEF3080_SKILL_INSTALL_ROOT"] = str(explicit_root)
        explicit_missing = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(empty_cache),
            expect=3,
            env=explicit_env,
        )
        explicit_request = json.loads(explicit_missing.stdout)["installation_request"]
        explicit_skill = next(item for item in explicit_request["installations"] if item.get("skill") == "beautiful-feishu-whiteboard")
        if explicit_skill.get("install_root") != str((explicit_root / "beautiful-feishu-whiteboard").resolve()):
            raise SystemExit("explicit host Skill registry root was not honored")
        if explicit_skill.get("requires_host_registration") or not explicit_skill.get("command"):
            raise SystemExit("explicit host Skill registry did not enable the approval-gated file installer")
        if len(explicit_request.get("approval_commands", [])) != 2:
            raise SystemExit("explicit CLI/Skill install plan must emit both approval-gated commands")

        optional = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "all",
            "--json",
            "--isolated",
            "--tool-cache", str(empty_cache),
            env=isolated_env,
        )
        optional_report = json.loads(optional.stdout)
        if optional_report.get("overall_status") != "PARTIAL" or optional_report.get("installation_request", {}).get("required"):
            raise SystemExit("non-Feishu dependency reporting must SKIP optional adapters without requesting installation")

        refusal = run(
            sys.executable,
            str(SCRIPTS / "install_optional_dependencies.py"),
            "--tool", "whiteboard-cli",
            "--tool-cache", str(empty_cache),
            expect=3,
            env=isolated_env,
        )
        if "explicit user approval" not in refusal.stderr:
            raise SystemExit("installer did not refuse execution without explicit user approval")
        run(
            sys.executable,
            str(SCRIPTS / "install_optional_dependencies.py"),
            "--tool", "whiteboard-cli",
            "--tool-cache", str(empty_cache),
            "--dry-run",
            env=isolated_env,
        )
        no_registry = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            "--user-approved",
            expect=3,
            env=isolated_env,
        )
        if "no verified host Agent Skill registry root" not in no_registry.stderr:
            raise SystemExit("skill installer did not block an unregistered execution directory")
        host_dry_run = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            "--dry-run",
            env=isolated_env,
        )
        host_plan = json.loads(host_dry_run.stdout)["installation"]
        if not host_plan.get("requires_host_registration") or host_plan.get("command") is not None:
            raise SystemExit("installer dry-run guessed a host registry from its execution path")
        skill_refusal = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            "--install-root", str(tmp_path / "refused-skills"),
            expect=3,
            env=isolated_env,
        )
        if "explicit user approval" not in skill_refusal.stderr:
            raise SystemExit("skill installer did not refuse execution without explicit user approval")
        skill_dry_run = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            "--install-root", str(tmp_path / "portable-skills"),
            "--dry-run",
            env=isolated_env,
        )
        skill_plan = json.loads(skill_dry_run.stdout)["installation"]
        if skill_plan["source"]["repo"] != "zarazhangrui/beautiful-feishu-whiteboard":
            raise SystemExit("skill install plan omitted the verified GitHub source")
        if skill_plan.get("download_url") != "https://github.com/zarazhangrui/beautiful-feishu-whiteboard/archive/refs/heads/main.zip":
            raise SystemExit("skill install plan omitted the verified GitHub archive")
        if not skill_plan.get("requires_agent_reload") or "requires_codex_restart" in skill_plan:
            raise SystemExit("skill install plan must use an agent-agnostic reload requirement")
        expected_install = (tmp_path / "portable-skills" / "beautiful-feishu-whiteboard").resolve()
        if skill_plan["install_root"] != str(expected_install):
            raise SystemExit("skill install plan ignored the host agent skill root")

        local_archive = tmp_path / "beautiful-feishu-whiteboard.zip"
        archive_root = "beautiful-feishu-whiteboard-main"
        with zipfile.ZipFile(local_archive, "w") as bundle:
            bundle.writestr(
                f"{archive_root}/SKILL.md",
                "---\nname: beautiful-feishu-whiteboard\nversion: 1.1.1\ndescription: fixture\n---\n",
            )
            bundle.writestr(f"{archive_root}/CATALOG.md", "# Catalogue\n")
            bundle.writestr(f"{archive_root}/RULES.md", "# Rules\n")
            bundle.writestr(f"{archive_root}/templates/example/design.md", "# Example\n")
        portable_root = tmp_path / "installed-agent-skills"
        portable_install = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            "--install-root", str(portable_root),
            "--archive", str(local_archive),
            "--user-approved",
            env=isolated_env,
        )
        if "REGISTRATION PENDING" not in portable_install.stdout or "Do not treat this dependency as PASS" not in portable_install.stdout:
            raise SystemExit("file installer falsely reported host registration success")
        if portable_install.stdout.startswith("PASS") or "\nPASS " in portable_install.stdout:
            raise SystemExit("file installer conflated file verification with dependency PASS")
        installed_skill = portable_root / "beautiful-feishu-whiteboard"
        if not (installed_skill / "SKILL.md").is_file() or not (installed_skill / "templates").is_dir():
            raise SystemExit("portable skill installer did not preserve the complete skill folder")
        no_overwrite = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            "--install-root", str(portable_root),
            "--archive", str(local_archive),
            "--user-approved",
            expect=1,
            env=isolated_env,
        )
        if "will not be overwritten" not in no_overwrite.stderr:
            raise SystemExit("portable skill installer did not protect an existing destination")

        unsafe_archive = tmp_path / "unsafe-skill.zip"
        with zipfile.ZipFile(unsafe_archive, "w") as bundle:
            bundle.writestr("beautiful-feishu-whiteboard-main/../../outside.txt", "unsafe\n")
        unsafe_install = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            "--install-root", str(tmp_path / "unsafe-agent-skills"),
            "--archive", str(unsafe_archive),
            "--user-approved",
            expect=1,
            env=isolated_env,
        )
        if "unsafe archive member" not in unsafe_install.stderr:
            raise SystemExit("portable skill installer did not reject archive path traversal")

        fake_cache = tmp_path / "fake-cache"
        fake_node = tmp_path / "node"
        fake_node.write_text("#!/bin/sh\necho v20.0.0\n", encoding="utf-8")
        fake_node.chmod(0o755)
        for tool_id, spec in dependency_config["tools"].items():
            prefix = fake_cache / tool_id / spec["install_version"]
            package_root = prefix / "node_modules" / Path(spec["package"])
            bin_root = package_root / "bin"
            bin_root.mkdir(parents=True, exist_ok=True)
            target = bin_root / "cli"
            if tool_id == "lark-cli":
                target.write_text(f"#!/bin/sh\necho 'lark-cli version {spec['install_version']}'\n", encoding="utf-8")
            else:
                target.write_text("#!/bin/sh\necho 'whiteboard help'\n", encoding="utf-8")
            target.chmod(0o755)
            (package_root / "package.json").write_text(json.dumps({"name": spec["package"], "version": spec["install_version"]}), encoding="utf-8")
            shim_dir = prefix / "node_modules" / ".bin"
            shim_dir.mkdir(parents=True, exist_ok=True)
            (shim_dir / spec["command"]).symlink_to(Path("..") / Path(spec["package"]) / "bin" / "cli")
        passing_env = isolated_env.copy()
        passing_env["NODE"] = str(fake_node)
        registered_runtime_root = tmp_path / "registered-runtime-skills"
        registered_main_skill = registered_runtime_root / "3080-brief"
        registered_main_skill.mkdir(parents=True)
        (registered_main_skill / "SKILL.md").write_text(
            "---\nname: 3080-brief\ndescription: fixture\n---\n",
            encoding="utf-8",
        )
        staged_only = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(fake_cache),
            "--skill-root", str(registered_runtime_root),
            expect=3,
            env=passing_env,
        )
        staged_skill_check = next(
            check for check in json.loads(staged_only.stdout)["checks"] if check["id"] == "beautiful-feishu-whiteboard"
        )
        if staged_skill_check["status"] != "BLOCKED":
            raise SystemExit("a dependency copied outside the registered runtime root was incorrectly accepted")

        registered_dependency = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(fake_cache),
            "--skill-root", str(portable_root),
            "--host-capability", "lark-doc",
            "--host-capability", "lark-whiteboard",
            env=passing_env,
        )
        if json.loads(registered_dependency.stdout).get("overall_status") != "PASS":
            raise SystemExit("dependency installed in the declared runtime registry did not pass recheck")

        fake_skill_root = tmp_path / "fake-skills"
        fake_skill = fake_skill_root / "beautiful-feishu-whiteboard"
        (fake_skill / "templates").mkdir(parents=True)
        (fake_skill / "SKILL.md").write_text(
            "---\nname: beautiful-feishu-whiteboard\nversion: 1.1.1\ndescription: fixture\n---\n",
            encoding="utf-8",
        )
        (fake_skill / "CATALOG.md").write_text("# Catalogue\n", encoding="utf-8")
        (fake_skill / "RULES.md").write_text("# Rules\n", encoding="utf-8")
        runtime_unready = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(fake_cache),
            "--skill-root", str(fake_skill_root),
            expect=3,
            env=passing_env,
        )
        runtime_unready_report = json.loads(runtime_unready.stdout)
        blocked_host_capabilities = {
            check["id"] for check in runtime_unready_report["checks"]
            if check.get("kind") == "host_capability" and check["status"] == "BLOCKED"
        }
        if blocked_host_capabilities != {"lark-doc", "lark-whiteboard"}:
            raise SystemExit("installed files were incorrectly treated as executable host readiness")
        passing = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(fake_cache),
            "--skill-root", str(fake_skill_root),
            "--host-capability", "lark-doc",
            "--host-capability", "lark-whiteboard",
            env=passing_env,
        )
        passing_report = json.loads(passing.stdout)
        if passing_report.get("overall_status") != "PASS":
            raise SystemExit(f"compatible cached Feishu dependencies did not pass: {passing_report}")

        whiteboard_spec = dependency_config["tools"]["whiteboard-cli"]
        whiteboard_package = fake_cache / "whiteboard-cli" / whiteboard_spec["install_version"] / "node_modules" / Path(whiteboard_spec["package"]) / "package.json"
        whiteboard_package.write_text(json.dumps({"name": whiteboard_spec["package"], "version": "0.2.12"}), encoding="utf-8")
        mismatch = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(fake_cache),
            "--skill-root", str(fake_skill_root),
            "--host-capability", "lark-doc",
            "--host-capability", "lark-whiteboard",
            expect=3,
            env=passing_env,
        )
        mismatch_report = json.loads(mismatch.stdout)
        whiteboard_check = next(check for check in mismatch_report["checks"] if check["id"] == "whiteboard-cli")
        if whiteboard_check["status"] != "BLOCKED" or "exact policy 0.2.11" not in whiteboard_check["reason"]:
            raise SystemExit("whiteboard CLI version drift was not blocked")

        whiteboard_package.write_text(json.dumps({"name": whiteboard_spec["package"], "version": "0.2.11"}), encoding="utf-8")
        (fake_skill / "CATALOG.md").unlink()
        skill_contract_failure = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(fake_cache),
            "--skill-root", str(fake_skill_root),
            "--host-capability", "lark-doc",
            "--host-capability", "lark-whiteboard",
            expect=3,
            env=passing_env,
        )
        skill_check = next(check for check in json.loads(skill_contract_failure.stdout)["checks"] if check["id"] == "beautiful-feishu-whiteboard")
        if skill_check["status"] != "BLOCKED" or "CATALOG.md" not in skill_check["reason"]:
            raise SystemExit("incomplete beautiful-feishu-whiteboard installation was not blocked")

    run(
        sys.executable,
        str(SCRIPTS / "aggregate_reviews.py"),
        str(FIXTURES / "review-reader.json"),
        str(FIXTURES / "review-source.json"),
        str(FIXTURES / "review-visual.json"),
    )
    trigger_suite = json.loads((SKILL / "evals" / "trigger_cases.json").read_text(encoding="utf-8"))
    boundary_suite = json.loads((SKILL / "evals" / "boundary_cases.json").read_text(encoding="utf-8"))
    output_coverage = json.loads((SKILL / "evals" / "output_coverage.json").read_text(encoding="utf-8"))
    json.loads((SKILL / "evals" / "review.schema.json").read_text(encoding="utf-8"))
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill_text.split("---", 2)[1].casefold()
    for alias in config["trigger"]["aliases"]:
        if alias.casefold() not in frontmatter:
            raise SystemExit(f"trigger alias missing from frontmatter description: {alias}")
    for required in ("do not use for editing or polishing", "generic summary", "standalone whiteboard"):
        if required.casefold() not in frontmatter:
            raise SystemExit(f"non-trigger metadata contract missing: {required}")
    trigger_cases = trigger_suite.get("cases", [])
    if len(trigger_cases) != 20:
        raise SystemExit(f"trigger suite must contain exactly 20 scored cases, got {len(trigger_cases)}")
    case_ids = [case.get("id") for case in trigger_cases]
    if len(case_ids) != len(set(case_ids)) or any(not case_id for case_id in case_ids):
        raise SystemExit("trigger case IDs must be present and unique")
    required_case_fields = {"id", "split", "should_trigger", "category", "query", "rationale"}
    for case in trigger_cases:
        missing = required_case_fields - set(case)
        if missing:
            raise SystemExit(f"trigger case {case.get('id', '<unknown>')} missing fields: {sorted(missing)}")
        if case["split"] not in {"train", "validation"}:
            raise SystemExit(f"trigger case {case['id']} has invalid split: {case['split']}")
        if not isinstance(case["should_trigger"], bool):
            raise SystemExit(f"trigger case {case['id']} should_trigger must be boolean")
        if not all(isinstance(case[field], str) and case[field].strip() for field in ("category", "query", "rationale")):
            raise SystemExit(f"trigger case {case['id']} has empty category, query, or rationale")

    positives = [case for case in trigger_cases if case["should_trigger"]]
    negatives = [case for case in trigger_cases if not case["should_trigger"]]
    if len(positives) != 10 or len(negatives) != 10:
        raise SystemExit(f"trigger suite must be balanced 10/10, got {len(positives)} positive and {len(negatives)} negative")
    train_cases = [case for case in trigger_cases if case["split"] == "train"]
    validation_cases = [case for case in trigger_cases if case["split"] == "validation"]
    if len(train_cases) != 12 or len(validation_cases) != 8:
        raise SystemExit(f"trigger suite must use a fixed 12/8 train-validation split, got {len(train_cases)}/{len(validation_cases)}")
    for split in ("train", "validation"):
        split_cases = [case for case in trigger_cases if case["split"] == split]
        split_positive = sum(case["should_trigger"] for case in split_cases)
        if split_positive * 2 != len(split_cases):
            raise SystemExit(f"trigger split {split} must contain equal positive and negative cases")
    required_positive_categories = {"explicit_alias", "implicit_full_intent", "casual_language", "buried_in_long_context", "english_implicit"}
    positive_categories = {case["category"] for case in positives}
    if not required_positive_categories <= positive_categories:
        raise SystemExit(f"trigger positives missing categories: {sorted(required_positive_categories - positive_categories)}")
    required_negative_categories = {"edit_in_place", "generic_summary", "whiteboard_only", "review_existing", "explicit_negation"}
    negative_categories = {case["category"] for case in negatives}
    if not required_negative_categories <= negative_categories:
        raise SystemExit(f"trigger negatives missing categories: {sorted(required_negative_categories - negative_categories)}")
    hard_negative_categories = {case["category"] for case in negatives if case.get("hard_negative")}
    if hard_negative_categories != {"edit_in_place", "whiteboard_only", "explicit_negation"}:
        raise SystemExit("hard negatives must cover edit-in-place, whiteboard-only, and explicit-negation boundaries")

    evaluation = trigger_suite.get("evaluation", {})
    if evaluation.get("runs_per_case") != 3:
        raise SystemExit("trigger suite must specify 3 runs per case")
    if evaluation.get("validation_min_balanced_accuracy") != 0.9:
        raise SystemExit("trigger suite validation balanced-accuracy threshold must be 0.9")
    if not evaluation.get("runner_contract"):
        raise SystemExit("trigger suite runner contract is missing")

    boundary_cases = boundary_suite.get("cases", [])
    if len(boundary_cases) < 4:
        raise SystemExit("boundary suite must contain at least 4 policy-review cases")
    for case in boundary_cases:
        if case.get("status") != "policy_review":
            raise SystemExit(f"boundary case {case.get('id', '<unknown>')} must remain policy_review")
        if "should_trigger" in case:
            raise SystemExit(f"boundary case {case.get('id', '<unknown>')} must not enter automated scoring")
        if not isinstance(case.get("recommended_label"), bool):
            raise SystemExit(f"boundary case {case.get('id', '<unknown>')} recommended_label must be boolean")
    if not output_coverage.get("source_archetypes") or not output_coverage.get("failure_archetypes"):
        raise SystemExit("output coverage archetypes are empty")
    replay = config.get("blind_reader_replay", {})
    if replay.get("question_count") != 3 or replay.get("primary_role") != "primary":
        raise SystemExit("blind-reader replay contract is missing or invalid")
    if set(replay.get("roles", {})) != {"primary", "technical", "decision"}:
        raise SystemExit("blind-reader replay roles are incomplete")
    if len(replay.get("escalation_conditions", [])) != 6:
        raise SystemExit("blind-reader replay escalation gate is incomplete")
    opening = config.get("tldr", {}).get("opening_unit", {})
    if opening != {
        "primary_judgment_count": 1,
        "support_lines_min": 1,
        "support_lines_max": 3,
        "allowed_support_roles": ["evidence", "action", "boundary"],
        "fixed_label_prefixes": ["结论", "证据", "行动", "下一步", "边界", "Conclusion", "Evidence", "Action", "Next step", "Boundary"],
        "fixed_label_failure_count": 2,
    }:
        raise SystemExit("TLDR opening-unit contract is missing or inconsistent")
    if {"default_summary_lines_min", "default_summary_lines_max"} & set(config.get("tldr", {})):
        raise SystemExit("legacy summary-line configuration must not return")
    language_policy = config.get("language_policy", {})
    if language_policy.get("default_output_basis") != "source_primary_language":
        raise SystemExit("language policy default must follow source primary language")
    if language_policy.get("allowed_override_basis") != "explicit_user_request":
        raise SystemExit("language policy override must require an explicit user request")
    if "conversation_language" not in language_policy.get("forbidden_inference_bases", []):
        raise SystemExit("language policy must reject conversation language as override evidence")
    expression = config.get("expression_quality", {})
    if expression.get("required_relation_priorities") != ["P0", "P1"]:
        raise SystemExit("expression contract must protect P0 and P1 relations")
    if expression.get("claim_strength_order") != [
        "unknown", "reported", "observed", "suggestive", "supported", "demonstrated", "causal"
    ]:
        raise SystemExit("expression claim-strength order is missing or inconsistent")
    thin_guardrail = expression.get("thin_source_guardrail", {})
    if thin_guardrail.get("source_snapshot_required") is not True:
        raise SystemExit("thin-source guardrail must require a non-appendix source snapshot")
    if (
        thin_guardrail.get("max_expansion_ratio") != 4.0
        or thin_guardrail.get("minimum_output_unit_ceiling") != 240
        or thin_guardrail.get("max_body_sections") != 2
    ):
        raise SystemExit("thin-source expansion ceiling is missing or inconsistent")
    profiles = expression.get("runtime_profiles", {})
    if set(profiles) != {"fast", "standard", "strict"}:
        raise SystemExit("expression runtime profiles must define fast, standard, and strict")
    if any(profile.get("hard_gates") != "all" for profile in profiles.values()):
        raise SystemExit("every runtime profile must retain all deterministic hard gates")
    if profiles["fast"].get("selection") != "explicit_user_request_only" or profiles["fast"].get("review") != "self_check_only":
        raise SystemExit("fast profile must be explicit and cannot claim independent review")
    if profiles["fast"].get("audit_sequence_terminal") != "after_self_check":
        raise SystemExit("fast profile must stop the audit sequence after self-check")
    if profiles["standard"].get("selection") != "default" or profiles["standard"].get("review") != "three_independent_reviewers":
        raise SystemExit("standard profile must remain the independently reviewed default")
    if profiles["strict"].get("relation_replay") != "all_non_appendix_p0_p1":
        raise SystemExit("strict profile must replay every non-appendix P0/P1 relation")
    if len(expression.get("style_warning_groups", [])) < 6:
        raise SystemExit("expression warning groups do not cover both Chinese and English")
    replay_path = SKILL / "references" / "blind-reader-replay.md"
    if not replay_path.is_file() or "Run Blind Reader Replay only after" not in replay_path.read_text(encoding="utf-8"):
        raise SystemExit("blind-reader replay reference is missing")
    if "run_3080.py record-review" not in skill_text or "references/blind-reader-replay.md" not in skill_text:
        raise SystemExit("blind-reader replay is not connected to the runtime workflow")
    print("3080-brief evals PASS")


if __name__ == "__main__":
    main()
