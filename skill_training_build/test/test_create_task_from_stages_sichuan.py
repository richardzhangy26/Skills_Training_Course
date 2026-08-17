from pathlib import Path

import pytest

from skill_training_build.create_task_from_stages_sichuan import (
    COURSE_DIR,
    RELATION_GRAPH_PATH,
    START_FLOW_IS_DEFAULT,
    STAGES_DIR,
    UNIFIED_BACKGROUND_IMAGE,
    UNIFIED_INTERACTIVE_ROUNDS,
    Defaults,
    FlowSpec,
    StageSpec,
    assign_default_flags,
    build_flow_payload,
    build_prompt_edges,
    build_step_payload,
    extract_jump_commands,
    get_or_upload_cover,
    parse_mermaid_relationships,
    parse_stage_markdown_file,
    parse_stages_directory,
    validate_jump_edges,
)


def test_parse_stage_markdown_file_supports_current_format() -> None:
    stage_file = STAGES_DIR / "stage1_START.md"
    stage = parse_stage_markdown_file(stage_file)

    assert stage.stage_no == 1
    assert stage.code == "START"
    assert "开场" in stage.step_name
    assert stage.prologue
    assert stage.llm_prompt
    assert "NEXT_TO_DESIGN_REQUIREMENTS" in stage.jump_commands
    assert "TASK_COMPLETE" in stage.jump_commands


def test_extract_jump_commands_deduplicates_and_preserves_order() -> None:
    text = """
    请输出 NEXT_TO_A
    然后 NEXT_TO_B
    重复 NEXT_TO_A
    最后 TASK_COMPLETE
    """
    commands = extract_jump_commands(text)
    assert commands == ["NEXT_TO_A", "NEXT_TO_B", "TASK_COMPLETE"]


def test_parse_mermaid_relationships_contains_expected_edges() -> None:
    _, edges = parse_mermaid_relationships(RELATION_GRAPH_PATH)
    assert ("START", "DESIGN_REQUIREMENTS") in edges
    assert ("START", "LAYOUT_REQUIREMENTS") in edges
    assert ("START", "EDA_REQUIREMENTS") in edges
    assert ("START", "TASK_COMPLETE") in edges


def test_dual_source_edges_validation_passes_for_current_course() -> None:
    stages = parse_stages_directory(STAGES_DIR)
    _, graph_edges = parse_mermaid_relationships(RELATION_GRAPH_PATH)
    prompt_edges = build_prompt_edges(stages)

    # 不抛异常即通过
    validate_jump_edges(prompt_edges, graph_edges)


def test_build_step_payload_forces_unified_rounds_and_cover() -> None:
    stage = StageSpec(
        stage_no=99,
        code="DUMMY",
        step_name="测试阶段",
        description="描述",
        prologue="开场白",
        llm_prompt="提示词",
        transition_prompt="过渡",
        flow_condition="条件",
        trainer_name="",
        model_id="",
        agent_id="",
        avatar_nid="",
        source_rounds=3,
        jump_commands=["TASK_COMPLETE"],
        source_path=Path("dummy.md"),
    )
    defaults = Defaults(
        model_id="MODEL_DEFAULT",
        agent_id="AGENT_DEFAULT",
        trainer_name="TRAINER_DEFAULT",
        avatar_nid="AVATAR_DEFAULT",
    )
    cover = {"fileId": "f1", "fileUrl": "https://example.com/x.png"}
    payload = build_step_payload(
        train_task_id="task123",
        step_id="step123",
        stage=stage,
        position={"x": 1, "y": 2},
        defaults=defaults,
        script_step_cover=cover,
    )

    assert payload["stepDetailDTO"]["interactiveRounds"] == UNIFIED_INTERACTIVE_ROUNDS
    assert payload["stepDetailDTO"]["scriptStepCover"] == cover
    assert payload["stepDetailDTO"]["modelId"] == "MODEL_DEFAULT"
    assert payload["stepDetailDTO"]["agentId"] == "AGENT_DEFAULT"
    assert payload["stepDetailDTO"]["trainerName"] == "TRAINER_DEFAULT"


def test_unified_background_image_exists() -> None:
    assert UNIFIED_BACKGROUND_IMAGE.exists(), str(UNIFIED_BACKGROUND_IMAGE)
    assert COURSE_DIR.exists(), str(COURSE_DIR)


def test_get_or_upload_cover_uses_cache(tmp_path: Path) -> None:
    image_path = tmp_path / "bg.png"
    image_path.write_bytes(b"fake")
    upload_count = {"count": 0}

    def fake_uploader(path: Path):
        upload_count["count"] += 1
        return {"fileId": f"id-{path.name}", "fileUrl": "https://example.com/bg.png"}

    cache = {}
    first = get_or_upload_cover(image_path, cache, fake_uploader)
    second = get_or_upload_cover(image_path, cache, fake_uploader)

    assert first == second
    assert upload_count["count"] == 1


def test_assign_default_flags_sets_first_outgoing_as_default() -> None:
    flow_specs = [
        FlowSpec(source_code="START", condition="NEXT_TO_A", target_code="A"),
        FlowSpec(source_code="START", condition="NEXT_TO_B", target_code="B"),
        FlowSpec(source_code="A", condition="NEXT_TO_C", target_code="C"),
        FlowSpec(source_code="A", condition="TASK_COMPLETE", target_code="TASK_COMPLETE"),
        FlowSpec(source_code="B", condition="TASK_COMPLETE", target_code="TASK_COMPLETE"),
    ]
    assigned = assign_default_flags(flow_specs)
    defaults = [flag for _, flag in assigned]
    assert defaults == [1, 0, 1, 0, 1]


def test_start_flow_default_is_zero() -> None:
    assert START_FLOW_IS_DEFAULT == 0


def test_build_flow_payload_writes_is_default_correctly() -> None:
    payload_default = build_flow_payload(
        train_task_id="task1",
        flow_id="flow1",
        start_id="s1",
        end_id="e1",
        condition_text="NEXT_TO_A",
        transition_prompt="tp",
        is_default=1,
    )
    payload_not_default = build_flow_payload(
        train_task_id="task1",
        flow_id="flow2",
        start_id="s1",
        end_id="e2",
        condition_text="NEXT_TO_B",
        transition_prompt="tp",
        is_default=0,
    )

    assert payload_default["isDefault"] == 1
    assert payload_not_default["isDefault"] == 0

    with pytest.raises(ValueError):
        build_flow_payload(
            train_task_id="task1",
            flow_id="flow3",
            start_id="s1",
            end_id="e3",
            condition_text="NEXT_TO_C",
            transition_prompt="tp",
            is_default=2,
        )
