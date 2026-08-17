import argparse
import copy
import json
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PLATFORM_METADATA_FIELDS = (
    "scriptStepCover",
    "scriptStepResourceList",
    "knowledgeBaseSwitch",
    "knowledgeBaseId",
    "searchEngineSwitch",
    "whiteBoardSwitch",
    "videoSwitch",
    "historyRecordNum",
    "agentVoiceId",
    "digitalHumanType",
    "projectId",
    "stepExtProperty",
    "backgroundTheme",
    "transitionDescriptionUrl",
    "customDigitalHuman",
    "knowledgeResourceList",
    "trainTime",
    "isSkipStep",
    "endStrategy",
    "refResourceDesc",
    "isTransition",
)


def load_api_data(path: Path) -> List[Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    data = raw.get("data") if isinstance(raw, dict) else raw
    if not isinstance(data, list):
        raise ValueError(f"{path} 中未找到 data 列表")
    return data


def detail(step: Dict[str, Any]) -> Dict[str, Any]:
    return step.get("stepDetailDTO", {})


def validate_linear_flow(
    steps: List[Dict[str, Any]],
    flows: List[Dict[str, Any]],
) -> List[str]:
    by_id = {step.get("stepId"): step for step in steps}
    if len(by_id) != len(steps):
        raise ValueError("剧本.json 中存在重复 stepId")

    start_ids = [
        step["stepId"]
        for step in steps
        if detail(step).get("nodeType") == "SCRIPT_START"
    ]
    end_ids = [
        step["stepId"]
        for step in steps
        if detail(step).get("nodeType") == "SCRIPT_END"
    ]
    if len(start_ids) != 1 or len(end_ids) != 1:
        raise ValueError(f"START/END 数量异常: START={len(start_ids)}, END={len(end_ids)}")

    outgoing: Dict[str, List[Dict[str, Any]]] = {}
    incoming: Dict[str, List[Dict[str, Any]]] = {}
    for flow in flows:
        start_id = flow.get("scriptStepStartId")
        end_id = flow.get("scriptStepEndId")
        if start_id not in by_id or end_id not in by_id:
            raise ValueError(f"连线引用了未知节点: {start_id} -> {end_id}")
        outgoing.setdefault(start_id, []).append(flow)
        incoming.setdefault(end_id, []).append(flow)

    start_id = start_ids[0]
    end_id = end_ids[0]
    for step_id, step in by_id.items():
        expected_out = 0 if step_id == end_id else 1
        expected_in = 0 if step_id == start_id else 1
        actual_out = len(outgoing.get(step_id, []))
        actual_in = len(incoming.get(step_id, []))
        name = detail(step).get("stepName", "未命名节点")
        if actual_out != expected_out:
            raise ValueError(f"节点出边数量异常: {name}({step_id}) out={actual_out}")
        if actual_in != expected_in:
            raise ValueError(f"节点入边数量异常: {name}({step_id}) in={actual_in}")

    chain = []
    current = start_id
    seen = set()
    while True:
        if current in seen:
            raise ValueError(f"流程存在环: {current}")
        seen.add(current)
        chain.append(current)
        if current == end_id:
            break
        current = outgoing[current][0]["scriptStepEndId"]

    if len(seen) != len(steps):
        orphan_ids = sorted(set(by_id) - seen)
        raise ValueError(f"存在无法从 START 到达的孤立节点: {', '.join(orphan_ids)}")

    return chain


def is_zero_round_liuchang(step: Dict[str, Any]) -> bool:
    step_detail = detail(step)
    return (
        step_detail.get("trainerName") == "刘畅"
        and step_detail.get("interactiveRounds") == 0
    )


def is_zero_round_answer(step: Dict[str, Any], trainer_name: str) -> bool:
    step_detail = detail(step)
    return (
        trainer_name != "刘畅"
        and step_detail.get("trainerName") == trainer_name
        and step_detail.get("interactiveRounds") == 0
    )


def merge_prologues(source_steps: List[Dict[str, Any]]) -> str:
    prologues = [detail(step).get("prologue", "").strip() for step in source_steps]
    return "\n\n".join(prologue for prologue in prologues if prologue)


def merge_zero_round_steps(
    business_step_ids: List[str],
    by_id: Dict[str, Dict[str, Any]],
    outgoing_by_start: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    merged_entries = []
    merge_groups = []
    idx = 0

    while idx < len(business_step_ids):
        step_id = business_step_ids[idx]
        step = by_id[step_id]

        if is_zero_round_liuchang(step):
            merged_entries.append(
                {
                    "step": copy.deepcopy(step),
                    "sourceStepIds": [step_id],
                    "outgoingFlow": outgoing_by_start.get(step_id),
                    "merged": False,
                }
            )

            next_idx = idx + 1
            group_ids: List[str] = []
            if next_idx < len(business_step_ids):
                next_step = by_id[business_step_ids[next_idx]]
                answer_trainer = detail(next_step).get("trainerName", "")
                while next_idx < len(business_step_ids):
                    candidate_id = business_step_ids[next_idx]
                    candidate_step = by_id[candidate_id]
                    if not is_zero_round_answer(candidate_step, answer_trainer):
                        break
                    group_ids.append(candidate_id)
                    next_idx += 1

            if group_ids:
                source_steps = [by_id[source_id] for source_id in group_ids]
                merged_step = copy.deepcopy(source_steps[0])
                detail(merged_step)["prologue"] = merge_prologues(source_steps)
                merged_entries.append(
                    {
                        "step": merged_step,
                        "sourceStepIds": group_ids,
                        "outgoingFlow": outgoing_by_start.get(group_ids[-1]),
                        "merged": len(group_ids) > 1,
                        "triggerStepId": step_id,
                    }
                )
                if len(group_ids) > 1:
                    merge_groups.append(
                        {
                            "triggerStepId": step_id,
                            "triggerStepName": detail(step).get("stepName", ""),
                            "trainerName": detail(source_steps[0]).get("trainerName", ""),
                            "sourceStepIds": group_ids,
                            "keptStepId": group_ids[0],
                            "removedStepIds": group_ids[1:],
                        }
                    )
                idx = next_idx
                continue

            idx += 1
            continue

        merged_entries.append(
            {
                "step": copy.deepcopy(step),
                "sourceStepIds": [step_id],
                "outgoingFlow": outgoing_by_start.get(step_id),
                "merged": False,
            }
        )
        idx += 1

    return merged_entries, merge_groups


def inline_json_string(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def code_block(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    return f"```\n{text}\n```"


def get_cover_file_url(step_detail: Dict[str, Any]) -> str:
    cover = step_detail.get("scriptStepCover")
    if isinstance(cover, dict):
        return cover.get("fileUrl") or ""
    return ""


def safe_filename_part(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", value)
    return value.strip("_") or "step"


def infer_image_suffix(url: str, content_type: str = "") -> str:
    path = urllib.parse.urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return suffix
    content_type_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    return content_type_map.get(content_type.lower(), ".png")


def download_background_images(
    entries: List[Dict[str, Any]],
    image_dir: Path,
    markdown_path: Path,
) -> Dict[str, str]:
    image_dir.mkdir(parents=True, exist_ok=True)
    local_paths = {}
    url_to_local_path = {}

    for idx, entry in enumerate(entries, start=1):
        step = entry["step"]
        step_detail = detail(step)
        cover = step_detail.get("scriptStepCover") if isinstance(step_detail.get("scriptStepCover"), dict) else {}
        file_url = cover.get("fileUrl") or ""
        if not file_url:
            continue

        if file_url in url_to_local_path:
            local_paths[step["stepId"]] = url_to_local_path[file_url]
            continue

        suffix = infer_image_suffix(file_url, cover.get("contentType") or "")
        filename = f"stage_{idx:02d}_{safe_filename_part(step['stepId'])}{suffix}"
        target_path = image_dir / filename
        with urllib.request.urlopen(file_url, timeout=30) as response:
            with target_path.open("wb") as target_file:
                shutil.copyfileobj(response, target_file)

        relative_path = target_path.relative_to(markdown_path.parent).as_posix()
        local_paths[step["stepId"]] = relative_path
        url_to_local_path[file_url] = relative_path
        print(f"已下载背景图: {relative_path}")

    return local_paths


def format_markdown(
    entries: List[Dict[str, Any]],
    background_paths: Optional[Dict[str, str]] = None,
) -> str:
    background_paths = background_paths or {}
    sections = []
    for idx, entry in enumerate(entries, start=1):
        step = entry["step"]
        step_detail = detail(step)
        flow = entry.get("outgoingFlow") or {}
        background_image = background_paths.get(step.get("stepId")) or get_cover_file_url(step_detail)
        sections.append(
            "\n".join(
                [
                    f"### 阶段{idx}: {step_detail.get('stepName', '')}",
                    f"**Step ID**: {step.get('stepId', '')}",
                    f"**虚拟训练官名字**: {step_detail.get('trainerName', '')}",
                    f"**模型**: {step_detail.get('modelId', '')}",
                    f"**声音**: {step_detail.get('agentId') or ''}",
                    f"**形象**: {step_detail.get('avatarNid') or ''}",
                    f"**阶段描述**: {step_detail.get('description', '')}",
                    f"**背景图**: {background_image}",
                    f"**互动轮次**: {step_detail.get('interactiveRounds', 0)}轮",
                    "**开场白**:",
                    code_block(step_detail.get("prologue", "")),
                    "**提示词**:",
                    code_block(step_detail.get("llmPrompt", "")),
                    f"**flowCondition**: {inline_json_string(flow.get('flowCondition', ''))}",
                    "**transitionPrompt**:",
                    code_block(flow.get("transitionPrompt", "")),
                ]
            )
        )
    return "\n\n".join(sections) + "\n"


def extract_metadata(entry: Dict[str, Any]) -> Dict[str, Any]:
    step_detail = detail(entry["step"])
    return {
        field: copy.deepcopy(step_detail[field])
        for field in PLATFORM_METADATA_FIELDS
        if field in step_detail
    }


def build_resources_json(
    entries: List[Dict[str, Any]],
    script_json_path: Path,
    flow_json_path: Path,
) -> Dict[str, Any]:
    return {
        "version": 1,
        "sourceScriptJson": str(script_json_path),
        "sourceFlowJson": str(flow_json_path),
        "metadataFields": list(PLATFORM_METADATA_FIELDS),
        "steps": [
            {
                "originalStepId": entry["step"].get("stepId", ""),
                "stepName": detail(entry["step"]).get("stepName", ""),
                "sourceStepIds": entry["sourceStepIds"],
                "metadata": extract_metadata(entry),
            }
            for entry in entries
        ],
    }


def format_dry_run_markdown(
    original_business_count: int,
    entries: List[Dict[str, Any]],
    merge_groups: List[Dict[str, Any]],
) -> str:
    removed_count = original_business_count - len(entries)
    lines = [
        "# 湖南科技大学新闻采访 0 轮卡片合并 dry-run",
        "",
        f"- 原业务节点数: {original_business_count}",
        f"- 合并后业务节点数: {len(entries)}",
        f"- 删除等效冗余节点数: {removed_count}",
        f"- 合并组数: {len(merge_groups)}",
        "",
        "## 合并组",
        "",
    ]
    for idx, group in enumerate(merge_groups, start=1):
        lines.extend(
            [
                f"### 合并组 {idx}",
                f"- 触发节点: {group['triggerStepName']} ({group['triggerStepId']})",
                f"- 回答人: {group['trainerName']}",
                f"- 合并数量: {len(group['sourceStepIds'])} -> 1",
                f"- 保留节点: {group['keptStepId']}",
                f"- 删除节点: {', '.join(group['removedStepIds'])}",
                "",
            ]
        )

    lines.extend(["## 合并后顺序", "", "| 序号 | Step ID | 训练官 | 轮次 | 阶段名称 | 来源节点数 |", "|---:|---|---|---:|---|---:|"])
    for idx, entry in enumerate(entries, start=1):
        step = entry["step"]
        step_detail = detail(step)
        lines.append(
            "| {idx} | {step_id} | {trainer} | {rounds} | {name} | {count} |".format(
                idx=idx,
                step_id=step.get("stepId", ""),
                trainer=step_detail.get("trainerName", ""),
                rounds=step_detail.get("interactiveRounds", 0),
                name=step_detail.get("stepName", "").replace("|", "\\|"),
                count=len(entry["sourceStepIds"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="合并刘畅 0 轮提问后的连续同人 0 轮回答卡片")
    parser.add_argument("script_json", type=Path, help="平台 queryScriptStepList 导出的剧本.json")
    parser.add_argument("flow_json", type=Path, help="平台 queryScriptStepFlowList 导出的 scriptstepflow.json")
    parser.add_argument("--output-md", type=Path, help="合并后的训练剧本配置 Markdown")
    parser.add_argument("--dry-run-md", type=Path, help="合并 dry-run 报告 Markdown")
    parser.add_argument("--resources-json", type=Path, help="保留节点平台资源 metadata JSON")
    parser.add_argument(
        "--download-background-images",
        action="store_true",
        help="下载 scriptStepCover.fileUrl 到本地，并在 Markdown 背景图字段写入相对路径",
    )
    parser.add_argument(
        "--background-image-dir",
        type=Path,
        help="背景图下载目录，默认写入输出 Markdown 同级 background_images/",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_json_path = args.script_json
    flow_json_path = args.flow_json
    output_dir = script_json_path.parent
    output_md = args.output_md or output_dir / "训练剧本配置_合并0轮.md"
    dry_run_md = args.dry_run_md or output_dir / "训练剧本配置_合并0轮_dry_run.md"
    resources_json = args.resources_json or output_dir / "训练剧本配置_合并0轮.resources.json"

    steps = load_api_data(script_json_path)
    flows = load_api_data(flow_json_path)
    chain = validate_linear_flow(steps, flows)
    by_id = {step["stepId"]: step for step in steps}
    outgoing_by_start = {flow["scriptStepStartId"]: flow for flow in flows}
    business_step_ids = [
        step_id
        for step_id in chain
        if detail(by_id[step_id]).get("nodeType") == "SCRIPT_NODE"
    ]

    entries, merge_groups = merge_zero_round_steps(business_step_ids, by_id, outgoing_by_start)
    background_paths = {}
    if args.download_background_images:
        image_dir = args.background_image_dir or output_md.parent / "background_images"
        background_paths = download_background_images(entries, image_dir, output_md)

    output_md.write_text(format_markdown(entries, background_paths=background_paths), encoding="utf-8")
    dry_run_md.write_text(
        format_dry_run_markdown(len(business_step_ids), entries, merge_groups),
        encoding="utf-8",
    )
    resources_json.write_text(
        json.dumps(build_resources_json(entries, script_json_path, flow_json_path), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    removed_count = len(business_step_ids) - len(entries)
    print(f"原业务节点数: {len(business_step_ids)}")
    print(f"合并后业务节点数: {len(entries)}")
    print(f"删除等效冗余节点数: {removed_count}")
    print(f"合并组数: {len(merge_groups)}")
    for group in merge_groups:
        print(f"- {group['trainerName']}: {len(group['sourceStepIds'])} -> 1 ({group['keptStepId']})")
    print(f"已输出: {output_md}")
    print(f"已输出: {dry_run_md}")
    print(f"已输出: {resources_json}")


if __name__ == "__main__":
    main()
