#!/usr/bin/env python3
"""Run a 20-question MATH-500 evaluation through the existing local proxy."""
import argparse
import json
import os
import time
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import dotenv_values
from evalscope import TaskConfig, run_task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='claude-opus-5')
    parser.add_argument('--api-url', default='http://127.0.0.1:8787/v1')
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--concurrency', type=int, default=2)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    key = os.environ.get('LLM_API_KEY') or dotenv_values(root / '.env').get('LLM_API_KEY')
    if not key:
        raise SystemExit('LLM_API_KEY is missing from environment and repository .env')
    timestamp = datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d_%H%M%S')
    output = args.resume or Path(__file__).parent / f'{args.model}_math500_20_{timestamp}'
    output.mkdir(parents=True, exist_ok=True)
    config = TaskConfig(
        model=args.model,
        api_url=args.api_url,
        api_key=key,
        eval_type='openai_api',
        datasets=['math_500'],
        limit=4,
        repeats=1,
        seed=42,
        eval_batch_size=args.concurrency,
        generation_config={
            'temperature': 0,
            'max_tokens': 4096,
            'stream': True,
            'timeout': 180,
            'retries': 1,
            'retry_interval': 2,
        },
        judge={'strategy': 'rule'},
        work_dir=str(output),
        no_timestamp=True,
        use_cache=str(args.resume) if args.resume else None,
        rerun_review=bool(args.resume),
        enable_progress_tracker=True,
        ignore_errors=False,
    )
    manifest = {
        'started_at': datetime.now(ZoneInfo('Asia/Singapore')).isoformat(),
        'evalscope_version': version('evalscope'),
        'model': args.model,
        'api_url': args.api_url,
        'dataset': 'math_500',
        'dataset_id': 'AI-ModelScope/MATH-500',
        'sampling': 'first 4 items in each of the 5 difficulty subsets',
        'expected_samples': 20,
        'shots': 0,
        'generation': config.generation_config.model_dump(mode='json'),
        'judge': 'EvalScope mathematical equivalence rules; no judge model',
        'use_cache': str(args.resume) if args.resume else None,
    }
    manifest_path = output / 'run_manifest.json'
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        manifest['previous_attempts'] = previous.get('previous_attempts', []) + [
            {k: v for k, v in previous.items() if k != 'previous_attempts'}
        ]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f'OUTPUT_DIR={output}', flush=True)
    started = time.monotonic()
    try:
        run_task(config)
        manifest['status'] = 'completed'
    except Exception as exc:
        manifest['status'] = 'failed'
        manifest['error_type'] = type(exc).__name__
        manifest['http_status'] = getattr(exc, 'status_code', None)
        raise
    finally:
        manifest['elapsed_seconds'] = round(time.monotonic() - started, 2)
        manifest['finished_at'] = datetime.now(ZoneInfo('Asia/Singapore')).isoformat()
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
