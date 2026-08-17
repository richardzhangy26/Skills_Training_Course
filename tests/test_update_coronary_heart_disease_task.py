import copy
import json
from pathlib import Path

import pytest

from skill_training_build import update_coronary_heart_disease_task as updater


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "coronary_heart_disease"
    / "live_snapshot_sanitized.json"
)


def load_snapshot() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def get_step(snapshot: dict, step_id: str) -> dict:
    return next(item for item in snapshot["steps"] if item["stepId"] == step_id)


class FakeGateway:
    def __init__(
        self,
        snapshot: dict,
        *,
        fail_step_id: str | None = None,
    ) -> None:
        self.snapshot = copy.deepcopy(snapshot)
        self.mutations: list[tuple[str, str]] = []
        self.fail_step_id = fail_step_id

    def export_snapshot(self, task_id: str) -> dict:
        assert task_id == updater.TASK_ID
        return copy.deepcopy(self.snapshot)

    def edit_configuration(self, payload: dict) -> None:
        self.mutations.append(("configuration", payload["trainTaskId"]))

    def edit_step(self, payload: dict) -> None:
        self.mutations.append(("step", payload["stepId"]))
        if payload["stepId"] == self.fail_step_id:
            raise RuntimeError(f"写入失败：{payload['stepId']}")

    def edit_score_item(self, payload: dict) -> None:
        self.mutations.append(("score", payload["itemId"]))

    def edit_flow(self, payload: dict) -> None:
        self.mutations.append(("flow", payload["flowId"]))


def test_default_run_is_dry_run_and_performs_no_platform_mutation(
    tmp_path: Path,
) -> None:
    gateway = FakeGateway(load_snapshot())

    report = updater.run_coronary_update(gateway, backup_dir=tmp_path)

    assert report["dry_run"] is True
    assert report["updated_count"] == 0
    assert gateway.mutations == []
    assert Path(report["backup_path"]).exists()
    plan_path = Path(report["plan_path"])
    assert plan_path.exists()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["taskId"] == updater.TASK_ID
    assert len(plan["steps"]) == 19
    assert len(plan["scoreItems"]) == 5
    assert len(plan["flows"]) == 1


def test_plan_matches_real_coronary_steps_by_step_id_not_api_order() -> None:
    snapshot = load_snapshot()
    snapshot["steps"].reverse()

    plan = updater.build_update_plan(snapshot)

    assert [item["stepId"] for item in plan["steps"]] == list(
        updater.TARGET_STEP_IDS
    )
    assert [item["stepId"] for item in plan["steps"]] != [
        item["stepId"]
        for item in snapshot["steps"]
        if item["stepId"] in updater.TARGET_STEP_IDS
    ]


def test_mismatched_expected_step_name_aborts_before_platform_mutation(
    tmp_path: Path,
) -> None:
    snapshot = load_snapshot()
    target = next(
        item
        for item in snapshot["steps"]
        if item["stepId"] == updater.CASE1_INFO_STEP_ID
    )
    target["stepDetailDTO"]["stepName"] = "已被其他人改名"
    gateway = FakeGateway(snapshot)

    with pytest.raises(
        updater.PreflightError,
        match=updater.CASE1_INFO_STEP_ID,
    ):
        updater.run_coronary_update(
            gateway,
            backup_dir=tmp_path,
            apply=True,
        )

    assert gateway.mutations == []


