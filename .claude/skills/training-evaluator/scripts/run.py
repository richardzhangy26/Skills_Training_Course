"""
training-evaluator 入口脚本

调用底层 skill_training_evaluation/main.py 对单文件或目录批量评测，
输出 JSON 报告到对话日志同目录，并渲染 ASCII 汇总表。

用法:
    python run.py --teacher <file_or_dir> --dialogue <file_or_dir>
                  [--runs N] [--concurrency 4] [--eval-dir <path>]

规则:
    - teacher 和 dialogue 必须同为文件，或同为目录（不支持混合）。
    - 目录模式：递归查找 dialogue 目录下所有 *_dialogue.{json,txt}，
      按对话文件的顶层任务子目录名匹配 teacher 目录下的同名 *.md/.docx。
    - 报告落点：<dialogue 同目录>/<dialogue 前缀>_evaluation[_run{i}].json
    - --runs N: 每个评测重复跑 N 次（取不同 run 编号），用于观测评分稳定性。
"""
import argparse
import asyncio
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional

HERE = Path(__file__).parent.resolve()
DEFAULT_EVAL_DIR = Path("/Users/zhangyichi/工作/能力训练/skill_training_evaluation")

TEACHER_EXT = (".md", ".docx", ".txt")
DIALOGUE_EXT = (".json", ".txt")


def resolve_eval_dir(explicit: Optional[str]) -> Path:
    if explicit:
        p = Path(explicit).resolve()
        if not (p / "main.py").exists():
            print(f"[错误] --eval-dir 下未找到 main.py: {p}", file=sys.stderr)
            sys.exit(2)
        return p
    if (DEFAULT_EVAL_DIR / "main.py").exists():
        return DEFAULT_EVAL_DIR
    env = os.getenv("TRAINING_EVAL_DIR")
    if env and (Path(env) / "main.py").exists():
        return Path(env).resolve()
    print(
        "[错误] 未找到 skill_training_evaluation 目录。"
        "请用 --eval-dir 指定，或设 TRAINING_EVAL_DIR 环境变量。",
        file=sys.stderr,
    )
    sys.exit(2)


def find_teacher_doc(teacher_dir: Path, task_name: str) -> Optional[Path]:
    for ext in TEACHER_EXT:
        p = teacher_dir / f"{task_name}{ext}"
        if p.exists():
            return p
    return None


def discover_jobs(teacher: Path, dialogue: Path) -> List[Tuple[str, str, Path, Path]]:
    """返回 [(task_name, label, teacher_doc, dialogue_file), ...]"""
    if teacher.is_file() and dialogue.is_file():
        return [(dialogue.stem, "single", teacher, dialogue)]

    if teacher.is_dir() and dialogue.is_dir():
        jobs: List[Tuple[str, str, Path, Path]] = []
        dlg_files = []
        for ext in DIALOGUE_EXT:
            dlg_files.extend(dialogue.rglob(f"*_dialogue{ext}"))
        dlg_files = sorted({p.resolve() for p in dlg_files})

        for dlg in dlg_files:
            try:
                rel_parts = dlg.relative_to(dialogue).parts
            except ValueError:
                continue
            if not rel_parts:
                continue
            task_name = rel_parts[0]
            teacher_doc = find_teacher_doc(teacher, task_name)
            if not teacher_doc:
                print(f"[跳过] 未找到教师文档: {task_name}")
                continue
            label = "/".join(rel_parts[:-1]) or task_name
            jobs.append((task_name, label, teacher_doc, dlg))
        return jobs

    print("[错误] teacher 与 dialogue 必须同为文件或同为目录", file=sys.stderr)
    sys.exit(2)


def output_path_for(dialogue_file: Path, run_idx: int, total_runs: int) -> Path:
    stem = dialogue_file.name
    for suffix in ("_dialogue.json", "_dialogue.txt"):
        if stem.endswith(suffix):
            base = stem[: -len(suffix)]
            break
    else:
        base = dialogue_file.stem

    suffix = f"_evaluation_run{run_idx}.json" if total_runs > 1 else "_evaluation.json"
    return dialogue_file.with_name(base + suffix)


def pdf_output_path_for(dialogue_file: Path, run_idx: int, total_runs: int) -> Path:
    stem = dialogue_file.name
    for suffix in ("_dialogue.json", "_dialogue.txt"):
        if stem.endswith(suffix):
            base = stem[: -len(suffix)]
            break
    else:
        base = dialogue_file.stem

    suffix = f"_evaluation_run{run_idx}.pdf" if total_runs > 1 else "_evaluation.pdf"
    return dialogue_file.with_name(base + suffix)


