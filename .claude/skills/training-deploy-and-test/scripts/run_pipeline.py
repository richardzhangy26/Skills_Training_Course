#!/usr/bin/env python3
"""
训练部署与自动测试 Pipeline

端到端自动化流程：
1. 为训练剧本的每个阶段生成背景图 (training-background-generator)
2. 将训练剧本导入到 Polymas 平台 (create_task_from_markdown.py)
3. 使用「优秀学生」和「中等学生」两个档位自动进行对话测试 (auto_script_train.py)

使用方式:
    python run_pipeline.py <剧本配置.md> [--task-id <任务ID>] [--skip-bg] [--skip-import] [--skip-test] [--profiles good,medium]

环境变量 (从项目根目录 .env 加载):
    AUTHORIZATION: Polymas Bearer Token (必需)
    COOKIE: 浏览器 Cookie 字符串 (必需)
    TASK_ID: 训练任务 ID (可通过 --task-id 覆盖)
    ARK_API_KEY / DOUBAO_MODEL: Doubao SDK 模式 (默认)
    LLM_API_KEY / LLM_MODEL / LLM_API_URL: Doubao POST 模式
    MODEL_TYPE: doubao_sdk (默认) 或 doubao_post
    LOG_FORMAT: txt / json / both (默认 both)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve project root so we can import project modules and locate scripts.
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent  # training-deploy-and-test/
SKILLS_ROOT = SKILL_DIR.parent  # .claude/skills/
PROJECT_ROOT = SKILLS_ROOT.parent.parent  # 能力训练/

# Load .env from project root
try:
    from dotenv import load_dotenv

    # Project root .env first (main config)
    load_dotenv(PROJECT_ROOT / ".env")
    # skill_training_build .env as fallback
    load_dotenv(PROJECT_ROOT / "skill_training_build" / ".env")
    # skills .env for background generator
    load_dotenv(SKILLS_ROOT / ".env")
except ImportError:
    pass  # python-dotenv not installed; rely on already-exported env vars

# Add project root to sys.path so we can import WorkflowTester directly
sys.path.insert(0, str(PROJECT_ROOT))


# ===========================================================================
# Utilities
# ===========================================================================


def _print_banner(title: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def _run_subprocess(
    cmd: list[str], description: str, cwd: str | Path | None = None
) -> bool:
    """Run a subprocess and stream its output. Returns True on success."""
    _print_banner(description)
    print(f"▶ {' '.join(str(c) for c in cmd)}\n")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            timeout=600,  # 10 minute timeout
        )
        if proc.returncode != 0:
            print(f"\n❌ {description} 失败 (exit code {proc.returncode})")
            return False
        print(f"\n✅ {description} 完成")
        return True
    except subprocess.TimeoutExpired:
        print(f"\n❌ {description} 超时 (>600s)")
        return False
    except FileNotFoundError as e:
        print(f"\n❌ 命令未找到: {e}")
        return False


# ===========================================================================
# Step 1: Background Image Generation
# ===========================================================================


def step_generate_backgrounds(md_path: Path) -> bool:
    """Generate background images for each training stage."""
    bg_script = (
        SKILLS_ROOT
        / "training-background-generator"
        / "scripts"
        / "generate_background.py"
    )

    if not bg_script.exists():
        print(f"⚠️  背景图生成脚本不存在: {bg_script}")
        print("   跳过背景图生成步骤。")
        return True  # Non-fatal: continue pipeline

    cmd = [sys.executable, str(bg_script), str(md_path)]
    return _run_subprocess(cmd, "📸 Step 1/3: 生成阶段背景图")


# ===========================================================================
# Step 2: Import to Platform
# ===========================================================================


def step_import_to_platform(md_path: Path, task_id: str) -> bool:
    """Import the training script to Polymas platform."""
    import_script = (
        PROJECT_ROOT / "skill_training_build" / "create_task_from_markdown.py"
    )

    if not import_script.exists():
        print(f"❌ 导入脚本不存在: {import_script}")
        return False

    # Validate required env vars
    auth = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not auth or not cookie:
        print("❌ 缺少必要的环境变量: AUTHORIZATION 和/或 COOKIE")
        print("   请在 .env 文件中配置，或从浏览器 DevTools 获取。")
        return False

    cmd = [sys.executable, str(import_script), str(md_path), task_id]
    return _run_subprocess(
        cmd,
        "📦 Step 2/3: 导入训练剧本到平台",
        cwd=PROJECT_ROOT / "skill_training_build",
    )


# ===========================================================================
# Step 3: Auto Dialogue Test
# ===========================================================================


def step_auto_test(task_id: str, profiles: list[str], md_path: Path) -> dict[str, bool]:
    """
    Run auto dialogue test for each student profile.

    Uses WorkflowTester programmatically (not subprocess) to avoid
    interactive input() prompts in auto_script_train.py's main block.
    """
    _print_banner("🧪 Step 3/3: 自动对话测试")

    results: dict[str, bool] = {}

    for profile_key in profiles:
        print(f"\n{'─' * 50}")
        print(f"▶ 测试档位: {profile_key}")
        print(f"{'─' * 50}")

        try:
            # Import fresh each time to avoid state leaks
            from auto_script_train import WorkflowTester

            tester = WorkflowTester()

            # Configure non-interactively
            tester.model_type = os.getenv("MODEL_TYPE", "doubao_post")
            tester._initialize_doubao_client()
            tester.student_profile_key = profile_key
            tester.log_format = os.getenv("LOG_FORMAT", "both")

            # Set log context path to the markdown file for organized logging
            tester.log_context_path = md_path.resolve()

            # Run the auto test
            print(f"\n🚀 开始 {tester.STUDENT_PROFILES[profile_key]['label']} 测试...")
            tester.run_with_doubao(task_id)

            results[profile_key] = True
            print(f"\n✅ {profile_key} 测试完成")

        except Exception as e:
            print(f"\n❌ {profile_key} 测试失败: {e}")
            import traceback

            traceback.print_exc()
            results[profile_key] = False

        # Brief pause between test runs
        if profile_key != profiles[-1]:
            print("\n⏳ 等待 3 秒后开始下一个档位测试...")
            time.sleep(3)

    return results


# ===========================================================================
# Pipeline Orchestrator
# ===========================================================================


def run_pipeline(
    md_path: Path,
    task_id: str,
    profiles: list[str],
    skip_bg: bool = False,
    skip_import: bool = False,
    skip_test: bool = False,
) -> bool:
    """
    Execute the full pipeline.

    Returns True if all steps succeeded.
    """
    _print_banner("🚀 训练部署与自动测试 Pipeline")
    print(f"  剧本文件: {md_path}")
    print(f"  任务 ID:  {task_id}")
    print(f"  测试档位: {', '.join(profiles)}")
    print(f"  跳过背景图: {'是' if skip_bg else '否'}")
    print(f"  跳过导入:   {'是' if skip_import else '否'}")
    print(f"  跳过测试:   {'是' if skip_test else '否'}")

    all_ok = True

    # ---- Step 1: Background images ----
    if not skip_bg:
        if not step_generate_backgrounds(md_path):
            print("\n⚠️  背景图生成失败，继续后续步骤...")
            # Non-fatal: backgrounds are optional
    else:
        print("\n⏭  跳过背景图生成")

    # ---- Step 2: Import to platform ----
    if not skip_import:
        if not step_import_to_platform(md_path, task_id):
            print("\n❌ 平台导入失败，中止 Pipeline。")
            return False
    else:
        print("\n⏭  跳过平台导入")

    # ---- Step 3: Auto dialogue test ----
    if not skip_test:
        test_results = step_auto_test(task_id, profiles, md_path)

        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        for profile, success in test_results.items():
            label = "✅ 通过" if success else "❌ 失败"
            print(f"  {profile}: {label}")

        if not all(test_results.values()):
            all_ok = False
    else:
        print("\n⏭  跳过自动测试")

    # ---- Summary ----
    _print_banner("Pipeline 执行完毕")
    if all_ok:
        print("✅ 所有步骤成功完成！")
        print(f"\n📁 日志目录: {PROJECT_ROOT / 'log'}")
    else:
        print("⚠️  部分步骤存在问题，请检查上方输出。")

    return all_ok


# ===========================================================================
# CLI Entry Point
# ===========================================================================


def main():
    parser = argparse.ArgumentParser(
        description="训练部署与自动测试 Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完整流程
  python run_pipeline.py 训练剧本配置.md --task-id abc123

  # 跳过背景图，只导入和测试
  python run_pipeline.py 训练剧本配置.md --task-id abc123 --skip-bg

  # 只运行测试（已手动导入）
  python run_pipeline.py 训练剧本配置.md --task-id abc123 --skip-bg --skip-import

  # 自定义测试档位
  python run_pipeline.py 训练剧本配置.md --task-id abc123 --profiles good,bad
        """,
    )

    parser.add_argument(
        "markdown_path",
        type=str,
        help="训练剧本配置 Markdown 文件路径",
    )
    parser.add_argument(
        "--task-id",
        type=str,
        default=None,
        help="训练任务 ID (默认从 TASK_ID 环境变量读取)",
    )
    parser.add_argument(
        "--profiles",
        type=str,
        default="good,medium",
        help="测试的学生档位，逗号分隔 (默认: good,medium)",
    )
    parser.add_argument("--skip-bg", action="store_true", help="跳过背景图生成")
    parser.add_argument("--skip-import", action="store_true", help="跳过平台导入")
    parser.add_argument("--skip-test", action="store_true", help="跳过自动测试")

    args = parser.parse_args()

    # Resolve markdown path
    md_path = Path(args.markdown_path).expanduser().resolve()
    if not md_path.exists():
        print(f"❌ 文件不存在: {md_path}")
        sys.exit(1)

    # Resolve task ID
    task_id = args.task_id or os.getenv("TASK_ID")
    if not task_id:
        print("❌ 未指定 task_id。请通过 --task-id 参数或 TASK_ID 环境变量提供。")
        sys.exit(1)

    # Parse profiles
    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    valid_profiles = {"good", "medium", "bad"}
    invalid = set(profiles) - valid_profiles
    if invalid:
        print(f"❌ 无效的学生档位: {invalid}. 可选: {valid_profiles}")
        sys.exit(1)

    # Run pipeline
    success = run_pipeline(
        md_path=md_path,
        task_id=task_id,
        profiles=profiles,
        skip_bg=args.skip_bg,
        skip_import=args.skip_import,
        skip_test=args.skip_test,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