def test_case1_teacher_feedback_is_applied_to_target_steps() -> None:
    snapshot = load_snapshot()
    info = updater.build_target_step(
        get_step(snapshot, updater.CASE1_INFO_STEP_ID)
    )["stepDetailDTO"]
    exam = updater.build_target_step(
        get_step(snapshot, updater.CASE1_PHYSICAL_STEP_ID)
    )["stepDetailDTO"]
    auxiliary = updater.build_target_step(
        get_step(snapshot, updater.CASE1_AUXILIARY_STEP_ID)
    )["stepDetailDTO"]
    treatment = updater.build_target_step(
        get_step(snapshot, updater.CASE1_TREATMENT_STEP_ID)
    )["stepDetailDTO"]
    paired_exam = updater.build_target_step(
        get_step(snapshot, updater.CASE1_PAIRED_EXAM_STEP_ID)
    )["stepDetailDTO"]

    assert "西医与中医初步考虑什么诊断？" in info["llmPrompt"]
    assert "西医大致考虑什么方向" not in info["llmPrompt"]
    assert "**话术示例**" not in info["llmPrompt"]
    assert "你能想到冠心病心绞痛的方向" not in info["llmPrompt"]
    assert "干湿性啰音" in exam["llmPrompt"]
    assert "干湿啰音" not in exam["llmPrompt"]

    assert "患者需要做哪些辅助检查？" in auxiliary["prologue"]
    assert "CK-MB" not in auxiliary["prologue"]
    assert "CK-MB 18 U/L" in auxiliary["llmPrompt"]
    assert "肌钙蛋白I 0.02 ng/mL" in auxiliary["llmPrompt"]
    assert "总胆固醇 7.5 mmol/L" in auxiliary["llmPrompt"]
    assert "甘油三酯 3.3 mmol/L" in auxiliary["llmPrompt"]
    assert "低密度脂蛋白 5.2 mmol/L" in auxiliary["llmPrompt"]
    assert "高密度脂蛋白 0.6 mmol/L" in auxiliary["llmPrompt"]
    assert "分析合理" in auxiliary["prologue"]
    assert "锁定稳定型心绞痛，思路很清楚" not in auxiliary["llmPrompt"]
    assert "辅助检查结果已呈现" not in auxiliary["llmPrompt"]
    assert "结果已呈现给学生" not in auxiliary["llmPrompt"]
    assert "数值正常可排除急性心肌梗死" not in auxiliary["llmPrompt"]
    assert "不能仅凭单次正常结果绝对排除急性心肌梗死" in auxiliary[
        "llmPrompt"
    ]

    assert treatment["stepName"] == "中西医结合治疗方案"
    assert "中医治则、主方、具体药物组成" in treatment["llmPrompt"]
    assert "西医治疗原则、具体药物" in treatment["llmPrompt"]
    assert "仅依据学生在本节点亲自说出的内容" in treatment["llmPrompt"]

    assert "接下来" in paired_exam["prologue"]
    assert "趁热打铁" not in paired_exam["prologue"]


def test_case2_sequence_voice_and_hard_gates_are_applied() -> None:
    snapshot = load_snapshot()
    interview = updater.build_target_step(
        get_step(snapshot, updater.CASE2_INTERVIEW_STEP_ID)
    )["stepDetailDTO"]
    supplement = updater.build_target_step(
        get_step(snapshot, updater.CASE2_INFO_STEP_ID)
    )["stepDetailDTO"]
    auxiliary = updater.build_target_step(
        get_step(snapshot, updater.CASE2_AUXILIARY_STEP_ID)
    )["stepDetailDTO"]
    diagnosis = updater.build_target_step(
        get_step(snapshot, updater.CASE2_DIAGNOSIS_STEP_ID)
    )["stepDetailDTO"]

    assert updater.CASE2_PATIENT_CLOSING in interview["llmPrompt"]
    assert "`进入信息补充`" not in interview["llmPrompt"]
    assert supplement["stepName"] == "信息补充与初步研判"
    assert supplement["prologue"].startswith("下面进入信息补充。")
    assert "安排哪些辅助检查" not in supplement["prologue"]
    assert "信息补充与辅助检查规划" not in supplement["llmPrompt"]
    assert "检查设想" not in supplement["llmPrompt"]
    assert "安排哪些辅助检查" not in supplement["llmPrompt"]
    assert "进入体格检查" in supplement["llmPrompt"]

    assert "患者需要做哪些辅助检查？" in auxiliary["prologue"]
    assert "CK-MB" not in auxiliary["prologue"]
    assert "锁定不稳定型心绞痛，思路很清楚" not in auxiliary["llmPrompt"]
    assert "只指出遗漏的检查类别或解读维度" in auxiliary["llmPrompt"]
    assert "辅助检查结果已呈现" not in auxiliary["llmPrompt"]
    assert "结果已呈现给学生" not in auxiliary["llmPrompt"]
    assert "数值正常可排除急性心肌梗死" not in auxiliary["llmPrompt"]
    assert "不能仅凭单次正常结果绝对排除急性心肌梗死" in auxiliary[
        "llmPrompt"
    ]

    assert "中医病名、证型、辨证依据是三个独立必答项" in diagnosis[
        "llmPrompt"
    ]
    assert "只依据学生最新一轮回答" in diagnosis["llmPrompt"]
    assert "学生此前在本诊断节点" not in diagnosis["llmPrompt"]
    assert "原发性高血压2级" not in diagnosis["llmPrompt"]
    assert "单次血压不能直接确诊原发性高血压" in diagnosis["llmPrompt"]


