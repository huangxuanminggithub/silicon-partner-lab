import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import veripr
from veripr import BrandOptions, cli, config, rollup


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

    def test_pyc_deletion_ignored_but_real_test_deletion_caught(self) -> None:
        self.assertFalse(veripr.is_test_source_file("tests/__pycache__/test_app.cpython-312.pyc"))
        self.assertTrue(veripr.is_test_source_file("tests/test_app.py"))

        (self.repo / "test_app.py").unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "delete test file")

        r = veripr.generate_receipt(self.repo)
        self.assertEqual(r.verdict, "CHEAT_SIGNALS_DETECTED")
        self.assertIn("test_app.py", r.test_files_deleted)

    def test_toml_custom_policy_rulepack(self) -> None:
        rulepack = (
            Path(__file__).resolve().parent.parent
            / "pro_kit"
            / "rulepacks"
            / "strict-fintech-payments.toml"
        )
        policy = config.load_policy(rulepack)
        (self.repo / "billing.py").write_text(
            "def charge(amount):\n    return float(amount) * 1.05\n", encoding="utf-8"
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "float billing")

        r = veripr.generate_receipt(self.repo, policy=policy)
        rules = {f.rule for f in r.findings}
        self.assertEqual(r.verdict, "CHEAT_SIGNALS_DETECTED")
        self.assertIn("no-float-money-math", rules)

    def test_pro_bilingual_whitelabel_html_and_signoff(self) -> None:
        (self.repo / "app.py").write_text("def add(a, b):\n    return a + b\n# ok\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "doc update")

        r = veripr.generate_receipt(self.repo, commands=["python3 -m unittest test_app.py"])
        html_doc = veripr.render_html(
            r,
            brand=BrandOptions(
                vendor_name="极光工作室",
                client_name="星辰科技",
                project_name="支付网关 v2",
                milestone="M1",
                lang="zh",
                include_signoff=True,
            ),
        )
        self.assertIn("极光工作室", html_doc)
        self.assertIn("星辰科技", html_doc)
        self.assertIn("交付验收签字栏", html_doc)
        self.assertIn("SHA-256 不可篡改封签", html_doc)

    def test_pro_sprint_rollup_and_cli_fail_exit(self) -> None:
        (self.repo / "app.py").write_text("def add(a, b):\n    return a + b  # type: ignore\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "suppress typecheck")

        rows = rollup.audit_commit_range(self.repo, limit=5)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].verdict, "CHEAT_SIGNALS_DETECTED")
        csv_text = rollup.render_rollup_csv(rows)
        self.assertIn("CHEAT_SIGNALS_DETECTED", csv_text)
        html_text = rollup.render_rollup_html("demo-repo", rows)
        self.assertIn("Sprint Engineering Accountability Scorecard", html_text)

        rc = cli.main(["--repo", str(self.repo), "--fail-on-cheat"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
