#!/usr/bin/env python3
"""
后台测试脚本 - 由 run_pipeline.py --background-test 启动

独立进程运行对话测试，日志输出到文件，不阻塞主进程。

用法:
    python run_test_background.py <task_id> <profiles> <md_path>
    # profiles: 逗号分隔，如 "good,medium"
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_DIR.parent
PROJECT_ROOT = SKILLS_ROOT.parent.parent

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT / "skill_training_build" / ".env")
    load_dotenv(SKILLS_ROOT / ".env")
except ImportError:
    pass

sys.path.insert(0, str(PROJECT_ROOT))


def main():
    if len(sys.argv) != 4:
        print(f"用法: {sys.argv[0]} <task_id> <profiles> <md_path>")
        sys.exit(1)

    task_id = sys.argv[1]
    profiles = sys.argv[2].split(",")
    md_path = Path(sys.argv[3]).resolve()

    # Redirect stdout/stderr to log file
    log_dir = PROJECT_ROOT / "log" / "background_test"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"bg_test_{task_id}_{timestamp}.log"

    with open(log_file, "w", encoding="utf-8") as f:
        # Redirect output
        sys.stdout = f
        sys.stderr = f

        print(f"=== 后台测试启动 ===")
        print(f"时间: {datetime.now().isoformat()}")
        print(f"任务 ID: {task_id}")
        print(f"档位: {profiles}")
        print(f"剧本: {md_path}")
        print()

        for profile_key in profiles:
            print(f"\n{'─' * 50}")
            print(f"▶ 测试档位: {profile_key}")
            print(f"{'─' * 50}")

            try:
                from auto_script_train import WorkflowTester

                tester = WorkflowTester()
                tester.model_type = os.getenv("MODEL_TYPE", "doubao_post")
                tester._initialize_doubao_client()
                tester.student_profile_key = profile_key
                tester.log_format = os.getenv("LOG_FORMAT", "both")
                tester.log_context_path = md_path

                print(f"\n🚀 开始 {tester.STUDENT_PROFILES[profile_key]['label']} 测试...")
                tester.run_with_doubao(task_id)
                print(f"\n✅ {profile_key} 测试完成")

            except Exception as e:
                print(f"\n❌ {profile_key} 测试失败: {e}")
                import traceback
                traceback.print_exc()

            if profile_key != profiles[-1]:
                time.sleep(3)

        print(f"\n=== 后台测试结束 ===")
        print(f"时间: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
