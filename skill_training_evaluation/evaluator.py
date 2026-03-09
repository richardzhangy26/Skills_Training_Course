"""
LLM 评测核心逻辑 - 简化版
"""

from typing import List, Dict, Optional
from types_def import (
    DimensionScore,
    EvaluationLevel,
    EvaluationReport,
    DialogueData,
    SubDimensionScore,
)
from config import get_dimensions_config, load_prompts
from utils import format_dialogue_for_llm, parse_llm_response, call_llm


async def evaluate_dimension(
    dimension_name: str,
    config,
    teacher_doc: str,
    dialogue_text: str,
    workflow_config: Optional[str],
    prompts: Dict[str, Dict[str, str]],
    api_key: str,
    base_url: str,
    model: str,
) -> DimensionScore:
    """评测单个维度"""
    print(f"\n正在评测: {dimension_name}...")

    sub_dimension_scores: List[SubDimensionScore] = []
    dimension_prompts = prompts.get(dimension_name, {})
    workflow_text = workflow_config or ""

    for sub_dim in config.sub_dimensions:
        print(f"  - 子维度: {sub_dim.name}...")

        prompt_template = dimension_prompts.get(sub_dim.name)
        if not prompt_template:
            print(f"    未找到 prompt: {sub_dim.name}")
            continue

        prompt = (
            prompt_template.replace("${teacherDoc}", teacher_doc)
            .replace("${dialogueText}", dialogue_text)
        )
        if "${workflowConfig}" in prompt_template:
            prompt = prompt.replace("${workflowConfig}", workflow_text)
        elif workflow_text:
            prompt = f"{prompt}\n\n## 工作流配置\n{workflow_text}"

        try:
            llm_response = await call_llm(
                prompt=prompt, api_key=api_key, base_url=base_url, model=model
            )
            result = parse_llm_response(llm_response)

            sub_dimension_scores.append(
                SubDimensionScore(
                    sub_dimension=result["sub_dimension"],
                    score=int(result["score"]),
                    full_score=int(result["full_score"]),
                    rating=result.get("rating", "未知"),
                    score_range=result.get("score_range", ""),
                    judgment_basis=result.get("judgment_basis", ""),
                    issues=result.get("issues", []),
                    highlights=result.get("highlights", []),
                )
            )
        except Exception as error:
            print(f"    评测失败: {sub_dim.name} - {error}")
            sub_dimension_scores.append(
                SubDimensionScore(
                    sub_dimension=sub_dim.name,
                    score=0,
                    full_score=sub_dim.full_score,
                    rating="评估失败",
                    judgment_basis=f"系统错误: {error}",
                )
            )

    total_score = sum(s.score for s in sub_dimension_scores)

    # 确定评级
    ratio = total_score / config.full_score if config.full_score > 0 else 0
    if ratio >= 0.9:
        level = "优秀"
    elif ratio >= 0.75:
        level = "良好"
    elif ratio >= 0.6:
        level = "合格"
    else:
        level = "不合格"

    # 汇总分析
    analysis = "\n\n".join(
        f"【{s.sub_dimension}】({s.score}/{s.full_score}分): {s.judgment_basis}"
        for s in sub_dimension_scores
    )

    # 检查是否触发一票否决
    is_veto = (
        config.is_veto
        and config.veto_threshold is not None
        and total_score < config.veto_threshold
    )

    score = DimensionScore(
        dimension=dimension_name,
        score=total_score,
        full_score=config.full_score,
        weight=config.weight,
        level=level,
        analysis=analysis,
        sub_scores=sub_dimension_scores,
        is_veto=is_veto,
        weighted_score=total_score,
    )

    print(f"  {dimension_name}: {score.score:.1f}分 - {score.level}")
    return score


async def evaluate(
    teacher_doc: str,
    dialogue_data: DialogueData,
    api_key: str,
    base_url: str,
    model: str,
    workflow_config: Optional[str] = None,
    prompts_path: Optional[str] = None,
) -> EvaluationReport:
    """执行完整评测"""
    print("\n" + "=" * 70)
    print("开始 LLM 驱动的智能体评测")
    print("=" * 70)

    prompts = load_prompts(prompts_path)
    dimensions_config = get_dimensions_config(prompts_path)
    dialogue_text = format_dialogue_for_llm(dialogue_data)

    dimension_scores: List[DimensionScore] = []
    veto_reasons: List[str] = []

    for dim_name, config in dimensions_config.items():
        score = await evaluate_dimension(
            dimension_name=dim_name,
            config=config,
            teacher_doc=teacher_doc,
            dialogue_text=dialogue_text,
            workflow_config=workflow_config,
            prompts=prompts,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

        dimension_scores.append(score)

        if score.is_veto:
            veto_reasons.append(
                f"{score.dimension}得分{score.score:.1f}分，低于{config.veto_threshold}分阈值"
            )

    # 计算总分和最终等级
    total_score = sum(dim.weighted_score for dim in dimension_scores)

    if veto_reasons:
        final_level = EvaluationLevel.VETO
        pass_criteria_met = False
    elif total_score >= 90:
        final_level = EvaluationLevel.EXCELLENT
        pass_criteria_met = True
    elif total_score >= 75:
        final_level = EvaluationLevel.GOOD
        pass_criteria_met = True
    elif total_score >= 60:
        final_level = EvaluationLevel.PASS
        pass_criteria_met = True
    else:
        final_level = EvaluationLevel.FAIL
        pass_criteria_met = False

    # 提取关键问题和建议
    issues = []
    suggestions = []
    for dim in dimension_scores:
        for sub in dim.sub_scores:
            if sub.score < sub.full_score * 0.6:
                issue = sub.issues[0].description if sub.issues else sub.judgment_basis
                issues.append(f"【{dim.dimension}-{sub.sub_dimension}】{issue}")
            if sub.rating in ["不足", "较差"]:
                suggestions.append(
                    f"【{dim.dimension}-{sub.sub_dimension}】建议优化: {sub.judgment_basis[:50]}..."
                )

    # 生成摘要
    analysis_lines = [
        f"## 评测结论: {final_level.value} ({total_score:.1f}/100)",
        "",
        "### 各维度得分",
    ]
    for dim in dimension_scores:
        ratio = dim.score / dim.full_score if dim.full_score > 0 else 0
        status = "PASS" if ratio >= 0.6 else "FAIL"
        analysis_lines.append(f"[{status}] **{dim.dimension}**: {dim.score:.1f}/{dim.full_score}")

    report = EvaluationReport(
        task_id=dialogue_data.metadata.task_id,
        total_score=total_score,
        final_level=final_level,
        dimensions=dimension_scores,
        analysis="\n".join(analysis_lines),
        issues=issues,
        suggestions=suggestions,
        pass_criteria_met=pass_criteria_met,
        veto_reasons=veto_reasons,
    )

    print("\n" + "=" * 70)
    print(f"评测完成! 总分: {total_score:.1f} - {final_level.value}")
    print("=" * 70)

    return report
