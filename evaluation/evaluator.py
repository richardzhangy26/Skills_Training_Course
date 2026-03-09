"""
核心评测协调器
"""

from typing import Optional

from .types import (
    TeacherDocument,
    DialogueData,
    EvaluationReport,
    DimensionScore,
    EvaluatorConfig,
)
from . import rules_evaluator
from . import llm_evaluator


async def evaluate(
    teacher_doc: TeacherDocument,
    dialogue_data: DialogueData,
    config: EvaluatorConfig,
    dialogue_file: Optional[str] = None,
) -> EvaluationReport:
    """
    执行完整评测

    Args:
        teacher_doc: 教师文档
        dialogue_data: 对话数据
        config: 评测配置
        dialogue_file: 对话文件路径（用于报告记录）

    Returns:
        EvaluationReport: 评测报告
    """
    # 1. 规则评测（目标达成度、流程遵循度）
    rule_scores = rules_evaluator.evaluate(teacher_doc, dialogue_data)

    # 2. LLM评测（交互体验性、幻觉与边界、教学策略）
    llm_scores = await llm_evaluator.evaluate(teacher_doc, dialogue_data, config)

    # 3. 合并所有维度得分
    all_dimensions = []
    all_dimensions.extend(rule_scores.values())
    all_dimensions.extend(llm_scores.values())

    # 4. 计算总分
    total_score = sum(dim.score for dim in all_dimensions)

    # 5. 确定等级
    level = _determine_level(total_score)

    # 6. 生成总结
    all_scores = {**rule_scores, **llm_scores}
    summary = await llm_evaluator.generate_summary(all_scores, config)

    # 7. 获取任务ID
    task_id = dialogue_data.metadata.task_id or "unknown"

    return EvaluationReport(
        task_id=task_id,
        total_score=round(total_score, 1),
        level=level,
        dimensions=all_dimensions,
        summary=summary,
        dialogue_file=dialogue_file,
    )


def evaluate_sync(
    teacher_doc: TeacherDocument,
    dialogue_data: DialogueData,
    config: EvaluatorConfig,
    dialogue_file: Optional[str] = None,
) -> EvaluationReport:
    """
    同步执行完整评测（供非异步环境使用）

    Args:
        teacher_doc: 教师文档
        dialogue_data: 对话数据
        config: 评测配置
        dialogue_file: 对话文件路径（用于报告记录）

    Returns:
        EvaluationReport: 评测报告
    """
    import asyncio
    return asyncio.run(evaluate(teacher_doc, dialogue_data, config, dialogue_file))


def _determine_level(total_score: float) -> str:
    """
    根据总分确定等级

    评分标准：
    - 优秀：90分及以上
    - 良好：80-89分
    - 合格：60-79分
    - 不合格：60分以下
    """
    if total_score >= 90:
        return "优秀"
    elif total_score >= 80:
        return "良好"
    elif total_score >= 60:
        return "合格"
    else:
        return "不合格"


async def evaluate_batch(
    teacher_doc: TeacherDocument,
    dialogue_files: list,
    config: EvaluatorConfig,
    max_concurrent: int = 3,
) -> dict:
    """
    批量评测多个对话文件

    Args:
        teacher_doc: 教师文档
        dialogue_files: 对话文件路径列表
        config: 评测配置
        max_concurrent: 最大并发数

    Returns:
        dict: 批量评测报告
    """
    import asyncio
    from .parsers import parse_dialogue

    semaphore = asyncio.Semaphore(max_concurrent)

    async def evaluate_one(file_path: str) -> Optional[EvaluationReport]:
        async with semaphore:
            try:
                dialogue_data = parse_dialogue(file_path)
                return await evaluate(teacher_doc, dialogue_data, config, file_path)
            except Exception as e:
                print(f"评测失败 {file_path}: {e}")
                return None

    tasks = [evaluate_one(f) for f in dialogue_files]
    results = await asyncio.gather(*tasks)

    # 过滤掉失败的
    reports = [r for r in results if r is not None]

    # 计算统计信息
    if not reports:
        return {
            "batch_summary": {
                "total_files": len(dialogue_files),
                "success_count": 0,
                "failed_count": len(dialogue_files),
                "avg_score": 0,
                "score_distribution": {"优秀": 0, "良好": 0, "合格": 0, "不合格": 0},
            },
            "individual_reports": [],
        }

    scores = [r.total_score for r in reports]
    avg_score = sum(scores) / len(scores)

    distribution = {"优秀": 0, "良好": 0, "合格": 0, "不合格": 0}
    for r in reports:
        distribution[r.level] = distribution.get(r.level, 0) + 1

    return {
        "batch_summary": {
            "total_files": len(dialogue_files),
            "success_count": len(reports),
            "failed_count": len(dialogue_files) - len(reports),
            "avg_score": round(avg_score, 2),
            "score_distribution": distribution,
        },
        "individual_reports": [r.model_dump() for r in reports],
    }
