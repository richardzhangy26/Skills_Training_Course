"""
智能体评估主脚本 - 简化版
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluator import evaluate
from file_parsers import parse_input_files
from types_def import EvaluationReport


def load_env() -> dict:
    """从环境变量加载配置"""
    if load_dotenv:
        env_paths = [
            Path(__file__).parent / ".env",
            Path(__file__).parent.parent / ".env",
            Path.cwd() / ".env",
        ]
        for path in env_paths:
            if path.exists():
                load_dotenv(path)
                print(f"已加载配置: {path}")
                break

    return {
        "api_key": os.getenv("LLM_API_KEY", ""),
        "api_url": os.getenv("LLM_API_URL", ""),
        "model": os.getenv("LLM_MODEL", "gpt-4o"),
    }


def get_file_path(prompt: str) -> str:
    """交互式输入文件路径"""
    while True:
        file_path = input(prompt).strip()
        if not file_path:
            print("错误: 文件路径不能为空")
            continue
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在: {file_path}")
            continue
        return file_path


def report_to_dict(report: EvaluationReport) -> dict:
    """将报告转换为字典"""
    return {
        "task_id": report.task_id,
        "total_score": report.total_score,
        "final_level": report.final_level.value,
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


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能体评估工具")
    parser.add_argument("--teacher-doc", help="教师文档文件路径")
    parser.add_argument("--dialogue-record", help="对话记录文件路径")
    parser.add_argument("--workflow-config", help="工作流配置文件路径(.md/.docx)")
    parser.add_argument("--api-key", help="LLM API 密钥")
    parser.add_argument("--api-url", help="LLM API 地址")
    parser.add_argument("--model", help="LLM 模型名称")
    parser.add_argument("--output", default="evaluation_report.json", help="输出报告路径")
    parser.add_argument("--prompts", default="prompts.json", help="提示词文件路径")

    args = parser.parse_args()
    env_config = load_env()

    # 合并配置
    api_key = args.api_key or env_config["api_key"]
    api_url = args.api_url or env_config["api_url"]
    model = args.model or env_config["model"]

    # 交互式输入
    if not args.teacher_doc:
        print("\n请输入教师文档文件路径:")
        args.teacher_doc = get_file_path("> ")

    if not args.dialogue_record:
        print("\n请输入对话记录文件路径:")
        args.dialogue_record = get_file_path("> ")

    # 验证配置
    if not api_key:
        print("错误: 未配置 LLM API 密钥")
        sys.exit(1)

    if not api_url:
        print("错误: 未配置 LLM API 地址")
        sys.exit(1)

    prompts_path = Path(__file__).parent / args.prompts
    if not prompts_path.exists():
        print(f"错误: 提示词文件不存在: {prompts_path}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("智能体评估工具")
    print("=" * 70)
    print(f"教师文档: {args.teacher_doc}")
    print(f"对话记录: {args.dialogue_record}")
    print(f"模型: {model}")
    print("=" * 70 + "\n")

    try:
        teacher_doc, dialogue_data, workflow_config = parse_input_files(
            args.teacher_doc, args.dialogue_record, args.workflow_config
        )

        report = await evaluate(
            teacher_doc=teacher_doc,
            dialogue_data=dialogue_data,
            api_key=api_key,
            base_url=api_url,
            model=model,
            workflow_config=workflow_config,
            prompts_path=str(prompts_path),
        )

        output_data = report_to_dict(report)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n评估报告已保存: {args.output}")
        print(f"总分: {report.total_score:.1f} / 100")
        print(f"等级: {report.final_level.value}")
        print(f"通过: {'是' if report.pass_criteria_met else '否'}")

        if report.veto_reasons:
            print("\n一票否决原因:")
            for reason in report.veto_reasons:
                print(f"  - {reason}")

    except Exception as error:
        print(f"\n错误: {error}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
