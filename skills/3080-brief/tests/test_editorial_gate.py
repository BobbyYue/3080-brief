"""Exercise the actual aggregation and final receipt consumption paths."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import reader_value
import editorial_gate
from editorial_fixture import structural_review


class EditorialGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.text = self.base / "brief.md"
        self.text.write_text("A meets the response limit; B is more accurate in this internal sample.")
        self.render = self.base / "render.png"
        self.render.write_bytes(b"STRUCTURAL FIXTURE NOT A REAL RENDER")
        def entry(path):
            return {"path": str(path), "sha256": reader_value.sha256(path)}
        self.bundle = {"version": 1, "artifact_binding": "a" * 64,
                       "text": [entry(self.text)], "source": [entry(self.text)], "renders": [entry(self.render)]}
        self.inputs = self.save("inputs.json", self.bundle)
        self.reviews = []
        for role in editorial_gate.AXES:
            review = {"reviewer_role": role, "artifact_set_id": "a" * 64, "review_round": 1,
                      "verdict": "PASS", "checks": [{"name": "structural", "result": "PASS", "reason": "STRUCTURAL FIXTURE"}],
                      "blocking_issues": [], "unsupported_claims": [], "missing_coverage": [], "required_fixes": [],
                      "reader_value": structural_review(editorial_gate.AXES[role], "a" * 64, self.text.read_text(), self.text.read_text(), self.render)}
            self.reviews.append(self.save(role + ".json", review))
        self.result = self.base / "aggregate.json"

    def tearDown(self):
        self.temp.cleanup()

    def save(self, name, payload):
        path = self.base / name
        path.write_text(json.dumps(payload))
        return path

    def aggregate(self):
        return subprocess.run([sys.executable, str(ROOT / "scripts/aggregate_reviews.py"),
                               *map(str, self.reviews), "--reader-value-inputs", str(self.inputs),
                               "--output", str(self.result)], capture_output=True, text=True)

    def test_actual_aggregate_and_final_revalidation(self):
        result = self.aggregate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(self.result.read_text())
        self.assertEqual(editorial_gate.verify_receipt(receipt), [])
        self.text.write_text("Changed conclusion after review.")
        self.assertTrue(editorial_gate.verify_receipt(receipt))

    def test_bare_pass_results_are_rejected(self):
        payload = json.loads(self.reviews[0].read_text())
        del payload["reader_value"]
        self.reviews[0].write_text(json.dumps(payload))
        self.assertEqual(self.aggregate().returncode, 1)

    def test_unresolved_visual_does_not_pass(self):
        payload = json.loads(self.reviews[2].read_text())
        payload["reader_value"]["checks"]["presentation"].update(status="fail", action="revise")
        self.reviews[2].write_text(json.dumps(payload))
        self.assertEqual(self.aggregate().returncode, 1)

    def test_final_gate_requires_original_bound_reviews(self):
        self.assertEqual(self.aggregate().returncode, 0)
        receipt = json.loads(self.result.read_text())
        self.assertTrue(editorial_gate.verify_receipt({"verdict": "PASS", "artifact_set_id": "a" * 64}))
        payload = json.loads(self.reviews[0].read_text())
        payload["verdict"] = "FAIL"
        self.reviews[0].write_text(json.dumps(payload))
        self.assertTrue(editorial_gate.verify_receipt(receipt))

    def test_unrelated_bundle_cannot_review_actual_delivery(self):
        self.assertEqual(self.aggregate().returncode, 0)
        receipt = json.loads(self.result.read_text())
        different = copy.deepcopy(self.bundle)
        actual = self.base / "actual.md"
        actual.write_text("A different delivered conclusion.")
        different["text"] = [{"path": str(actual), "sha256": reader_value.sha256(actual)}]
        self.assertTrue(editorial_gate.verify_receipt(receipt, different))

    def test_scoped_stop_requires_current_editorial_evidence(self):
        import plan_review_scope
        layers = {name: {"file": {"sha256": reader_value.sha256(self.text)}}
                  for name in ("content", "source", "visual", "layout_desktop", "layout_mobile")}
        layers["layout_desktop"]["file"]["sha256"] = reader_value.sha256(self.render)
        plan = {"editorial_version": 1, "plan_id": "plan", "changed_layers": ["layout_desktop"], "after_layers": layers}
        self.assertTrue(plan_review_scope.validate_editorial_scope(plan, {}))
        receipt = {"editorial_inputs": {key: self.bundle[key] for key in ("text", "source", "renders")},
                   "reader_value": structural_review(("expression", "selection", "meaning", "unit_roles", "presentation"), "plan", self.text.read_text(), self.text.read_text(), self.render)}
        self.assertEqual(plan_review_scope.validate_editorial_scope(plan, receipt), [])
        changed_body = self.base / "changed-body.md"
        changed_body.write_text("A newly changed body outside the summary.")
        layers["content"]["body"] = {"sha256": reader_value.sha256(changed_body)}
        self.assertTrue(plan_review_scope.validate_editorial_scope(plan, receipt))
        del layers["content"]["body"]
        self.render.write_bytes(b"changed")
        self.assertTrue(plan_review_scope.validate_editorial_scope(plan, receipt))

    def test_empty_or_failed_original_checks_block(self):
        payload = json.loads(self.reviews[0].read_text())
        for checks in ([], [{"result": "FAIL", "reason": "A material qualifier is absent"}]):
            payload["checks"] = checks
            self.assertTrue(editorial_gate.validate(payload, self.bundle))

    def test_fast_mode_is_checked_without_claiming_independence(self):
        folder = self.base / "fast"
        command = [sys.executable, str(ROOT / "scripts/editorial_gate.py")]
        inputs = ["--text", str(self.text), "--source", str(self.text), "--renders", str(self.render)]
        result = subprocess.run(command + ["prepare-fast", *inputs, "--output", str(folder)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        bundle = json.loads((folder / "reader-value-inputs.json").read_text())
        reviews = [folder / (role + ".json") for role in editorial_gate.AXES]
        aggregate = [sys.executable, str(ROOT / "scripts/aggregate_reviews.py"), *map(str, reviews),
                     "--reader-value-inputs", str(folder / "reader-value-inputs.json"), "--self-check", "--output", str(self.result)]
        self.assertEqual(subprocess.run(aggregate, capture_output=True).returncode, 1)
        for path in reviews:
            data = json.loads(path.read_text())
            data.update(verdict="PASS", checks=[{"name": "fixture", "result": "PASS", "reason": "Structural self-check fixture"}],
                        reader_value=structural_review(editorial_gate.AXES[data["reviewer_role"]], bundle["artifact_binding"], self.text.read_text(), self.text.read_text(), self.render))
            path.write_text(json.dumps(data))
        self.assertEqual(subprocess.run(aggregate, capture_output=True).returncode, 0)
        result = subprocess.run(command + ["verify-fast", *inputs, "--result", str(self.result)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SELF_CHECK_ONLY", result.stdout)
        self.text.write_text("Changed final artifact")
        self.assertEqual(subprocess.run(command + ["verify-fast", *inputs, "--result", str(self.result)], capture_output=True).returncode, 1)


if __name__ == "__main__":
    unittest.main()
