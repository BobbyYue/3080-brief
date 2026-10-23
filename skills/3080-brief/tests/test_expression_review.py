"""Packet wiring tests, not a claim of semantic model accuracy."""
import argparse
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_review_packet as review
import editorial_gate
import reader_value
from body_fixture import make_body


class ExpressionPacketTests(unittest.TestCase):
    def test_existing_roles_receive_contextual_review_and_hash_changes(self):
        fields = ("source_snapshot inventory claim_ledger tldr body draft user_request "
                  "source_outline source_excerpts visual_spec html_design_plan validation_notes "
                  "whiteboard_summary whiteboard_preview document_preview full_page_preview "
                  "geometry_report full_page_replay readiness_receipt body_visible_text brief_json").split()
        args = argparse.Namespace(**dict.fromkeys(fields, ""), round=1)
        self.assertEqual(set(review.ROLE_NAMES), {"reader", "source", "visual"})
        with tempfile.TemporaryDirectory() as directory:
            draft = Path(directory) / "draft.md"
            draft.write_text("A bounded finding.", encoding="utf-8")
            args.draft = str(draft)
            source = Path(directory) / "source.md"
            source.write_text("Synthetic source and limits.")
            args.brief_json, _ = make_body(directory, draft, source)
            ids = set()
            for role in review.ROLE_NAMES:
                packet, identity = review.packet_for(role, args)
                ids.add(identity)
                for axis in editorial_gate.AXES[role]:
                    self.assertIn(reader_value.GUIDANCE[axis], packet)
                for text in ("location + quote", "protected meaning", "nonblocking", "scoped revalidation"):
                    self.assertIn(text, packet)
            self.assertEqual(len(ids), 1)
            packet, _ = review.packet_for("reader", args)
            self.assertIn("Mandatory TLDR units are not template defects", packet)
            packet, _ = review.packet_for("visual", args)
            self.assertIn("not counts of cards", packet)
            draft.write_text("A changed finding.", encoding="utf-8")
            _, changed = review.packet_for("reader", args)
            self.assertNotIn(changed, ids)


if __name__ == "__main__":
    unittest.main()
