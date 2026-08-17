import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from skill_training_build import update_remote_sensing_tasks as updater
from skill_training_build.create_task_from_markdown import parse_markdown


def make_step(step_id, name, node_type="SCRIPT_NODE", resources=None):
    return {
        "trainTaskId": "task-1",
        "stepId": step_id,
        "positionDTO": {"x": "100", "y": "100"},
        "stepDetailDTO": {
            "nodeType": node_type,
            "stepName": name,
            "description": f"{name}描述",
            "prologue": f"{name}开场",
            "llmPrompt": f"{name}提示词",
            "interactiveRounds": 3,
            "trainerName": "旧角色",
            "modelId": "Doubao-Seed-1.6",
            "agentId": "old-voice",
            "agentVoiceId": "old-param",
            "avatarNid": "old-avatar",
            "customDigitalHuman": "old-human",
            "scriptStepCover": {"fileId": f"cover-{step_id}"},
            "scriptStepResourceList": resources or [],
            "knowledgeBaseSwitch": 1,
            "knowledgeBaseId": "kb-1",
            "searchEngineSwitch": 1,
            "isSkipStep": "1",
        },
    }


def make_flow(flow_id, start_id, end_id, condition):
    return {
        "trainTaskId": "task-1",
        "flowId": flow_id,
        "scriptStepStartId": start_id,
        "scriptStepEndId": end_id,
        "flowCondition": condition,
        "flowConfiguration": {
            "relation": "and",
            "conditions": [
                {
                    "text": "条件组1",
                    "relation": "and",
                    "conditions": [{"text": condition}],
                }
            ],
        },
        "transitionPrompt": "旧转场",
        "transitionHistoryNum": 0,
    }


def make_markdown_step(index, name, condition):
    return {
        "stepName": name,
        "description": f"{name}新描述",
        "prologue": f"{name}新开场",
        "llmPrompt": f"{name}新提示词",
        "interactiveRounds": index + 2,
        "flowCondition": condition,
        "transitionPrompt": f"{name}转场",
    }


def make_rubric_items():
    return [
        {
            "itemName": "一、指标理解",
            "score": 3,
            "description": "指标描述",
            "requireDetail": "指标要求",
        },
        {
            "itemName": "二、数据选择",
            "score": 3,
            "description": "数据描述",
            "requireDetail": "数据要求",
        },
        {
            "itemName": "三、证据解释",
            "score": 2,
            "description": "证据描述",
            "requireDetail": "证据要求",
        },
        {
            "itemName": "四、综合反思",
            "score": 2,
            "description": "反思描述",
            "requireDetail": "反思要求",
        },
    ]


def make_score_items():
    return [
        {
            "trainTaskId": "task-1",
            "itemId": f"score-{index}",
            "itemName": f"旧评分{index}",
            "score": 1,
            "description": "旧描述",
            "requireDetail": "旧要求",
        }
        for index in range(1, 5)
    ]


def test_linearize_snapshot_follows_flow_topology_not_api_order():
    start = make_step("start", "START", "SCRIPT_START")
    one = make_step("one", "阶段一")
    two = make_step("two", "阶段二")
    end = make_step("end", "END", "SCRIPT_END")
    steps = [two, end, start, one]
    flows = [
        make_flow("f2", "one", "two", "进入阶段二"),
        make_flow("f3", "two", "end", "训练完成"),
        make_flow("f1", "start", "one", ""),
    ]

    chain = updater.linearize_snapshot({"steps": steps, "flows": flows})

    assert chain.start["stepId"] == "start"
    assert [step["stepId"] for step in chain.business_steps] == ["one", "two"]
    assert chain.end["stepId"] == "end"
    assert [flow["flowId"] for flow in chain.flows] == ["f1", "f2", "f3"]


def test_linearize_snapshot_rejects_branching_graph():
    steps = [
        make_step("start", "START", "SCRIPT_START"),
        make_step("one", "阶段一"),
        make_step("two", "阶段二"),
        make_step("end", "END", "SCRIPT_END"),
    ]
    flows = [
        make_flow("f1", "start", "one", ""),
        make_flow("f2", "one", "two", "进入阶段二"),
        make_flow("f3", "one", "end", "训练完成"),
    ]

    with pytest.raises(updater.PreflightError, match="线性"):
        updater.linearize_snapshot({"steps": steps, "flows": flows})


