#!/usr/bin/env python3
"""
训练部署与自动测试 Pipeline

端到端自动化流程：
Step 0: 创建训练任务（可选）
        ├── 解析 Markdown 基础配置（任务名称、描述）
        ├── 生成封面图（使用 Doubao API 或第一阶段背景图）
        ├── 调用 API 创建训练任务
        └── 自动将 TASK_ID 写入 .env
Step 1: 为训练剧本的每个阶段生成背景图 (training-background-generator)
Step 2: 将训练剧本导入到 Polymas 平台 (create_task_from_markdown.py)
Step 3: 使用「优秀学生」和「中等学生」两个档位自动进行对话测试 (auto_script_train.py)

使用方式:
    # 创建新任务并完整部署
    python run_pipeline.py <剧本配置.md> --create-task --course-id <课程ID>

    # 仅创建任务（不执行后续步骤）
    python run_pipeline.py <剧本配置.md> --create-only --course-id <课程ID>

    # 使用现有任务部署（向后兼容）
    python run_pipeline.py <剧本配置.md> --task-id <任务ID>

    # 从环境变量读取 TASK_ID，如果不存在则自动创建
    python run_pipeline.py <剧本配置.md> --course-id <课程ID>

环境变量 (从项目根目录 .env 加载):
    AUTHORIZATION: Polymas Bearer Token (必需)
    COOKIE: 浏览器 Cookie 字符串 (必需)
    COURSE_ID: 课程 ID (创建新任务时需要，可被 --course-id 覆盖)
    TASK_ID: 训练任务 ID (使用现有任务时，可被 --task-id 覆盖)
    ARK_API_KEY / DOUBAO_MODEL: Doubao SDK 模式 (生成封面图时需要)
    MODEL_TYPE: doubao_sdk (默认) 或 doubao_post
    LOG_FORMAT: txt / json / both (默认 both)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

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

# Add skill_training_build to path for importing create_configuration_from_markdown
sys.path.insert(0, str(PROJECT_ROOT / "skill_training_build"))


# ===========================================================================
# Constants
# ===========================================================================

PLACEHOLDER_VALUES = {
    "",
    "待生成",
    "(待生成)",
    "（待生成）",
    "选填",
    "(选填)",
    "（选填）",
}


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


def is_placeholder_value(value: str) -> bool:
    """Check if a value is a placeholder."""
    normalized = value.strip() if value else ""
    compact = normalized.replace(" ", "")
    return compact in PLACEHOLDER_VALUES


def normalize_md_value(raw_value: str) -> str:
    """Normalize markdown field value."""
    value = raw_value.strip()
    if not value:
        return ""
    value = re.sub(r'（[^）]*选填[^）]*）', '', value)
    value = re.sub(r'\([^)]*选填[^)]*\)', '', value)
    value = re.sub(r'（[^）]*默认为空[^）]*）', '', value)
    value = re.sub(r'\([^)]*默认为空[^)]*\)', '', value)
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1].strip()
    if value.startswith(""") and value.endswith("""):
        value = value[1:-1].strip()
    return value


def extract_base_field(content: str, label: str) -> str:
    """Extract a field from markdown content."""
    pattern = re.compile(
        rf"^\s*-\s*\*\*{re.escape(label)}\*\*\s*[：:]\s*(.+?)\s*$",
        flags=re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        return ""
    return normalize_md_value(match.group(1))


def parse_base_configuration(markdown_path: Path) -> Tuple[str, str, str]:
    """
    Parse base configuration from markdown.
    Returns: (task_name, description, background_image)
    """
    content = markdown_path.read_text(encoding="utf-8")
    task_name = extract_base_field(content, "任务名称")
    description = extract_base_field(content, "任务描述")
    background_image = extract_base_field(content, "背景图")

    return task_name, description, background_image


def write_task_id_to_env(task_id: str, env_path: Path | None = None) -> Path:
    """Write TASK_ID to .env file and update current process environment."""
    if env_path is None:
        env_path = PROJECT_ROOT / ".env"

    env_path = Path(env_path)
    task_line = f'TASK_ID="{task_id}"\n'

    if env_path.exists():
        original_text = env_path.read_text(encoding="utf-8")
        lines = original_text.splitlines(keepends=True)
        kept_lines = [
            line for line in lines
            if not re.match(r"^\s*TASK_ID\s*=", line)
        ]
        new_text = "".join(kept_lines)
        if new_text and not new_text.endswith("\n"):
            new_text += "\n"
        new_text += task_line
    else:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        new_text = task_line

    env_path.write_text(new_text, encoding="utf-8")
    os.environ["TASK_ID"] = task_id
    return env_path


# ===========================================================================
# Step 0: Create Training Task
# ===========================================================================


def generate_cover_prompt(task_name: str, task_description: str) -> str:
    """Generate cover image prompt based on task info."""
    # Keywords matching for specific prompt templates
    prompt_templates = {
        "离心泵": "工业化工厂，离心泵运行场景，技术人员在仔细检查泵的状态，高清现代化工业设备，蓝色和灰色调，工业气氛浓厚，精密检测仪器，16:9宽屏，电影级质感，光影细节丰富",
        "汽蚀": "工业现场，泵的故障诊断场景，工程师手持诊断工具，高科技仪器，动态光线，深蓝色和银灰色调，紧张专业的工作氛围，16:9宽屏，科技感十足",
        "精馏": "化学实验室，精馏装置运行中，液体流动通过冷凝管，蒸馏烧瓶加热，科学仪器精密排列，蓝白调，科技感强，专业教学环境，玻璃仪器闪烁反光，16:9宽屏，细节丰富",
        "展馆": "现代科技展馆内部，宽敞明亮的展厅，各种创意展示品，参观者在互动体验，科技感强烈，现代建筑风格，柔和的照明，开放式空间，16:9宽屏，沉浸感十足",
        "非暴力沟通": "温暖的协作工作室，两个人在进行深入沟通交流，放松的氛围，柔和的自然光线，绿植点缀，现代简约风格，友好和谐，16:9宽屏，人性化气氛",
        "投资": "现代办公会议室，投资推介会场景，专业的演讲者，观众认真听讲，高档的会议设备，蓝色商务调，专业严谨的氛围，大屏幕显示，16:9宽屏，企业级质感",
        "大豆": "金黄色的大豆田，成熟的豆荚饱满，阳光洒在田野上，农业专家在田间考察，丰收的喜悦，蓝天白云，16:9宽屏，田园风光，农业科学研究氛围",
        "栽培": "现代化温室大棚，绿色植物茁壮成长，农业科技人员在进行栽培实验，专业的培育设备，生机勃勃，16:9宽屏，现代农业科技氛围",
        "化工": "现代化工厂全景，管道纵横交错，反应塔高耸，安全设施完备，黄昏时分的工业美景，16:9宽屏，现代工业科技氛围",
    }

    combined_text = (task_name + " " + task_description).lower()
    for keyword, template in prompt_templates.items():
        if keyword.lower() in combined_text:
            return template

    # Default prompt
    default_prompt = (
        f"现代教学培训场景，专业人士在讲解'{task_name}'，"
        "互动教学环境，科技感和教育感结合，光线充足，"
        "氛围积极向上，现代化设施，16:9宽屏，高清质感，"
        "细节丰富，专业呈现"
    )
    return default_prompt


def generate_cover_image(prompt: str) -> str | None:
    """
    Generate cover image using Doubao API.
    Returns image URL or None on failure.
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("⚠️  openai 包未安装，无法生成封面图")
        return None

    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("⚠️  未设置 ARK_API_KEY，无法生成封面图")
        return None

    try:
        client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )
        model = "doubao-seedream-4-0-250828"

        response = client.images.generate(
            model=model,
            prompt=prompt,
            size="2K",  # 2560x1440，16:9比例
            response_format="url",
            extra_body={"watermark": True},
        )
        return response.data[0].url
    except Exception as e:
        print(f"⚠️  封面图生成失败: {e}")
        return None


