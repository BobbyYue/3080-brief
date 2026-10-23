"""Real readiness -> packet -> aggregate -> delivery CLI with structural fixtures."""
import base64
import json
import subprocess
import sys
import unittest
from unittest import mock
from pathlib import Path

import test_reader_answers as fixtures
from editorial_fixture import structural_review
from body_fixture import make_body, structural_body

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import editorial_gate
import reader_answers as answers
import deliver
import checked_delivery
import lifecycle_delivery
import writing_lifecycle as lifecycle
from lifecycle_fixture import prepare_flow
from native_lifecycle_fixture import prepare_native_flow


class CheckedDeliveryCLITests(unittest.TestCase):
    def cli(self, script, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / script), *map(str, args)],
                              capture_output=True, text=True)

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def setUp(self):
        self.fixture = fixtures.ReaderAnswersTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base
        for answer in self.fixture.plan["answers"]:
            answer["claim_ids"] = ["C0"]
        ledger = self.base / "ledger.json"
        answers.save(ledger, {"claims": [{"id": "C0", "priority": "P0", "source_location": "Fixture source", "source_identity": "Fixture only",
            "evidence_ceiling": "source_fact", "output_assertion": "source_fact", "protected_relations": ["Structural fixture"]}]})
        self.brief_json, self.body_record = make_body(self.base, self.fixture.artifact_path,
                                                     self.fixture.source_path, ledger=ledger)
        self.fixture.prepare()
        evidence = self.fixture.write_evidence_files()
        answer_receipt = self.base / "answers-receipt.json"
        self.assert_ok(self.cli("reader_answers.py", "verify", "--manifest", evidence["manifest"],
            "--responses", evidence["responses"], "--evaluation", evidence["evaluation"], "--output", answer_receipt))
        self.artifact = self.fixture.artifact_path
        preview = self.base / "preview.png"
        preview.write_bytes(b"STRUCTURAL FIXTURE ONLY; NOT RENDERED EVIDENCE")
        self.paths = {
            "brief-json": self.brief_json,
            "source-snapshot": self.fixture.source_path, "inventory": self.fixture.source_path,
            "claim-ledger": ledger, "tldr": self.artifact, "body": self.artifact, "draft": self.artifact,
            "delivery-artifact": self.artifact, "source-outline": self.fixture.source_path,
            "source-excerpts": self.fixture.source_path, "validation-notes": self.fixture.source_path,
            "document-preview": preview,
        }
        self.common = [part for key, path in self.paths.items() for part in ("--" + key, str(path))]
        self.readiness = self.base / "readiness.json"
        self.assert_ok(self.cli("validate_review_readiness.py", *self.common,
            "--reader-answer-receipt", answer_receipt, "--output", self.readiness))
        packets = self.base / "packets"
        self.assert_ok(self.cli("build_review_packet.py", *self.common,
            "--readiness-receipt", self.readiness, "--output", packets))
        self.inputs_path = packets / "reader-value-inputs.json"
        bundle = answers.load(self.inputs_path)
        self.reviews = []
        for role, axes in editorial_gate.AXES.items():
            review = {"reviewer_role": role, "artifact_set_id": bundle["artifact_binding"], "review_round": 1,
                "verdict": "PASS", "checks": [{"name": "Fixture integrity", "result": "PASS", "reason": "STRUCTURAL FIXTURE ONLY"}],
                "blocking_issues": [], "unsupported_claims": [], "missing_coverage": [], "required_fixes": [],
                "reader_value": structural_review(axes, bundle["artifact_binding"], self.artifact.read_text(), self.fixture.source_path.read_text(), preview)}
            if role in {"reader", "source"}:
                review["body_completion"] = structural_body(self.body_record, role)
            path = self.base / (role + ".json")
            answers.save(path, review)
            self.reviews.append(path)
        self.result = self.base / "aggregate.json"
        self.assert_ok(self.cli("aggregate_reviews.py", *self.reviews,
            "--reader-value-inputs", self.inputs_path, "--output", self.result))
        self.args = [*self.common, "--readiness-receipt", str(self.readiness), "--review-result", str(self.result)]
        self.flow = prepare_native_flow(lifecycle, self.base, self.artifact, self.result, self.fixture.lock_path)
        self.args += ["--lifecycle-run", str(self.flow["run"])]

    def test_actual_complete_path_returns_exact_reviewed_file(self):
        result = self.cli("deliver.py", *self.args)
        self.assert_ok(result)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["delivery_state"], "checked")
        self.assertEqual(base64.b64decode(envelope["payload"]), self.artifact.read_bytes())
        self.assertFalse(envelope["external_action_authorized"])
        self.assertEqual(envelope["lifecycle"]["profile"], "functional")
        self.assertEqual(envelope["lifecycle"]["rounds"], 1)

    def test_empty_body_blocks_readiness_packet_and_delivery(self):
        brief = answers.load(self.brief_json)
        brief["body"] = []
        brief["reading_path"].update(section_questions=[], section_density=[])
        answers.save(self.brief_json, brief)
        result = self.cli("validate_review_readiness.py", *self.common,
            "--reader-answer-receipt", self.base / "answers-receipt.json", "--output", self.base / "blocked-readiness.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("nonempty full body", result.stdout)
        blocked = answers.load(self.base / "blocked-readiness.json")
        self.assertEqual(blocked["status"], "blocked")
        result = self.cli("build_review_packet.py", *self.common,
            "--readiness-receipt", self.readiness, "--output", self.base / "blocked-packets")
        self.assertNotEqual(result.returncode, 0)
        result = self.cli("deliver.py", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_bare_existing_reader_pass_cannot_bypass_body_judgments(self):
        review = answers.load(self.reviews[0])
        del review["body_completion"]
        answers.save(self.reviews[0], review)
        result = self.cli("aggregate_reviews.py", *self.reviews, "--reader-value-inputs", self.inputs_path,
                          "--output", self.base / "body-blocked-aggregate.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("body_completion", result.stdout)
        self.assertNotEqual(self.cli("verify_reviewed_artifacts.py", *self.args[:-2]).returncode, 0)
        result = self.cli("deliver.py", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_stale_body_plan_blocks_previously_passing_delivery(self):
        plan = Path(answers.load(self.brief_json)["body_plan"]["path"])
        plan.write_text(plan.read_text() + "\n")
        result = self.cli("deliver.py", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_native_body_fail_is_semantic_but_missing_evidence_is_technical(self):
        import contextlib
        import writing_execution
        from unittest.mock import patch
        packet = self.base / "packets" / "review_packet_reader.md"
        state = {"packet_sets": [{"packets": {"reader": writing_execution.ref(packet)},
                                 "owner": writing_execution.ref(self.inputs_path)}]}
        @contextlib.contextmanager
        def fake_task(*args, **kwargs):
            yield state
        review = answers.load(self.reviews[0])
        review["verdict"] = "FAIL"
        review["body_completion"]["requirements"][0].update(status="fail", reason="Synthetic explanation remains insufficient.")
        with patch.object(writing_execution, "task", fake_task):
            writing_execution.validate_native_return(self.flow["run"], review, "reader", packet)
            del review["body_completion"]
            with self.assertRaises(ValueError):
                writing_execution.validate_native_return(self.flow["run"], review, "reader", packet)

    def test_missing_lifecycle_flag_releases_no_payload(self):
        result = self.cli("deliver.py", *self.args[:-2])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_native_pass_without_lifecycle_stages_is_blocked(self):
        run = self.base / "prewrite-only"
        lifecycle.init_run(run, self.flow["plan"], "functional", [self.flow["source"]])
        args = [*self.args[:-1], str(run)]
        self.assert_ok(self.cli("verify_reviewed_artifacts.py", *self.args[:-2]))
        result = self.cli("deliver.py", *args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_literary_profile_cannot_deliver_a_functional_brief(self):
        flow = prepare_flow(lifecycle, self.base, self.artifact, profile="literary")
        self.assert_ok(self.cli("verify_reviewed_artifacts.py", *self.args[:-2]))
        result = self.cli("deliver.py", *self.args[:-1], flow["run"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_native_current_file_cannot_reuse_older_lifecycle_candidate(self):
        older = self.base / "older.md"
        older.write_text("An older bounded candidate; not the current brief.")
        base = self.base / "older-flow"
        base.mkdir()
        flow = prepare_flow(lifecycle, base, older, native_result=self.result)
        self.assert_ok(self.cli("verify_reviewed_artifacts.py", *self.args[:-2]))
        result = self.cli("deliver.py", *self.args[:-1], flow["run"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_stale_lifecycle_measurement_blocks_native_pass(self):
        self.flow["report"].write_text('{"status":"pass"}')
        self.assert_ok(self.cli("verify_reviewed_artifacts.py", *self.args[:-2]))
        result = self.cli("deliver.py", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_native_plan_is_linked_and_fields_are_derived_not_separately_authored(self):
        with lifecycle.session(self.flow["run"]) as state:
            expected = lifecycle_delivery.native_plan_fields(self.fixture.plan)
            self.assertEqual(state["plan"]["native_context"]["reader_plan_lock"], lifecycle.ref(self.fixture.lock_path))
            for key, value in expected.items():
                self.assertEqual(state["plan"][key], value)

    def test_task_reader_answer_or_format_drift_is_rejected(self):
        for key in ("task", "reader", "required_answers", "format"):
            plan = lifecycle.load_json(self.flow["plan"])
            if key == "required_answers":
                plan[key][0]["expected"] = "A different answer"
            elif key == "reader":
                plan[key]["need"] = "A different reader decision"
            else:
                plan[key] = "html" if key == "format" else "A different task"
            path = self.base / (key + "-plan.json")
            answers.save(path, plan)
            run = self.base / (key + "-run")
            lifecycle.init_run(run, path, "functional", [self.fixture.source_path])
            with self.subTest(key=key), self.assertRaises(checked_delivery.DeliveryBlocked):
                lifecycle_delivery.verify_native_context(lifecycle, run, self.artifact,
                                                        [self.fixture.source_path], self.fixture.lock_path)

    def test_different_lifecycle_source_cannot_hide_behind_matching_native_result(self):
        base = self.base / "different-source"
        base.mkdir()
        flow = prepare_flow(lifecycle, base, self.artifact, native_result=self.result)
        self.assert_ok(self.cli("verify_reviewed_artifacts.py", *self.args[:-2]))
        result = self.cli("deliver.py", *self.args[:-1], flow["run"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_unfinished_lifecycle_batch_blocks_native_pass(self):
        lifecycle.start_review(self.flow["run"], self.artifact)
        self.assert_ok(self.cli("verify_reviewed_artifacts.py", *self.args[:-2]))
        result = self.cli("deliver.py", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_lifecycle_evidence_changed_during_real_check_releases_nothing(self):
        original = lifecycle.verify_delivery

        def mutate_after_check(*args, **kwargs):
            result = original(*args, **kwargs)
            self.flow["source"].write_text("Changed during delivery")
            return result

        with mock.patch.object(lifecycle, "verify_delivery", side_effect=mutate_after_check), \
                self.assertRaises(checked_delivery.DeliveryBlocked):
            deliver.checked_brief(self.args)

    def test_identical_but_different_native_result_path_is_not_registered(self):
        other = self.base / "same-review-other-path.json"
        other.write_bytes(self.result.read_bytes())
        args = list(self.args)
        args[args.index("--review-result") + 1] = str(other)
        self.assert_ok(self.cli("verify_reviewed_artifacts.py", *args[:-2]))
        result = self.cli("deliver.py", *args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_cannot_deliver_an_unreviewed_other_file(self):
        other = self.base / "other.md"
        other.write_text("A different unreviewed conclusion.")
        args = list(self.args)
        args[args.index("--delivery-artifact") + 1] = str(other)
        result = self.cli("deliver.py", *args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_missing_original_review_blocks(self):
        self.reviews[0].unlink()
        self.assertNotEqual(self.cli("deliver.py", *self.args).returncode, 0)

    def test_successful_preparation_is_not_final_review(self):
        args = list(self.args)
        args[args.index("--review-result") + 1] = str(self.readiness)
        result = self.cli("deliver.py", *args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_post_review_change_invalidates_delivery(self):
        self.artifact.write_text(self.artifact.read_text() + "\nUnsupported promise.\n")
        self.assertNotEqual(self.cli("deliver.py", *self.args).returncode, 0)

    def test_self_check_cannot_impersonate_independent_review(self):
        result = answers.load(self.result)
        result["review_method"] = "self-check"
        answers.save(self.result, result)
        self.assertNotEqual(self.cli("deliver.py", *self.args).returncode, 0)

    def test_unbound_legacy_artifact_requires_binding_not_new_style_review(self):
        args = list(self.args)
        index = args.index("--delivery-artifact")
        del args[index:index + 2]
        self.assertNotEqual(self.cli("deliver.py", *args).returncode, 0)

    def test_aba_candidate_change_uses_digest_from_real_verification(self):
        accepted = self.artifact.read_bytes()
        unreviewed = b"All periods and users are safe; no limits remain."
        self.artifact.write_bytes(unreviewed)
        real_verify = deliver.verification.verify

        def verify_different_version(args, **kwargs):
            self.artifact.write_bytes(accepted)
            result = real_verify(args, **kwargs)
            self.assertEqual(result, 0, "Real verification must actually accept B")
            self.artifact.write_bytes(unreviewed)
            return result

        with mock.patch.object(deliver.verification, "verify", side_effect=verify_different_version), \
             self.assertRaises(checked_delivery.DeliveryBlocked):
            deliver.checked_brief(self.args)
        self.assertEqual(self.artifact.read_bytes(), unreviewed)


if __name__ == "__main__":
    unittest.main()