def test_build_step_payload_updates_content_and_preserves_platform_metadata():
    existing = make_step(
        "one",
        "旧阶段",
        resources=[
            {
                "fileId": "file-1",
                "fileName": "旧证据图.png",
                "sort": 2,
                "isRequired": 0,
            },
            {
                "fileId": None,
                "fileName": None,
                "resourceTypeNid": "blank-type",
            },
            {
                "fileId": "file-2",
                "fileName": "补充图.png",
                "sort": 1,
                "isRequired": 0,
            },
        ],
    )
    original = copy.deepcopy(existing)
    markdown_step = {
        "stepName": "新阶段",
        "description": "新描述",
        "prologue": "新开场",
        "llmPrompt": "新提示词",
        "interactiveRounds": 6,
    }

    payload = updater.build_step_payload(
        existing,
        markdown_step,
        train_task_id="task-1",
        resource_renames={"旧证据图.png": "准确证据图.png"},
        required_resource_names={"准确证据图.png"},
        resource_priority=["准确证据图.png", "补充图.png"],
    )

    detail = payload["stepDetailDTO"]
    assert detail["stepName"] == "新阶段"
    assert detail["description"] == "新描述"
    assert detail["prologue"] == "新开场"
    assert detail["llmPrompt"] == "新提示词"
    assert detail["interactiveRounds"] == 6
    assert detail["trainerName"] == "星航"
    assert detail["agentId"] == "Tg9LpKo68D"
    assert detail["agentVoiceId"] == "zh_male_tiancaitongsheng_mars_bigtts"
    assert detail["avatarNid"] == "Pzd7n2rwRc"
    assert detail["customDigitalHuman"] == "qqg4vg3DwY"
    assert detail["isSkipStep"] == "0"
    assert detail["scriptStepCover"] == {"fileId": "cover-one"}
    assert detail["knowledgeBaseId"] == "kb-1"
    assert [item["fileName"] for item in detail["scriptStepResourceList"]] == [
        "准确证据图.png",
        "补充图.png",
    ]
    assert [item["sort"] for item in detail["scriptStepResourceList"]] == [1, 2]
    assert [item["isRequired"] for item in detail["scriptStepResourceList"]] == [
        1,
        0,
    ]
    assert all(
        "scriptStepResourceId" not in item
        for item in detail["scriptStepResourceList"]
    )
    ext_resources = detail["stepExtProperty"]["resources"]
    assert len(ext_resources) == 1
    assert ext_resources[0]["nid"] == "default"
    assert [
        item["fileName"] for item in ext_resources[0]["list"]
    ] == ["准确证据图.png", "补充图.png"]
    assert [
        item["isRequired"] for item in ext_resources[0]["list"]
    ] == [True, False]
    assert existing == original


def test_build_step_payload_can_keep_only_reviewed_resources_after_rename():
    existing = make_step(
        "one",
        "旧阶段",
        resources=[
            {
                "fileId": "file-1",
                "fileName": "误命名全景图.jpg",
                "sort": 1,
                "isRequired": 0,
            },
            {
                "fileId": "file-2",
                "fileName": "无关补充图.jpg",
                "sort": 2,
                "isRequired": 0,
            },
        ],
    )

    payload = updater.build_step_payload(
        existing,
        {"stepName": "新阶段"},
        train_task_id="task-1",
        resource_renames={"误命名全景图.jpg": "维纳姆湾局部图.jpg"},
        allowed_resource_names={"维纳姆湾局部图.jpg"},
    )

    assert [
        item["fileName"]
        for item in payload["stepDetailDTO"]["scriptStepResourceList"]
    ] == ["维纳姆湾局部图.jpg"]


def test_build_step_payload_adds_uploaded_resource_idempotently():
    existing = make_step(
        "one",
        "旧阶段",
        resources=[
            {
                "scriptStepResourceId": "row-1",
                "trainTaskId": "task-1",
                "scriptStepId": "one",
                "fileId": "file-speed",
                "fileName": "流速图.png",
                "sort": 1,
                "isRequired": 0,
            }
        ],
    )
    addition = {
        "fileId": "file-height",
        "fileName": "ICESat-2高程变化图.jpg",
        "fileUrl": "https://example.invalid/height.jpg",
        "contentType": "image/jpeg",
        "thumbnail": "https://example.invalid/height.jpg",
    }

    payload = updater.build_step_payload(
        existing,
        {"stepName": "多源监测"},
        train_task_id="task-1",
        allowed_resource_names={"流速图.png", "ICESat-2高程变化图.jpg"},
        required_resource_names={"流速图.png", "ICESat-2高程变化图.jpg"},
        resource_priority=["流速图.png", "ICESat-2高程变化图.jpg"],
        additional_resources=[addition, addition],
    )

    resources = payload["stepDetailDTO"]["scriptStepResourceList"]
    assert [item["fileId"] for item in resources] == [
        "file-speed",
        "file-height",
    ]
    assert "scriptStepResourceId" not in resources[1]
    assert resources[1]["trainTaskId"] == "task-1"
    assert resources[1]["scriptStepId"] == "one"
    assert resources[1]["isRequired"] == 1


