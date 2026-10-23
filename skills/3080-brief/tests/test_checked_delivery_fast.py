"""Exercise disclosed Fast exports with synthetic native/process evidence only."""
import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import editorial_gate
import writing_lifecycle as lifecycle
from editorial_fixture import structural_review
from lifecycle_fixture import prepare_flow, save
from body_fixture import make_body, structural_body


class FastDeliveryTests(unittest.TestCase):
    def cli(self, script, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / script), *map(str, args)],
                              capture_output=True, text=True)

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.text = self.base / "brief.md"
        self.text.write_text("Synthetic bounded conclusion; eligibility remains unknown.")
        self.render = self.base / "render.png"
        self.render.write_bytes(b"SYNTHETIC STRUCTURAL FIXTURE; NOT A REAL RENDER")
        self.brief_json, self.body_record = make_body(self.base, self.text, self.text)
        folder = self.base / "fast"
        self.inputs = ["--text", self.text, "--source", self.text, "--renders", self.render, "--brief-json", self.brief_json]
        prepared = self.cli("editorial_gate.py", "prepare-fast", *self.inputs, "--output", folder)
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        bundle = lifecycle.load_json(folder / "reader-value-inputs.json")
        reviews = []
        for role, axes in editorial_gate.AXES.items():
            path = folder / (role + ".json")
            review = lifecycle.load_json(path)
            review.update(verdict="PASS", checks=[{"name": "Fixture integrity", "result": "PASS", "reason": "SYNTHETIC SELF-CHECK"}],
                reader_value=structural_review(axes, bundle["artifact_binding"], self.text.read_text(), self.text.read_text(), self.render))
            if role in {"reader", "source"}:
                review["body_completion"] = structural_body(self.body_record, role)
            save(path, review)
            reviews.append(path)
        self.result = self.base / "fast-result.json"
        result = self.cli("aggregate_reviews.py", *reviews, "--reader-value-inputs", folder / "reader-value-inputs.json",
                          "--self-check", "--output", self.result)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.flow = prepare_flow(lifecycle, self.base, self.text, native_result=self.result)
        self.args = [*self.inputs, "--result", self.result, "--delivery-artifact", self.text,
                     "--explicit-fast-choice", "--lifecycle-run", self.flow["run"]]

    def test_fast_returns_exact_self_checked_not_independent_bytes(self):
        result = self.cli("deliver.py", "fast", *self.args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["delivery_state"], "self-checked")
        self.assertEqual(envelope["review_method"], "self-check")
        self.assertEqual(envelope["lifecycle"]["status"], "pass")
        self.assertFalse(envelope["external_action_authorized"])
        self.assertEqual(base64.b64decode(envelope["payload"]), self.text.read_bytes())

    def test_fast_cannot_bypass_empty_body_after_self_check(self):
        brief = lifecycle.load_json(self.brief_json)
        brief["body"] = []
        brief["reading_path"].update(section_questions=[], section_density=[])
        save(self.brief_json, brief)
        result = self.cli("deliver.py", "fast", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_fast_missing_body_judgments_fail_aggregation(self):
        inputs = self.base / "fast" / "reader-value-inputs.json"
        reviews = [self.base / "fast" / (r + ".json") for r in editorial_gate.AXES]
        review = lifecycle.load_json(reviews[1])
        del review["body_completion"]
        save(reviews[1], review)
        result = self.cli("aggregate_reviews.py", *reviews, "--reader-value-inputs", inputs,
                          "--self-check", "--output", self.base / "fast-body-failed.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("body_completion", result.stdout)
        self.assertNotEqual(self.cli("deliver.py", "fast", *self.args).returncode, 0)

    def test_fast_requires_explicit_choice_and_run(self):
        for args in (self.args[:-2], [p for p in self.args if p != "--explicit-fast-choice"]):
            result = self.cli("deliver.py", "fast", *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_native_fast_pass_does_not_waive_missing_stages(self):
        native = self.cli("editorial_gate.py", "verify-fast", *self.inputs, "--result", self.result)
        self.assertEqual(native.returncode, 0, native.stdout + native.stderr)
        run = self.base / "prewrite-only"
        lifecycle.init_run(run, self.flow["plan"], "functional", [self.flow["source"]])
        result = self.cli("deliver.py", "fast", *self.args[:-1], run)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_fast_cannot_reuse_stale_measurement(self):
        self.flow["report"].write_text('{"status":"pass"}')
        result = self.cli("deliver.py", "fast", *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_fast_cannot_reuse_literary_profile(self):
        flow = prepare_flow(lifecycle, self.base, self.text, profile="literary")
        result = self.cli("deliver.py", "fast", *self.args[:-1], flow["run"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
