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

    def test_live_precheck_client_error_still_returns_redacted_json_and_markdown_reports(self):
        from online_e2e.cli import main
        from online_e2e.contracts import load_target_config
        from online_e2e.reports import ReportWriter
        from online_e2e.run_store import DurableRunStore
        from online_e2e.runner import ExpertE2ERunner
        from online_e2e.synthetic_backend import SyntheticRegressionBackend
        from online_e2e.transport import ClientError

        class InaccessibleLiveBackend(SyntheticRegressionBackend):
            environment = "live"

            def precheck(self, target):
                raise ClientError(
                    "ASSISTANT_NOT_ACCESSIBLE",
                    "assistants",
                    "private-user private-assistant private-cookie",
                )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = load_target_config("data-law-case-expert", root=ROOT)
            backend = InaccessibleLiveBackend(target)

            def factory(arguments):
                return ExpertE2ERunner(
                    target,
                    backend,
                    DurableRunStore(root / "state"),
                    ReportWriter(root / "reports"),
                )

            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "data-law-case-expert",
                        "dry-run",
                        "full",
                        "--run-id",
                        "run_inaccessible",
                        "--env-file",
                        "/unused/explicit.env",
                    ],
                    runner_factory=factory,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(stdout.getvalue().splitlines()), 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "BLOCKED")
            self.assertEqual(payload["code"], "ASSISTANT_NOT_ACCESSIBLE")
            stages = {stage["name"]: stage for stage in payload["stages"]}
            self.assertEqual(stages["PRECHECK"]["status"], "BLOCKED")
            self.assertEqual(stages["PRECHECK"]["detail"], "ASSISTANT_NOT_ACCESSIBLE")
            self.assertNotIn("RUNNING", {stage["status"] for stage in payload["stages"]})
            self.assertIn(
                "ASSISTANT_NOT_ACCESSIBLE",
                {blocker["code"] for blocker in payload["blockers"]},
            )
            self.assertTrue(Path(payload["report_json"]).is_file())
            self.assertTrue(Path(payload["report_markdown"]).is_file())
            combined = (
                Path(payload["report_json"]).read_text(encoding="utf-8")
                + Path(payload["report_markdown"]).read_text(encoding="utf-8")
                + stdout.getvalue()
                + stderr.getvalue()
            )
            for secret in ("private-user", "private-assistant", "private-cookie"):
                self.assertNotIn(secret, combined)

    def test_runner_store_or_report_failure_keeps_cli_stdout_single_json(self):
        from online_e2e.cli import main

        class BrokenRunner:
            def run(self, *args, **kwargs):
                raise OSError("private report filesystem detail")

        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(
                [
                    "data-law-case-expert",
                    "dry-run",
                    "full",
                    "--run-id",
                    "run_report_failure",
                    "--env-file",
                    "/unused/explicit.env",
                ],
                runner_factory=lambda arguments: BrokenRunner(),
            )
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(stdout.getvalue().splitlines()), 1)
        self.assertEqual(json.loads(stdout.getvalue())["code"], "INTERNAL_ERROR")
        self.assertNotIn("private report filesystem detail", stdout.getvalue() + stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
