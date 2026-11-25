"""Restore preserved scriptStepCover objects after a graph cutover."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path


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


def latest_backup(task_id: str) -> Path:
    candidates = sorted(
        path
        for path in (ROOT / "平台备份").glob(f"*/{task_id}.json")
        if not path.name.endswith("deployment-receipt.json")
    )
    if not candidates:
        raise RuntimeError(f"未找到备份: {task_id}")
    return candidates[-1]


def restore(task_id: str, config_path: Path) -> None:
    backup_path = latest_backup(task_id)
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
    cover_by_url = {}
    for item in backup.get("steps", []):
        cover = item.get("stepDetailDTO", {}).get("scriptStepCover") or {}
        url = str(cover.get("fileUrl") or "").strip()
        if url and cover.get("fileId"):
            cover_by_url[url] = cover

    local_steps = base.parse_markdown(config_path)
    live_steps = base.get_business_script_steps(base.query_script_steps(task_id))
    if len(local_steps) != 8 or len(live_steps) != 8:
        raise RuntimeError(f"节点数异常: local={len(local_steps)}, live={len(live_steps)}")

    for local, live in zip(local_steps, live_steps):
        background = str(local.get("backgroundImage") or "").strip()
        cover = cover_by_url.get(background)
        if not cover:
            raise RuntimeError(f"备份中未找到封面: {background}")
        payload = copy.deepcopy(live)
        payload["trainTaskId"] = task_id
        payload["stepId"] = live.get("stepId")
        payload["courseId"] = COURSE_ID
        payload.setdefault("stepDetailDTO", {})["scriptStepCover"] = copy.deepcopy(cover)
        if not base.edit_script_step(payload):
            raise RuntimeError(f"恢复封面失败: {local.get('stepName')}")

    refreshed = base.get_business_script_steps(base.query_script_steps(task_id))
    for local, live in zip(local_steps, refreshed):
        expected_url = str(local.get("backgroundImage") or "").strip()
        actual_cover = live.get("stepDetailDTO", {}).get("scriptStepCover") or {}
        if actual_cover.get("fileUrl") != expected_url or not actual_cover.get("fileId"):
            raise RuntimeError(f"封面回读失败: {local.get('stepName')}")
    print(f"✅ Covers restored and verified: {task_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", choices=sorted(TASKS), required=True)
    args = parser.parse_args()
    base.load_env_config()
    restore(args.task_id, TASKS[args.task_id])


if __name__ == "__main__":
    main()
