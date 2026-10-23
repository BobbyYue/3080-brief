"""Preserve scoped revalidation; synthetic evidence is not real reader review."""
import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import plan_review_scope as scope
import reader_value
from editorial_fixture import structural_review
import writing_lifecycle as lifecycle
from lifecycle_fixture import prepare_flow
from body_fixture import make_body, structural_body
import editorial_gate


class ScopedDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.text = self.base / "brief.md"
        self.text.write_text("Only the inspected sample is known; rollout remains undecided.")
        self.render = self.base / "render.png"
        self.render.write_bytes(b"STRUCTURAL FIXTURE NOT A REAL RENDER")
        self.brief_json, self.body_record = make_body(self.base, self.text, self.text)
        record = lambda path: {"path": str(path), "sha256": reader_value.sha256(path)}
        layers = {name: {"fixture": {"sha256": reader_value.sha256(self.text)}} for name in scope.LAYERS}
        layers["content"]["fixture"]["path"] = str(self.text)
        layers["layout_desktop"]["fixture"]["sha256"] = reader_value.sha256(self.render)
        self.plan = {"schema_version": 1, "editorial_version": 1, "changed_layers": ["layout_desktop"],
            "after_layers": layers, "required_checks": ["desktop_geometry"], "required_reviews": list(scope.ROLES),
            "body_completion": self.body_record,
            "stop_when_required_scope_passes": True, "delivery_artifact": record(self.text)}
        self.plan["plan_id"] = scope.stable_id(self.plan)
        receipt = {"schema_version": 1, "plan_id": self.plan["plan_id"], "checks": {"desktop_geometry": "PASS"},
            "reviews": {r: "PASS" for r in scope.ROLES}, "review_results": {},
            "editorial_inputs": {"text": [record(self.text)], "source": [record(self.text)], "renders": [record(self.render)],
                                 "body_completion": self.body_record, "body_candidate": record(self.text)},
            "reader_value": structural_review(("expression", "selection", "meaning", "unit_roles", "presentation"),
                self.plan["plan_id"], self.text.read_text(), self.text.read_text(), self.render)}
        for role in scope.ROLES:
            review = {"reviewer_role": role, "artifact_set_id": self.plan["plan_id"], "review_round": 1,
                      "verdict": "PASS", "checks": [{"name": "Fixture", "result": "PASS", "reason": "SYNTHETIC ONLY"}],
                      "blocking_issues": [], "unsupported_claims": [], "missing_coverage": [], "required_fixes": [],
                      "reader_value": structural_review(editorial_gate.AXES[role], self.plan["plan_id"],
                          self.text.read_text(), self.text.read_text(), self.render)}
            if role in {"reader", "source"}:
                review["body_completion"] = structural_body(self.body_record, role)
            path = self.base / (role + ".json")
            scope.write_json(path, review)
            receipt["review_results"][role] = record(path)
        self.plan_path, self.receipt = self.base / "plan.json", self.base / "checks.json"
        scope.write_json(self.plan_path, self.plan)
        scope.write_json(self.receipt, receipt)
        verified = self.base / "verified-checks.json"
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/plan_review_scope.py"), "verify",
            "--plan", str(self.plan_path), "--receipt", str(self.receipt), "--output", str(verified)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.receipt = verified
        self.flow = prepare_flow(lifecycle, self.base, self.text, native_result=self.receipt)

    def run_cli(self, *, draft=False):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts/deliver.py"),
            *(["draft", "scoped"] if draft else ["scoped"]),
            "--plan", str(self.plan_path), "--receipt", str(self.receipt),
            "--lifecycle-run", str(self.flow["run"])], capture_output=True, text=True)

    def prepare_scoped_failure(self, rounds=3):
        checks = scope.load_json(self.receipt)
        checks.pop("status")
        checks.pop("issues")
        checks["checks"]["desktop_geometry"] = "FAIL"
        raw = self.base / "failed-checks-input.json"
        scope.write_json(raw, checks)
        self.receipt = self.base / "failed-scoped-result.json"
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/plan_review_scope.py"), "verify",
            "--plan", str(self.plan_path), "--receipt", str(raw), "--output", str(self.receipt)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(scope.load_json(self.receipt)["status"], "fail")
        base = self.base / "scoped-draft-flow"
        base.mkdir()
        self.flow = prepare_flow(lifecycle, base, self.text, native_result=self.receipt, rounds=rounds, verdict="fail")

    def test_scoped_three_rounds_cannot_replace_missing_original_review_evidence(self):
        self.prepare_scoped_failure()
        result = self.run_cli(draft=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertNotEqual(self.run_cli().returncode, 0)

    def test_scoped_failure_cannot_exhaust_budget_after_one_round(self):
        self.prepare_scoped_failure(rounds=1)
        result = self.run_cli(draft=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_scoped_draft_does_not_waive_current_evidence_binding(self):
        self.prepare_scoped_failure()
        self.text.write_text("A different unreviewed claim.")
        result = self.run_cli(draft=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_native_result_output_never_overwrites_an_existing_record(self):
        original = self.receipt.read_bytes()
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/plan_review_scope.py"), "verify",
            "--plan", str(self.plan_path), "--receipt", str(self.receipt), "--output", str(self.receipt)],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.receipt.read_bytes(), original)

    def test_scope_without_captured_baseline_is_not_finished_delivery(self):
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_missing_run_flag_blocks_scoped_delivery(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/deliver.py"), "scoped",
            "--plan", str(self.plan_path), "--receipt", str(self.receipt)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_other_scoped_receipt_cannot_substitute_for_registered_result(self):
        other = self.base / "other-receipt.json"
        other.write_bytes(self.receipt.read_bytes())
        self.receipt = other
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_changed_lifecycle_source_blocks_valid_scoped_review(self):
        self.flow["source"].write_text("Changed after candidate review")
        native = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/plan_review_scope.py"), "verify",
            "--plan", str(self.plan_path), "--receipt", str(self.receipt)], capture_output=True, text=True)
        self.assertEqual(native.returncode, 0, native.stdout + native.stderr)
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_changed_final_artifact_cannot_reuse_scope_pass(self):
        self.text.write_text("Rollout is now definitely approved.")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_unbound_final_artifact_is_not_deliverable(self):
        del self.plan["delivery_artifact"]
        self.plan["plan_id"] = scope.stable_id({k: v for k, v in self.plan.items() if k != "plan_id"})
        scope.write_json(self.plan_path, self.plan)
        self.assertNotEqual(self.run_cli().returncode, 0)

    def test_final_file_cannot_be_detached_from_reviewed_layers(self):
        other = self.base / "other.md"
        other.write_text("All users are now proven safe.")
        self.plan["delivery_artifact"] = {"path": str(other), "sha256": reader_value.sha256(other)}
        self.plan["plan_id"] = scope.stable_id({k: v for k, v in self.plan.items() if k != "plan_id"})
        scope.write_json(self.plan_path, self.plan)
        receipt = scope.load_json(self.receipt)
        receipt["plan_id"] = self.plan["plan_id"]
        receipt["reader_value"]["artifact_binding"] = self.plan["plan_id"]
        scope.write_json(self.receipt, receipt)
        self.assertNotEqual(self.run_cli().returncode, 0)


if __name__ == "__main__":
    unittest.main()
