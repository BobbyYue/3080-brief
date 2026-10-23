"""Verify original-review reuse through the actual snapshot/plan/delivery path."""
import argparse
import json
import subprocess
import sys
import unittest
from pathlib import Path

import test_checked_delivery_cli as fixtures
from editorial_fixture import structural_review

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import plan_review_scope as scope
import reader_value
import writing_lifecycle as lifecycle


class ScopedReviewProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CheckedDeliveryCLITests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base
        self.text = self.fixture.artifact
        self.source = self.fixture.fixture.source_path
        self.render = self.fixture.paths["document-preview"]
        layers = {"source": self.source, "content": self.text, "visual": self.render,
                  "layout_desktop": self.render, "layout_mobile": self.render}
        self.snapshot_args = [part for name, path in layers.items() for part in ("--input", f"{name}:file={path}")]
        self.snapshot_args += ["--brief-json", self.fixture.brief_json]
        self.snapshot_args += [part for role, path in zip(scope.ROLES, self.fixture.reviews)
                              for part in ("--review", f"{role}={path}")]
        self.before, self.after = self.base / "before.json", self.base / "after.json"
        for output in (self.before, self.after):
            result = self.fixture.cli("plan_review_scope.py", "snapshot", *self.snapshot_args,
                "--delivery-artifact", self.text, "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.plan_path = self.base / "scope.json"
        self.assertEqual(self.fixture.cli("plan_review_scope.py", "plan", "--before", self.before,
            "--after", self.after, "--output", self.plan_path).returncode, 0)
        self.plan = scope.load_json(self.plan_path)
        record = lambda path: {"path": str(path), "sha256": reader_value.sha256(path)}
        receipt = {"schema_version": 1, "plan_id": self.plan["plan_id"],
            "checks": {name: "PASS" for name in self.plan["required_checks"]}, "reviews": {},
            "editorial_inputs": {"text": [record(self.text)], "source": [record(self.source)], "renders": [record(self.render)],
                                 "body_completion": self.fixture.body_record, "body_candidate": record(self.text)},
            "reader_value": structural_review(("expression", "selection", "meaning", "unit_roles", "presentation"),
                self.plan["plan_id"], self.text.read_text(), self.source.read_text(), self.render)}
        self.receipt_path = self.base / "scope-receipt.json"
        scope.write_json(self.receipt_path, receipt)
        verified = self.base / "verified-scope-result.json"
        result = self.fixture.cli("plan_review_scope.py", "verify", "--plan", self.plan_path,
                                 "--receipt", self.receipt_path, "--output", verified)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.receipt_path = verified
        lifecycle.start_review(self.fixture.flow["run"], self.text)
        lifecycle.finish_review(self.fixture.flow["run"], self.receipt_path, "pass")

    def run_delivery(self):
        return self.fixture.cli("deliver.py", "scoped", "--plan", self.plan_path, "--receipt", self.receipt_path,
                                "--lifecycle-run", self.fixture.flow["run"])

    def test_valid_original_reviews_remain_reusable(self):
        self.assertEqual(set(self.plan["reused_review_inputs"]), set(scope.ROLES))
        result = self.run_delivery()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_scoped_missing_body_context_blocks_acceptance(self):
        receipt = scope.load_json(self.receipt_path)
        del receipt["editorial_inputs"]["body_completion"]
        scope.write_json(self.receipt_path, receipt)
        result = self.run_delivery()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_scoped_reused_body_evidence_must_still_match_source_outline(self):
        import body_completion
        data = body_completion.current(self.fixture.body_record)
        path = body_completion.resolve(data["plan"]["inputs"]["source_outline"]["path"])
        path.write_text(path.read_text() + "\nNew source question")
        result = self.run_delivery()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_body_change_requires_content_revalidation_not_layout_reuse(self):
        import body_completion
        brief = scope.load_json(self.fixture.brief_json)
        brief["body"][0]["blocks"][0]["text"] += " The relevant scope remains limited."
        scope.write_json(self.fixture.brief_json, brief)
        after = scope.load_json(self.after)
        after["body_completion"] = body_completion.context(self.fixture.brief_json)
        scope.write_json(self.after, after)
        result = self.fixture.cli("plan_review_scope.py", "plan", "--before", self.before,
            "--after", self.after, "--output", self.base / "body-change-scope.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        plan = scope.load_json(self.base / "body-change-scope.json")
        self.assertIn("content", plan["changed_layers"])
        self.assertEqual(plan["scope"], "full_audit")

    def test_changed_original_review_blocks(self):
        result = scope.load_json(self.fixture.reviews[0])
        result["verdict"] = "FAIL"
        scope.write_json(self.fixture.reviews[0], result)
        blocked = self.run_delivery()
        self.assertNotEqual(blocked.returncode, 0)
        self.assertEqual(blocked.stdout, "")

    def test_deleted_original_reviews_block(self):
        for path in self.fixture.reviews:
            path.unlink()
        self.assertNotEqual(self.run_delivery().returncode, 0)

    def test_snapshot_rejects_detached_final_file(self):
        other = self.base / "unreviewed.md"
        other.write_text("All days and all users are proven safe.")
        result = self.fixture.cli("plan_review_scope.py", "snapshot", *self.snapshot_args,
            "--delivery-artifact", other, "--output", self.base / "detached.json")
        self.assertNotEqual(result.returncode, 0)

    def test_visible_content_change_cannot_be_mislabeled_layout_only(self):
        before = scope.load_json(self.before)
        after = scope.load_json(self.after)
        # Preserve the declared content layer; change only the final-file layer.
        after["delivery_artifact"] = dict(after["delivery_artifact"], sha256="b" * 64, content_sha256="c" * 64)
        self.text.write_text("All users are approved now.")
        after["delivery_artifact"]["sha256"] = reader_value.sha256(self.text)
        after["layers"]["layout_desktop"]["final"] = dict(after["delivery_artifact"])
        scope.write_json(self.after, after)
        result = self.fixture.cli("plan_review_scope.py", "plan", "--before", self.before,
            "--after", self.after, "--output", self.base / "new-scope.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = scope.load_json(self.base / "new-scope.json")
        self.assertEqual(plan["scope"], "full_audit")
        self.assertEqual(set(plan["required_reviews"]), set(scope.ROLES))


if __name__ == "__main__":
    unittest.main()
