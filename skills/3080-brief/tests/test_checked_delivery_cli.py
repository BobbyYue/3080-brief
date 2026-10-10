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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import editorial_gate
import reader_answers as answers
import deliver
import checked_delivery


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
        self.fixture.prepare()
        evidence = self.fixture.write_evidence_files()
        answer_receipt = self.base / "answers-receipt.json"
        self.assert_ok(self.cli("reader_answers.py", "verify", "--manifest", evidence["manifest"],
            "--responses", evidence["responses"], "--evaluation", evidence["evaluation"], "--output", answer_receipt))
        self.artifact = self.fixture.artifact_path
        preview = self.base / "preview.png"
        preview.write_bytes(b"STRUCTURAL FIXTURE ONLY; NOT RENDERED EVIDENCE")
        ledger = self.base / "ledger.json"
        answers.save(ledger, {"claims": [{"id": "C0", "priority": "P0", "source_location": "Fixture source", "source_identity": "Fixture only",
            "evidence_ceiling": "source_fact", "output_assertion": "source_fact", "protected_relations": ["Structural fixture"]}]})
        self.paths = {
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
            path = self.base / (role + ".json")
            answers.save(path, review)
            self.reviews.append(path)
        self.result = self.base / "aggregate.json"
        self.assert_ok(self.cli("aggregate_reviews.py", *self.reviews,
            "--reader-value-inputs", self.inputs_path, "--output", self.result))
        self.args = [*self.common, "--readiness-receipt", str(self.readiness), "--review-result", str(self.result)]

    def test_actual_complete_path_returns_exact_reviewed_file(self):
        result = self.cli("deliver.py", *self.args)
        self.assert_ok(result)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["delivery_state"], "checked")
        self.assertEqual(base64.b64decode(envelope["payload"]), self.artifact.read_bytes())
        self.assertFalse(envelope["external_action_authorized"])

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