def test_case2_flow_keeps_endpoints_and_changes_only_trigger_text() -> None:
    snapshot = load_snapshot()
    current = next(
        item
        for item in snapshot["flows"]
        if item["flowId"] == updater.CASE2_INTERVIEW_FLOW_ID
    )

    target = updater.build_target_flow(current)

    assert target["scriptStepStartId"] == current["scriptStepStartId"]
    assert target["scriptStepEndId"] == current["scriptStepEndId"]
    assert target["flowCondition"] == updater.CASE2_PATIENT_CLOSING
    assert target["flowConfiguration"]["conditions"][0]["conditions"][0][
        "text"
    ] == updater.CASE2_PATIENT_CLOSING


def test_case3_teacher_feedback_is_applied_to_target_steps() -> None:
    snapshot = load_snapshot()
    supplement = updater.build_target_step(
        get_step(snapshot, updater.CASE3_INFO_STEP_ID)
    )["stepDetailDTO"]
    physical = updater.build_target_step(
        get_step(snapshot, updater.CASE3_PHYSICAL_STEP_ID)
    )["stepDetailDTO"]
    auxiliary = updater.build_target_step(
        get_step(snapshot, updater.CASE3_AUXILIARY_STEP_ID)
    )["stepDetailDTO"]
    treatment = updater.build_target_step(
        get_step(snapshot, updater.CASE3_TREATMENT_STEP_ID)
    )["stepDetailDTO"]
    paired_exam = updater.build_target_step(
        get_step(snapshot, updater.CASE3_PAIRED_EXAM_STEP_ID)
    )["stepDetailDTO"]

    assert "抓紧时间" in supplement["prologue"]
    assert "咱们抓紧。" not in supplement["prologue"]
    assert "**话术示例**" not in supplement["llmPrompt"]
    assert "你能想到冠心病心梗的方向" not in supplement["llmPrompt"]
    assert "抓紧时间看体征" in physical["prologue"]
    assert "体温36.4℃" in physical["prologue"]
    assert "脉细涩无力" in physical["prologue"]
    assert "未闻及干湿性啰音" in physical["prologue"]
    assert "各瓣膜听诊区未闻及病理性杂音" in physical["prologue"]
    assert "无压痛、无反跳痛" in physical["prologue"]
    assert physical["prologue"].index("脉细涩无力。") < physical[
        "prologue"
    ].index("先说说")

    assert "肌钙蛋白I 12.6 ng/mL" in auxiliary["prologue"]
    assert "CK-MB 85 U/L" in auxiliary["prologue"]
    assert "总胆固醇 7.2 mmol/L" in auxiliary["prologue"]
    assert "甘油三酯 3.1 mmol/L" in auxiliary["prologue"]
    assert "低密度脂蛋白 4.8 mmol/L" in auxiliary["prologue"]
    assert "高密度脂蛋白 0.9 mmol/L" in auxiliary["prologue"]

    assert treatment["stepName"] == "中西医结合治疗方案"
    assert "中医治则、主方、具体药物组成" in treatment["llmPrompt"]
    assert "西医治疗原则、具体药物" in treatment["llmPrompt"]

    assert "为何急性心梗患者硝酸甘油含服无效？" in paired_exam[
        "prologue"
    ]
    assert "请结合血管病理与中医病机作答" not in paired_exam[
        "llmPrompt"
    ]
    assert updater.CASE3_NITROGLYCERIN_ANSWER in paired_exam["llmPrompt"]


@pytest.mark.parametrize(
    "step_id",
    [
        "VPDz2YNGXNhmljg0yDjZ",
        "Z8DbqV1QX1iQnoK6la0X",
        "5vamqgVPGVivQ5A22a4y",
    ],
)
def test_summary_starts_with_standard_answer_then_numeric_score(
    step_id: str,
) -> None:
    target = updater.build_target_step(get_step(load_snapshot(), step_id))
    prompt = target["stepDetailDTO"]["llmPrompt"]

    assert prompt.index("【标准答案】") < prompt.index("【评分与点评】")
    assert "总分：__/100" in prompt
    for label in (
        "人文沟通与急救素养：__/10",
        "问诊采集：__/35",
        "辅助检查与体征解读：__/15",
        "中西医诊断与鉴别：__/20",
        "中西医结合治疗方案：__/20",
        "扣分原因",
    ):
        assert label in prompt
    assert "含【标准答案】与【评分与点评】即视为已完成总结" in prompt
    assert "总结报告≤400字" not in prompt