def download_cover_image(url: str, output_path: Path) -> bool:
    """Download cover image from URL to local path."""
    try:
        import requests
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        output_path.write_bytes(response.content)
        return True
    except Exception as e:
        print(f"⚠️  封面图下载失败: {e}")
        return False


def step_create_task(md_path: Path, course_id: str) -> Tuple[bool, str | None]:
    """
    Step 0: Create training task.

    Returns: (success, task_id)
    """
    _print_banner("🆕 Step 0/3: 创建训练任务")

    # 1. Parse base configuration
    print("\n📖 解析基础配置...")
    task_name, description, bg_image = parse_base_configuration(md_path)

    if not task_name:
        print("❌ Markdown 缺少基础配置字段：任务名称")
        print("   请在 Markdown 开头添加：")
        print("   ## 基础配置")
        print("   - **任务名称**: 您的任务名称")
        print("   - **任务描述**: 任务描述")
        return False, None

    if not description:
        print("❌ Markdown 缺少基础配置字段：任务描述")
        return False, None

    print(f"   ✓ 任务名称: {task_name}")
    print(f"   ✓ 任务描述: {description[:50]}...")

    # 2. Generate or find cover image
    print("\n🖼️  准备任务封面图...")
    cover_path = None

    # Try to use provided background image
    if bg_image and not is_placeholder_value(bg_image):
        if not re.match(r"^[a-zA-Z]+://", bg_image):
            # Local path
            cover_path = Path(bg_image)
            if not cover_path.is_absolute():
                cover_path = (md_path.parent / bg_image).resolve()
            if cover_path.exists():
                print(f"   ✓ 使用指定背景图: {cover_path}")
            else:
                print(f"   ⚠️ 指定背景图不存在: {cover_path}")
                cover_path = None

    # If no valid cover, try to generate one
    if cover_path is None:
        print("   🎨 使用 Doubao API 生成封面图...")
        prompt = generate_cover_prompt(task_name, description)
        print(f"   提示词: {prompt[:60]}...")

        cover_url = generate_cover_image(prompt)

        if cover_url:
            # Download to local
            covers_dir = md_path.parent / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            cover_path = covers_dir / "task_cover.png"

            if download_cover_image(cover_url, cover_path):
                print(f"   ✓ 封面图已下载: {cover_path}")
            else:
                print("   ⚠️ 封面图下载失败，将使用平台默认封面")
                cover_path = None
        else:
            print("   ⚠️ 封面图生成失败，将使用平台默认封面")

    # 3. Import create_configuration function and create task
    print("\n🚀 调用 API 创建训练任务...")
    try:
        from create_configuration_from_markdown import (
            BaseConfiguration,
            create_configuration,
            upload_cover_image,
        )

        base_config = BaseConfiguration(
            train_task_name=task_name,
            description=description,
            background_image=str(cover_path) if cover_path else "",
        )

        # Upload cover image if exists
        train_task_cover = {"fileId": "", "fileUrl": ""}
        if cover_path and cover_path.exists():
            print(f"   📤 上传封面图...")
            uploaded = upload_cover_image(cover_path)
            if uploaded:
                train_task_cover = uploaded
                print(f"   ✓ 封面上传成功")
            else:
                print(f"   ⚠️ 封面上传失败，使用默认封面")

        # Create task
        task_id = create_configuration(
            base_config=base_config,
            course_id=course_id,
            train_task_cover=train_task_cover,
        )

        print(f"\n✅ 训练任务创建成功!")
        print(f"   任务 ID: {task_id}")
        print(f"   任务名称: {task_name}")

        # 4. Write TASK_ID to .env
        env_path = write_task_id_to_env(task_id)
        print(f"\n📝 TASK_ID 已写入: {env_path}")

        return True, task_id

    except ImportError as e:
        print(f"❌ 导入 create_configuration_from_markdown 失败: {e}")
        return False, None
    except Exception as e:
        print(f"❌ 创建训练任务失败: {e}")
        return False, None


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