def test_build_step_payload_can_replace_old_file_id_with_renamed_upload():
    existing = make_step(
        "one",
        "旧阶段",
        resources=[
            {
                "fileId": "old-file",
                "fileName": "误命名图.png",
                "sort": 1,
                "isRequired": 0,
            }
        ],
    )
    replacement = {
        "fileId": "new-file",
        "fileName": "准确命名图.png",
        "fileUrl": "https://example.invalid/new.png",
        "contentType": "image/png",
    }

    payload = updater.build_step_payload(
        existing,
        {"stepName": "新阶段"},
        train_task_id="task-1",
        excluded_file_ids={"old-file"},
        allowed_resource_names={"准确命名图.png"},
        required_resource_names={"准确命名图.png"},
        additional_resources=[replacement],
    )

    resources = payload["stepDetailDTO"]["scriptStepResourceList"]
    assert [(item["fileId"], item["fileName"]) for item in resources] == [
        ("new-file", "准确命名图.png")
    ]


def test_build_flow_payload_updates_top_and_nested_condition():
    flow = make_flow("f1", "one", "two", "旧条件")

    payload = updater.build_flow_payload(
        flow,
        train_task_id="task-1",
        condition="进入新阶段",
        transition_prompt="完成上一站，飞往下一站。",
    )

    assert payload["flowCondition"] == "进入新阶段"
    assert (
        payload["flowConfiguration"]["conditions"][0]["conditions"][0]["text"]
        == "进入新阶段"
    )
    assert payload["transitionPrompt"] == "完成上一站，飞往下一站。"
    assert payload["transitionHistoryNum"] == 10


def test_build_flow_payload_can_retarget_an_existing_edge():
    flow = make_flow("f1", "one", "two", "旧条件")

    payload = updater.build_flow_payload(
        flow,
        train_task_id="task-1",
        condition="进入插入阶段",
        transition_prompt="飞往新阶段。",
        start_id="one",
        end_id="inserted",
    )

    assert payload["scriptStepStartId"] == "one"
    assert payload["scriptStepStartHandle"] == "one-source-bottom"
    assert payload["scriptStepEndId"] == "inserted"
    assert payload["scriptStepEndHandle"] == "inserted-target-top"


def test_build_new_flow_payload_uses_quick_single_condition_shape():
    payload = updater.build_new_flow_payload(
        train_task_id="task-1",
        flow_id="new-flow",
        start_id="inserted",
        end_id="next",
        condition="进入多源融合阶段",
        transition_prompt="多源证据已经齐备，进入综合判断。",
    )

    assert payload["flowId"] == "new-flow"
    assert payload["scriptStepStartHandle"] == "inserted-source-bottom"
    assert payload["scriptStepEndHandle"] == "next-target-top"
    assert payload["flowCondition"] == "进入多源融合阶段"
    assert (
        payload["flowConfiguration"]["conditions"][0]["conditions"][0]["text"]
        == "进入多源融合阶段"
    )
    assert payload["isDefault"] == 1
    assert payload["flowSettingType"] == "quick"
    assert payload["transitionHistoryNum"] == 10


def test_build_inserted_step_payload_clones_background_but_renews_resources():
    template = make_step(
        "norway",
        "旧挪威阶段",
        resources=[
            {
                "scriptStepResourceId": "resource-row-1",
                "trainTaskId": "task-1",
                "scriptStepId": "norway",
                "fileId": "file-1",
                "fileName": "边界图.png",
                "sort": 1,
                "isRequired": 0,
            },
            {
                "scriptStepResourceId": "resource-row-2",
                "trainTaskId": "task-1",
                "scriptStepId": "norway",
                "fileId": "file-2",
                "fileName": "流速图.png",
                "sort": 2,
                "isRequired": 0,
            },
        ],
    )
    markdown_step = {
        "stepName": "挪威多源冰川监测",
        "description": "监测速度与厚度",
        "prologue": "进入监测",
        "llmPrompt": "新提示词",
        "interactiveRounds": 5,
    }

    payload = updater.build_inserted_step_payload(
        template,
        markdown_step,
        train_task_id="task-1",
        new_step_id="new-step",
        position={"x": "1700", "y": "300"},
        allowed_resource_names={"流速图.png"},
        required_resource_names={"流速图.png"},
    )

    assert payload["stepId"] == "new-step"
    assert payload["positionDTO"] == {"x": "1700", "y": "300"}
    assert payload["stepDetailDTO"]["scriptStepCover"] == {
        "fileId": "cover-norway"
    }
    resources = payload["stepDetailDTO"]["scriptStepResourceList"]
    assert len(resources) == 1
    assert resources[0]["fileName"] == "流速图.png"
    assert "scriptStepResourceId" not in resources[0]
    assert resources[0]["trainTaskId"] == "task-1"
    assert resources[0]["scriptStepId"] == "new-step"
    assert resources[0]["isRequired"] == 1
    ext_item = payload["stepDetailDTO"]["stepExtProperty"]["resources"][0][
        "list"
    ][0]
    assert ext_item["scriptStepId"] == "new-step"
    assert ext_item["trainTaskId"] == "task-1"


