"""Synthetic end-to-end enforcement tests, not claims of writing quality."""
import contextlib
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import direct_expression
import reader_answers
import writing_lifecycle as lifecycle
import writing_execution
import lifecycle_delivery
import plan_review_scope
import review_wire
import editorial_gate
import reader_value
import body_completion
from lifecycle_fixture import prepare_flow, save
from expression_fixture import structural_expression
import test_reader_answers as opening_fixture
import test_checked_delivery_cli as full_fixture
import test_checked_delivery_fast as fast_fixture
import test_checked_delivery_scoped as scoped_fixture


class ReadingSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_authoring_excerpts_and_visual_metadata_do_not_inflate_occurrences(self):
        text = "不要关闭审计日志。\n本次演练使用合成样本。"
        candidate = self.root / "brief.md"
        candidate.write_text(text, encoding="utf-8")
        excerpts = self.root / "tldr.md"
        excerpts.write_text(text, encoding="utf-8")
        spec = save(self.root / "visual.json", {"metadata": "不能省略的内部提示，不是可见内容"})
        bundle = {"body_candidate": body_completion.ref(candidate),
                  "text": [body_completion.ref(p) for p in (candidate, excerpts, spec)]}
        visible = editorial_gate.expression_text(bundle)
        self.assertEqual(visible, text)
        combined = "\n".join(reader_value.read_text(e["path"]) for e in bundle["text"])
        template = reader_value.template(("expression",), "fixture", combined, expression_text=visible)
        review = template["checks"]["expression"]["direct_expression"]
        self.assertEqual(review["text_sha256"], direct_expression.sha(text))
        self.assertEqual(len(review["comparisons"]), 1)
        self.assertEqual(len(review["comparisons"][0]["occurrences"]), 1)
        self.assertEqual(review["whole_text"]["clusters"], [])

    def test_real_repetition_in_delivered_candidate_is_preserved(self):
        text = "不要关闭审计日志。\n不要关闭审计日志。"
        candidate = self.root / "brief.md"
        candidate.write_text(text, encoding="utf-8")
        visible = editorial_gate.expression_text({"body_candidate": body_completion.ref(candidate)})
        record = direct_expression.template(visible)
        self.assertEqual(len(record["comparisons"][0]["occurrences"]), 2)
        self.assertTrue(record["whole_text"]["clusters"])

    def test_actual_render_snapshot_is_used_and_bound_to_html(self):
        candidate = self.root / "brief.html"
        candidate.write_text('<style>.hidden{display:none}</style><p>先复核发布条件。</p><p class="hidden">不能省略的内部草稿</p>')
        snapshot = self.root / "visible.txt"
        snapshot.write_text("先复核发布条件。", encoding="utf-8")
        bundle = {"delivery_artifact": body_completion.ref(candidate),
                  "body_visible_text": body_completion.visible_ref(snapshot, candidate)}
        self.assertEqual(editorial_gate.expression_text(bundle), snapshot.read_text())
        changed = copy.deepcopy(bundle)
        changed["body_visible_text"]["candidate_sha256"] = "different"
        with self.assertRaisesRegex(ValueError, "another candidate"):
            editorial_gate.expression_text(changed)
        snapshot.write_text("替换后的快照", encoding="utf-8")
        with self.assertRaises(ValueError):
            editorial_gate.expression_text(bundle)

    def test_css_hidden_content_cannot_replace_render_evidence(self):
        candidate = self.root / "brief.html"
        candidate.write_text('<style>.hidden{display:none}</style><p class="hidden">不能省略的内部草稿</p>')
        with self.assertRaisesRegex(ValueError, "body-visible-text"):
            editorial_gate.expression_text({"body_candidate": body_completion.ref(candidate)})

    def test_feishu_xml_uses_text_not_markup_as_reading_surface(self):
        candidate = self.root / "brief.xml"
        candidate.write_text('<doc><heading>先复核发布条件</heading><p>不要关闭审计日志。</p></doc>', encoding="utf-8")
        value = editorial_gate.expression_text({"body_candidate": body_completion.ref(candidate)})
        self.assertNotIn("<", value)
        self.assertIn("不要关闭审计日志。", value)


class PlanAndUnitIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.text = self.root / "unit.txt"
        self.text.write_text("不能省略的责任：记录回滚结果。\n不能省略的责任：复核发布条件。", encoding="utf-8")

    def test_reader_lock_requires_expression_plan_and_existing_answers(self):
        fixture = opening_fixture.ReaderAnswersTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        for bad in (None, {}, dict(fixture.plan["expression_plan"], lead_answer_ids=["missing"])):
            with self.subTest(value=bad):
                plan = copy.deepcopy(fixture.plan)
                plan["expression_plan"] = bad
                save(fixture.plan_path, plan)
                with self.assertRaisesRegex(ValueError, "expression_plan"):
                    reader_answers.lock_plan(fixture.plan_path, fixture.source_path)

    def test_native_adapter_derives_expression_plan_and_rejects_drift(self):
        fixture = opening_fixture.ReaderAnswersTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.prepare()
        flow = prepare_flow(lifecycle, self.root, self.text)
        run, bound = self.root / "native-run", self.root / "native-plan.json"
        lifecycle_delivery.init_from_native(run, flow["plan"], fixture.lock_path, bound)
        self.assertEqual(lifecycle.load_json(bound)["expression_plan"], fixture.plan["expression_plan"])
        lifecycle_delivery.verify_native_context(lifecycle, run, self.text, [fixture.source_path], fixture.lock_path)
        changed = lifecycle.load_json(bound)
        changed["expression_plan"]["opening_reason"] = "SYNTHETIC different reason, not the original lock."
        changed_path = save(self.root / "drifted.json", changed)
        drifted = self.root / "drifted-run"
        lifecycle.init_run(drifted, changed_path, "functional", [fixture.source_path])
        with self.assertRaisesRegex(ValueError, "expression plan drifted"):
            lifecycle_delivery.verify_native_context(lifecycle, drifted, self.text, [fixture.source_path], fixture.lock_path)

    def test_functional_init_cannot_skip_preplan(self):
        flow = prepare_flow(lifecycle, self.root, self.text)
        plan = lifecycle.load_json(flow["plan"])
        del plan["expression_plan"]
        path = save(self.root / "no-plan.json", plan)
        with self.assertRaisesRegex(ValueError, "expression_plan"):
            lifecycle.init_run(self.root / "missing-preplan", path, "functional", [flow["source"]])

    def test_unit_rejects_missing_stale_or_unresolved_comparison(self):
        flow = prepare_flow(lifecycle, self.root, self.text)
        run = self.root / "unit-run"
        lifecycle.init_run(run, flow["plan"], "functional", [flow["source"]])
        original = lifecycle.load_json(flow["unit"])
        for bad in (None, dict(original["expression_review"], text_sha256="stale"),
                    dict(original["expression_review"], stage="after"),
                    dict(original["expression_review"], comparisons=[])):
            with self.subTest(review=bad):
                record = dict(original, expression_review=bad)
                path = save(self.root / "bad-unit.json", record)
                with self.assertRaisesRegex(ValueError, "direct_expression"):
                    lifecycle.record_unit(run, self.text, path)
        record = copy.deepcopy(original)
        record["expression_review"]["whole_text"]["decision"] = "revise"
        path = save(self.root / "unresolved-unit.json", record)
        with self.assertRaisesRegex(ValueError, "unresolved reader effort"):
            lifecycle.record_unit(run, self.text, path)
        lifecycle.record_unit(run, self.text, flow["unit"])
        with lifecycle.session(run) as state:
            self.assertEqual(len(state["units"]), 1)

    def test_comparison_engine_changes_invalidate_lifecycle(self):
        flow = prepare_flow(lifecycle, self.root, self.text)
        replacement = self.root / "different-engine.py"
        replacement.write_text("# Synthetic changed validator")
        with patch.object(direct_expression, "__file__", str(replacement)):
            with self.assertRaisesRegex(ValueError, "implementation changed"):
                with lifecycle.session(flow["run"]):
                    pass


