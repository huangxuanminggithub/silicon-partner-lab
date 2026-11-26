import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import veripr


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


class TestVeriPR(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test User")

        (self.repo / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (self.repo / "test_app.py").write_text(
            "import unittest\n"
            "from app import add\n"
            "class T(unittest.TestCase):\n"
            "    def test_add(self):\n"
            "        self.assertEqual(add(1, 2), 3)\n"
            "        self.assertEqual(add(0, 0), 0)\n"
            "        self.assertEqual(add(-1, 1), 0)\n",
            encoding="utf-8",
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "initial")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_clean_change_passes(self) -> None:
        (self.repo / "app.py").write_text(
            "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
            encoding="utf-8",
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "add mul")

        r = veripr.generate_receipt(self.repo, commands=["python3 -m unittest test_app.py"])
        self.assertEqual(r.verdict, "VERIFIED_CLEAN")
        self.assertEqual(len(r.receipt_sha256), 64)
        self.assertEqual(r.commands[0].exit_code, 0)
        self.assertIn("VERIFIED CLEAN", veripr.render_markdown(r))
        self.assertIn(r.receipt_sha256, veripr.render_html(r))

    def test_adversarial_ai_cheat_signals_detected(self) -> None:
        # Simulate an AI agent cheating to make things pass:
        # 1. Adds @unittest.skip and removes 3 assertions
        # 2. Adds # type: ignore and silent except: pass
        # 3. Touches sensitive auth/login.py path
        (self.repo / "test_app.py").write_text(
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    @unittest.skip('flaky')\n"
            "    def test_add(self):\n"
            "        pass\n",
            encoding="utf-8",
        )
        auth_dir = self.repo / "auth"
        auth_dir.mkdir()
        (auth_dir / "login.py").write_text(
            "def login(user):  # type: ignore\n"
            "    try:\n"
            "        return user.ok\n"
            "    except Exception:\n"
            "        pass\n",
            encoding="utf-8",
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "ai shortcut commit")

        r = veripr.generate_receipt(self.repo, commands=["python3 -m unittest test_app.py"])
        rules = {f.rule for f in r.findings}

        self.assertEqual(r.verdict, "CHEAT_SIGNALS_DETECTED")
        self.assertIn("test-skip-added", rules)
        self.assertIn("net-assertion-drop", rules)
        self.assertIn("typecheck-suppression", rules)
        self.assertIn("silent-except-pass", rules)
        self.assertIn("sensitive-path-touched", rules)

    def test_failing_command_sets_failed_verdict(self) -> None:
        (self.repo / "app.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "break add")

        r = veripr.generate_receipt(self.repo, commands=["python3 -m unittest test_app.py"])
        self.assertEqual(r.verdict, "VERIFICATION_FAILED")
        self.assertNotEqual(r.commands[0].exit_code, 0)


if __name__ == "__main__":
    unittest.main()