def test_build_score_payload_preserves_item_id_and_uses_rubric_content():
    existing = {
        "trainTaskId": "task-1",
        "itemId": "score-1",
        "itemName": "旧评分",
        "score": 3,
        "description": "旧描述",
        "requireDetail": "旧要求",
    }
    rubric_item = {
        "itemName": "数据选择合理性",
        "score": 3,
        "description": "新描述",
        "requireDetail": "新要求",
    }

    payload = updater.build_score_payload(
        existing, rubric_item, train_task_id="task-1"
    )

    assert payload == {
        "trainTaskId": "task-1",
        "itemId": "score-1",
        "itemName": "数据选择合理性",
        "score": 3,
        "description": "新描述",
        "requireDetail": "新要求",
    }


def test_build_configuration_payload_preserves_content_and_unifies_entry_voice():
    existing = {
        "trainTaskId": "task-1",
        "trainTaskName": "原任务",
        "description": "原描述",
        "trainType": "text",
        "trainTaskCover": {"fileId": "cover-1"},
        "entranceVoiceNid": "old-entry-voice",
        "entranceVoiceSpeed": 0.0,
    }

    payload = updater.build_configuration_payload(
        existing, task_id="task-1", course_id="course-1"
    )

    assert payload["trainTaskName"] == "原任务"
    assert payload["description"] == "原描述"
    assert payload["trainTaskCover"] == {"fileId": "cover-1"}
    assert payload["entranceVoiceNid"] == "Tg9LpKo68D"
    assert payload["courseId"] == "course-1"


def test_write_backup_removes_credentials(tmp_path):
    snapshot = {
        "configuration": {"trainTaskId": "task-1"},
        "Authorization": "secret-auth",
        "nested": {"cookie": "secret-cookie", "value": "保留"},
    }

    target = updater.write_backup(snapshot, tmp_path, label="task-1")
    text = target.read_text(encoding="utf-8")
    saved = json.loads(text)

    assert "secret-auth" not in text
    assert "secret-cookie" not in text
    assert saved["nested"]["value"] == "保留"


def test_build_task_update_plan_updates_stage_exit_flows_not_start_edge():
    snapshot = {
        "configuration": {"trainTaskId": "task-1"},
        "steps": [
            make_step("start", "START", "SCRIPT_START"),
            make_step("one", "旧阶段一"),
            make_step("two", "旧阶段二"),
            make_step("end", "END", "SCRIPT_END"),
        ],
        "flows": [
            make_flow("f0", "start", "one", ""),
            make_flow("f1", "one", "two", "旧条件一"),
            make_flow("f2", "two", "end", "旧条件二"),
        ],
        "scoreItems": make_score_items(),
    }
    markdown_steps = [
        make_markdown_step(1, "阶段一", "进入阶段二阶段"),
        make_markdown_step(2, "阶段二", "训练完成"),
    ]

    plan = updater.build_task_update_plan(
        snapshot,
        markdown_steps,
        make_rubric_items(),
        task_id="task-1",
        course_id="course-1",
        stage_resource_specs=[{}, {}],
    )

    assert plan["inserted"] is False
    assert not [
        operation
        for operation in plan["operations"]
        if operation["kind"].startswith("create_")
    ]
    flow_operations = [
        operation
        for operation in plan["operations"]
        if operation["kind"] == "edit_flow"
    ]
    assert [operation["payload"]["flowId"] for operation in flow_operations] == [
        "f1",
        "f2",
    ]
    assert [
        operation["payload"]["flowCondition"]
        for operation in flow_operations
    ] == ["进入阶段二阶段", "训练完成"]
    assert len(
        [
            operation
            for operation in plan["operations"]
            if operation["kind"] == "edit_score"
        ]
    ) == 4
    assert plan["operations"][0]["kind"] == "edit_configuration"
    assert (
        plan["operations"][0]["payload"]["entranceVoiceNid"]
        == "Tg9LpKo68D"
    )


