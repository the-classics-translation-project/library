"""Offline tests for the read-only guide task planner."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from guide_task_planner import plan_entries, _guide_exists


class GuidePlannerTests(unittest.TestCase):
    def test_three_languages_one_common_guide(self):
        works = [{"id": "gutenberg-36", "targets": ["ja", "ko", "fr"], "ready": True}]
        rows = plan_entries(works, [], lambda work, lang: False)
        self.assertEqual(1, sum(r["type"] == "work_analysis" for r in rows))
        self.assertEqual(3, sum(r["type"] == "target_guide" for r in rows))
        self.assertEqual("proposed", rows[0]["state"])
        self.assertTrue(all(r["state"] == "awaiting_work_analysis" for r in rows[1:]))
        self.assertEqual(rows, plan_entries(works, [], lambda w, t: False))

    def test_existing_work_reference_releases_targets(self):
        works = [{"id": "gutenberg-36", "targets": ["ja", "ko"], "ready": True}]
        rows = plan_entries(works, [], lambda w, t: t is None or t == "ja")
        self.assertEqual(["completed", "completed", "proposed"],
                         [r["state"] for r in rows])

    def test_legacy_combined_issue_covers_two_outputs(self):
        works = [{"id": "gutenberg-36", "targets": ["ja", "ko"], "ready": True}]
        legacy = [{"issue": 12, "request": {"work": "gutenberg-36", "target": "ja"}}]
        rows = plan_entries(works, legacy, lambda w, t: False)
        self.assertEqual("covered_by_legacy_issue", rows[0]["state"])
        self.assertEqual(12, rows[0]["issue"])
        self.assertEqual("covered_by_legacy_issue", rows[1]["state"])
        self.assertEqual("awaiting_work_analysis", rows[2]["state"])

    def test_saved_pointer_requires_correct_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self.assertFalse(_guide_exists(directory))
            body = b"# Work reference\n"
            sha = hashlib.sha256(body).hexdigest()
            (directory / f"{sha}.md").write_bytes(body)
            (directory / "current.json").write_text(json.dumps({"sha256": sha}))
            self.assertTrue(_guide_exists(directory))
            (directory / f"{sha}.md").write_text("corrupt")
            with self.assertRaises(ValueError):
                _guide_exists(directory)

    def test_unready_source_is_blocked(self):
        rows = plan_entries([{"id": "gutenberg-9", "targets": ["ja"], "ready": False}],
                            [], lambda w, t: False)
        self.assertEqual(1, len(rows))
        self.assertEqual("blocked", rows[0]["state"])

    def test_durable_handoff_documents(self):
        root = Path(__file__).resolve().parents[1]
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        status = (root / "STATUS.md").read_text(encoding="utf-8")
        roadmap = (root / "docs/automation-roadmap.md").read_text(encoding="utf-8")
        self.assertIn("automation-roadmap.md", agents)
        self.assertIn("automation-roadmap.md", status)
        for label in ("M1.", "M2.", "M3.", "M4.",
                      "Maintaining a trustworthy handoff", "Issue #12"):
            # The legacy request appears in narrative with or without emphasis.
            if label == "Issue #12":
                self.assertIn("#12", roadmap)
            else:
                self.assertIn(label, roadmap)


if __name__ == "__main__":
    unittest.main()
