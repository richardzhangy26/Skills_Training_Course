"""批量导入精神分析流派训练剧本到 Polymas 平台。

从 Markdown 配置文件批量创建训练节点，自动匹配 PDF 资源到 knowledgeResourceList，
统一智能体人设，从"流派选择引导"路由节点分支出来。
"""

import os
import sys
import json
import copy
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from create_task_from_markdown import (
    parse_markdown,
    create_script_step,
    create_script_flow,
    upload_cover_image,
    is_remote_url,
    build_script_step_cover_from_url,
    load_env_config,
)

TRAIN_TASK_ID = "XBDgqJorLJU52N2MjdNO"
ROUTING_STEP_ID = "pbDQprZ2OrsYlGK5EaWL"
END_STEP_ID = "XBDgqJorLJUVPGeYXdNO"
KNOWLEDGE_BASE_ID = "b2gFtJz2LJ"

AGENT_CONFIG = {
    "agentId": "Tg2LpKo18D",
    "avatarNid": "tL1WGGJXZJ",
    "digitalHumanType": None,
    "projectId": "",
    "agentVoiceId": "zh_female_cancan_mars_bigtts",
    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
    "knowledgeBaseSwitch": 1,
}

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "skills_training_course" / "西南医科大学-临床心理检测与治疗" / "精神分析流派能力训练"
RESOURCE_JSON = BASE_DIR / "skills_training_course" / "西南医科大学-临床心理检测与治疗" / "资源库详情.json"

SCHOOLS = [
    {"name": "社会文化学派", "config_file": "1-经典分支/1.3-社会文化学派/社会文化学派训练剧本.md", "routing_condition": "PSYCHOANALYSIS_SOCIOCULTURAL"},
    {"name": "自体心理学", "config_file": "2-当代范式/2.1-自体心理学/自体心理学-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_SELF"},
    {"name": "主体间性精神分析", "config_file": "2-当代范式/2.2-主体间性精神分析/主体间性精神分析-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_INTERSUBJECTIVE"},
    {"name": "关系精神分析", "config_file": "2-当代范式/2.3-关系精神分析/关系精神分析-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_RELATIONAL"},
    {"name": "依恋精神分析", "config_file": "3-发展与应用/3.1-依恋精神分析/依恋精神分析-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_ATTACHMENT"},
    {"name": "创伤精神分析", "config_file": "3-发展与应用/3.3-创伤精神分析/创伤精神分析-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_TRAUMA"},
    {"name": "拉康学派", "config_file": "4-哲学与前沿/4.1-拉康学派/拉康学派-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_LACAN"},
    {"name": "存在主义精神分析", "config_file": "4-哲学与前沿/4.2-存在主义精神分析/存在主义精神分析-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_EXISTENTIAL"},
    {"name": "文化精神分析", "config_file": "4-哲学与前沿/4.3-文化精神分析/文化精神分析-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_CULTURAL"},
    {"name": "神经精神分析", "config_file": "4-哲学与前沿/4.4-神经精神分析/神经精神分析-训练剧本配置.md", "routing_condition": "PSYCHOANALYSIS_NEURO"},
]


def normalize_name(name):
    return name.replace(" ", "").replace("_", "").replace(":", "：").lower().strip()


def load_resource_map(json_path):
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    resource_map = {}
    for school in data.get("schools", []):
        for person in school.get("persons", []):
            for f in person.get("files", []):
                resource_map[f["fileName"]] = f
    normalized_map = {normalize_name(k): v for k, v in resource_map.items()}
    print(f"   资源文件总数: {len(resource_map)}")
    return resource_map, normalized_map


def build_knowledge_resource_list(pdf_names, resource_map, normalized_map):
    result = []
    matched = 0
    unmatched = []
    for idx, pdf_name in enumerate(pdf_names, start=1):
        entry = resource_map.get(pdf_name) or normalized_map.get(normalize_name(pdf_name))
        if not entry:
            unmatched.append(pdf_name)
            continue
        item = {
            "sort": idx,
            "fileId": entry["fileId"],
            "fileName": entry["fileName"],
            "fileUrl": entry["fileUrl"],
            "contentType": entry["contentType"],
            "type": "knowledge",
            "category": "知识库",
            "resourceTypeNid": "",
            "description": "",
            "thumbnail": "",
            "isRequired": 0,
        }
        result.append(item)
        matched += 1
    return result, matched, unmatched


def apply_agent_config(steps):
    for step in steps:
        step["agentId"] = AGENT_CONFIG["agentId"]
        step["avatarNid"] = AGENT_CONFIG["avatarNid"]
        step["agentVoiceId"] = AGENT_CONFIG["agentVoiceId"]
        step["digitalHumanType"] = AGENT_CONFIG["digitalHumanType"]
        step["projectId"] = AGENT_CONFIG["projectId"]
        step["knowledgeBaseId"] = AGENT_CONFIG["knowledgeBaseId"]
        step["knowledgeBaseSwitch"] = AGENT_CONFIG["knowledgeBaseSwitch"]