def test_build_task_update_plan_inserts_stage_and_retargets_last():
    combined_resources = [
        {
            "scriptStepResourceId": "resource-row-1",
            "trainTaskId": "task-1",
            "scriptStepId": "one",
            "fileId": "file-area",
            "fileName": "面积图.png",
            "sort": 1,
            "isRequired": 0,
        },
        {
            "scriptStepResourceId": "resource-row-2",
            "trainTaskId": "task-1",
            "scriptStepId": "one",
            "fileId": "file-speed",
            "fileName": "流速图.png",
            "sort": 2,
            "isRequired": 0,
        },
    ]
    snapshot = {
        "configuration": {"trainTaskId": "task-1"},
        "steps": [
            make_step("start", "START", "SCRIPT_START"),
            make_step("one", "旧冰川综合", resources=combined_resources),
            make_step("two", "旧总结"),
            make_step("end", "END", "SCRIPT_END"),
        ],
        "flows": [
            make_flow("f0", "start", "one", ""),
            make_flow("f1", "one", "two", "旧条件一"),
            make_flow("f2", "two", "end", "旧条件二"),
        ],
        "scoreItems": make_score_items(),
    }
    markdown_steps = [
        make_markdown_step(1, "冰川基础", "进入多源监测阶段"),
        make_markdown_step(2, "多源监测", "进入总结阶段"),
        make_markdown_step(3, "总结", "训练完成"),
    ]
    resource_specs = [
        {
            "allowed": ["面积图.png"],
            "required": ["面积图.png"],
            "priority": ["面积图.png"],
        },
        {
            "allowed": ["流速图.png"],
            "required": ["流速图.png"],
            "priority": ["流速图.png"],
        },
        {},
    ]

    plan = updater.build_task_update_plan(
        snapshot,
        markdown_steps,
        make_rubric_items(),
        task_id="task-1",
        course_id="course-1",
        stage_resource_specs=resource_specs,
        insert_index=1,
        new_step_id="inserted",
        new_flow_id="new-flow",
    )

    assert plan["inserted"] is True
    create_operations = [
        operation
        for operation in plan["operations"]
        if operation["kind"].startswith("create_")
    ]
    assert create_operations[0]["kind"] == "create_step"
    assert create_operations[0]["payload"]["stepId"] == "inserted"
    assert create_operations[0]["payload"]["courseId"] == "course-1"
    assert create_operations[1]["kind"] == "create_flow"
    assert create_operations[1]["payload"]["scriptStepStartId"] == "inserted"
    assert create_operations[1]["payload"]["scriptStepEndId"] == "two"
    assert plan["operations"][-1]["kind"] == "edit_flow"
    assert plan["operations"][-1]["safety"] == "retarget-last"
    assert plan["operations"][-1]["payload"]["flowId"] == "f1"
    assert plan["operations"][-1]["payload"]["scriptStepEndId"] == "inserted"
    inserted_resources = create_operations[0]["payload"]["stepDetailDTO"][
        "scriptStepResourceList"
    ]
    assert [item["fileName"] for item in inserted_resources] == ["流速图.png"]
    edited_one = next(
        operation["payload"]
        for operation in plan["operations"]
        if operation["kind"] == "edit_step"
        and operation["payload"]["stepId"] == "one"
    )
    assert [
        item["fileName"]
        for item in edited_one["stepDetailDTO"]["scriptStepResourceList"]
    ] == ["面积图.png"]


def test_build_task_update_plan_rejects_non_unique_or_non_chinese_exit_tokens():
    snapshot = {
        "configuration": {"trainTaskId": "task-1"},
        "steps": [
            make_step("start", "START", "SCRIPT_START"),
            make_step("one", "旧阶段一"),
            make_step("two", "旧阶段二"),
            make_step("end", "END", "SCRIPT_END"),
        ],
        "flows": [
            make_flow("f0", "start", "one", ""),
            make_flow("f1", "one", "two", "旧条件一"),
            make_flow("f2", "two", "end", "旧条件二"),
        ],
        "scoreItems": make_score_items(),
    }
    markdown_steps = [
        make_markdown_step(1, "阶段一", "NEXT_TO_STAGE2"),
        make_markdown_step(2, "阶段二", "NEXT_TO_STAGE2"),
    ]

    with pytest.raises(updater.PreflightError, match="跳转"):
        updater.build_task_update_plan(
            snapshot,
            markdown_steps,
            make_rubric_items(),
            task_id="task-1",
            course_id="course-1",
            stage_resource_specs=[{}, {}],
        )


