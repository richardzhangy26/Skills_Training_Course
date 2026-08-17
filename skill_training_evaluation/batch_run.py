"""
批量评测 launcher

并发启动多个 main.py 子进程，对一个课程目录下所有 (任务 × 档位) 的对话日志跑评测。
评测报告输出到对话日志同目录，文件名 = 对话文件名替换 _dialogue.json -> _evaluation.json。

用法:
    python batch_run.py \
        --course-docs /Users/.../skills_training_course/中山大学-材料力学 \
        --course-logs /Users/.../log/中山大学-材料力学 \
        [--concurrency 4] [--prefer json|txt]
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional

SCRIPT_DIR = Path(__file__).parent.resolve()
MAIN_PY = SCRIPT_DIR / "main.py"


def discover_jobs(
    course_docs: Path,
    course_logs: Path,
    prefer: str = "json",
) -> List[Tuple[str, str, Path, Path]]:
    """返回 [(task_name, profile, teacher_doc, dialogue_file), ...]"""
    jobs: List[Tuple[str, str, Path, Path]] = []
    other_ext = "txt" if prefer == "json" else "json"

    for task_dir in sorted(course_logs.iterdir()):
        if not task_dir.is_dir():
            continue
        task_name = task_dir.name

        # 匹配教师文档：优先 .md，回退 .docx
        teacher_doc: Optional[Path] = None
        for ext in (".md", ".docx"):
            candidate = course_docs / f"{task_name}{ext}"
            if candidate.exists():
                teacher_doc = candidate
                break
        if not teacher_doc:
            print(f"[跳过] 未找到教师文档: {task_name}")
            continue

        for profile_dir in sorted(task_dir.iterdir()):
            if not profile_dir.is_dir():
                continue
            profile = profile_dir.name

            dialogue_files = sorted(profile_dir.glob(f"*_dialogue.{prefer}"))
            if not dialogue_files:
                dialogue_files = sorted(profile_dir.glob(f"*_dialogue.{other_ext}"))
            if not dialogue_files:
                print(f"[跳过] 无对话文件: {task_name}/{profile}")
                continue

            # 取最新的一份对话
            dialogue_file = dialogue_files[-1]
            jobs.append((task_name, profile, teacher_doc, dialogue_file))

    return jobs


def output_path_for(dialogue_file: Path) -> Path:
    """报告输出路径：对话日志同目录, *_dialogue.* -> *_evaluation.json"""
    name = dialogue_file.name
    for suffix in ("_dialogue.json", "_dialogue.txt"):
        if name.endswith(suffix):
            return dialogue_file.with_name(name[: -len(suffix)] + "_evaluation.json")
    return dialogue_file.with_suffix(".evaluation.json")


async def run_one(
    sem: asyncio.Semaphore,
    idx: int,
    total: int,
    task_name: str,
    profile: str,
    teacher_doc: Path,
    dialogue_file: Path,
) -> Tuple[str, str, int, Path, float]:
    """启动一个 main.py 子进程"""
    output_file = output_path_for(dialogue_file)
    log_file = output_file.with_suffix(".log")

    cmd = [
        sys.executable,
        str(MAIN_PY),
        "--teacher-doc", str(teacher_doc),
        "--dialogue-record", str(dialogue_file),
        "--output", str(output_file),
    ]

    async with sem:
        print(f"[{idx}/{total}] ▶ 启动: {task_name} / {profile}")
        start = time.time()
        with open(log_file, "w", encoding="utf-8") as logf:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=logf,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(SCRIPT_DIR),
            )
            rc = await proc.wait()
        elapsed = time.time() - start
        status = "✓" if rc == 0 else "✗"
        print(f"[{idx}/{total}] {status} 完成: {task_name} / {profile}  ({elapsed:.1f}s, rc={rc})")
        return task_name, profile, rc, output_file, elapsed


async def main():
    parser = argparse.ArgumentParser(description="批量评测 launcher")
    parser.add_argument("--course-docs", required=True, help="教师文档课程目录")
    parser.add_argument("--course-logs", required=True, help="对话日志课程目录")
    parser.add_argument("--concurrency", type=int, default=4, help="并发子进程数")
    parser.add_argument("--prefer", choices=["json", "txt"], default="json", help="优先选用的对话文件格式")
    parser.add_argument("--only", default="", help="只跑指定任务(逗号分隔的任务文件夹名)")
    args = parser.parse_args()

    course_docs = Path(args.course_docs).resolve()
    course_logs = Path(args.course_logs).resolve()

    jobs = discover_jobs(course_docs, course_logs, prefer=args.prefer)

    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        jobs = [j for j in jobs if j[0] in wanted]
        missing = wanted - {j[0] for j in jobs}
        if missing:
            print(f"[警告] 未找到任务: {missing}")
    if not jobs:
        print("没有可执行的评测任务")
        sys.exit(1)

    print(f"\n发现 {len(jobs)} 个评测任务，并发数 = {args.concurrency}\n")
    for i, (task_name, profile, doc, dlg) in enumerate(jobs, 1):
        print(f"  {i:2d}. {task_name} / {profile}")
        print(f"      doc: {doc.name}")
        print(f"      dlg: {dlg.name}")
    print()

    sem = asyncio.Semaphore(args.concurrency)
    started = time.time()
    results = await asyncio.gather(
        *[run_one(sem, i, len(jobs), *job) for i, job in enumerate(jobs, 1)]
    )
    total_elapsed = time.time() - started

    print("\n" + "=" * 70)
    print(f"全部完成 ({total_elapsed:.1f}s)")
    print("=" * 70)
    ok = sum(1 for r in results if r[2] == 0)
    fail = len(results) - ok
    print(f"成功: {ok} / 失败: {fail}")
    if fail:
        print("\n失败任务:")
        for task_name, profile, rc, out, _ in results:
            if rc != 0:
                print(f"  - {task_name} / {profile}  -> 查看日志: {out.with_suffix('.log')}")


if __name__ == "__main__":
    asyncio.run(main())
