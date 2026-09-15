"""Structural regressions; these fixtures are not genuine visual reader tests."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reader_answers import object_digest, digest
from validate_visual_replay import validate


class VisualCoreAnswersTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.image = Path(self.temp.name) / "fixture.png"
        self.image.write_bytes(b"structural image hash fixture only")
        self.ledger = {"claims": [{"id": "A", "priority": "P0"}, {"id": "B", "priority": "P0"}]}
        self.spec = {"blocks": [{"visual_role": "anchor", "claim_ids": ["A", "B"]}]}
        self.report = {"reader_role": "visual_blind", "visual_artifact_id": digest(self.image), "review_round": 1,
                       "replay": {"main_judgment": "Dispersion is lower after filtering.", "supporting_evidence": ["D7 revenue is higher for the high group than the low group."],
                                  "next_action_or_boundary": "Observed, not a causal effect.", "reading_path": "Two comparisons", "unresolved_confusion": []},
                       "evaluation": {"verdict": "PASS", "main_judgment_claim_ids": ["A"], "evidence_claim_ids": ["B"], "action_or_boundary_claim_ids": [],
                                      "reading_path_clear": True, "unresolved_confusion_blocks_decision": False, "blocking_issues": [], "required_fixes": []}}
        self.report["evaluation"].update({"replay_sha256": object_digest(self.report["replay"]), "ledger_sha256": object_digest(self.ledger), "visual_spec_sha256": object_digest(self.spec),
            "claim_replays": [{"claim_id": "A", "reader_quote": self.report["replay"]["main_judgment"], "relation_preserved": True, "source_rationale": "Fixture dispersion result"},
                              {"claim_id": "B", "reader_quote": self.report["replay"]["supporting_evidence"][0], "relation_preserved": True, "source_rationale": "Fixture high/low comparison"}]})

    def tearDown(self):
        self.temp.cleanup()

    def test_all_core_claims_pass(self):
        self.assertEqual(validate(self.report, self.image, self.ledger, self.spec), ("PASS", []))

    def test_one_understood_anchor_cannot_rescue_missing_second_claim(self):
        self.report["evaluation"]["claim_replays"].pop()
        self.assertEqual(validate(self.report, self.image, self.ledger, self.spec)[0], "FAIL")

    def test_correct_tokens_without_comparison_fail_source_relation(self):
        self.report["evaluation"]["claim_replays"][1]["relation_preserved"] = False
        self.assertEqual(validate(self.report, self.image, self.ledger, self.spec)[0], "FAIL")

    def test_lost_material_qualifier_fails(self):
        self.report["evaluation"]["claim_replays"][0]["relation_preserved"] = False
        self.assertEqual(validate(self.report, self.image, self.ledger, self.spec)[0], "FAIL")

    def test_expected_answer_not_in_raw_replay_fails(self):
        self.report["evaluation"]["claim_replays"][0]["reader_quote"] = "A fabricated expected answer"
        self.assertEqual(validate(self.report, self.image, self.ledger, self.spec)[0], "FAIL")

    def test_changed_source_replay_or_visual_is_stale(self):
        for field in ("replay_sha256", "ledger_sha256", "visual_spec_sha256"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.report)
                changed["evaluation"][field] = "0" * 64
                self.assertEqual(validate(changed, self.image, self.ledger, self.spec)[0], "FAIL")


if __name__ == "__main__":
    unittest.main()