def test_build_task_update_plan_rejects_resource_stage_name_misalignment():
    snapshot = {
        "configuration": {"trainTaskId": "task-1"},
        "steps": [
            make_step("start", "START", "SCRIPT_START"),
            make_step("one", "旧阶段"),
            make_step("end", "END", "SCRIPT_END"),
        ],
        "flows": [
            make_flow("f0", "start", "one", ""),
            make_flow("f1", "one", "end", "旧条件"),
        ],
        "scoreItems": make_score_items(),
    }

    with pytest.raises(updater.PreflightError, match="资源清单"):
        updater.build_task_update_plan(
            snapshot,
            [make_markdown_step(1, "阶段一", "训练完成")],
            make_rubric_items(),
            task_id="task-1",
            course_id="course-1",
            stage_resource_specs=[{"stageName": "错误阶段"}],
        )


class FakeGateway:
    def __init__(self, snapshot, backup_root):
        self.snapshot = copy.deepcopy(snapshot)
        self.backup_root = Path(backup_root)
        self.events = []

    def _assert_backup_exists(self):
        assert list(self.backup_root.glob("*/snapshot.json"))

    def export_snapshot(self, task_id):
        assert task_id == self.snapshot["configuration"]["trainTaskId"]
        return copy.deepcopy(self.snapshot)

    def edit_configuration(self, payload):
        self._assert_backup_exists()
        self.events.append(("edit_configuration", payload["trainTaskId"]))
        self.snapshot["configuration"] = copy.deepcopy(payload)

    def edit_step(self, payload):
        self._assert_backup_exists()
        self.events.append(("edit_step", payload["stepId"]))
        for index, step in enumerate(self.snapshot["steps"]):
            if step["stepId"] == payload["stepId"]:
                self.snapshot["steps"][index] = copy.deepcopy(payload)
                return
        raise AssertionError("missing step")

    def create_step(self, payload):
        self._assert_backup_exists()
        self.events.append(("create_step", payload["stepId"]))
        self.snapshot["steps"].append(copy.deepcopy(payload))

    def edit_flow(self, payload):
        self._assert_backup_exists()
        self.events.append(("edit_flow", payload["flowId"]))
        for index, flow in enumerate(self.snapshot["flows"]):
            if flow["flowId"] == payload["flowId"]:
                self.snapshot["flows"][index] = copy.deepcopy(payload)
                return
        raise AssertionError("missing flow")

    def create_flow(self, payload):
        self._assert_backup_exists()
        self.events.append(("create_flow", payload["flowId"]))
        self.snapshot["flows"].append(copy.deepcopy(payload))

    def edit_score(self, payload):
        self._assert_backup_exists()
        self.events.append(("edit_score", payload["itemId"]))
        for index, item in enumerate(self.snapshot["scoreItems"]):
            if item["itemId"] == payload["itemId"]:
                self.snapshot["scoreItems"][index] = copy.deepcopy(payload)
                return
        raise AssertionError("missing score")


def test_apply_update_plan_writes_backup_before_mutation_and_verifies(tmp_path):
    snapshot = {
        "configuration": {
            "trainTaskId": "task-1",
            "trainTaskName": "原任务",
            "description": "原描述",
            "trainType": "text",
            "trainTaskCover": {},
            "entranceVoiceNid": "old-voice",
        },
        "steps": [
            make_step("start", "START", "SCRIPT_START"),
            make_step("one", "旧阶段一"),
            make_step("two", "旧阶段二"),
            make_step("end", "END", "SCRIPT_END"),
        ],
        "flows": [
            make_flow("f0", "start", "one", ""),
            make_flow("f1", "one", "two", "旧条件一"),
            make_flow("f2", "two", "end", "旧条件二"),
        ],
        "scoreItems": make_score_items(),
    }
    plan = updater.build_task_update_plan(
        snapshot,
        [
            make_markdown_step(1, "阶段一", "进入阶段二阶段"),
            make_markdown_step(2, "阶段二", "训练完成"),
        ],
        make_rubric_items(),
        task_id="task-1",
        course_id="course-1",
        stage_resource_specs=[{}, {}],
    )
    gateway = FakeGateway(snapshot, tmp_path)

    report = updater.apply_update_plan(
        gateway,
        plan,
        original_snapshot=snapshot,
        backup_dir=tmp_path,
    )

    assert report["verified"] is True
    assert Path(report["backupPath"]).exists()
    assert gateway.events[0] == ("edit_configuration", "task-1")
    assert updater.verify_task_snapshot(gateway.snapshot, plan) == []


