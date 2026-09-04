"""`python -m online_e2e` 的单 JSON CLI。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import sys

from .clients import PdsClient, TeachingCenterClient
from .contracts import load_target_config
from .fixtures import validate_run_id
from .live_backend import LiveRegressionBackend
from .reports import ReportWriter
from .requests_transport import RequestsTransport
from .run_store import DurableRunStore
from .runner import ExpertE2ERunner
from .transport import ClientError


class CLIUsageError(ValueError):
    pass


class JSONArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise CLIUsageError("CLI_USAGE")


def _parser():
    parser = JSONArgumentParser(prog="python -m online_e2e", add_help=True)
    parser.add_argument("target_alias")
    parser.add_argument("mode", choices=("dry-run", "apply"))
    parser.add_argument("suite", choices=("full",))
    parser.add_argument("--run-id")
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--confirmation-token")
    return parser


def _new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{timestamp}-{secrets.token_hex(4)}"


def build_runner(arguments):
    project_root = Path(__file__).resolve().parents[1]
    try:
        target = load_target_config(arguments.target_alias, root=project_root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        raise ClientError("TARGET_NOT_FOUND", "load_target") from None
    transport = RequestsTransport.from_env_file(arguments.env_file)
    store = DurableRunStore(project_root / ".online-e2e-state")
    pds = PdsClient(
        transport,
        confirmation_manager=store.confirmations,
        target_id=target.target_id,
    )
    teaching = TeachingCenterClient(
        transport,
        confirmation_manager=store.confirmations,
        target_id=target.target_id,
    )
    backend = LiveRegressionBackend(pds, teaching)
    return ExpertE2ERunner(
        target,
        backend,
        store,
        ReportWriter(project_root / "reports" / "online-e2e"),
    )


def main(argv=None, *, runner_factory=build_runner) -> int:
    try:
        arguments = _parser().parse_args(argv)
        run_id = arguments.run_id or _new_run_id()
        validate_run_id(run_id)
        runner = runner_factory(arguments)
        payload = runner.run(
            run_id,
            mode=arguments.mode,
            confirmation_token=arguments.confirmation_token,
        )
        exit_code = 0
    except CLIUsageError:
        payload = {"status": "BLOCKED", "code": "CLI_USAGE"}
        exit_code = 2
    except ClientError as error:
        payload = {"status": "BLOCKED", **error.as_dict()}
        exit_code = 2
    except ValueError:
        payload = {"status": "BLOCKED", "code": "INVALID_INPUT"}
        exit_code = 2
    except Exception:
        payload = {"status": "BLOCKED", "code": "INTERNAL_ERROR"}
        exit_code = 1
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    if exit_code:
        sys.stderr.write(f"online_e2e: {payload['code']}\n")
    return exit_code