def test_case_specific_summary_standards_are_medically_consistent() -> None:
    snapshot = load_snapshot()
    case2 = updater.build_target_step(
        get_step(snapshot, updater.CASE2_SUMMARY_STEP_ID)
    )["stepDetailDTO"]["llmPrompt"]
    case3 = updater.build_target_step(
        get_step(snapshot, updater.CASE3_SUMMARY_STEP_ID)
    )["stepDetailDTO"]["llmPrompt"]

    assert "可合并原发性高血压2级" not in case2
    assert "单次血压不能直接确诊原发性高血压" in case2
    assert "抗凝" in case2
    assert "低分子肝素" in case2
    assert "高脂血症" in case3
    assert "原发性高血压病2级（很高危）" in case3


def test_target_configuration_changes_only_task_name() -> None:
    current = load_snapshot()["configuration"]
    original = copy.deepcopy(current)

    target = updater.build_target_configuration(current)

    assert target["trainTaskName"] == "冠心病的中西医结合诊疗模拟训练"
    assert target["extConfig"]["trainTaskName"] == (
        "冠心病的中西医结合诊疗模拟训练"
    )
    target["trainTaskName"] = original["trainTaskName"]
    target["extConfig"]["trainTaskName"] = original["extConfig"][
        "trainTaskName"
    ]
    assert target == original


def test_score_plan_is_branch_aware_and_totals_100() -> None:
    current = load_snapshot()["scoreItems"]

    target = updater.build_target_score_items(current)

    assert [item["score"] for item in target] == [10, 35, 15, 20, 20]
    assert sum(item["score"] for item in target) == 100
    assert [item["itemId"] for item in target] == [
        item["itemId"] for item in current
    ]
    assert [item["itemName"] for item in target] == [
        "一、人文沟通与急救素养",
        "二、问诊采集",
        "三、辅助检查与体征解读",
        "四、中西医诊断与鉴别",
        "五、中西医结合治疗方案",
    ]
    for item in target:
        assert "按当前进入的病例" in item["requireDetail"]
        assert "扣分原因" in item["requireDetail"]
        assert "病例一" in item["requireDetail"]
        assert "病例二" in item["requireDetail"]
        assert "病例三" in item["requireDetail"]
    auxiliary_item = target[2]["requireDetail"]
    assert "病例三不设置检查规划环节" in auxiliary_item
    assert "不得因未规划检查扣分" in auxiliary_item


def test_apply_writes_backup_before_configuration_steps_and_scores(
    tmp_path: Path,
) -> None:
    class BackupAssertingGateway(FakeGateway):
        def edit_configuration(self, payload: dict) -> None:
            assert list(tmp_path.rglob("snapshot.json"))
            super().edit_configuration(payload)

    gateway = BackupAssertingGateway(load_snapshot())

    report = updater.run_coronary_update(
        gateway,
        backup_dir=tmp_path,
        apply=True,
    )

    expected = [("configuration", updater.TASK_ID)]
    expected.extend(("step", step_id) for step_id in updater.TARGET_STEP_IDS)
    expected.extend(
        ("score", item["itemId"])
        for item in updater.SCORE_SPECS
    )
    assert gateway.mutations == expected
    assert report["dry_run"] is False
    assert report["updated_count"] == len(expected)


def test_flow_change_requires_explicit_include_flows_switch(
    tmp_path: Path,
) -> None:
    gateway = FakeGateway(load_snapshot())

    report = updater.run_coronary_update(
        gateway,
        backup_dir=tmp_path,
        apply=True,
        include_flows=True,
    )

    assert gateway.mutations[-1] == (
        "flow",
        updater.CASE2_INTERVIEW_FLOW_ID,
    )
    assert report["flow_updates_enabled"] is True


def test_backup_removes_credential_like_keys(tmp_path: Path) -> None:
    snapshot = load_snapshot()
    snapshot["Authorization"] = "secret-authorization"
    snapshot["nestedSecret"] = {
        "COOKIE": "secret-cookie",
        "safe": "保留",
    }
    gateway = FakeGateway(snapshot)

    report = updater.run_coronary_update(gateway, backup_dir=tmp_path)
    backup_text = Path(report["backup_path"]).read_text(encoding="utf-8")

    assert "secret-authorization" not in backup_text
    assert "secret-cookie" not in backup_text
    assert "保留" in backup_text


