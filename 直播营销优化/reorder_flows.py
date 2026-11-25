"""Recreate a verified linear graph so the START edge is flowList[0]."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from skill_training_build import create_task_from_markdown as base
from deploy_configs import TASKS, create_flow


def ordered_chain(task_id: str) -> tuple[str, str, list[dict]]:
    steps = base.query_script_steps(task_id)
    flows = base.query_script_step_flows(task_id)
    start_id, end_id = base.extract_start_end_ids(steps)
    if not start_id or not end_id or len(flows) != 9:
        raise RuntimeError("流程不是预期的8节点9连线结构")
    by_start = {}
    for flow in flows:
        key = flow.get("scriptStepStartId")
        if key in by_start:
            raise RuntimeError(f"节点存在多条出边: {key}")
        by_start[key] = flow
    chain = []
    current = start_id
    for _ in range(9):
        flow = by_start.get(current)
        if not flow:
            raise RuntimeError(f"线性流程断开: {current}")
        chain.append(flow)
        current = flow.get("scriptStepEndId")
    if current != end_id:
        raise RuntimeError("流程未到达END")
    return start_id, end_id, chain


def recreate(task_id: str, chain: list[dict]) -> None:
    for flow in base.query_script_step_flows(task_id):
        if not base.delete_script_step_flow(task_id, flow["flowId"]):
            raise RuntimeError(f"删除连线失败: {flow.get('flowId')}")
    for flow in chain:
        create_flow(
            task_id,
            flow["scriptStepStartId"],
            flow["scriptStepEndId"],
            str(flow.get("flowCondition") or ""),
            str(flow.get("transitionPrompt") or ""),
            is_default=int(flow.get("isDefault") or 1),
        )


def verify_order(task_id: str, start_id: str, chain: list[dict]) -> None:
    live = base.query_script_step_flows(task_id)
    if len(live) != len(chain):
        raise RuntimeError(f"连线数异常: {len(live)}")
    if live[0].get("scriptStepStartId") != start_id:
        raise RuntimeError("flowList第一条仍不是START出边")
    expected = [
        (flow.get("scriptStepStartId"), flow.get("scriptStepEndId"), flow.get("flowCondition") or "")
        for flow in chain
    ]
    actual = [
        (flow.get("scriptStepStartId"), flow.get("scriptStepEndId"), flow.get("flowCondition") or "")
        for flow in live
    ]
    if actual != expected:
        raise RuntimeError(f"flowList顺序不一致: {actual}")
    print(f"✅ START-first flow order verified: {task_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", choices=sorted(TASKS), required=True)
    args = parser.parse_args()
    base.load_env_config()
    start_id, _, chain = ordered_chain(args.task_id)
    recreate(args.task_id, chain)
    verify_order(args.task_id, start_id, chain)


if __name__ == "__main__":
    main()
