"""Actual regression paths with synthetic reviews, not evidence of semantic quality."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import body_completion as body
import brief_model
from body_fixture import make_body, save, structural_body


class BodyCompletionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.source = self.base / "source.md"
        self.source.write_text("A thin source reports one inspected sample. Other samples remain untested.")
        self.candidate = self.base / "candidate.md"
        self.candidate.write_text("# 3080 Brief\nA bounded finding.\n")
        self.brief, self.record = make_body(self.base, self.candidate, self.source)
        self.doc = body.load(self.brief)
        self.plan = body.load(body.resolve(self.doc["body_plan"]["path"]))
        self.bundle = {"body_completion": self.record, "body_candidate": body.ref(self.candidate)}

    def reject(self, doc, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            brief_model.validate_document(doc)

    def review(self, role="reader"):
        return {"reviewer_role": role, "body_completion": structural_body(self.record, role)}

    def test_empty_body_with_empty_reading_path_arrays_is_blocked(self):
        self.doc["body"] = []
        self.doc["reading_path"].update(section_questions=[], section_density=[])
        self.reject(self.doc, "nonempty full body")

    def test_original_one_line_appendix_is_not_a_complete_body(self):
        self.doc["body"] = [{"heading": "Keep necessary context", "blocks": [
            {"type": "paragraph", "text": "@files save a read, not file tokens."}]}]
        self.reject(self.doc, "unresolved body requirement")

    def test_heading_or_empty_paragraph_cannot_answer(self):
        for blocks in ([], [{"type": "paragraph", "text": "  ", "answers": ["B1"]}],
                       [{"type": "paragraph", "text": [], "answers": ["B1"]}]):
            with self.subTest(blocks=blocks):
                self.doc["body"][0]["blocks"] = blocks
                self.reject(self.doc, "empty")

    def test_tldr_visual_and_hidden_mappings_do_not_count(self):
        block = self.doc["body"][0]["blocks"][0]
        del block["answers"]
        self.doc["opening"]["answers"] = ["B1"]
        self.doc["questions"][0]["answers"] = ["B1"]
        self.reject(self.doc, "unresolved body requirement")
        self.doc["body"][0]["blocks"] = [{"type": "details", "priority": "P2", "summary": "More",
                                         "paragraphs": ["A complete hidden answer"], "answers": ["B1"]}]
        self.reject(self.doc, "visible explanation")

    def test_body_repeating_only_tldr_is_blocked(self):
        self.doc["body"][0]["blocks"][0]["text"] = self.doc["opening"]["lines"][0]
        self.reject(self.doc, "merely repeats TLDR")

    def test_unknown_answer_id_and_missing_plan_fail_closed(self):
        self.doc["body"][0]["blocks"][0]["answers"] = ["UNKNOWN"]
        self.reject(self.doc, "unknown requirements")
        del self.doc["body_plan"]
        self.reject(self.doc, "missing body evidence")

    def test_config_cannot_disable_body_gate(self):
        self.doc["body"] = []
        with self.assertRaisesRegex(ValueError, "nonempty full body"):
            brief_model.validate_document(self.doc, config={"body_completion": {"required": False},
                                                           "reading_path_contract": {"required": False}})

    def test_locked_request_source_ledger_outline_and_plan_are_live_bound(self):
        for entry in [*self.plan["inputs"].values(), self.doc["body_plan"]]:
            path = body.resolve(entry["path"])
            original = path.read_bytes()
            path.write_bytes(original + b"\nchanged")
            with self.subTest(path=path.name):
                self.reject(self.doc, "stale body evidence")
            path.write_bytes(original)

    def test_p01_missing_unknown_and_conflicting_claim_mappings_fail(self):
        for change in (lambda p: p["requirements"][0].update(claim_ids=["C404"]),
                       lambda p: p.update(requirements=[]),
                       lambda p: p.update(excluded_claims=[{"claim_id": "C01", "reason": "Excluded"}])):
            plan = copy.deepcopy(self.plan)
            change(plan)
            with self.assertRaises(ValueError):
                body.validate_plan(plan)

    def test_actual_source_paths_cannot_be_substituted_with_same_bytes(self):
        other = self.base / "other.md"
        other.write_bytes(self.source.read_bytes())
        with self.assertRaisesRegex(ValueError, "different source_snapshot"):
            body.context(self.brief, source_snapshot=other)

    def test_thin_source_one_paragraph_is_structurally_accepted(self):
        self.assertEqual(len(self.doc["body"]), 1)
        self.assertEqual(brief_model.validate_document(self.doc), [])
        self.assertEqual(body.candidate_errors(body.current(self.record), self.candidate), [])
        for role in body.ROLES:
            self.assertEqual(body.review_errors(self.review(role), self.bundle), [])

    def test_per_obligation_judgment_quotes_source_and_reason_required(self):
        for role in body.ROLES:
            for mutation in (lambda r: r.pop("body_completion"),
                             lambda r: r["body_completion"].update(requirements=[]),
                             lambda r: r["body_completion"]["requirements"][0].update(quotes=[]),
                             lambda r: r["body_completion"]["requirements"][0].update(reason=""),
                             lambda r: r["body_completion"]["requirements"][0]["quotes"][0].update(block="TLDR")):
                review = self.review(role)
                mutation(review)
                self.assertTrue(body.review_errors(review, self.bundle))
        source = self.review("source")
        source["body_completion"]["requirements"][0]["source_quote"] = "Invented evidence"
        self.assertTrue(body.review_errors(source, self.bundle))

    def test_semantic_failure_is_not_promoted_to_structural_pass(self):
        review = self.review()
        review["body_completion"]["requirements"][0].update(status="fail", reason="The mapped answer omits the requested mechanism.")
        self.assertEqual(body.review_errors(review, self.bundle), ["body completion unresolved answer: reader B1"])

    def test_scope_checks_expose_unaltered_request_and_independent_outline(self):
        packet = body.packet(self.record, "reader")
        for field in ("user_request", "source_outline"):
            self.assertIn(body.read_ref(self.plan["inputs"][field]), packet)
        review = self.review()
        review["body_completion"]["scope_check"]["request_quote"] = "An author's narrower rewrite"
        self.assertTrue(body.review_errors(review, self.bundle))

    def test_summary_exception_needs_exact_quote_and_both_existing_checks(self):
        request = body.resolve(self.plan["inputs"]["user_request"]["path"])
        request.write_text("Only produce the TLDR; omit the body.")
        self.plan["inputs"]["user_request"] = body.ref(request)
        self.plan.update(scope="summary-only", requirements=[],
                         excluded_claims=[{"claim_id": "C01", "reason": "Explicit summary-only request"}],
                         summary_only_request_quote=request.read_text())
        lock = save(self.base / "summary.lock.json", self.plan)
        self.doc.update(body_plan=body.ref(lock), body=[])
        self.doc["reading_path"].update(section_questions=[], section_density=[])
        save(self.brief, self.doc)
        self.record = body.context(self.brief)
        self.bundle["body_completion"] = self.record
        for role in body.ROLES:
            review = self.review(role)
            self.assertEqual(body.review_errors(review, self.bundle), [])
            review["body_completion"]["excluded_claims"] = []
            self.assertTrue(body.review_errors(review, self.bundle))
        self.plan["summary_only_request_quote"] = "compact"
        with self.assertRaisesRegex(ValueError, "exact request quote"):
            body.validate_plan(self.plan)

    def test_compact_is_not_inferred_as_body_omission_permission(self):
        request = body.resolve(self.plan["inputs"]["user_request"]["path"])
        request.write_text("Keep it compact.")
        self.plan["inputs"]["user_request"] = body.ref(request)
        lock = save(self.base / "compact.lock.json", self.plan)
        self.doc.update(body_plan=body.ref(lock), body=[])
        self.reject(self.doc, "nonempty full body")

    def test_candidate_cannot_omit_mapped_body_or_move_it_before_heading(self):
        for content in ("A bounded finding.", "The inspected sample supplies this finding; other samples are not established by this evidence.\nSynthetic body explanation"):
            self.candidate.write_text(content)
            self.assertTrue(body.candidate_errors(body.current(self.record), self.candidate))

    def test_html_hidden_script_style_details_and_fake_snapshot_are_rejected(self):
        content = "<h2>Synthetic body explanation</h2><p>" + self.doc["body"][0]["blocks"][0]["text"] + "</p>"
        html = self.base / "candidate.html"
        snapshot = self.base / "visible.txt"
        snapshot.write_text(self.candidate.read_text())
        for wrapper in ("<script>{}</script>", "<style>{}</style>", "<div hidden>{}</div>",
                        '<div style="opacity:0">{}</div>', "<details>{}</details>"):
            html.write_text(wrapper.format(content))
            with self.subTest(wrapper=wrapper):
                self.assertTrue(body.candidate_errors(body.current(self.record), html, body.visible_ref(snapshot, html)))
        html.write_text("<style>.fallback{display:none}</style>" + content)
        with self.assertRaisesRegex(ValueError, "body-visible-text"):
            body.candidate_errors(body.current(self.record), html)
        ref = body.visible_ref(snapshot, html)
        self.assertEqual(body.candidate_errors(body.current(self.record), html, ref), [])
        html.write_text(html.read_text() + "<p>Changed</p>")
        self.assertTrue(body.candidate_errors(body.current(self.record), html, ref))

    def test_docx_integrity_is_binary_and_native_body_text_is_checked(self):
        docx = self.base / "candidate.docx"
        explanation = self.doc["body"][0]["blocks"][0]["text"]
        for hidden in (False, True):
            xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
            xml += '<w:p><w:r><w:t>Synthetic body explanation</w:t></w:r></w:p>'
            xml += '<w:p><w:r>' + ('<w:rPr><w:vanish/></w:rPr>' if hidden else '')
            xml += '<w:t>' + explanation + '</w:t></w:r></w:p></w:body></w:document>'
            with zipfile.ZipFile(docx, "w") as archive:
                archive.writestr("word/document.xml", xml)
            bundle = dict(self.bundle, delivery_artifact=body.ref(docx))
            self.assertEqual(bool(body.review_errors(self.review(), bundle)), hidden)

    def test_lock_cli_refuses_overwrite(self):
        args = [sys.executable, str(ROOT / "scripts/body_completion.py"), "lock", "--plan",
                str(self.base / "synthetic-body-plan-input.json"), "--output", str(self.base / "another.lock.json")]
        for key, entry in self.plan["inputs"].items():
            args += ["--" + key.replace("_", "-"), entry["path"]]
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 1)

    def test_cli_relative_paths_resolve_from_working_directory(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/body_completion.py"), "check",
            "--brief-json", self.brief.name, "--candidate", self.candidate.name], cwd=self.base, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["body_completion"]["brief"]["path"], str(self.brief.resolve()))
        args = [sys.executable, str(ROOT / "scripts/body_completion.py"), "lock", "--plan",
                "synthetic-body-plan-input.json", "--output", "relative.lock.json"]
        for key, entry in self.plan["inputs"].items():
            args += ["--" + key.replace("_", "-"), Path(entry["path"]).name]
        result = subprocess.run(args, cwd=self.base, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_html_and_feishu_renderers_cannot_bypass_empty_body(self):
        document = body.load(ROOT / "evals/fixtures/html-brief.json")
        document["body"] = []
        document["reading_path"].update(section_questions=[], section_density=[])
        path = save(self.base / "empty.json", document)
        for script, output, extra in (("build_feishu_brief.py", "out.xml", []),
                ("build_html_brief.py", "out.html", ["--design-plan", str(ROOT / "evals/fixtures/html-design.json")])):
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / script), str(path),
                str(ROOT / "evals/fixtures/visual-spec.json"), str(self.base / output), *extra], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nonempty full body", result.stdout + result.stderr)
            self.assertFalse((self.base / output).exists())


if __name__ == "__main__":
    unittest.main()
