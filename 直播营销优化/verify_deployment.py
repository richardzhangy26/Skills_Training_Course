"""Fresh end-to-end verification for the live-marketing deployment."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skill_training_build import create_task_from_markdown as base


ROOT = Path(__file__).resolve().parent
TASKS = {
    "4ba83GPlOOu4JBjbedz6": (
        ROOT / "三农产品直播试播——走进田间地头" / "训练剧本配置.md",
        "eWU7FQ2Uam",
        "Tg6LpKo38D",
        "Za9I4Dx5Gw",
    ),
    "MRaAgyBN1PTJXV6oPxpZ": (
        ROOT / "服装穿搭直播试播——小个子女生专场" / "训练剧本配置.md",
        "wDBypVJ3u6",
        "TTS2cuBiT",
        "iL87nmUAwe",
    ),
    "GnxX4Q7Zg4cr0WNA4xq0": (
        ROOT / "生活好物混场直播试播——家庭清洁+厨房神器专场" / "训练剧本配置.md",
        "nWNqH57bKD",
        "TTS2cuBiI",
        "retztwDJCE",
    ),
}


def verify_task(task_id: str, config: Path, digital: str, voice: str, avatar: str) -> dict:
    local = base.parse_markdown(config)
    live_all = base.query_script_steps(task_id)
    live_business = base.get_business_script_steps(live_all)
    flows = base.query_script_step_flows(task_id)
    start_id, end_id = base.extract_start_end_ids(live_all)
    assert len(local) == len(live_business) == 8
    assert len(flows) == 9
    assert flows[0].get("scriptStepStartId") == start_id

    live_by_name = {
        item.get("stepDetailDTO", {}).get("stepName"): item for item in live_business
    }
    for stage in local:
        item = live_by_name.get(stage.get("stepName"))
        assert item is not None, stage.get("stepName")
        detail = item.get("stepDetailDTO") or {}
        cover = detail.get("scriptStepCover") or {}
        assert detail.get("llmPrompt") == stage.get("llmPrompt")
        assert detail.get("prologue") == stage.get("prologue")
        assert detail.get("interactiveRounds") == stage.get("interactiveRounds")
        assert detail.get("modelId") == "Doubao-Seed-1.6"
        assert detail.get("customDigitalHuman") == digital
        assert detail.get("agentId") == voice
        assert detail.get("avatarNid") == avatar
        assert cover.get("fileUrl") == stage.get("backgroundImage")
        assert cover.get("fileId")

    flow_by_start = {}
    for flow in flows:
        source = flow.get("scriptStepStartId")
        assert source not in flow_by_start
        flow_by_start[source] = flow
    stage_by_id = {item.get("stepId"): item for item in live_business}
    current = start_id
    names = []
    conditions = []
    for _ in range(9):
        flow = flow_by_start[current]
        conditions.append(str(flow.get("flowCondition") or ""))
        current = flow.get("scriptStepEndId")
        if current != end_id:
            names.append(stage_by_id[current].get("stepDetailDTO", {}).get("stepName"))
    assert current == end_id
    assert names == [stage.get("stepName") for stage in local]
    assert conditions == [""] + [str(stage.get("flowCondition") or "") for stage in local]

    logs = {}
    for profile in ("good", "medium"):
        log_dir = PROJECT_ROOT / "log" / f"task_{task_id}" / profile
        candidates = sorted(log_dir.glob("*_dialogue.json"))
        assert candidates, f"missing {task_id}/{profile} log"
        latest = candidates[-1]
        payload = json.loads(latest.read_text(encoding="utf-8"))
        metadata = payload.get("metadata") or {}
        stages = payload.get("stages") or []
        assert metadata.get("student_profile") == profile
        assert len(stages) == 8, (task_id, profile, len(stages), latest)
        logs[profile] = {
            "path": str(latest),
            "rounds": metadata.get("total_rounds"),
            "stages": len(stages),
        }

    backups = sorted((ROOT / "平台备份").glob(f"*/{task_id}.json"))
    receipts = sorted((ROOT / "平台备份").glob(f"*/{task_id}-deployment-receipt.json"))
    assert backups and receipts
    return {
        "taskId": task_id,
        "stages": len(local),
        "flows": len(flows),
        "startFirst": True,
        "contentMediaExact": True,
        "logs": logs,
        "backup": str(backups[-1]),
        "receipt": str(receipts[-1]),
    }


def main() -> None:
    base.load_env_config()
    results = [
        verify_task(task_id, config, digital, voice, avatar)
        for task_id, (config, digital, voice, avatar) in TASKS.items()
    ]
    print(json.dumps({"verified": True, "tasks": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
