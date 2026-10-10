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


class ScopedDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.text = self.base / "brief.md"
        self.text.write_text("Only the inspected sample is known; rollout remains undecided.")
        self.render = self.base / "render.png"
        self.render.write_bytes(b"STRUCTURAL FIXTURE NOT A REAL RENDER")
        record = lambda path: {"path": str(path), "sha256": reader_value.sha256(path)}
        layers = {name: {"fixture": {"sha256": reader_value.sha256(self.text)}} for name in scope.LAYERS}
        layers["content"]["fixture"]["path"] = str(self.text)
        layers["layout_desktop"]["fixture"]["sha256"] = reader_value.sha256(self.render)
        self.plan = {"schema_version": 1, "editorial_version": 1, "changed_layers": ["layout_desktop"],
            "after_layers": layers, "required_checks": ["desktop_geometry"], "required_reviews": [],
            "stop_when_required_scope_passes": True, "delivery_artifact": record(self.text)}
        self.plan["plan_id"] = scope.stable_id(self.plan)
        receipt = {"schema_version": 1, "plan_id": self.plan["plan_id"], "checks": {"desktop_geometry": "PASS"}, "reviews": {},
            "editorial_inputs": {"text": [record(self.text)], "source": [record(self.text)], "renders": [record(self.render)]},
            "reader_value": structural_review(("expression", "selection", "meaning", "unit_roles", "presentation"),
                self.plan["plan_id"], self.text.read_text(), self.text.read_text(), self.render)}
        self.plan_path, self.receipt = self.base / "plan.json", self.base / "checks.json"
        scope.write_json(self.plan_path, self.plan)
        scope.write_json(self.receipt, receipt)

    def run_cli(self):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts/deliver.py"), "scoped",
            "--plan", str(self.plan_path), "--receipt", str(self.receipt)], capture_output=True, text=True)

    def test_scoped_path_does_not_require_another_full_audit(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["review_method"], "scoped-revalidation")
        self.assertEqual(base64.b64decode(envelope["payload"]), self.text.read_bytes())

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
