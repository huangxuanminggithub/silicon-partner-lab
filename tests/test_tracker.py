import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ops"))
import tracker


class TestHumanActionTracker(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.json_path = Path(self.tmp.name) / "HUMAN_ACTION_ITEMS.json"
        self.md_path = Path(self.tmp.name) / "HUMAN_ACTION_ITEMS.md"
        seed = {
            "experiment_id": "EXP-001",
            "phase": "Phase 1",
            "updated_at": "2026-11-26T00:00:00Z",
            "items": [
                {
                    "id": "H-001",
                    "priority": "P0",
                    "status": "TODO",
                    "category": "TEST",
                    "title": "Connect Google Drive",
                    "estimated_minutes": 1,
                    "cost_usd": "0.00",
                    "why_human_needed": "Auth required",
                    "steps": ["Click connect"],
                    "unlocks": "Cloud backup",
                    "notes": "",
                }
            ],
        }
        self.json_path.write_text(json.dumps(seed), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_render_and_status_update(self) -> None:
        tracker.sync_markdown(self.json_path, self.md_path)
        md1 = self.md_path.read_text(encoding="utf-8")
        self.assertIn("H-001", md1)
        self.assertIn("⬜ TODO", md1)

        tracker.set_status(self.json_path, self.md_path, "H-001", "DONE", "Connected!")
        md2 = self.md_path.read_text(encoding="utf-8")
        self.assertIn("✅ DONE", md2)
        self.assertIn("Connected!", md2)

    def test_add_item_and_duplicate_guard(self) -> None:
        tracker.add_item(
            self.json_path,
            self.md_path,
            "H-002",
            "P1",
            "LAUNCH",
            "Post on V2EX",
            5,
            "0.00",
            "Account required",
            ["Copy post", "Publish"],
            "First traffic",
        )
        data = tracker.load_data(self.json_path)
        self.assertEqual(len(data["items"]), 2)
        with self.assertRaises(ValueError):
            tracker.add_item(
                self.json_path,
                self.md_path,
                "H-002",
                "P1",
                "LAUNCH",
                "Dup",
                1,
                "0.00",
                "x",
                ["y"],
                "z",
            )


if __name__ == "__main__":
    unittest.main()
