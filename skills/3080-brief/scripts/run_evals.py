#!/usr/bin/env python3
import json
import os
import py_compile
import re
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
    json.loads((SKILL / "references" / "brief.schema.json").read_text(encoding="utf-8"))
    theme_registry = json.loads((SKILL / "assets" / "themes" / "beautiful-feishu-themes.json").read_text(encoding="utf-8"))
    themes = theme_registry.get("themes") or []
    if len(themes) != 22:
        raise SystemExit(f"theme registry must contain the 22 allowed themes, found {len(themes)}")
    banned = {name.casefold() for name in config.get("banned_whiteboard_styles", [])}
    if any(theme.get("name", "").casefold() in banned for theme in themes):
        raise SystemExit("theme registry contains a banned whiteboard style")
    required_tokens = {"background", "surface", "surface_subtle", "ink", "muted", "rule", "accent", "accent2", "visual_primary", "visual_accent", "radius", "border_width", "content_width", "section_gap"}
    for theme in themes:
        if not required_tokens <= set(theme.get("tokens") or {}):
            raise SystemExit(f"theme {theme.get('name', '<unnamed>')} is missing required HTML/visual tokens")
    if not (SKILL / "assets" / "themes" / "LICENSE.beautiful-feishu-whiteboard.txt").is_file():
        raise SystemExit("theme adaptation must include the upstream MIT notice")
    expression_suite = json.loads((SKILL / "evals" / "expression_cases.json").read_text(encoding="utf-8"))
    inventory_zh = FIXTURES / "inventory-zh-source.md"

    review_packet_text = (SCRIPTS / "build_review_packet.py").read_text(encoding="utf-8")
    if "Every value-bearing title, heading, and lead identifies the actual object" not in review_packet_text:
        raise SystemExit("reader review packet omitted the concrete value-expression gate")

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
    run(sys.executable, str(SCRIPTS / "validate_visual_spec.py"), str(FIXTURES / "html-visual-spec.json"), str(FIXTURES / "claim-ledger.json"))
    run(sys.executable, str(SCRIPTS / "validate_brief.py"), str(FIXTURES / "html-brief.json"), str(FIXTURES / "visual-spec.json"))

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

        html_output = tmp_path / "synthetic-brief.html"
        run(
            sys.executable,
            str(SCRIPTS / "build_html_brief.py"),
            str(FIXTURES / "html-brief.json"),
            str(FIXTURES / "html-visual-spec.json"),
            str(html_output),
        )
        run(
            sys.executable,
            str(SCRIPTS / "preflight_check.py"),
            str(html_output),
            "--format", "html",
            "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
            "--source-inventory", str(inventory_zh),
        )
        run(
            sys.executable,
            str(SCRIPTS / "validate_html_output.py"),
            str(html_output),
            "--visual-spec", str(FIXTURES / "html-visual-spec.json"),
        )
        html_text = html_output.read_text(encoding="utf-8")
        for expected in ("@media print", "@media (max-width", "class=\"one-picture\"", "data-priority=\"P2\"", "data-theme=\"avocado-press\""):
            if expected not in html_text:
                raise SystemExit(f"HTML renderer omitted required output feature: {expected}")

        stage_story_output = tmp_path / "stage-story-brief.html"
        stage_story_spec = FIXTURES / "html-stage-story-visual-spec.json"
        run(
            sys.executable,
            str(SCRIPTS / "build_html_brief.py"),
            str(FIXTURES / "html-brief.json"),
            str(stage_story_spec),
            str(stage_story_output),
        )
        run(
            sys.executable,
            str(SCRIPTS / "validate_html_output.py"),
            str(stage_story_output),
            "--visual-spec", str(stage_story_spec),
        )
        stage_story_text = stage_story_output.read_text(encoding="utf-8")
        for expected in ('data-composition="stage_story"', "14 分钟", "4 分钟", "8 倍", "首次分析中位数"):
            if expected not in stage_story_text:
                raise SystemExit(f"stage-story renderer omitted visible payload: {expected}")
        view_box = re.search(r'<svg[^>]+viewBox="0 0 ([0-9.]+) ([0-9.]+)"', stage_story_text)
        if not view_box or float(view_box.group(1)) / float(view_box.group(2)) < 1.2:
            raise SystemExit("stage-story renderer produced a sparse vertical one-picture canvas")

        empty_annotation_spec = json.loads((FIXTURES / "html-visual-spec.json").read_text(encoding="utf-8"))
        empty_annotation_spec["blocks"].append({
            "id": "B03",
            "type": "annotation",
            "visual_role": "support",
            "relationship": "annotation",
            "render_target": "html",
            "interaction": "none",
            "claim_ids": ["C04"],
            "title": "Title-only block",
        })
        empty_annotation_path = tmp_path / "empty-annotation.json"
        empty_annotation_path.write_text(json.dumps(empty_annotation_spec, ensure_ascii=False), encoding="utf-8")
        empty_annotation = run(
            sys.executable,
            str(SCRIPTS / "validate_visual_spec.py"),
            str(empty_annotation_path),
            str(FIXTURES / "claim-ledger.json"),
            expect=1,
        )
        if "no visible payload" not in empty_annotation.stdout:
            raise SystemExit("visual-spec gate did not reject a title-only annotation block")
        for theme in themes:
            themed_spec = json.loads((FIXTURES / "html-visual-spec.json").read_text(encoding="utf-8"))
            themed_spec["style"] = theme["name"]
            themed_spec["style_rationale"] = "Registry-wide render verification for a content-fit selected theme."
            themed_spec_path = tmp_path / f"theme-{theme['slug']}.json"
            themed_spec_path.write_text(json.dumps(themed_spec, ensure_ascii=False), encoding="utf-8")
            themed_output = tmp_path / f"theme-{theme['slug']}.html"
            run(sys.executable, str(SCRIPTS / "build_html_brief.py"), str(FIXTURES / "html-brief.json"), str(themed_spec_path), str(themed_output))
            if f'data-theme="{theme["slug"]}"' not in themed_output.read_text(encoding="utf-8"):
                raise SystemExit(f"HTML renderer did not apply registered theme {theme['name']}")

        feishu_output = tmp_path / "synthetic-brief.xml"
        run(
            sys.executable,
            str(SCRIPTS / "build_feishu_brief.py"),
            str(FIXTURES / "html-brief.json"),
            str(FIXTURES / "visual-spec.json"),
            str(feishu_output),
        )
        run(
            sys.executable,
            str(SCRIPTS / "preflight_check.py"),
            str(feishu_output),
            "--format", "xml",
            "--claim-ledger", str(FIXTURES / "claim-ledger.json"),
            "--source-inventory", str(inventory_zh),
        )
        feishu_text = feishu_output.read_text(encoding="utf-8")
        for expected in ("<colgroup>", 'vertical-align="top"', "<blockquote>", "#F5F7FA"):
            if expected not in feishu_text:
                raise SystemExit(f"Feishu renderer omitted required native output feature: {expected}")
        if feishu_text.count('<whiteboard type="svg">') < 2:
            raise SystemExit("Feishu renderer did not preserve the source-grounded body figure")

        reading_room_spec = json.loads((FIXTURES / "html-visual-spec.json").read_text(encoding="utf-8"))
        reading_room_spec["style"] = "Reading Room"
        reading_room_spec["style_rationale"] = "长篇复盘面向正式读者，需要更强的出版感与章节秩序。"
        reading_room_path = tmp_path / "reading-room-spec.json"
        reading_room_path.write_text(json.dumps(reading_room_spec, ensure_ascii=False), encoding="utf-8")
        reading_room_html = tmp_path / "reading-room.html"
        run(sys.executable, str(SCRIPTS / "build_html_brief.py"), str(FIXTURES / "html-brief.json"), str(reading_room_path), str(reading_room_html))
        reading_room_text = reading_room_html.read_text(encoding="utf-8")
        if 'data-theme="reading-room"' not in reading_room_text or reading_room_text == html_text:
            raise SystemExit("HTML theme selection did not produce a distinct selected theme")

        for case_name, replacement, expected_error in (
            ("banned", {"style": "Riso Brut"}, "theme is banned"),
            ("unknown", {"style": "Imaginary Theme"}, "unknown Beautiful Feishu Whiteboard theme"),
            ("missing-rationale", {"style_rationale": ""}, "style_rationale"),
        ):
            invalid_spec = json.loads((FIXTURES / "visual-spec.json").read_text(encoding="utf-8"))
            invalid_spec.update(replacement)
            invalid_spec_path = tmp_path / f"{case_name}-theme.json"
            invalid_spec_path.write_text(json.dumps(invalid_spec, ensure_ascii=False), encoding="utf-8")
            invalid_theme = run(
                sys.executable,
                str(SCRIPTS / "validate_visual_spec.py"),
                str(invalid_spec_path),
                str(FIXTURES / "claim-ledger.json"),
                expect=1,
            )
            if expected_error not in invalid_theme.stdout:
                raise SystemExit(f"visual theme gate did not reject {case_name}")

        dense_first = json.loads((FIXTURES / "html-brief.json").read_text(encoding="utf-8"))
        dense_first["body"][0]["blocks"].insert(0, {"type": "table", "headers": ["A"], "rows": [["B"]]})
        dense_first_path = tmp_path / "dense-first.json"
        dense_first_path.write_text(json.dumps(dense_first, ensure_ascii=False), encoding="utf-8")
        dense_failure = run(
            sys.executable,
            str(SCRIPTS / "validate_brief.py"),
            str(dense_first_path),
            str(FIXTURES / "visual-spec.json"),
            expect=1,
        )
        if "must explain the judgment before" not in dense_failure.stdout:
            raise SystemExit("shared brief gate did not reject an unexplained dense body section")
        invalid_html = tmp_path / "external-runtime.html"
        invalid_html.write_text(html_text.replace("</body>", '<script src="https://example.invalid/chart.js"></script></body>'), encoding="utf-8")
        external_failure = run(
            sys.executable,
            str(SCRIPTS / "validate_html_output.py"),
            str(invalid_html),
            "--visual-spec", str(FIXTURES / "html-visual-spec.json"),
            expect=1,
        )
        if "external runtime resources" not in external_failure.stdout:
            raise SystemExit("HTML validator did not reject an external runtime resource")

        chart_gallery_spec = {
            "title": "Renderer coverage fixture",
            "language": "en",
            "style": "Avocado Press",
            "style_rationale": "定量图表族测试需要克制、清晰并支持多种比较关系。",
            "reading_path": "Render supported P0 chart families",
            "blocks": [
                {"id": "L", "type": "line", "claim_ids": ["C"], "title": "Trend changes", "metric_scope": {"metric": "value"}, "items": [{"label": "A", "value": 1}, {"label": "B", "value": 3}]},
                {"id": "S", "type": "slope", "claim_ids": ["C"], "title": "Before and after differ", "metric_scope": {"metric": "value"}, "items": [{"label": "A", "start": 1, "end": 4}]},
                {"id": "P", "type": "scatter", "claim_ids": ["C"], "title": "Observed pairs differ", "metric_scope": {"metric": "pair"}, "items": [{"label": "A", "x": 1, "y": 2}, {"label": "B", "x": 2, "y": 4}]},
                {"id": "H", "type": "heatmap", "claim_ids": ["C"], "title": "Segments differ", "metric_scope": {"metric": "score"}, "rows": ["R1"], "columns": ["C1", "C2"], "cells": [{"row": "R1", "column": "C1", "value": 1}, {"row": "R1", "column": "C2", "value": 2}]},
                {"id": "F", "type": "funnel", "claim_ids": ["C"], "title": "Scope narrows", "metric_scope": {"metric": "count"}, "items": [{"label": "Start", "value": 100}, {"label": "End", "value": 60}]}
            ]
        }
        gallery_spec = tmp_path / "chart-gallery.json"
        gallery_spec.write_text(json.dumps(chart_gallery_spec), encoding="utf-8")
        gallery_svg = tmp_path / "chart-gallery.svg"
        run(sys.executable, str(SCRIPTS / "render_visual_spec.py"), str(gallery_spec), str(gallery_svg))
        gallery_text = gallery_svg.read_text(encoding="utf-8")
        for title in ("Trend changes", "Before and after differ", "Observed pairs differ", "Segments differ", "Scope narrows"):
            if title not in gallery_text:
                raise SystemExit(f"native SVG renderer omitted chart family fixture: {title}")

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
    if "### 7. Replay Reader Understanding" not in skill_text or "references/blind-reader-replay.md" not in skill_text:
        raise SystemExit("blind-reader replay is not connected to the runtime workflow")
    print("3080-brief evals PASS")


if __name__ == "__main__":
    main()