def test_verify_task_snapshot_reports_content_drift(tmp_path):
    snapshot = {
        "configuration": {
            "trainTaskId": "task-1",
            "trainTaskName": "原任务",
            "description": "原描述",
            "trainType": "text",
            "trainTaskCover": {},
            "entranceVoiceNid": "old-voice",
        },
        "steps": [
            make_step("start", "START", "SCRIPT_START"),
            make_step("one", "旧阶段一"),
            make_step("end", "END", "SCRIPT_END"),
        ],
        "flows": [
            make_flow("f0", "start", "one", ""),
            make_flow("f1", "one", "end", "旧条件"),
        ],
        "scoreItems": make_score_items(),
    }
    plan = updater.build_task_update_plan(
        snapshot,
        [make_markdown_step(1, "阶段一", "训练完成")],
        make_rubric_items(),
        task_id="task-1",
        course_id="course-1",
        stage_resource_specs=[{}],
    )
    gateway = FakeGateway(snapshot, tmp_path)
    updater.apply_update_plan(
        gateway,
        plan,
        original_snapshot=snapshot,
        backup_dir=tmp_path,
    )
    gateway.snapshot["steps"][1]["stepDetailDTO"]["llmPrompt"] = "平台漂移"

    errors = updater.verify_task_snapshot(gateway.snapshot, plan)

    assert any("llmPrompt" in error for error in errors)


class FakeResponse:
    def __init__(self, body, status_code=200):
        self._body = body
        self.status_code = status_code

    def json(self):
        return copy.deepcopy(self._body)


class FakeRequester:
    def __init__(self, endpoint_data):
        self.endpoint_data = endpoint_data
        self.calls = []

    def post(self, url, **kwargs):
        endpoint = url.rsplit("/", 1)[-1]
        self.calls.append((endpoint, copy.deepcopy(kwargs.get("json"))))
        body = self.endpoint_data.get(
            endpoint, {"code": 200, "success": True, "data": None}
        )
        return FakeResponse(body)


def test_polymas_gateway_exports_and_mutates_only_requested_task():
    requester = FakeRequester(
        {
            "queryConfiguration": {
                "code": 200,
                "data": {"trainTaskId": "task-1"},
            },
            "queryScriptStepList": {"success": True, "data": [{"stepId": "s"}]},
            "queryScriptStepFlowList": {
                "code": "200",
                "data": [{"flowId": "f"}],
            },
            "queryScoreItemList": {
                "code": 200,
                "data": [{"itemId": "i"}],
            },
        }
    )
    gateway = updater.PolymasAbilityTrainGateway(
        course_id="course-1",
        headers={"Authorization": "secret", "Cookie": "secret"},
        requester=requester,
        api_base="https://example.invalid/abilityTrain",
    )

    snapshot = gateway.export_snapshot("task-1")
    gateway.edit_step({"trainTaskId": "task-1", "stepId": "s"})
    gateway.create_step({"trainTaskId": "task-1", "stepId": "new"})
    gateway.edit_flow({"trainTaskId": "task-1", "flowId": "f"})
    gateway.create_flow({"trainTaskId": "task-1", "flowId": "new-f"})
    gateway.edit_score({"trainTaskId": "task-1", "itemId": "i"})

    assert snapshot["configuration"]["trainTaskId"] == "task-1"
    assert snapshot["steps"] == [{"stepId": "s"}]
    assert snapshot["flows"] == [{"flowId": "f"}]
    assert snapshot["scoreItems"] == [{"itemId": "i"}]
    assert requester.calls[4][0] == "editScriptStep"
    assert requester.calls[4][1]["courseId"] == "course-1"
    assert requester.calls[5][0] == "createScriptStep"
    assert requester.calls[5][1]["courseId"] == "course-1"
    assert [call[0] for call in requester.calls[-3:]] == [
        "editScriptStepFlow",
        "createScriptStepFlow",
        "editScoreItem",
    ]


def test_polymas_gateway_rejects_api_failure_without_leaking_headers():
    requester = FakeRequester(
        {
            "queryConfiguration": {
                "code": 401,
                "msg": "invalid session",
                "data": None,
            }
        }
    )
    gateway = updater.PolymasAbilityTrainGateway(
        course_id="course-1",
        headers={"Authorization": "top-secret", "Cookie": "cookie-secret"},
        requester=requester,
        api_base="https://example.invalid/abilityTrain",
    )

    with pytest.raises(RuntimeError) as exc_info:
        gateway.export_snapshot("task-1")

    message = str(exc_info.value)
    assert "queryConfiguration" in message
    assert "invalid session" in message
    assert "top-secret" not in message
    assert "cookie-secret" not in message


