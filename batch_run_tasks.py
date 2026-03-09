#!/usr/bin/env python3
"""
批量运行多个任务的自动化脚本
用法: python batch_run_tasks.py
"""
import os
import sys
import subprocess
import time

# ============ 配置区域 ============
# 要运行的任务ID列表
TASK_IDS = [
    "GEaZp9LAwJcXk8K7BxjM",
    "9VDE9O8Q2XHljZbLkDjG",
    "LRdRY6zQNehALbBbnPxj",
]

# 要运行的学生档位: good=优秀学生, medium=需要引导的学生
PROFILES = [
    ("good", "优秀学生"),
    ("medium", "需要引导的学生"),
]

# 模型类型: doubao_sdk 或 doubao_post
MODEL_TYPE = os.getenv("MODEL_TYPE", "doubao_post")

# 日志格式: txt, json, both
LOG_FORMAT = "both"

# 每个任务运行之间的延迟(秒)
TASK_DELAY = 2
# ==================================


def run_task(task_id: str, profile_key: str, profile_label: str) -> bool:
    """运行单个任务"""
    print("\n" + "=" * 70)
    print(f"🎯 开始运行任务: {task_id}")
    print(f"👤 学生档位: {profile_label} ({profile_key})")
    print(f"🤖 模型类型: {MODEL_TYPE}")
    print("=" * 70)

    # 设置环境变量
    env = os.environ.copy()
    env["TASK_ID"] = task_id
    env["MODEL_TYPE"] = MODEL_TYPE
    env["LOG_FORMAT"] = LOG_FORMAT
    env["STUDENT_PROFILE"] = profile_key  # 用于传递给主脚本

    # 使用 Mode 3 (Doubao 自动生成答案模式)
    # 通过输入重定向来模拟用户选择: 3 = 自动化模式, 然后选择档位
    # 这里我们创建一个输入序列来模拟交互
    inputs = []

    # 根据 MODEL_TYPE 选择
    if MODEL_TYPE == "doubao_sdk":
        inputs.append("1")  # 选择 Doubao SDK
    else:
        inputs.append("2")  # 选择 Doubao POST

    # 选择运行模式 3 (自动化)
    inputs.append("3")

    # 选择学生档位
    if profile_key == "good":
        inputs.append("1")  # 优秀学生
    elif profile_key == "medium":
        inputs.append("2")  # 需要引导的学生
    else:
        inputs.append("3")  # 答非所问的学生

    # 对话示例路径 (跳过)
    inputs.append("")

    # 知识库路径 (跳过)
    inputs.append("")

    # 构建输入字符串
    input_text = "\n".join(inputs) + "\n"

    try:
        # 运行主脚本
        result = subprocess.run(
            [sys.executable, "auto_script_train.py"],
            input=input_text,
            text=True,
            env=env,
            capture_output=False,  # 直接输出到终端
        )

        if result.returncode == 0:
            print(f"\n✅ 任务 {task_id} - {profile_label} 运行完成")
            return True
        else:
            print(f"\n❌ 任务 {task_id} - {profile_label} 运行失败，返回码: {result.returncode}")
            return False

    except Exception as e:
        print(f"\n❌ 运行任务时出错: {str(e)}")
        return False


def main():
    print("=" * 70)
    print("📋 批量任务运行工具")
    print("=" * 70)
    print(f"\n任务列表: {len(TASK_IDS)} 个")
    for tid in TASK_IDS:
        print(f"  - {tid}")
    print(f"\n学生档位: {len(PROFILES)} 个")
    for key, label in PROFILES:
        print(f"  - {label} ({key})")
    print(f"\n预计总运行次数: {len(TASK_IDS) * len(PROFILES)} 次")
    print("=" * 70)

    # 直接开始运行（无需确认）
    print("\n🚀 3秒后开始运行...")
    time.sleep(3)

    # 记录结果
    results = []
    total = len(TASK_IDS) * len(PROFILES)
    current = 0

    for task_id in TASK_IDS:
        for profile_key, profile_label in PROFILES:
            current += 1
            print(f"\n\n{'#' * 70}")
            print(f"# 进度: {current}/{total}")
            print(f"{'#' * 70}")

            success = run_task(task_id, profile_key, profile_label)
            results.append({
                "task_id": task_id,
                "profile": profile_label,
                "success": success,
            })

            if current < total:
                print(f"\n⏳ 等待 {TASK_DELAY} 秒后开始下一个任务...")
                time.sleep(TASK_DELAY)

    # 输出总结
    print("\n\n" + "=" * 70)
    print("📊 运行总结")
    print("=" * 70)

    success_count = sum(1 for r in results if r["success"])
    fail_count = total - success_count

    print(f"\n总计: {total} 个任务")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")

    if fail_count > 0:
        print("\n失败的任务:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['task_id']} ({r['profile']})")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