def test_step_write_failure_stops_remaining_steps_scores_and_flow(
    tmp_path: Path,
) -> None:
    failing_id = updater.TARGET_STEP_IDS[1]
    gateway = FakeGateway(load_snapshot(), fail_step_id=failing_id)

    with pytest.raises(RuntimeError, match=failing_id):
        updater.run_coronary_update(
            gateway,
            backup_dir=tmp_path,
            apply=True,
        )

    assert gateway.mutations == [
        ("configuration", updater.TASK_ID),
        ("step", updater.TARGET_STEP_IDS[0]),
        ("step", failing_id),
    ]


def test_live_gateway_uses_verified_endpoints_and_payload_shapes() -> None:
    class FakeResponse:
        def __init__(self, data):
            self.data = data
            self.status_code = 200

        def json(self):
            return {"code": 200, "success": True, "data": self.data}

    class FakeRequester:
        def __init__(self):
            self.calls = []

        def post(self, url, *, headers, json, timeout):
            endpoint = url.rsplit("/", 1)[-1]
            self.calls.append((endpoint, copy.deepcopy(json), headers, timeout))
            query_data = {
                "queryConfiguration": {"trainTaskId": updater.TASK_ID},
                "queryScriptStepList": [],
                "queryScriptStepFlowList": [],
                "queryScoreItemList": [],
            }
            return FakeResponse(query_data.get(endpoint))

    requester = FakeRequester()
    gateway = updater.PolymasAbilityTrainGateway(
        course_id="course-1",
        library_folder_id="library-1",
        headers={"Authorization": "secret", "Cookie": "secret"},
        requester=requester,
        api_base="https://example.test/teacher-course/abilityTrain",
    )

    snapshot = gateway.export_snapshot(updater.TASK_ID)
    gateway.edit_configuration({"trainTaskId": updater.TASK_ID})
    gateway.edit_step({"stepId": "step-1"})
    gateway.edit_score_item(
        {"trainTaskId": updater.TASK_ID, "itemId": "score-1"}
    )
    gateway.edit_flow(
        {"trainTaskId": updater.TASK_ID, "flowId": "flow-1"}
    )

    assert set(snapshot) == {
        "configuration",
        "steps",
        "flows",
        "scoreItems",
    }
    assert [call[0] for call in requester.calls] == [
        "queryConfiguration",
        "queryScriptStepList",
        "queryScriptStepFlowList",
        "queryScoreItemList",
        "editConfiguration",
        "editScriptStep",
        "editScoreItem",
        "editScriptStepFlow",
    ]
    assert requester.calls[4][1]["courseId"] == "course-1"
    assert requester.calls[5][1] == {
        "stepId": "step-1",
        "trainTaskId": updater.TASK_ID,
        "courseId": "course-1",
        "libraryFolderId": "library-1",
    }


def test_build_live_gateway_uses_course_id_from_target_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from skill_training_build import create_task_from_markdown as ctm

    monkeypatch.setattr(ctm, "load_env_config", lambda: None)
    monkeypatch.setattr(
        ctm,
        "require_course_id",
        lambda: pytest.fail("不应读取与当前任务不匹配的 .env COURSE_ID"),
    )
    monkeypatch.setattr(ctm, "get_headers", lambda: {"Authorization": "test"})
    monkeypatch.setattr(
        ctm,
        "get_ability_train_api_base",
        lambda: "https://example.test/teacher-course/abilityTrain",
    )

    gateway = updater.build_live_gateway()

    assert gateway.course_id == updater.COURSE_ID
    assert gateway.library_folder_id == updater.LIBRARY_FOLDER_ID


