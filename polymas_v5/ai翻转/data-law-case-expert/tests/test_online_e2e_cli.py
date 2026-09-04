from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class OnlineE2ECLITests(unittest.TestCase):
    def test_cli_passes_exact_arguments_and_prints_one_json_document(self):
        from online_e2e.cli import main

        captured = {}

        class Runner:
            def run(self, run_id, *, mode, confirmation_token=None):
                captured.update(
                    run_id=run_id, mode=mode, confirmation_token=confirmation_token
                )
                return {"run_id": run_id, "mode": mode, "suite": "full", "status": "BLOCKED"}

        def factory(arguments):
            captured["target_alias"] = arguments.target_alias
            captured["env_file"] = str(arguments.env_file)
            return Runner()

        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(
                [
                    "data-law-case-expert",
                    "apply",
                    "full",
                    "--run-id",
                    "run_001",
                    "--env-file",
                    "/tmp/explicit.env",
                    "--confirmation-token",
                    "token-only-in-memory",
                ],
                runner_factory=factory,
            )

        self.assertEqual(exit_code, 0)
        lines = stdout.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["status"], "BLOCKED")
        self.assertEqual(
            captured,
            {
                "target_alias": "data-law-case-expert",
                "env_file": "/tmp/explicit.env",
                "run_id": "run_001",
                "mode": "apply",
                "confirmation_token": "token-only-in-memory",
            },
        )
        self.assertEqual(stderr.getvalue(), "")

    def test_cli_usage_error_is_one_json_and_diagnostic_is_stderr_only(self):
        from online_e2e.cli import main

        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["data-law-case-expert", "dry-run", "full"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(len(stdout.getvalue().splitlines()), 1)
        self.assertEqual(json.loads(stdout.getvalue())["code"], "CLI_USAGE")
        self.assertIn("CLI_USAGE", stderr.getvalue())

    def test_module_entrypoint_missing_env_returns_auth_required_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "does-not-exist.env"
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "online_e2e",
                    "data-law-case-expert",
                    "dry-run",
                    "full",
                    "--run-id",
                    "run_002",
                    "--env-file",
                    str(missing),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["code"], "AUTH_REQUIRED")
        self.assertNotIn(str(missing), result.stdout)
        self.assertIn("AUTH_REQUIRED", result.stderr)

    def test_help_is_one_json_document_on_stdout_with_zero_exit(self):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT)
        for flag in ("--help", "-h"):
            with self.subTest(flag=flag):
                result = subprocess.run(
                    [sys.executable, "-m", "online_e2e", flag],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    env=environment,
                    check=False,
                )
                self.assertEqual(result.returncode, 0)
                self.assertEqual(len(result.stdout.splitlines()), 1)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["code"], "HELP")
                self.assertIn("usage", payload)
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
