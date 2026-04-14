#!/usr/bin/env python3
"""
generate_evaluation_report.py

生成智能体配置评估 PDF 报告的入口脚本。

输入:
  --teacher-doc      教师标准文档 (.md / .txt / .docx)
  --dialogue         学生测试对话日志 (.txt / .json, 来自 auto_script_train.py)
  --workflow-config  (可选) 工作流配置文档 (.md / .docx)

输出:
  --output-pdf       多维度 PDF 评估报告 (默认 evaluation_report.pdf)
  --output-json      (可选) 同时输出一份 JSON 结构化报告

评分标准遵循 prompts.ts 中的 STANDARD_SCORES (5 维度 / 21 子维度, 满分 100)。

环境变量 (读取自 .env 或 shell):
  LLM_API_KEY        Polymas API key (必需)
  LLM_API_URL        POST 接口 URL (必需)
                     示例: http://llm-service.polymas.com/api/openai/v1/chat/completions
  LLM_MODEL          模型名 (默认 Doubao-1.5-pro-32k;
                     若需 Claude Sonnet 4.6, 请设为 claude-sonnet-4-6)
  LLM_SERVICE_CODE   Polymas 调用路由 (默认 SI_Ability)
  USE_POST_API       兼容标记 (本脚本始终走 POST 接口, 此变量仅作提示)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore


REPO_ROOT = Path(__file__).resolve().parent
EVAL_PKG_DIR = REPO_ROOT / "skill_training_evaluation"
PROMPTS_JSON_PATH = EVAL_PKG_DIR / "prompts.json"
PROMPTS_TS_PATH = REPO_ROOT / "prompts.ts"
BUILD_SCRIPT = EVAL_PKG_DIR / "scripts" / "build_prompts_json.py"

# Put skill_training_evaluation/ on sys.path so its modules can import each other
# using bare names (the package was authored with that expectation).
if str(EVAL_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_PKG_DIR))


def _load_env() -> None:
    if load_dotenv is None:
        return
    for candidate in [
        REPO_ROOT / ".env",
        Path.cwd() / ".env",
        EVAL_PKG_DIR / ".env",
    ]:
        if candidate.exists():
            load_dotenv(candidate, override=False)
            print(f"🔧 Loaded env from {candidate}")
            break


def _ensure_prompts_json() -> None:
    """Populate prompts.json from prompts.ts if it is empty or missing."""
    needs_build = False
    if not PROMPTS_JSON_PATH.exists():
        needs_build = True
    else:
        try:
            data = json.loads(PROMPTS_JSON_PATH.read_text(encoding="utf-8"))
            if not data:
                needs_build = True
        except json.JSONDecodeError:
            needs_build = True

    if not needs_build:
        return

    if not PROMPTS_TS_PATH.exists():
        raise SystemExit(
            f"❌ prompts.json 为空且找不到源文件 {PROMPTS_TS_PATH}; "
            "无法自动构建评分模板。"
        )
    if not BUILD_SCRIPT.exists():
        raise SystemExit(f"❌ 缺少构建脚本: {BUILD_SCRIPT}")

    print(f"🔁 prompts.json 为空或缺失, 从 {PROMPTS_TS_PATH.name} 构建...")
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            "❌ 构建 prompts.json 失败:\n"
            + (result.stdout or "")
            + (result.stderr or "")
        )
    print((result.stdout or "").strip())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="生成智能体配置评估 PDF 报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--teacher-doc", "-t", required=True,
                        help="教师标准文档路径 (.md/.txt/.docx)")
    parser.add_argument("--dialogue", "-d", required=True,
                        help="对话日志路径 (.txt/.json)")
    parser.add_argument("--workflow-config", "-w", default=None,
                        help="(可选) 工作流配置文档 (.md/.docx)")
    parser.add_argument("--output-pdf", "-o", default="evaluation_report.pdf",
                        help="PDF 输出路径 (默认 evaluation_report.pdf)")
    parser.add_argument("--output-json", "-j", default=None,
                        help="(可选) 同时输出 JSON 结构化报告路径")
    return parser.parse_args()


def _report_to_dict(report) -> dict:
    """Mirror of skill_training_evaluation/main.py::report_to_dict."""
    return {
        "task_id": report.task_id,
        "total_score": report.total_score,
        "final_level": report.final_level.value if hasattr(report.final_level, "value") else str(report.final_level),
        "dimensions": [
            {
                "dimension": dim.dimension,
                "score": dim.score,
                "full_score": dim.full_score,
                "weight": dim.weight,
                "level": dim.level,
                "analysis": dim.analysis,
                "sub_scores": [
                    {
                        "sub_dimension": sub.sub_dimension,
                        "score": sub.score,
                        "full_score": sub.full_score,
                        "rating": sub.rating,
                        "score_range": sub.score_range,
                        "judgment_basis": sub.judgment_basis,
                        "issues": [
                            {
                                "description": issue.description,
                                "location": issue.location,
                                "quote": issue.quote,
                                "severity": issue.severity,
                                "impact": issue.impact,
                            }
                            for issue in sub.issues
                        ],
                        "highlights": [
                            {
                                "description": h.description,
                                "location": h.location,
                                "quote": h.quote,
                                "impact": h.impact,
                            }
                            for h in sub.highlights
                        ],
                    }
                    for sub in dim.sub_scores
                ],
                "is_veto": dim.is_veto,
                "weighted_score": dim.weighted_score,
            }
            for dim in report.dimensions
        ],
        "analysis": report.analysis,
        "issues": report.issues,
        "suggestions": report.suggestions,
        "pass_criteria_met": report.pass_criteria_met,
        "veto_reasons": report.veto_reasons,
        "evaluated_at": datetime.now().isoformat(),
    }


async def _run(args: argparse.Namespace) -> int:
    _load_env()
    _ensure_prompts_json()

    # Validate env
    api_key = os.getenv("LLM_API_KEY", "").strip()
    api_url = os.getenv("LLM_API_URL", "").strip()
    model = os.getenv("LLM_MODEL", "Doubao-1.5-pro-32k").strip()
    service_code = os.getenv("LLM_SERVICE_CODE", "SI_Ability").strip() or None

    if not api_key:
        raise SystemExit("❌ 未配置 LLM_API_KEY; 请在 .env 或环境变量中设置")
    if not api_url:
        raise SystemExit("❌ 未配置 LLM_API_URL; 请在 .env 或环境变量中设置")

    print("=" * 70)
    print("🚀 智能体配置评估")
    print("=" * 70)
    print(f"🔧 Model:   {model}")
    print(f"🔧 API URL: {api_url}")
    print(f"🔧 Service: {service_code or '(未设置)'}")
    print(f"📝 Teacher: {args.teacher_doc}")
    print(f"💬 Dialogue: {args.dialogue}")
    if args.workflow_config:
        print(f"🔄 Workflow: {args.workflow_config}")
    print("=" * 70)

    # Lazy imports so sys.path tweak above is applied first.
    from file_parsers import parse_input_files  # type: ignore  # noqa: E402
    from evaluator import evaluate  # type: ignore  # noqa: E402
    from pdf_report import generate_pdf  # type: ignore  # noqa: E402

    teacher_doc, dialogue_data, workflow_config = parse_input_files(
        args.teacher_doc, args.dialogue, args.workflow_config
    )

    report = await evaluate(
        teacher_doc=teacher_doc,
        dialogue_data=dialogue_data,
        api_key=api_key,
        base_url=api_url,
        model=model,
        workflow_config=workflow_config,
        prompts_path=str(PROMPTS_JSON_PATH),
        service_code=service_code,
    )

    # Render PDF
    output_pdf = Path(args.output_pdf).resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    generate_pdf(
        report=report,
        output_path=str(output_pdf),
        model_name=model,
        dialogue_file=args.dialogue,
    )

    # Optional JSON
    if args.output_json:
        output_json = Path(args.output_json).resolve()
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with output_json.open("w", encoding="utf-8") as f:
            json.dump(_report_to_dict(report), f, ensure_ascii=False, indent=2)
        print(f"📄 JSON  → {output_json}")

    level = report.final_level.value if hasattr(report.final_level, "value") else str(report.final_level)
    print("=" * 70)
    print(f"✅ 总分 {report.total_score:.1f}/100 · 等级 {level} · PDF → {output_pdf}")
    print("=" * 70)
    return 0


def main() -> int:
    args = _parse_args()
    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        print("\n已取消", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