def test_case3_report_payload_matches_ability_node_submit_shape() -> None:
    original = get_step(load_snapshot(), updater.CASE3_AUXILIARY_STEP_ID)
    original["stepDetailDTO"]["scriptStepResourceList"] = []
    original["stepDetailDTO"]["stepExtProperty"] = {
        "trainSubType": "ability",
        "resources": None,
        "bgMediaType": 1,
        "bgMediaVolume": 80,
    }

    payload = updater.build_case3_report_resource_step(original)

    assert set(payload) == {"stepId", "stepDetailDTO", "positionDTO"}
    assert payload["stepId"] == updater.CASE3_AUXILIARY_STEP_ID
    detail = payload["stepDetailDTO"]
    assert detail["trainSubType"] == "ability"
    assert "scriptStepResourceList" not in detail
    assert "resources" not in detail
    assert "trainSubType" not in detail["stepExtProperty"]
    assert detail["stepExtProperty"]["bgMediaType"] == 1
    resource_groups = detail["stepExtProperty"]["resources"]
    assert all("nid" not in group for group in resource_groups)
    resource_group = next(group for group in resource_groups if group["list"])
    assert resource_group["category"] == "未分类"
    resource = resource_group["list"][0]
    assert resource["fileId"] == updater.CASE3_REPORT_FILE_ID
    assert resource["fileUrl"] == updater.CASE3_REPORT_FILE_URL
    assert resource["thumbnail"] == updater.CASE3_REPORT_FILE_URL
    assert resource["scriptStepId"] == updater.CASE3_AUXILIARY_STEP_ID
    assert resource["trainTaskId"] == updater.TASK_ID
    assert "scriptStepResourceId" not in resource


def test_ability_submit_payload_matches_frontend_resource_cleanup() -> None:
    original = get_step(load_snapshot(), updater.CASE1_INFO_STEP_ID)
    original["stepDetailDTO"]["scriptStepResourceList"] = [
        {
            "scriptStepResourceId": "existing-link",
            "fileId": "existing-file",
            "fileName": "既有资源.pdf",
            "fileUrl": "https://example.test/existing.pdf",
            "thumbnail": "https://example.test/existing.png",
            "resourceTypeNid": "resource-type",
            "category": "教学资料",
            "type": "resource",
            "sort": 2,
            "isRequired": 1,
            "description": "保留",
        }
    ]

    payload = updater.build_ability_step_submit_payload(original)

    resource_group = payload["stepDetailDTO"]["stepExtProperty"][
        "resources"
    ][0]
    assert "nid" not in resource_group
    assert resource_group["category"] == "教学资料"
    resource = resource_group["list"][0]
    assert "scriptStepResourceId" not in resource
    assert resource["scriptStepId"] == updater.CASE1_INFO_STEP_ID
    assert resource["fileId"] == "existing-file"
    assert resource["isRequired"] is True
    assert resource["description"] == "保留"


def test_ability_submit_payload_preserves_empty_resource_category_shells() -> None:
    original = get_step(load_snapshot(), updater.CASE1_INFO_STEP_ID)

    payload = updater.build_ability_step_submit_payload(original)

    groups = payload["stepDetailDTO"]["stepExtProperty"]["resources"]
    assert groups
    assert all(set(group) == {"category", "list"} for group in groups)
    assert all(group["category"] == "未分类" for group in groups)
    assert all(group["list"] == [] for group in groups)


def test_case3_report_attachment_is_idempotent_when_query_lists_file(
    tmp_path: Path,
) -> None:
    snapshot = load_snapshot()
    step = get_step(snapshot, updater.CASE3_AUXILIARY_STEP_ID)
    step["stepDetailDTO"]["scriptStepResourceList"] = [
        {
            "scriptStepResourceId": "existing-link",
            "fileId": updater.CASE3_REPORT_FILE_ID,
            "fileUrl": "https://cdn.example.test/refreshed-report.png",
            "fileName": updater.CASE3_REPORT_FILE_NAME,
        }
    ]
    gateway = FakeGateway(snapshot)

    report = updater.run_case3_report_attachment(
        gateway,
        backup_dir=tmp_path,
    )

    assert report["updated_count"] == 0
    assert report["already_attached"] is True
    assert gateway.mutations == []
    assert Path(report["backup_path"]).exists()