def test_load_update_manifest_resolves_paths_and_validates_task_keys(tmp_path):
    (tmp_path / "one").mkdir()
    (tmp_path / "one" / "训练剧本配置.md").write_text(
        "placeholder", encoding="utf-8"
    )
    (tmp_path / "one" / "评价标准.md").write_text(
        "placeholder", encoding="utf-8"
    )
    manifest_path = tmp_path / "平台同步清单.json"
    manifest_path.write_text(
        json.dumps(
            {
                "courseId": "course-1",
                "backupDir": "backups",
                "tasks": [
                    {
                        "key": "1",
                        "taskId": "task-1",
                        "markdown": "one/训练剧本配置.md",
                        "rubric": "one/评价标准.md",
                        "stages": [],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    manifest = updater.load_update_manifest(manifest_path)

    assert manifest["courseId"] == "course-1"
    assert manifest["backupDir"] == tmp_path / "backups"
    assert manifest["tasks"][0]["markdownPath"] == (
        tmp_path / "one" / "训练剧本配置.md"
    )
    assert manifest["tasks"][0]["rubricPath"] == (
        tmp_path / "one" / "评价标准.md"
    )

    broken = json.loads(manifest_path.read_text(encoding="utf-8"))
    broken["tasks"].append(copy.deepcopy(broken["tasks"][0]))
    manifest_path.write_text(
        json.dumps(broken, ensure_ascii=False), encoding="utf-8"
    )
    with pytest.raises(updater.PreflightError, match="key"):
        updater.load_update_manifest(manifest_path)


def test_prepare_task_update_is_read_only_and_uses_injected_loaders(tmp_path):
    snapshot = {
        "configuration": {
            "trainTaskId": "task-1",
            "trainTaskName": "原任务",
            "description": "原描述",
            "trainType": "text",
            "trainTaskCover": {},
            "entranceVoiceNid": "old-voice",
        },
        "steps": [
            make_step("start", "START", "SCRIPT_START"),
            make_step("one", "旧阶段"),
            make_step("end", "END", "SCRIPT_END"),
        ],
        "flows": [
            make_flow("f0", "start", "one", ""),
            make_flow("f1", "one", "end", "旧条件"),
        ],
        "scoreItems": make_score_items(),
    }
    gateway = FakeGateway(snapshot, tmp_path)
    task_spec = {
        "key": "1",
        "taskId": "task-1",
        "markdownPath": tmp_path / "script.md",
        "rubricPath": tmp_path / "rubric.md",
        "stages": [{"stageName": "阶段一"}],
    }

    original, plan = updater.prepare_task_update(
        gateway,
        task_spec,
        course_id="course-1",
        markdown_loader=lambda _: [
            make_markdown_step(1, "阶段一", "训练完成")
        ],
        rubric_loader=lambda _: make_rubric_items(),
        id_factory=lambda: "unused-id",
    )

    assert original == snapshot
    assert plan["taskId"] == "task-1"
    assert gateway.events == []
    assert not list(tmp_path.glob("*/snapshot.json"))


def test_resolve_course_id_prefers_explicit_manifest_over_stale_environment():
    course_id, warning = updater.resolve_course_id(
        "course-from-link", "stale-course-from-env"
    )

    assert course_id == "course-from-link"
    assert warning is True


def test_module_entrypoint_guard_is_after_all_function_definitions():
    source = Path(updater.__file__).read_text(encoding="utf-8")

    assert source.rfind('if __name__ == "__main__":') > source.rfind("\ndef ")


def test_direct_script_entrypoint_can_import_sibling_package_modules(tmp_path):
    missing_manifest = tmp_path / "missing-manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            str(Path(updater.__file__)),
            "--manifest",
            str(missing_manifest),
        ],
        cwd=Path(updater.__file__).parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "No module named 'skill_training_build'" not in result.stderr
    assert str(missing_manifest) in result.stderr


def test_task2_final_transition_locks_to_the_summary_opening():
    workspace = Path(updater.__file__).parents[1]
    script_path = (
        workspace
        / "skills_training_course"
        / "中国农业大学-遥感地学分析"
        / "云游世界2"
        / "训练剧本配置.md"
    )
    steps = parse_markdown(script_path)

    assert steps[5]["prologue"] in steps[4]["transitionPrompt"]
    assert "禁止" in steps[4]["transitionPrompt"]
    assert "虚构" in steps[4]["transitionPrompt"]
