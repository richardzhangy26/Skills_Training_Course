"""stdout 单 JSON 的独立入口；evaluate 不加载凭证或发起网络请求。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from online_e2e.requests_transport import RequestsTransport
from online_e2e.safety import sanitize_json
from online_e2e.transport import ClientError
from .core import evaluate, load_config, preflight, write_reports
from .live_chat import run_suite


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError('invalid_arguments')


def main(argv=None, *, transport_factory=None):
    parser = _Parser(description='专家团只读预检与证据验收', add_help=False)
    parser.add_argument('mode', choices=('preflight', 'evaluate', 'run'))
    parser.add_argument('--config', required=True)
    parser.add_argument('--env-file')
    parser.add_argument('--evidence')
    parser.add_argument('--report-prefix')
    parser.add_argument('--run-id')
    parser.add_argument('--state-dir', type=Path)
    try:
        args = parser.parse_args(argv)
        if args.mode in ('preflight', 'run') and not args.env_file:
            raise ValueError('explicit_env_file_required')
        if args.mode == 'evaluate' and not args.evidence:
            raise ValueError('evidence_file_required')
        config = load_config(Path(args.config))
        if args.mode in ('preflight', 'run'):
            factory = transport_factory or RequestsTransport.from_env_file
            transport = factory(Path(args.env_file))
            if args.mode == 'preflight':
                report = preflight(config, transport)
            else:
                root = Path(__file__).resolve().parents[1]
                run_id = args.run_id or datetime.now(timezone.utc).strftime('team-%Y%m%dT%H%M%S%fZ')
                report = run_suite(config, transport,
                    args.state_dir or root / '.online-e2e-state' / 'team-acceptance', run_id)
                args.report_prefix = args.report_prefix or str(root / 'reports' / 'team-acceptance' / run_id)
        else:
            evidence = json.loads(Path(args.evidence).read_text(encoding='utf-8'))
            report = evaluate(config, evidence)
        if args.report_prefix:
            report['reports'] = write_reports(Path(args.report_prefix), report)
        code = {'pass': 0, 'fail': 1, 'unverified': 3}[report['status']]
    except ClientError as error:
        report, code = {'status': 'fail', 'error': error.code, 'operation': error.operation}, 2
    except (ValueError, OSError, TypeError, KeyError) as error:
        # 不输出可能含本地路径、证据正文或凭证的原始异常。
        known = {'explicit_env_file_required', 'evidence_file_required', 'invalid_arguments'}
        reason = str(error) if type(error) is ValueError and str(error) in known else 'invalid_input_or_report_io'
        report, code = {'status': 'fail', 'error': reason}, 2
    print(json.dumps(sanitize_json(report), ensure_ascii=False, sort_keys=True))
    return code