def process_background_images(steps, md_path, dry_run=False):
    global_cover = None
    for idx, step in enumerate(steps):
        bg = step.get("backgroundImage")
        if bg:
            if is_remote_url(bg):
                if not dry_run:
                    cover = build_script_step_cover_from_url(bg, existing_cover=step.get("scriptStepCover"))
                    step["scriptStepCover"] = cover
                    if idx == 0:
                        global_cover = cover
                else:
                    print(f"      阶段{idx+1} 背景图(URL): {bg[:60]}...")
            else:
                image_path = Path(bg)
                if not image_path.is_absolute():
                    image_path = (md_path.parent / image_path).resolve()
                if dry_run:
                    exists = "✅" if image_path.exists() else "❌"
                    print(f"      阶段{idx+1} 背景图: {exists} {image_path.name}")
                elif image_path.exists():
                    cover = upload_cover_image(image_path)
                    if cover:
                        step["scriptStepCover"] = cover
                        if idx == 0:
                            global_cover = cover
                    else:
                        print(f"      ⚠️ 背景图上传失败: {image_path.name}")
                else:
                    print(f"      ⚠️ 背景图不存在: {image_path}")
        elif idx > 0 and global_cover and not step.get("scriptStepCover") and not dry_run:
            step["scriptStepCover"] = global_cover


def import_school(school, resource_map, normalized_map, dry_run=False):
    school_name = school["name"]
    config_path = SCRIPTS_DIR / school["config_file"]
    routing_condition = school["routing_condition"]

    print(f"\n{'='*60}")
    print(f"📚 {school_name}  (路由: {routing_condition})")

    if not config_path.exists():
        print(f"   ❌ 配置文件不存在: {config_path}")
        return False

    steps = parse_markdown(config_path)
    if not steps:
        print(f"   ❌ 未解析到任何阶段")
        return False

    print(f"   阶段数: {len(steps)}")

    apply_agent_config(steps)

    total_matched = 0
    total_unmatched = 0
    for idx, step in enumerate(steps, start=1):
        pdf_names = step.get("knowledgeBasePDFs", [])
        if pdf_names:
            krl, matched, unmatched = build_knowledge_resource_list(pdf_names, resource_map, normalized_map)
            step["knowledgeResourceList"] = krl
            total_matched += matched
            total_unmatched += len(unmatched)
            status = f"✅ {matched}/{len(pdf_names)} PDF"
            if unmatched:
                status += f"  ❌ 未匹配: {', '.join(unmatched[:3])}"
            print(f"   阶段{idx} [{step.get('stepName', '?')}]: {status}")
        else:
            print(f"   阶段{idx} [{step.get('stepName', '?')}]: 无配套知识库")

    process_background_images(steps, config_path, dry_run=dry_run)

    if dry_run:
        print(f"   🧩 PDF总计: {total_matched} 匹配, {total_unmatched} 未匹配")
        return True

    print(f"\n   🚀 创建节点...")
    created_ids = []
    x_start = 500
    for idx, step in enumerate(steps):
        pos = {"x": x_start + (idx * 400), "y": 300}
        new_id = create_script_step(TRAIN_TASK_ID, step, pos)
        if new_id:
            created_ids.append(new_id)
        else:
            print(f"   ❌ 创建节点失败: {step.get('stepName')}")
            return False

    print(f"   🔗 创建连线...")
    print(f"      流派选择引导 -> {steps[0].get('stepName')} ({routing_condition})")
    if not create_script_flow(TRAIN_TASK_ID, ROUTING_STEP_ID, created_ids[0], routing_condition, ""):
        print(f"   ❌ 路由连线失败")
        return False

    for i in range(len(steps) - 1):
        condition = steps[i].get("flowCondition") or steps[i + 1].get("stepName", "下一步")
        transition = steps[i].get("transitionPrompt", "")
        print(f"      {steps[i].get('stepName')} -> {steps[i+1].get('stepName')} ({condition})")
        if not create_script_flow(TRAIN_TASK_ID, created_ids[i], created_ids[i + 1], condition, transition):
            print(f"   ❌ 阶段间连线失败")
            return False

    last_cond = steps[-1].get("flowCondition") or "TASK_COMPLETE"
    last_trans = steps[-1].get("transitionPrompt", "")
    print(f"      {steps[-1].get('stepName')} -> END ({last_cond})")
    if not create_script_flow(TRAIN_TASK_ID, created_ids[-1], END_STEP_ID, last_cond, last_trans):
        print(f"   ❌ 结束连线失败")
        return False

    print(f"   ✅ {school_name} 完成 ({len(steps)} 节点, {len(steps)+1} 连线)")
    return True


def main():
    parser = argparse.ArgumentParser(description="批量导入精神分析流派训练剧本")
    parser.add_argument("--dry-run", action="store_true", help="仅检查不实际创建")
    args = parser.parse_args()

    load_env_config()
    print("=" * 60)
    print("批量导入精神分析流派训练剧本")
    print(f"trainTaskId: {TRAIN_TASK_ID}")
    print(f"待导入流派: {len(SCHOOLS)} 个")
    if args.dry_run:
        print("🔍 DRY-RUN 模式")
    print("=" * 60)

    print(f"\n📖 加载资源库: {RESOURCE_JSON.name}")
    resource_map, normalized_map = load_resource_map(RESOURCE_JSON)

    success = 0
    fail = 0
    for school in SCHOOLS:
        try:
            if import_school(school, resource_map, normalized_map, dry_run=args.dry_run):
                success += 1
            else:
                fail += 1
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            fail += 1

    print(f"\n{'='*60}")
    print(f"完成: ✅ {success} 成功, ❌ {fail} 失败")


if __name__ == "__main__":
    main()
