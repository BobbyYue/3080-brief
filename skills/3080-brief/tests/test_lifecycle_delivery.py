"""Adapter fault injection only; these tests do not attest writing quality."""
import contextlib
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import checked_delivery as delivery
import deliver
import lifecycle_delivery as guard


class LifecycleDeliveryGuardTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.run = self.base / "run"
        self.run.mkdir()
        self.state = self.run / "lifecycle.json"
        self.state.write_text("{}")
        self.artifact = self.base / "brief.md"
        self.artifact.write_text("Adapter fixture; not a reviewed brief.")
        self.review = self.base / "native-result.json"
        self.review.write_text('{"verdict":"PASS"}')
        self.native = {"artifact_sha256": delivery.digest(self.artifact.read_bytes()), "status": "pass"}

    def module(self, **changes):
        value = {"status": "pass", "artifact_sha256": self.native["artifact_sha256"],
                 "evidence_paths": [str(self.state), str(self.review)], "rounds": 1, **changes}
        return types.SimpleNamespace(__file__=str(ROOT / "scripts/writing_lifecycle.py"),
                                     verify_delivery=mock.Mock(return_value=value))

    def test_missing_run_or_state_blocks_before_module_lookup(self):
        self.state.unlink()
        with mock.patch.object(guard.importlib, "import_module") as lookup, self.assertRaises(delivery.DeliveryBlocked):
            guard.verify(self.run, self.artifact, [self.review], self.native)
        lookup.assert_not_called()

    def test_missing_package_module_never_falls_back_to_another_skill(self):
        with mock.patch.object(guard.importlib, "import_module", side_effect=ModuleNotFoundError), \
                self.assertRaises(delivery.DeliveryBlocked):
            guard.verify(self.run, self.artifact, [self.review], self.native)
        other = self.module()
        other.__file__ = "/another-skill/scripts/writing_lifecycle.py"
        with mock.patch.object(guard.importlib, "import_module", return_value=other), \
                self.assertRaises(delivery.DeliveryBlocked):
            guard.verify(self.run, self.artifact, [self.review], self.native)
        other.verify_delivery.assert_not_called()

    def test_functional_profile_and_exact_native_result_are_not_optional(self):
        module = self.module()
        module.verify_delivery.side_effect = ValueError("Profile mismatch or stale version")
        with mock.patch.object(guard.importlib, "import_module", return_value=module), self.assertRaises(ValueError):
            guard.verify(self.run, self.artifact, [self.review], self.native)
        module.verify_delivery.assert_called_once_with(self.run.resolve(), self.artifact, "functional",
                                                       review_evidence=[self.review], draft=False)

    def test_nonfinal_draft_and_mismatched_byte_results_cannot_be_promoted(self):
        for changes in ({"status": "prepared"}, {"status": "review-incomplete-draft"},
                        {"artifact_sha256": "0" * 64}, {"evidence_paths": []}):
            with self.subTest(changes=changes), \
                    mock.patch.object(guard.importlib, "import_module", return_value=self.module(**changes)), \
                    self.assertRaises(delivery.DeliveryBlocked):
                guard.verify(self.run, self.artifact, [self.review], self.native)

    def test_draft_cannot_accept_a_pass_result(self):
        with mock.patch.object(guard.importlib, "import_module", return_value=self.module()), \
                self.assertRaises(delivery.DeliveryBlocked):
            guard.verify(self.run, self.artifact, [self.review], self.native, draft=True)

    def test_unwatched_lifecycle_evidence_cannot_release_payload(self):
        with mock.patch.object(guard.importlib, "import_module", return_value=self.module()), \
                self.assertRaises(delivery.DeliveryBlocked):
            delivery.pack(self.artifact, [self.state],
                          lambda: guard.verify(self.run, self.artifact, [self.review], self.native))

    def test_all_deliver_modes_require_run_even_with_output(self):
        for args in (["--review-result", "unused"], ["scoped", "--plan", "unused", "--receipt", "unused"],
                     ["draft", "--review-result", "unused"], ["draft", "scoped", "--plan", "unused", "--receipt", "unused"],
                     ["fast", "--text", "unused", "--source", "unused", "--renders", "unused", "--result", "unused",
                      "--delivery-artifact", "unused", "--explicit-fast-choice"]):
            output = self.base / "no-payload.json"
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                deliver.main([*args, "--output", str(output)])
            self.assertFalse(output.exists())

    def test_invalid_lifecycle_main_never_writes_an_output(self):
        output = self.base / "no-payload.json"
        with contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()):
            code = deliver.main(["scoped", "--plan", str(self.base / "missing-plan.json"),
                                 "--receipt", str(self.review), "--lifecycle-run", str(self.run),
                                 "--output", str(output)])
        self.assertEqual(code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