async def run_one(
    sem: asyncio.Semaphore,
    idx: int,
    total: int,
    task_name: str,
    label: str,
    teacher_doc: Path,
    dialogue_file: Path,
    run_idx: int,
    total_runs: int,
    eval_dir: Path,
) -> Tuple[str, str, int, int, Path, float]:
    output_file = output_path_for(dialogue_file, run_idx, total_runs)
    pdf_output_file = pdf_output_path_for(dialogue_file, run_idx, total_runs)
    log_file = output_file.with_suffix(".log")
    main_py = eval_dir / "main.py"

    cmd = [
        sys.executable, str(main_py),
        "--teacher-doc", str(teacher_doc),
        "--dialogue-record", str(dialogue_file),
        "--output", str(output_file),
        "--output-pdf", str(pdf_output_file),
    ]

    async with sem:
        run_tag = f" (run{run_idx}/{total_runs})" if total_runs > 1 else ""
        print(f"[{idx}/{total}]{run_tag} ▶ 启动: {task_name} / {label}")
        start = time.time()
        with open(log_file, "w", encoding="utf-8") as logf:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=logf, stderr=asyncio.subprocess.STDOUT, cwd=str(eval_dir),
            )
            rc = await proc.wait()
        elapsed = time.time() - start
        status = "✓" if rc == 0 else "✗"
        print(f"[{idx}/{total}]{run_tag} {status} 完成: {task_name} / {label}  ({elapsed:.1f}s, rc={rc})")
        return task_name, label, run_idx, rc, output_file, elapsed


async def main_async(args) -> List[Tuple[str, str, int, Path]]:
    teacher = Path(args.teacher).resolve()
    dialogue = Path(args.dialogue).resolve()
    if not teacher.exists() or not dialogue.exists():
        print("[错误] 路径不存在", file=sys.stderr)
        sys.exit(2)

    eval_dir = resolve_eval_dir(args.eval_dir)
    base_jobs = discover_jobs(teacher, dialogue)
    if not base_jobs:
        print("[错误] 未发现任何可评测的对话", file=sys.stderr)
        sys.exit(1)

    runs = max(1, args.runs)
    expanded_jobs = []
    for job in base_jobs:
        for run_idx in range(1, runs + 1):
            expanded_jobs.append((*job, run_idx))

    print(f"\n发现 {len(base_jobs)} 个对话 × {runs} 次评测 = {len(expanded_jobs)} 次 LLM 评测任务")
    print(f"并发数: {args.concurrency}  |  评测内核: {eval_dir}\n")
    for i, (task_name, label, doc, dlg, run_idx) in enumerate(expanded_jobs, 1):
        tag = f" run{run_idx}" if runs > 1 else ""
        print(f"  {i:2d}. {task_name} / {label}{tag}")
        print(f"      doc: {doc}")
        print(f"      dlg: {dlg}")
    print()

    sem = asyncio.Semaphore(args.concurrency)
    total = len(expanded_jobs)
    results = await asyncio.gather(*[
        run_one(sem, i, total, task_name, label, doc, dlg, run_idx, runs, eval_dir)
        for i, (task_name, label, doc, dlg, run_idx) in enumerate(expanded_jobs, 1)
    ])

    ok = sum(1 for r in results if r[3] == 0)
    fail = len(results) - ok
    print("\n" + "=" * 70)
    print(f"全部完成  成功={ok}  失败={fail}")
    print("=" * 70)
    if fail:
        for task_name, label, run_idx, rc, out, _ in results:
            if rc != 0:
                print(f"  ✗ {task_name} / {label} run{run_idx}  -> log: {out.with_suffix('.log')}")

    return [(t, lbl, ri, out) for (t, lbl, ri, rc, out, _) in results if rc == 0]


def main():
    parser = argparse.ArgumentParser(description="training-evaluator launcher")
    parser.add_argument("--teacher", required=True, help="教师文档: 单文件 或 课程目录")
    parser.add_argument("--dialogue", required=True, help="对话日志: 单文件 或 课程目录")
    parser.add_argument("--runs", type=int, default=1, help="每个评测重复跑 N 次（默认 1）")
    parser.add_argument("--concurrency", type=int, default=4, help="并发子进程数（默认 4）")
    parser.add_argument("--eval-dir", default=None, help="skill_training_evaluation 目录路径（可选）")
    parser.add_argument("--no-report", action="store_true", help="跑完不打印 ASCII 汇总表")
    args = parser.parse_args()

    reports = asyncio.run(main_async(args))
    if not args.no_report and reports:
        from ascii_report import render
        print("\n" + render([str(p) for _, _, _, p in reports]))


if __name__ == "__main__":
    main()
