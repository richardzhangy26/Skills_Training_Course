"""Safely cut over the three ordinary Polymas ability-training graphs."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from nanoid import generate

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skill_training_build import create_task_from_markdown as base


ROOT = Path(__file__).resolve().parent
COURSE_ID = "9VDE9334nvFZjWO2ZDjG"
TASKS = {
    "4ba83GPlOOu4JBjbedz6": ROOT / "三农产品直播试播——走进田间地头" / "训练剧本配置.md",
    "MRaAgyBN1PTJXV6oPxpZ": ROOT / "服装穿搭直播试播——小个子女生专场" / "训练剧本配置.md",
    "GnxX4Q7Zg4cr0WNA4xq0": ROOT / "生活好物混场直播试播——家庭清洁+厨房神器专场" / "训练剧本配置.md",
}


class DeployError(RuntimeError):
    pass


def is_success(payload: dict[str, Any]) -> bool:
    return payload.get("code") == 200 or payload.get("success") is True


def create_flow(
    task_id: str,
    start_id: str,
    end_id: str,
    condition: str,
    transition_prompt: str,
    *,
    is_default: int = 1,
) -> str:
    flow_id = generate(size=21)
    payload = {
        "trainTaskId": task_id,
        "flowId": flow_id,
        "scriptStepStartId": start_id,
        "scriptStepStartHandle": f"{start_id}-source-bottom",
        "scriptStepEndId": end_id,
        "scriptStepEndHandle": f"{end_id}-target-top",
        "flowSettingType": "quick",
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
        "transitionPrompt": transition_prompt,
        "transitionHistoryNum": base.DEFAULT_TRANSITION_HISTORY_NUM,
        "isDefault": is_default,
        "isError": False,
    }
    response = base.requests.post(
        base.ability_train_url("createScriptStepFlow"),
        headers=base.get_headers(),
        json=payload,
        timeout=20,
    )
    data = response.json()
    if not is_success(data):
        raise DeployError(f"创建连线失败 {start_id}->{end_id}: {data}")
    print(f"✅ Created flow: {start_id} -> {end_id} ({condition or 'START'})")
    return flow_id


def prepare_steps(
    config_path: Path, cover_by_url: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    steps = base.parse_markdown(config_path)
    if len(steps) != 8:
        raise DeployError(f"预期8个业务节点，实际解析到{len(steps)}个")
    if len({step.get("stepName") for step in steps}) != len(steps):
        raise DeployError("阶段名称存在重复")
    if steps[-1].get("flowCondition") != "训练完成":
        raise DeployError("最后阶段 flowCondition 必须为训练完成")

    base.resolve_steps_digital_humans(steps, config_path, course_id=COURSE_ID)
    for step in steps:
        background = str(step.get("backgroundImage") or "").strip()
        if background:
            if not base.is_remote_url(background):
                raise DeployError(f"背景图必须是已存在的远程URL: {background}")
            preserved_cover = cover_by_url.get(background)
            step["scriptStepCover"] = (
                copy.deepcopy(preserved_cover)
                if preserved_cover
                else base.build_script_step_cover_from_url(background)
            )
        if not step.get("customDigitalHuman"):
            raise DeployError(f"阶段缺少数字人: {step.get('stepName')}")
        if not step.get("llmPrompt") or "# Workflow & Interaction Rules" not in step["llmPrompt"]:
            raise DeployError(f"阶段提示词结构不完整: {step.get('stepName')}")
    return steps


def backup_task(
    task_id: str,
    config_path: Path,
    step_list: list[dict[str, Any]],
    flow_list: list[dict[str, Any]],
) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = ROOT / "平台备份" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    path = backup_dir / f"{task_id}.json"
    payload = {
        "taskId": task_id,
        "courseId": COURSE_ID,
        "configPath": str(config_path),
        "backupTime": datetime.now().isoformat(timespec="seconds"),
        "steps": step_list,
        "flows": flow_list,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 Backup: {path}")
    return path


def cleanup_new_graph(task_id: str, flow_ids: list[str], step_ids: list[str]) -> None:
    for flow_id in reversed(flow_ids):
        base.delete_script_step_flow(task_id, flow_id)
    for step_id in reversed(step_ids):
        base.delete_script_step(task_id, step_id)


def restore_start_flows(task_id: str, old_start_flows: list[dict[str, Any]]) -> None:
    for flow in old_start_flows:
        create_flow(
            task_id,
            flow["scriptStepStartId"],
            flow["scriptStepEndId"],
            str(flow.get("flowCondition") or ""),
            str(flow.get("transitionPrompt") or ""),
            is_default=int(flow.get("isDefault") or 1),
        )


def verify_graph(task_id: str, expected_steps: list[dict[str, Any]]) -> dict[str, Any]:
    live_steps = base.query_script_steps(task_id)
    live_flows = base.query_script_step_flows(task_id)
    start_id, end_id = base.extract_start_end_ids(live_steps)
    business = base.get_business_script_steps(live_steps)
    expected_names = [item.get("stepName") for item in expected_steps]
    if len(live_flows) != 9:
        raise DeployError(f"预期9条连线，实际{len(live_flows)}条")
    outgoing_start = [flow for flow in live_flows if flow.get("scriptStepStartId") == start_id]
    if len(outgoing_start) != 1:
        raise DeployError(f"START应只有1条出边，实际{len(outgoing_start)}条")

    expected_conditions = [""] + [str(step.get("flowCondition") or "") for step in expected_steps]
    start_keys = [flow.get("scriptStepStartId") for flow in live_flows]
    if len(set(start_keys)) != len(start_keys):
        raise DeployError("最终流程存在节点多条出边，不是单一线性链")
    actual_by_start = {flow.get("scriptStepStartId"): flow for flow in live_flows}
    name_by_id = {
        item.get("stepId"): item.get("stepDetailDTO", {}).get("stepName")
        for item in business
    }
    current = start_id
    traversed: list[str] = []
    traversed_names: list[str] = []
    actual_conditions: list[str] = []
    for _ in range(9):
        flow = actual_by_start.get(current)
        if not flow:
            raise DeployError(f"从节点{current}无法继续遍历")
        actual_conditions.append(str(flow.get("flowCondition") or ""))
        current = str(flow.get("scriptStepEndId") or "")
        traversed.append(current)
        if current != end_id:
            traversed_names.append(str(name_by_id.get(current) or ""))
    if current != end_id:
        raise DeployError(f"线性流程未到达END: {current} != {end_id}")
    if traversed_names != expected_names:
        raise DeployError(
            f"节点顺序/名称不一致: expected={expected_names}, actual={traversed_names}"
        )
    if actual_conditions != expected_conditions:
        raise DeployError(
            f"跳转条件不一致: expected={expected_conditions}, actual={actual_conditions}"
        )
    return {
        "businessStepCount": len(business),
        "flowCount": len(live_flows),
        "stepNames": traversed_names,
        "flowConditions": actual_conditions,
    }


def deploy_task(task_id: str, config_path: Path) -> dict[str, Any]:
    configured_course_id = str(base.os.getenv("COURSE_ID") or "").strip()
    if configured_course_id != COURSE_ID:
        raise DeployError(
            f"COURSE_ID不匹配：expected={COURSE_ID}, actual={configured_course_id}"
        )
    if task_id not in TASKS:
        raise DeployError(f"任务不在白名单: {task_id}")
    if not config_path.exists():
        raise DeployError(f"配置文件不存在: {config_path}")

    old_step_list = base.query_script_steps(task_id)
    old_flow_list = base.query_script_step_flows(task_id)
    cover_by_url: dict[str, dict[str, Any]] = {}
    for item in base.get_business_script_steps(old_step_list):
        cover = item.get("stepDetailDTO", {}).get("scriptStepCover") or {}
        file_url = str(cover.get("fileUrl") or "").strip()
        if file_url and cover.get("fileId"):
            cover_by_url[file_url] = copy.deepcopy(cover)
    new_steps = prepare_steps(config_path, cover_by_url)
    start_id, end_id = base.extract_start_end_ids(old_step_list)
    if not start_id or not end_id:
        raise DeployError("目标任务缺少START或END节点")
    old_business = base.get_business_script_steps(old_step_list)
    if not old_business:
        raise DeployError("目标任务当前没有业务节点，停止自动切换")
    backup_path = backup_task(task_id, config_path, old_step_list, old_flow_list)

    new_step_ids: list[str] = []
    new_flow_ids: list[str] = []
    cutover_started = False
    old_start_flows = [
        flow for flow in old_flow_list if flow.get("scriptStepStartId") == start_id
    ]
    if len(old_start_flows) != 1:
        raise DeployError(f"切换前START应只有1条出边，实际{len(old_start_flows)}条")

    try:
        for index, step_data in enumerate(new_steps):
            step_id = base.create_script_step(
                task_id,
                step_data,
                {"x": 100 + index * 400, "y": 650},
            )
            if not step_id:
                raise DeployError(f"创建节点失败: {step_data.get('stepName')}")
            new_step_ids.append(step_id)

        for index in range(len(new_steps) - 1):
            new_flow_ids.append(
                create_flow(
                    task_id,
                    new_step_ids[index],
                    new_step_ids[index + 1],
                    str(new_steps[index].get("flowCondition") or ""),
                    str(new_steps[index].get("transitionPrompt") or ""),
                )
            )
        new_flow_ids.append(
            create_flow(
                task_id,
                new_step_ids[-1],
                end_id,
                str(new_steps[-1].get("flowCondition") or "训练完成"),
                str(new_steps[-1].get("transitionPrompt") or ""),
            )
        )

        live_step_ids = {item.get("stepId") for item in base.query_script_steps(task_id)}
        live_flow_ids = {item.get("flowId") for item in base.query_script_step_flows(task_id)}
        if not set(new_step_ids).issubset(live_step_ids) or not set(new_flow_ids).issubset(live_flow_ids):
            raise DeployError("新图预创建后回读不完整，未执行切换")

        cutover_started = True
        for flow in old_start_flows:
            if not base.delete_script_step_flow(task_id, flow["flowId"]):
                raise DeployError("删除旧START出边失败")
        try:
            start_flow_id = create_flow(task_id, start_id, new_step_ids[0], "", "")
            new_flow_ids.append(start_flow_id)
        except Exception:
            restore_start_flows(task_id, old_start_flows)
            raise

        for flow in old_flow_list:
            if flow.get("flowId") in {item.get("flowId") for item in old_start_flows}:
                continue
            if not base.delete_script_step_flow(task_id, flow["flowId"]):
                raise DeployError(f"删除旧连线失败: {flow.get('flowId')}")
        for item in old_business:
            if not base.delete_script_step(task_id, item["stepId"]):
                raise DeployError(f"删除旧节点失败: {item.get('stepId')}")

        # queryScriptStepFlowList preserves creation order, and the ordinary
        # workflow tester treats data[0] as the START edge. Recreate the final
        # graph in traversal order so every runtime enters stage 1 reliably.
        for flow_id in list(new_flow_ids):
            if not base.delete_script_step_flow(task_id, flow_id):
                raise DeployError(f"重排前删除新连线失败: {flow_id}")
        new_flow_ids = [create_flow(task_id, start_id, new_step_ids[0], "", "")]
        for index in range(len(new_steps) - 1):
            new_flow_ids.append(
                create_flow(
                    task_id,
                    new_step_ids[index],
                    new_step_ids[index + 1],
                    str(new_steps[index].get("flowCondition") or ""),
                    str(new_steps[index].get("transitionPrompt") or ""),
                )
            )
        new_flow_ids.append(
            create_flow(
                task_id,
                new_step_ids[-1],
                end_id,
                str(new_steps[-1].get("flowCondition") or "训练完成"),
                str(new_steps[-1].get("transitionPrompt") or ""),
            )
        )

        verification = verify_graph(task_id, new_steps)
        receipt = {
            "taskId": task_id,
            "configPath": str(config_path),
            "backupPath": str(backup_path),
            "deployedAt": datetime.now().isoformat(timespec="seconds"),
            "verification": verification,
        }
        receipt_path = backup_path.parent / f"{task_id}-deployment-receipt.json"
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✅ Deployment verified: {task_id}")
        print(f"🧾 Receipt: {receipt_path}")
        return receipt
    except Exception:
        if not cutover_started:
            cleanup_new_graph(task_id, new_flow_ids, new_step_ids)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", choices=sorted(TASKS), required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base.load_env_config()
    receipt = deploy_task(args.task_id, TASKS[args.task_id])
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