def test_case3_report_attachment_writes_once_and_verifies(
    tmp_path: Path,
) -> None:
    class ResourceGateway(FakeGateway):
        def edit_step(self, payload: dict) -> None:
            super().edit_step(payload)
            resources = []
            for group in payload["stepDetailDTO"]["stepExtProperty"][
                "resources"
            ]:
                for item in group["list"]:
                    resource = copy.deepcopy(item)
                    resource["scriptStepResourceId"] = (
                        f"link-{resource['fileId']}"
                    )
                    resources.append(resource)
            detail = get_step(
                self.snapshot,
                updater.CASE3_AUXILIARY_STEP_ID,
            )["stepDetailDTO"]
            detail["scriptStepResourceList"] = resources
            detail["stepExtProperty"]["resources"] = None

    snapshot = load_snapshot()
    step = get_step(snapshot, updater.CASE3_AUXILIARY_STEP_ID)
    step["stepDetailDTO"]["scriptStepResourceList"] = [
        {
            "scriptStepResourceId": "old-link",
            "fileId": "old-file",
            "fileName": "原有资料.pdf",
            "fileUrl": "https://example.test/original.pdf",
            "thumbnail": "",
            "resourceTypeNid": "old-type",
            "category": "原有资料",
            "type": "resource",
            "sort": 1,
            "isRequired": 0,
            "description": "",
        }
    ]
    gateway = ResourceGateway(snapshot)

    report = updater.run_case3_report_attachment(
        gateway,
        backup_dir=tmp_path,
    )

    assert report["updated_count"] == 1
    assert report["already_attached"] is False
    assert gateway.mutations == [
        ("step", updater.CASE3_AUXILIARY_STEP_ID)
    ]


def test_case3_report_attachment_rejects_existing_resource_loss(
    tmp_path: Path,
) -> None:
    class DroppingGateway(FakeGateway):
        def edit_step(self, payload: dict) -> None:
            super().edit_step(payload)
            target_resource = next(
                copy.deepcopy(item)
                for group in payload["stepDetailDTO"]["stepExtProperty"][
                    "resources"
                ]
                for item in group["list"]
                if item["fileId"] == updater.CASE3_REPORT_FILE_ID
            )
            detail = get_step(
                self.snapshot,
                updater.CASE3_AUXILIARY_STEP_ID,
            )["stepDetailDTO"]
            detail["scriptStepResourceList"] = [target_resource]

    snapshot = load_snapshot()
    step = get_step(snapshot, updater.CASE3_AUXILIARY_STEP_ID)
    step["stepDetailDTO"]["scriptStepResourceList"] = [
        {
            "fileId": "old-file",
            "fileName": "原有资料.pdf",
            "fileUrl": "https://example.test/original.pdf",
            "resourceTypeNid": "old-type",
            "category": "原有资料",
        }
    ]

    with pytest.raises(RuntimeError, match="资源关联"):
        updater.run_case3_report_attachment(
            DroppingGateway(snapshot),
            backup_dir=tmp_path,
        )


def test_execute_update_plan_uses_ability_resource_submit_shape() -> None:
    class PayloadGateway(FakeGateway):
        def __init__(self, snapshot: dict) -> None:
            super().__init__(snapshot)
            self.step_payloads = []

        def edit_step(self, payload: dict) -> None:
            self.step_payloads.append(copy.deepcopy(payload))
            super().edit_step(payload)

    gateway = PayloadGateway(load_snapshot())
    plan = updater.build_update_plan(load_snapshot())

    updater.execute_update_plan(gateway, plan)

    assert gateway.step_payloads
    for payload in gateway.step_payloads:
        detail = payload["stepDetailDTO"]
        assert "scriptStepResourceList" not in detail
        assert all(
            set(group) == {"category", "list"}
            for group in detail["stepExtProperty"]["resources"]
        )


def test_course_context_repair_resubmits_only_mismatched_target_steps(
    tmp_path: Path,
) -> None:
    class CourseRepairGateway(FakeGateway):
        def edit_step(self, payload: dict) -> None:
            super().edit_step(payload)
            target = get_step(self.snapshot, payload["stepId"])
            target["stepDetailDTO"]["knowledgeBaseId"] = (
                updater.ORIGINAL_KNOWLEDGE_BASE_ID
            )

    snapshot = load_snapshot()
    wrong_step_ids = [
        updater.CASE1_INFO_STEP_ID,
        updater.CASE2_TREATMENT_STEP_ID,
    ]
    for step_id in wrong_step_ids:
        get_step(snapshot, step_id)["stepDetailDTO"]["knowledgeBaseId"] = (
            "wrong-course-knowledge-base"
        )
    gateway = CourseRepairGateway(snapshot)

    report = updater.run_course_context_repair(
        gateway,
        backup_dir=tmp_path,
    )

    assert report["updated_count"] == 2
    assert gateway.mutations == [
        ("step", step_id) for step_id in wrong_step_ids
    ]
    assert Path(report["post_snapshot_path"]).exists()


