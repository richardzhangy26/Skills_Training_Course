"""
命令行接口
"""

import sys
import asyncio
import argparse
from pathlib import Path

from . import parsers, evaluator, config
from .utils import save_json_report, format_score_report, find_dialogue_files


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="evaluation",
        description="AI对话式教学训练质量评测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 单文件评测
  python -m evaluation --teacher-doc 教学设计.docx --dialogue dialogue.json --output report.json

  # 批量评测
  python -m evaluation --teacher-doc 教学设计.docx --dialogue-dir ./logs/ --output-dir ./reports/

  # 显示详细输出
  python -m evaluation -t 教学设计.docx -d dialogue.json -v

环境变量配置 (.env):
  EVAL_API_KEY=your-api-key        # API密钥
  EVAL_API_URL=https://...         # API地址（可选）
  EVAL_MODEL=doubao-1.5-pro-32k    # 模型名称（可选）
        """,
    )

    # 必需参数
    parser.add_argument(
        "-t", "--teacher-doc",
        required=True,
        help="教师文档路径（支持.docx/.md/.txt）",
    )

    # 单文件模式
    parser.add_argument(
        "-d", "--dialogue",
        help="单个对话日志文件路径（支持.json/.txt）",
    )

    # 批量模式
    parser.add_argument(
        "-D", "--dialogue-dir",
        help="对话日志目录路径（批量评测模式）",
    )

    # 输出参数
    parser.add_argument(
        "-o", "--output",
        help="单个评测报告输出路径",
    )
    parser.add_argument(
        "-O", "--output-dir",
        help="批量评测报告输出目录",
    )

    # 并发控制
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=3,
        help="批量评测时的并发数（默认: 3）",
    )

    # 其他选项
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="输出格式（默认: text）",
    )

    return parser


async def evaluate_single(args, cfg) -> int:
    """单文件评测"""
    print(f"📝 加载教师文档: {args.teacher_doc}")
    teacher_doc = parsers.parse_teacher_doc(args.teacher_doc)

    print(f"💬 加载对话日志: {args.dialogue}")
    dialogue_data = parsers.parse_dialogue(args.dialogue)

    print("🔍 开始评测...")
    report = await evaluator.evaluate(teacher_doc, dialogue_data, cfg, args.dialogue)

    # 显示结果
    if args.verbose or args.format == "text":
        print("\n" + format_score_report(report))

    # 保存报告
    if args.output:
        save_json_report(report, args.output)
        print(f"\n✅ 报告已保存: {args.output}")

    return 0


async def evaluate_batch(args, cfg) -> int:
    """批量评测"""
    print(f"📝 加载教师文档: {args.teacher_doc}")
    teacher_doc = parsers.parse_teacher_doc(args.teacher_doc)

    # 查找对话文件
    dialogue_files = find_dialogue_files(args.dialogue_dir)
    if not dialogue_files:
        print(f"❌ 未找到对话文件: {args.dialogue_dir}")
        return 1

    print(f"📁 找到 {len(dialogue_files)} 个对话文件")
    print(f"🔄 使用 {args.workers} 个并发线程进行评测...\n")

    # 执行批量评测
    batch_report = await evaluator.evaluate_batch(
        teacher_doc, dialogue_files, cfg, args.workers
    )

    # 显示汇总
    summary = batch_report["batch_summary"]
    print("\n" + "=" * 50)
    print("📊 批量评测汇总")
    print("=" * 50)
    print(f"总文件数: {summary['total_files']}")
    print(f"成功: {summary['success_count']}")
    print(f"失败: {summary['failed_count']}")
    print(f"平均分: {summary['avg_score']}")
    print("-" * 50)
    print("等级分布:")
    for level, count in summary['score_distribution'].items():
        print(f"  {level}: {count}个")
    print("=" * 50)

    # 保存报告
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存汇总报告
        summary_path = output_dir / "batch_summary.json"
        save_json_report(batch_report, summary_path)
        print(f"\n✅ 汇总报告已保存: {summary_path}")

        # 保存单个报告
        for i, individual in enumerate(batch_report["individual_reports"]):
            dialogue_file = dialogue_files[i]
            file_name = Path(dialogue_file).stem
            report_path = output_dir / f"{file_name}_report.json"
            save_json_report(individual, report_path)

        print(f"✅ 单个报告已保存到: {output_dir}")

    return 0


def main() -> int:
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()

    # 验证参数
    if not args.dialogue and not args.dialogue_dir:
        parser.error("必须指定 --dialogue 或 --dialogue-dir 参数")

    # 加载配置
    try:
        cfg = config.load_config()
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("请确保设置了 EVAL_API_KEY 环境变量或 .env 文件")
        return 1

    # 执行评测
    try:
        if args.dialogue:
            # 单文件模式
            return asyncio.run(evaluate_single(args, cfg))
        else:
            # 批量模式
            return asyncio.run(evaluate_batch(args, cfg))
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        return 1
    except Exception as e:
        print(f"❌ 评测失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
