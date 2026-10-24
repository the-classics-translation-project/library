"""Offline tests for independently versioned work and target guide ZIP tasks."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ctp
from independent_guide_jobs import (
    DEFAULT_MODEL, prepare, export, import_result, validate_records,
)
from legacy_v1 import ProjectError, read_json, write_json
from translation_jobs import zip_files, _guide


class IndependentGuideJobsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.work = self.root / "books" / "gutenberg-36"
        shutil.copytree(ctp.ROOT / "examples/tree-work", self.work)
        shutil.rmtree(self.work / "editions")
        original = read_json(self.work / "work.json")
        original["id"] = "gutenberg-36"
        write_json(self.work / "work.json", original)
        write_json(self.work / "rights.json",
                   {"status": "acquired", "eligible": True, "reasons": []})
        shutil.copy(ctp.ROOT / "project.json", self.root / "project.json")
        write_json(self.root / "queue.json", {"schema_version": 1, "works": [
            {"id": "gutenberg-36", "source": {"type": "gutenberg", "id": 36},
             "targets": ["ja", "ko"], "requests": []}
        ]})
        (self.root / "prompts").mkdir()
        for name in ("work-analysis.md", "target-language-guide.md",
                     "whole-work-guide.md"):
            shutil.copy(ctp.ROOT / "prompts" / name, self.root / "prompts" / name)

    def package(self, kind="work_analysis", target=None, suffix="first",
                force=False, attempt="initial"):
        request = self.root / ("request-" + suffix + ".zip")
        result = export(self.root, kind, "gutenberg-36", target, request,
                        attempt=attempt, force=force)
        return request, result

    def response(self, request, content, label="unknown", **overrides):
        with ZipFile(request) as archive:
            manifest = json.loads(archive.read("input/manifest.json"))
        values = {"schema_version": 1, "task_type": manifest["task_type"],
                  "work": manifest["work"], "target": manifest["target"],
                  "job_sha256": manifest["job_sha256"],
                  "status": "complete", "model_label": label,
                  "guide_file": "guide.md"}
        values.update(overrides)
        reply = self.root / ("result-" + str(len(list(self.root.glob("result-*.zip")))) + ".zip")
        zip_files(reply, {"result.json": values, "guide.md": content})
        return reply

    def test_one_work_then_two_independent_languages(self):
        from guide_task_planner import discover
        initial = discover(self.root)["tasks"]
        self.assertEqual("proposed", initial[0]["state"])
        self.assertTrue(all(x["state"] == "awaiting_work_analysis"
                            for x in initial[1:]))
        request, receipt = self.package()
        self.assertEqual(receipt["requested_model"], "6 Extra High")
        self.assertFalse(receipt["relay_submitted"])
        with ZipFile(request) as archive:
            self.assertEqual(set(archive.namelist()),
                             {"README.md", "input/job.json", "input/manifest.json"})
            job = json.loads(archive.read("input/job.json"))
            self.assertIn("language-independent", job["guide_instructions"])
            self.assertEqual(job["requested_model"], DEFAULT_MODEL)
            self.assertIsNone(job["target"])
            self.assertIsNone(job["work_reference"])
            self.assertIn(b"6 Extra High", archive.read("README.md"))
        reply = self.response(request, "# Work guide\n\nSource relationships.")
        imported = import_result(self.root, request, reply)
        self.assertFalse(imported["already_imported"])
        self.assertEqual(_guide(self.work / "reference"),
                         "# Work guide\n\nSource relationships.")
        self.assertTrue(import_result(self.root, request, reply)["already_imported"])
        after = discover(self.root)["tasks"]
        self.assertEqual("completed", after[0]["state"])
        self.assertTrue(all(x["state"] == "proposed" for x in after[1:]))
        for code in ("ja", "ko"):
            package, metadata = self.package("target_guide", code, suffix=code)
            self.assertEqual(metadata["target"], code)
            with ZipFile(package) as archive:
                job = json.loads(archive.read("input/job.json"))
                self.assertIn(job["work_reference"]["markdown"], _guide(self.work / "reference"))
                self.assertIn(code, job["guide_instructions"])
            answer = self.response(package, "# Terminology\n\nTerms for " + code + ".",
                                   label="6 Extra High")
            imported = import_result(self.root, package, answer)
            self.assertEqual(imported["observed_model"], "6 Extra High")
            self.assertEqual(_guide(self.work / "editions" / code / "reference"),
                             "# Terminology\n\nTerms for " + code + ".")
        self.assertEqual([x["state"] for x in discover(self.root)["tasks"]],
                         ["completed", "completed", "completed"])
        validate_records(self.root)

    def test_rejected_incomplete_and_mismatched_results_never_install_guide(self):
        req, _ = self.package()
        cases = [
            ("incomplete", {"status": "incomplete"}),
            ("wrong hash", {"job_sha256": "f" * 64}),
            ("wrong target", {"target": "ja"}),
            ("missing attribution", {"model_label": ""}),
            ("wrong type", {"task_type": "target_guide"}),
        ]
        for _, changes in cases:
            answer = self.response(req, "# Proposed only", **changes)
            with self.assertRaises(ProjectError):
                import_result(self.root, req, answer)
            self.assertFalse((self.work / "reference" / "current.json").exists())

    def test_conflict_retries_and_versioned_regeneration(self):
        req, _ = self.package()
        first = self.response(req, "# First version")
        imported = import_result(self.root, req, first)
        collision = self.response(req, "# Conflicting answer")
        with self.assertRaises(ProjectError):
            import_result(self.root, req, collision)
        self.assertEqual(_guide(self.work / "reference"), "# First version")
        self.assertTrue((self.root / imported["guide"]).exists())
        with self.assertRaises(ProjectError):
            self.package(suffix="blocked")
        with self.assertRaises(ProjectError):
            self.package(suffix="unversioned", force=True)
        req2, _ = self.package(suffix="revision", force=True, attempt="second")
        second = self.response(req2, "# Second version")
        new_result = import_result(self.root, req2, second)
        self.assertNotEqual(imported["guide"], new_result["guide"])
        self.assertTrue((self.root / imported["guide"]).exists())
        self.assertEqual(_guide(self.work / "reference"), "# Second version")
        validate_records(self.root)

    def test_stale_source_is_rejected(self):
        req, _ = self.package()
        answer = self.response(req, "# Should not be installed")
        path = next((self.work / "source").glob("*.md"))
        path.write_text(path.read_text(encoding="utf-8") + "\nChanged",
                        encoding="utf-8")
        with self.assertRaises(ProjectError):
            import_result(self.root, req, answer)
        self.assertFalse((self.work / "reference/current.json").exists())

    def test_stale_pointer_is_rejected(self):
        req, _ = self.package()
        answer = self.response(req, "# First response")
        folder = self.work / "reference"
        folder.mkdir()
        alternate = "# Independent new guide"
        from legacy_v1 import digest
        sha = digest(alternate.encode())
        (folder / (sha + ".md")).write_text(alternate, encoding="utf-8")
        write_json(folder / "current.json", {"sha256": sha})
        with self.assertRaises(ProjectError):
            import_result(self.root, req, answer)
        self.assertEqual(_guide(folder), alternate)

    def test_zip_member_validation(self):
        req, _ = self.package()
        valid = self.response(req, "# Valid guide")
        with ZipFile(valid) as z:
            obj = json.loads(z.read("result.json"))
        extra = self.root / "extra.zip"
        zip_files(extra, {"result.json": obj, "guide.md": "# Guide",
                          "../escape": "danger"})
        with self.assertRaises(ProjectError):
            import_result(self.root, req, extra)
        duplicate = self.root / "duplicate.zip"
        with ZipFile(duplicate, "w", ZIP_DEFLATED) as z:
            z.writestr("result.json", json.dumps(obj))
            z.writestr("guide.md", "# Guide")
            z.writestr("guide.md", "# Different")
        with self.assertRaises(ProjectError):
            import_result(self.root, req, duplicate)
        symlink = self.root / "symlink.zip"
        with ZipFile(symlink, "w", ZIP_DEFLATED) as z:
            z.writestr("result.json", json.dumps(obj))
            entry = ZipInfo("guide.md")
            entry.create_system = 3
            entry.external_attr = (0o120777 << 16)
            z.writestr(entry, "something")
        with self.assertRaises(ProjectError):
            import_result(self.root, req, symlink)
        self.assertFalse((self.work / "reference/current.json").exists())

    def test_legacy_request_is_not_duplicated_by_default(self):
        from guide_task_planner import discover
        write_json(self.root / "guide-requests.json", {"schema_version": 1, "requests": [
            {"issue": 12, "request": {
                "work": "gutenberg-36", "target": "ja",
                "source_fingerprint": ctp.source_fingerprint(self.work)}}
        ]})
        rows = discover(self.root)["tasks"]
        self.assertEqual("covered_by_legacy_issue", rows[0]["state"])
        self.assertEqual("covered_by_legacy_issue", rows[1]["state"])
        with self.assertRaises(ProjectError):
            self.package()
        req, _ = self.package(suffix="explicit", force=True)
        self.assertTrue(req.exists())  # Manual deliberate override, no submission.

    def test_target_requires_authorized_language_and_soft_dependency_override(self):
        with self.assertRaises(ProjectError):
            self.package("target_guide", "fr")
        with self.assertRaises(ProjectError):
            self.package("target_guide", "ja")
        req, _ = self.package("target_guide", "ja", suffix="no-work", force=True)
        with ZipFile(req) as z:
            job = json.loads(z.read("input/job.json"))
            self.assertIsNone(job["work_reference"])
        output = import_result(self.root, req, self.response(req, "# Provisional terms"))
        self.assertEqual(output["target"], "ja")
        validate_records(self.root)

    def test_cli_commands(self):
        def run(*args):
            out = StringIO()
            with patch.object(ctp, "ROOT", self.root), \
                    patch.object(sys, "argv", ["ctp", *args]), redirect_stdout(out):
                status = ctp.main()
            self.assertEqual(status, 0, out.getvalue())
            return json.loads(out.getvalue())
        self.assertTrue(run("guide-task-plan")["read_only"])
        package = self.root / "cli-request.zip"
        result = run("guide-task-export", "work_analysis", "gutenberg-36",
                     "--output", str(package))
        self.assertEqual(result["requested_model"], "6 Extra High")
        reply = self.response(package, "# CLI guide")
        imported = run("guide-task-import", str(package), str(reply))
        self.assertEqual(imported["task_type"], "work_analysis")
        validate_records(self.root)


if __name__ == "__main__":
    unittest.main()