def test_cli_defaults_to_dry_run_when_gateway_is_injected(
    tmp_path: Path,
) -> None:
    gateway = FakeGateway(load_snapshot())

    report = updater.main(
        ["--backup-dir", str(tmp_path)],
        gateway=gateway,
    )

    assert report["dry_run"] is True
    assert gateway.mutations == []


def test_target_builders_are_idempotent_for_safe_retry() -> None:
    snapshot = load_snapshot()
    for step_id in updater.TARGET_STEP_IDS:
        first = updater.build_target_step(get_step(snapshot, step_id))
        second = updater.build_target_step(first)
        assert second == first

    flow = next(
        item
        for item in snapshot["flows"]
        if item["flowId"] == updater.CASE2_INTERVIEW_FLOW_ID
    )
    first_flow = updater.build_target_flow(flow)
    assert updater.build_target_flow(first_flow) == first_flow


def test_target_step_preserves_platform_managed_knowledge_base_id() -> None:
    original = get_step(load_snapshot(), updater.CASE1_AUXILIARY_STEP_ID)
    original["stepDetailDTO"]["knowledgeBaseId"] = "70swx8wpNZ"
    other_metadata = copy.deepcopy(
        original["stepDetailDTO"]["scriptStepResourceList"]
    )

    target = updater.build_target_step(original)

    assert target["stepDetailDTO"]["knowledgeBaseId"] == "70swx8wpNZ"
    assert (
        target["stepDetailDTO"]["scriptStepResourceList"]
        == other_metadata
    )


def test_partial_step_marker_is_rejected_instead_of_silently_skipped() -> None:
    step = get_step(load_snapshot(), updater.CASE1_AUXILIARY_STEP_ID)
    detail = step["stepDetailDTO"]
    detail["llmPrompt"] += (
        "\n# 教师7月24日修改覆盖规则·病例一辅助检查先问后给（最高优先级）"
    )

    with pytest.raises(updater.PreflightError, match="半更新"):
        updater.build_target_step(step)


@pytest.mark.parametrize(
    "step_id,keep_field",
    [
        (updater.CASE3_INFO_STEP_ID, "prologue"),
        (updater.CASE3_AUXILIARY_STEP_ID, "llmPrompt"),
        (updater.CASE3_PAIRED_EXAM_STEP_ID, "llmPrompt"),
    ],
)
def test_case3_partial_two_field_updates_are_rejected(
    step_id: str,
    keep_field: str,
) -> None:
    original = get_step(load_snapshot(), step_id)
    target = updater.build_target_step(original)
    partial = copy.deepcopy(original)
    partial["stepDetailDTO"][keep_field] = target["stepDetailDTO"][keep_field]

    with pytest.raises(updater.PreflightError, match="半更新"):
        updater.build_target_step(partial)


def test_partial_flow_update_is_rejected_instead_of_silently_skipped() -> None:
    snapshot = load_snapshot()
    flow = next(
        item
        for item in snapshot["flows"]
        if item["flowId"] == updater.CASE2_INTERVIEW_FLOW_ID
    )
    flow["flowCondition"] = updater.CASE2_PATIENT_CLOSING

    with pytest.raises(updater.PreflightError, match="半更新"):
        updater.build_target_flow(flow)


def test_apply_aborts_if_live_snapshot_changes_after_backup(
    tmp_path: Path,
) -> None:
    class ConcurrentEditGateway(FakeGateway):
        def __init__(self, snapshot: dict) -> None:
            super().__init__(snapshot)
            self.export_count = 0

        def export_snapshot(self, task_id: str) -> dict:
            self.export_count += 1
            result = super().export_snapshot(task_id)
            if self.export_count == 2:
                result["configuration"]["description"] += "（他人刚修改）"
            return result

    gateway = ConcurrentEditGateway(load_snapshot())

    with pytest.raises(updater.PreflightError, match="导出备份后已发生变化"):
        updater.run_coronary_update(
            gateway,
            backup_dir=tmp_path,
            apply=True,
        )

    assert gateway.mutations == []


def test_plan_pairs_shuffled_score_items_by_item_id() -> None:
    snapshot = load_snapshot()
    snapshot["scoreItems"].reverse()

    plan = updater.build_update_plan(snapshot)

    assert all(
        item["current"]["itemId"] == item["target"]["itemId"]
        for item in plan["scoreItems"]
    )