class DeliveryIntegrationTests(unittest.TestCase):
    def fixture(self, case):
        value = case()
        value.setUp()
        self.addCleanup(value.doCleanups)
        return value

    def test_full_aggregation_and_delivery_require_current_direct_expression(self):
        f = self.fixture(full_fixture.CheckedDeliveryCLITests)
        original = reader_answers.load(f.reviews[0])
        for change in ("missing", "stale", "unresolved", "old-version"):
            with self.subTest(change=change):
                review = copy.deepcopy(original)
                expression = review["reader_value"]["checks"]["expression"]
                if change == "missing":
                    del expression["direct_expression"]
                elif change == "stale":
                    expression["direct_expression"]["text_sha256"] = "stale"
                elif change == "unresolved":
                    expression["direct_expression"]["whole_text"]["decision"] = "revise"
                else:
                    review["reader_value"]["version"] = 4
                save(f.reviews[0], review)
                aggregated = f.cli("aggregate_reviews.py", *f.reviews, "--reader-value-inputs", f.inputs_path,
                                   "--output", f.base / (change + "-aggregate.json"))
                self.assertEqual(aggregated.returncode, 1, aggregated.stdout + aggregated.stderr)
                delivery = f.cli("deliver.py", *f.args)
                self.assertNotEqual(delivery.returncode, 0)
                self.assertEqual(delivery.stdout, "")
        save(f.reviews[0], original)

    def test_content_revision_is_not_a_transport_retry(self):
        f = self.fixture(full_fixture.CheckedDeliveryCLITests)
        packet = f.base / "packets/review_packet_reader.md"
        state = {"packet_sets": [{"packets": {"reader": writing_execution.ref(packet)},
                                  "owner": writing_execution.ref(f.inputs_path)}]}
        @contextlib.contextmanager
        def task(*args, **kwargs):
            yield state
        review = reader_answers.load(f.reviews[0])
        review["verdict"] = "FAIL"
        review["reader_value"]["checks"]["expression"]["direct_expression"]["whole_text"]["decision"] = "revise"
        with patch.object(writing_execution, "task", task):
            writing_execution.validate_native_return(f.flow["run"], review, "reader", packet)
            del review["reader_value"]["checks"]["expression"]["direct_expression"]
            with self.assertRaisesRegex(ValueError, "malformed fields"):
                writing_execution.validate_native_return(f.flow["run"], review, "reader", packet)

    def test_reader_packet_covers_visual_labels_and_avoids_author_rationales(self):
        f = self.fixture(full_fixture.CheckedDeliveryCLITests)
        packet = f.base / "packets/review_packet_reader.md"
        text = packet.read_text()
        self.assertIn("headings, visual labels, TLDR and body", text)
        self.assertIn("do not inherit the author's keep rationales", text)
        template = review_wire.read_packet(packet)["reader_value_template"]
        comparison = template["checks"]["expression"]["direct_expression"]
        self.assertEqual(comparison["opening"]["decision"], "pending")
        self.assertEqual(comparison["whole_text"]["decision"], "pending")
        self.assertEqual(comparison["stage"], "after")

    def test_fast_self_check_cannot_omit_comparison(self):
        f = self.fixture(fast_fixture.FastDeliveryTests)
        path = f.base / "fast/reader.json"
        review = reader_answers.load(path)
        del review["reader_value"]["checks"]["expression"]["direct_expression"]
        save(path, review)
        reviews = [f.base / "fast" / (role + ".json") for role in ("reader", "source", "visual")]
        result = f.cli("aggregate_reviews.py", *reviews, "--reader-value-inputs", f.base / "fast/reader-value-inputs.json",
                       "--self-check", "--output", f.base / "missing-expression.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("direct_expression", result.stdout)
        delivered = f.cli("deliver.py", "fast", *f.args)
        self.assertNotEqual(delivered.returncode, 0)
        self.assertEqual(delivered.stdout, "")

    def test_scoped_editorial_receipt_cannot_omit_or_ignore_expression(self):
        f = self.fixture(scoped_fixture.ScopedDeliveryTests)
        record = reader_answers.load(f.receipt)
        for mode in ("missing", "unresolved"):
            with self.subTest(mode=mode):
                modified = copy.deepcopy(record)
                expression = modified["reader_value"]["checks"]["expression"]
                if mode == "missing":
                    del expression["direct_expression"]
                else:
                    expression["direct_expression"]["whole_text"]["decision"] = "revise"
                errors = plan_review_scope.validate_editorial_scope(f.plan, modified)
                self.assertTrue(any("direct_expression" in error for error in errors), errors)
        self.assertEqual(plan_review_scope.validate_editorial_scope(f.plan, record), [])

    def test_compaction_keeps_expression_judgments_and_does_not_fill_missing_records(self):
        import reader_value
        from editorial_fixture import structural_review
        text = "不是扩大试点，而是先补齐回滚验证。\n不能省略的责任：记录回滚结果。"
        template = reader_value.template(("expression",), "synthetic-binding", text)
        review = structural_review(("expression",), "synthetic-binding", text)
        compact = review_wire.compact(review)
        restored = review_wire.expand(compact, template)
        self.assertEqual(restored, review)
        del compact["checks"]["expression"]["direct_expression"]
        self.assertNotIn("direct_expression", review_wire.expand(compact, template)["checks"]["expression"])


if __name__ == "__main__":
    unittest.main()
