"""Real native FAIL aggregation plus synthetic lifecycle, not a quality trial."""
import base64
import json
import sys
import unittest
from pathlib import Path

import test_checked_delivery_cli as fixtures
from native_lifecycle_fixture import prepare_native_flow

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import writing_lifecycle as lifecycle


class DraftDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CheckedDeliveryCLITests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base

    def prepare_failure(self, rounds=3, prior_verdicts=(), body_failure=False, expression_failure=False):
        for index, path in enumerate(self.fixture.reviews):
            original = json.loads(path.read_text())
            original["review_round"] = rounds
            if index == 0:
                original["verdict"] = "FAIL"
                original["checks"][0].update(result="FAIL", reason="Synthetic unresolved reader question")
                original["blocking_issues"] = ["Synthetic unresolved scope question; not real reader evidence"]
                original["required_fixes"] = ["Clarify the synthetic scope"]
                if body_failure:
                    original["body_completion"]["requirements"][0].update(
                        status="fail", reason="Synthetic body explanation omits the source-supported condition.")
                if expression_failure:
                    original["reader_value"]["checks"]["expression"]["direct_expression"]["whole_text"].update(
                        decision="revise", reading_effect="Synthetic unresolved cumulative reading burden.")
            path.write_text(json.dumps(original))
        result = self.fixture.cli("aggregate_reviews.py", *self.fixture.reviews,
            "--reader-value-inputs", self.fixture.inputs_path, "--output", self.fixture.result)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        base = self.base / "draft-process"
        base.mkdir()
        self.flow = prepare_native_flow(lifecycle, base, self.fixture.artifact, self.fixture.result,
            self.fixture.fixture.lock_path, rounds=rounds, verdict="fail", prior_verdicts=prior_verdicts)
        self.args = [*self.fixture.args[:-1], str(self.flow["run"])]

    def test_three_nonpass_rounds_return_exact_labeled_draft_not_acceptance(self):
        self.prepare_failure()
        output = self.base / "draft-envelope.json"
        result = self.fixture.cli("deliver.py", "draft", *self.args, "--output", output)
        self.fixture.assert_ok(result)
        envelope = json.loads(output.read_text())
        self.assertNotIn("payload", json.loads(result.stdout))
        self.assertEqual(envelope["delivery_state"], "draft")
        self.assertEqual(envelope["lifecycle"]["status"], "review-incomplete-draft")
        self.assertEqual(envelope["lifecycle"]["rounds"], 3)
        self.assertTrue(envelope["issues"])
        self.assertTrue(envelope["user_notice_required"])
        self.assertTrue(envelope["user_question_required"])
        self.assertFalse(envelope["external_action_authorized"])
        self.assertEqual(base64.b64decode(envelope["payload"]), self.fixture.artifact.read_bytes())
        self.assertIn(str(self.fixture.result.resolve()), envelope["lifecycle"]["evidence_paths"])

    def test_one_failed_round_cannot_claim_repair_exhaustion(self):
        self.prepare_failure(rounds=1)
        output = self.base / "no-envelope.json"
        result = self.fixture.cli("deliver.py", "draft", *self.args, "--output", output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse(output.exists())

    def test_body_judgment_failure_keeps_existing_labeled_draft_exit(self):
        self.prepare_failure(body_failure=True)
        result = self.fixture.cli("deliver.py", "draft", *self.args)
        self.fixture.assert_ok(result)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["delivery_state"], "draft")
        self.assertTrue(envelope["issues"])
        self.assertTrue(envelope["user_notice_required"])
        self.assertNotEqual(self.fixture.cli("deliver.py", *self.args).returncode, 0)

    def test_three_round_draft_still_requires_run_flag(self):
        self.prepare_failure()
        result = self.fixture.cli("deliver.py", "draft", *self.args[:-2])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_expression_failure_keeps_three_round_draft_without_claiming_acceptance(self):
        self.prepare_failure(expression_failure=True)
        result = self.fixture.cli("deliver.py", "draft", *self.args)
        self.fixture.assert_ok(result)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["delivery_state"], "draft")
        self.assertTrue(envelope["user_question_required"])
        self.assertFalse(envelope["external_action_authorized"])
        self.assertNotEqual(self.fixture.cli("deliver.py", *self.args).returncode, 0)

    def test_failed_task_cannot_use_complete_exit(self):
        self.prepare_failure()
        result = self.fixture.cli("deliver.py", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_current_pass_cannot_use_incomplete_draft_exit(self):
        result = self.fixture.cli("deliver.py", "draft", *self.fixture.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_prior_pass_does_not_hide_current_failure_or_prevent_labeled_draft(self):
        self.prepare_failure(prior_verdicts=("pass", "fail"))
        result = self.fixture.cli("deliver.py", "draft", *self.args)
        self.fixture.assert_ok(result)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["delivery_state"], "draft")
        self.assertTrue(envelope["issues"])
        self.assertFalse(envelope["external_action_authorized"])
        self.assertNotEqual(self.fixture.cli("deliver.py", *self.args).returncode, 0)

    def test_deleted_original_reviewer_blocks_draft(self):
        self.prepare_failure()
        self.fixture.reviews[0].unlink()
        result = self.fixture.cli("deliver.py", "draft", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_draft_rejects_changed_final_native_result(self):
        self.prepare_failure()
        original = json.loads(self.fixture.result.read_text())
        original["blocking_issues"].append("Added after lifecycle registration")
        self.fixture.result.write_text(json.dumps(original))
        result = self.fixture.cli("deliver.py", "draft", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
