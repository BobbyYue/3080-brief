#!/usr/bin/env python3
import json
import os
import py_compile
import subprocess
import sys
import tempfile
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
    json.loads((SKILL / "config" / "dependencies.json").read_text(encoding="utf-8"))
    json.loads((SKILL / "references" / "claim-ledger.schema.json").read_text(encoding="utf-8"))
    json.loads((SKILL / "references" / "visual-spec.schema.json").read_text(encoding="utf-8"))
    inventory_zh = FIXTURES / "inventory-zh-source.md"

    run(sys.executable, str(SCRIPTS / "validate_skill.py"), str(SKILL))
    run(sys.executable, str(SCRIPTS / "check_context_budget.py"), str(SKILL))
    run(sys.executable, str(SCRIPTS / "check_dependencies.py"), "--mode", "core")

    run(sys.executable, str(SCRIPTS / "preflight_check.py"), str(FIXTURES / "valid-brief.md"), "--source-inventory", str(inventory_zh))
    run(sys.executable, str(SCRIPTS / "preflight_check.py"), str(FIXTURES / "valid-brief.xml"), "--format", "xml", "--source-inventory", str(inventory_zh))
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
    run(sys.executable, str(SCRIPTS / "preflight_check.py"), str(FIXTURES / "invalid-audience-heading.md"), "--source-inventory", str(inventory_zh), expect=1)
    warning_result = run(sys.executable, str(SCRIPTS / "preflight_check.py"), str(FIXTURES / "warning-vague-brief.md"), "--source-inventory", str(inventory_zh))
    if "discouraged vague phrase" not in warning_result.stdout:
        raise SystemExit("preflight did not warn on configured discouraged phrase")

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
            "--inventory", str(SKILL / "references" / "source-inventory-template.md"),
            "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
            "--tldr", str(FIXTURES / "valid-brief.md"),
            "--body", str(FIXTURES / "valid-brief.md"),
            "--draft", str(FIXTURES / "valid-brief.md"),
            "--visual-spec", str(FIXTURES / "visual-spec.json"),
            "--whiteboard-preview", str(svg),
        )

    with tempfile.TemporaryDirectory(prefix="3080-brief-dependencies-") as tmp:
        tmp_path = Path(tmp)
        empty_cache = tmp_path / "empty-cache"
        isolated_env = os.environ.copy()
        isolated_env.pop("LARK_CLI", None)
        isolated_env.pop("WHITEBOARD_CLI", None)
        isolated_env.pop("BEAUTIFUL_FEISHU_WHITEBOARD_SKILL", None)
        isolated_env.pop("BRIEF3080_SKILL_ROOTS", None)
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
        requested_dependencies = {item.get("tool") or item.get("skill") for item in request.get("installations", [])}
        if requested_dependencies != {"lark-cli", "whiteboard-cli", "beautiful-feishu-whiteboard"}:
            raise SystemExit("installation request does not cover both Feishu CLIs and the whiteboard style skill")
        if len(request.get("approval_commands", [])) != 2:
            raise SystemExit("mixed CLI/skill dependency request must emit separate approval-gated commands")

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
        )
        if "explicit user approval" not in refusal.stderr:
            raise SystemExit("installer did not refuse execution without explicit user approval")
        run(
            sys.executable,
            str(SCRIPTS / "install_optional_dependencies.py"),
            "--tool", "whiteboard-cli",
            "--tool-cache", str(empty_cache),
            "--dry-run",
        )
        skill_refusal = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            expect=3,
        )
        if "explicit user approval" not in skill_refusal.stderr:
            raise SystemExit("skill installer did not refuse execution without explicit user approval")
        skill_dry_run = run(
            sys.executable,
            str(SCRIPTS / "install_skill_dependency.py"),
            "--skill", "beautiful-feishu-whiteboard",
            "--dry-run",
        )
        skill_plan = json.loads(skill_dry_run.stdout)["installation"]
        if skill_plan["source"]["repo"] != "zarazhangrui/beautiful-feishu-whiteboard" or not skill_plan["requires_codex_restart"]:
            raise SystemExit("skill install plan omitted the verified source or restart requirement")

        fake_cache = tmp_path / "fake-cache"
        fake_node = tmp_path / "node"
        fake_node.write_text("#!/bin/sh\necho v20.0.0\n", encoding="utf-8")
        fake_node.chmod(0o755)
        dependency_config = json.loads((SKILL / "config" / "dependencies.json").read_text(encoding="utf-8"))
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
        fake_skill_root = tmp_path / "fake-skills"
        fake_skill = fake_skill_root / "beautiful-feishu-whiteboard"
        (fake_skill / "templates").mkdir(parents=True)
        (fake_skill / "SKILL.md").write_text(
            "---\nname: beautiful-feishu-whiteboard\nversion: 1.1.1\ndescription: fixture\n---\n",
            encoding="utf-8",
        )
        (fake_skill / "CATALOG.md").write_text("# Catalogue\n", encoding="utf-8")
        (fake_skill / "RULES.md").write_text("# Rules\n", encoding="utf-8")
        passing = run(
            sys.executable,
            str(SCRIPTS / "check_dependencies.py"),
            "--mode", "feishu",
            "--json",
            "--isolated",
            "--tool-cache", str(fake_cache),
            "--skill-root", str(fake_skill_root),
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
    replay_path = SKILL / "references" / "blind-reader-replay.md"
    if not replay_path.is_file() or "Run Blind Reader Replay only after" not in replay_path.read_text(encoding="utf-8"):
        raise SystemExit("blind-reader replay reference is missing")
    if "### 7. Replay Reader Understanding" not in skill_text or "references/blind-reader-replay.md" not in skill_text:
        raise SystemExit("blind-reader replay is not connected to the runtime workflow")
    print("3080-brief evals PASS")


if __name__ == "__main__":
    main()