def step_import_to_platform(md_path: Path, task_id: str, delete_existing: bool = False) -> bool:
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

    # If delete_existing is True, we need to handle the interactive prompt
    # by providing "y" as input
    if delete_existing:
        _print_banner("📦 Step 2/3: 导入训练剧本到平台 (自动删除现有节点)")
        print(f"▶ {' '.join(str(c) for c in cmd)}\n")

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT / "skill_training_build"),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            # Provide "y" for the delete confirmation prompt
            stdout, _ = proc.communicate(input="y\n", timeout=600)
            print(stdout)
            if proc.returncode != 0:
                print(f"\n❌ 平台导入失败 (exit code {proc.returncode})")
                return False
            print("\n✅ 平台导入完成 (已删除旧节点)")
            return True
        except subprocess.TimeoutExpired:
            print("\n❌ 平台导入超时 (>600s)")
            return False
        except Exception as e:
            print(f"\n❌ 平台导入出错: {e}")
            return False

    # Standard import without auto-delete
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
    task_id: str | None,
    profiles: list[str],
    skip_bg: bool = False,
    skip_import: bool = False,
    skip_test: bool = False,
    delete_existing: bool = False,
    create_task: bool = False,
    create_only: bool = False,
    course_id: str | None = None,
) -> bool:
    """
    Execute the full pipeline.

    Returns True if all steps succeeded.
    """
    _print_banner("🚀 训练部署与自动测试 Pipeline")
    print(f"  剧本文件: {md_path}")
    print(f"  任务 ID:  {task_id or '(将自动创建)'}")
    print(f"  测试档位: {', '.join(profiles)}")
    print(f"  跳过背景图: {'是' if skip_bg else '否'}")
    print(f"  跳过导入:   {'是' if skip_import else '否'}")
    print(f"  跳过测试:   {'是' if skip_test else '否'}")
    print(f"  删除旧节点: {'是' if delete_existing else '否'}")
    print(f"  仅创建任务: {'是' if create_only else '否'}")

    all_ok = True

    # ---- Step 0: Create task (if needed) ----
    if create_task or (not task_id and not create_only):
        if not course_id:
            print("\n❌ 创建训练任务需要提供 COURSE_ID")
            print("   请通过 --course-id 参数或 COURSE_ID 环境变量提供。")
            return False

        success, new_task_id = step_create_task(md_path, course_id)
        if not success:
            print("\n❌ 训练任务创建失败，中止 Pipeline。")
            return False

        task_id = new_task_id

        if create_only:
            _print_banner("任务创建完成")
            print(f"✅ 训练任务已成功创建！")
            print(f"   任务 ID: {task_id}")
            print(f"   任务名称: {parse_base_configuration(md_path)[0]}")
            print(f"\n📝 TASK_ID 已写入 .env 文件")
            print("\n📋 后续可以使用以下命令进行部署：")
            print(f"   python run_pipeline.py '{md_path}' --task-id {task_id}")
            return True
    else:
        if not task_id:
            print("\n❌ 未指定 task_id，且未启用自动创建。")
            print("   请通过 --task-id 参数、TASK_ID 环境变量提供，")
            print("   或使用 --create-task 自动创建新任务。")
            return False

    # ---- Step 1: Background images ----
    if not skip_bg:
        if not step_generate_backgrounds(md_path):
            print("\n⚠️  背景图生成失败，继续后续步骤...")
            # Non-fatal: backgrounds are optional
    else:
        print("\n⏭  跳过背景图生成")

    # ---- Step 2: Import to platform ----
    if not skip_import:
        if not step_import_to_platform(md_path, task_id, delete_existing):
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
  # 创建新任务并完整部署
  python run_pipeline.py 训练剧本配置.md --create-task --course-id xxx

  # 仅创建任务（不执行后续步骤）
  python run_pipeline.py 训练剧本配置.md --create-only --course-id xxx

  # 使用现有任务部署（向后兼容）
  python run_pipeline.py 训练剧本配置.md --task-id abc123

  # 从环境变量读取配置
  export COURSE_ID=xxx
  export TASK_ID=abc123  # 可选，不设置则自动创建
  python run_pipeline.py 训练剧本配置.md

  # 完整流程（使用现有任务）
  python run_pipeline.py 训练剧本配置.md --task-id abc123

  # 跳过背景图，只导入和测试
  python run_pipeline.py 训练剧本配置.md --task-id abc123 --skip-bg

  # 只运行测试（已手动导入）
  python run_pipeline.py 训练剧本配置.md --task-id abc123 --skip-bg --skip-import

  # 自定义测试档位
  python run_pipeline.py 训练剧本配置.md --task-id abc123 --profiles good,bad

  # 删除现有节点后重新导入
  python run_pipeline.py 训练剧本配置.md --task-id abc123 --delete-existing
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
        "--course-id",
        type=str,
        default=None,
        help="课程 ID (创建新任务时需要，也可从 COURSE_ID 环境变量读取)",
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
    parser.add_argument("--delete-existing", action="store_true", help="删除平台上现有节点后重新导入")
    parser.add_argument("--create-task", action="store_true", help="强制创建新任务（即使 TASK_ID 已存在）")
    parser.add_argument("--create-only", action="store_true", help="仅创建任务，完成后退出，不执行后续部署步骤")

    args = parser.parse_args()

    # Resolve markdown path
    md_path = Path(args.markdown_path).expanduser().resolve()
    if not md_path.exists():
        print(f"❌ 文件不存在: {md_path}")
        sys.exit(1)

    # Resolve task ID
    task_id = args.task_id or os.getenv("TASK_ID")

    # Resolve course ID
    course_id = args.course_id or os.getenv("COURSE_ID")

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
        delete_existing=args.delete_existing,
        create_task=args.create_task,
        create_only=args.create_only,
        course_id=course_id,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
