#!/usr/bin/env python3
"""将一个已搭建的能力训练剧本按模块拆分为多个独立剧本并导入到新任务。

直接读取平台导出的 JSON（queryScriptStepList / queryScriptStepFlowList /
queryScoreItemList），按模块切分子图，重映射节点/连线 ID、重编号关卡名、
重写开场白与结束语、转换附件资源的读写形状，然后调接口在新任务中重建。

南理工示例分组：
  基础剧本 = 关卡1/2/3（封装/构造析构/组合）       —— 保留关卡二/三自选分支
  进阶剧本 = 关卡4/5/6（继承/多态/静态成员）→ 一/二/三
  高级剧本 = 关卡7/8 + 核心代码提交准备（模板/文件IO/综合实战）→ 一/二

用法：
  # 1) 干跑，核对结构，不调任何接口
  python split_script_into_tasks.py --dry-run

  # 2) 资源挂载探针：把关卡1.1克隆进一个目标任务，验证附件能挂上
  python split_script_into_tasks.py --probe <TASK_ID>

  # 3) 正式导入（每组一个已建好的空任务）
  python split_script_into_tasks.py --import \
      --basic <TASK_ID> --advanced <TASK_ID> --senior <TASK_ID>
  # 加 --no-scores 可跳过评分项写入
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

import requests
from nanoid import generate

# 复用 create_task_from_markdown 里已验证的接口封装
sys.path.insert(0, str(Path(__file__).parent))
from create_task_from_markdown import (  # noqa: E402
    ability_train_url,
    create_start_end_nodes,
    delete_script_step,
    delete_script_step_flow,
    edit_script_step,
    get_headers,
    load_env_config,
    query_script_step_flows,
    query_script_steps,
)
from create_score_items_from_rubric import create_score_item  # noqa: E402

# --- 常量 ---

DEFAULT_SOURCE_DIR = (
    Path(__file__).parent.parent
    / "skills_training_course"
    / "南京理工大学-程序设计基础"
)
SOURCE_COURSE_ID = "VPDz2K1XLYu5N2p8ODjZ"

CN = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八"}
CN2NUM = {v: k for k, v in CN.items()}

EMPTY_FLOW_CFG = {
    "relation": "and",
    "conditions": [
        {"text": "条件组1", "relation": "and", "conditions": [{"text": ""}]}
    ],
}

# 进阶/高级剧本首关重写的开场白（在原文基础上重编号并加篇章框定语）
ADVANCED_OPENING = (
    "欢迎来到进阶篇，新兵！基础篇你已为帝国筑牢封装、构造与析构、对象组合三大根基。"
    "从这一关起，我们攀登面向对象的进阶机制。\n\n"
    "关卡一·血脉传承：帝国战场上，每个单位都共享相同的根基——坐标、所属玩家、可见状态。"
    "战士和农人都会移动、都有血量，但战士巡逻、农人采集；野兽则同时拥有移动、资源与血量三种能力。"
    "聪明的架构师不重写代码，而是提取共同根基为祖先，让派生类各承其责。这，就是继承。"
)
SENIOR_OPENING = (
    "欢迎来到高级篇，新兵！封装、继承、多态你已尽数掌握，如今直面 C++ 最锋利的两把利器——泛型与持久化。\n\n"
    "关卡一·同模异质：兵器库里散落着为步兵、弓手、骑兵分别打造的计数牌，每一块只能统计一种兵种。"
    "铁匠怨声载道，斥候嫌代码臃肿，直到一位老工匠刻出一块『万能计数牌』——这，就是模板。"
)

GROUPS = {
    "基础": {
        "modules": [1, 2, 3],
        "special": ["选择关卡二或关卡三", "是否挑战过关卡三", "是否挑战过关卡二"],
        "renumber": {1: 1, 2: 2, 3: 3},
        "first_header_prefix": "关卡一：",
        "opening": None,  # 保留原「欢迎成为帝国时代的程序员」大开场
        "closing": (
            "基础篇到此结束——封装、构造与析构、对象成员与组合，三大根基你已全部通关。"
            "整顿行装，进阶篇的战场正在等你。"
        ),
        "scores": ["封装与类设计能力", "构造与析构机制掌握"],
    },
    "进阶": {
        "modules": [4, 5, 6],
        "special": [],
        "renumber": {4: 1, 5: 2, 6: 3},
        "first_header_prefix": "关卡四：",
        "opening": ADVANCED_OPENING,
        "closing": (
            "进阶篇到此结束——继承、多态、静态成员，面向对象的进阶机制你已尽数掌握。"
            "下一站，高级篇的模板与文件I/O。"
        ),
        "scores": ["继承体系设计与应用", "多态与虚函数机制", "静态成员与资源管理"],
    },
    "高级": {
        "modules": [7, 8],
        "special": ["核心代码提交准备"],
        "renumber": {7: 1, 8: 2},
        "first_header_prefix": "关卡七：",
        "opening": SENIOR_OPENING,
        "closing": None,  # 保留「核心代码提交准备 → END」原收尾（综合实战收口）
        "scores": ["模板编程与泛型设计", "文件IO与数据持久化", "综合实战：AI对战系统实现"],
    },
}


# --- 源数据加载 ---


def load_source(source_dir):
    sd = Path(source_dir)
    nodes = json.loads((sd / "queryscriptsteplist.json").read_text(encoding="utf-8"))["data"]
    flows = json.loads((sd / "queryscriptstepflowlist.json").read_text(encoding="utf-8"))["data"]
    score_path = sd / "queryscoreitemlist.json"
    scores = []
    if score_path.exists():
        scores = json.loads(score_path.read_text(encoding="utf-8"))["data"]
    return nodes, flows, scores


def detail_of(node):
    return node.get("stepDetailDTO", {})


def is_business(node):
    return detail_of(node).get("nodeType") == "SCRIPT_NODE"


def module_of(step_name):
    """从节点名解析所属模块号（1-8）；非模块节点返回 None。"""
    m = re.match(r"关卡([1-8])\.", step_name)
    if m:
        return int(m.group(1))
    m = re.match(r"关卡([一二三四五六七八])[：:]", step_name)
    if m:
        return CN2NUM[m.group(1)]
    return None


def renumber_name(step_name, rmap):
    m = re.match(r"(关卡)([1-8])(\..*)", step_name, re.S)
    if m:
        new = rmap.get(int(m.group(2)), int(m.group(2)))
        return f"关卡{new}{m.group(3)}"
    m = re.match(r"(关卡)([一二三四五六七八])([：:].*)", step_name, re.S)
    if m:
        old = CN2NUM[m.group(2)]
        new = rmap.get(old, old)
        return f"关卡{CN[new]}{m.group(3)}"
    return step_name


def is_header_name(step_name):
    return bool(re.match(r"关卡[一二三四五六七八][：:]", step_name))


# --- 资源读写形状转换 ---


def convert_resources(script_step_resource_list, new_task_id, new_step_id):
    """把读接口的 scriptStepResourceList 转成写接口的 stepExtProperty.resources。"""
    srl = script_step_resource_list or []
    groups = {}
    order = []
    for r in srl:
        if not r.get("fileId"):
            continue  # 跳过占位空资源（部分 header 节点）
        nid = r.get("resourceTypeNid") or r.get("nid") or "default"
        cat = r.get("category") or "未分类"
        key = (nid, cat)
        if key not in groups:
            groups[key] = {"nid": nid, "category": cat, "list": []}
            order.append(key)
        groups[key]["list"].append(
            {
                "type": r.get("type", "resource"),
                "fileId": r.get("fileId"),
                "fileName": r.get("fileName"),
                "thumbnail": r.get("thumbnail", ""),
                "fileUrl": r.get("fileUrl"),
                "isRequired": bool(r.get("isRequired")),
                "description": r.get("description", ""),
                "trainTaskId": new_task_id,
                "scriptStepId": new_step_id,
                "sort": r.get("sort"),
                "scriptStepResourceId": generate(size=20),
            }
        )
    return [groups[k] for k in order]


def build_clone_detail(src_detail, new_step_id, new_task_id, rmap, opening_override):
    """从源 stepDetailDTO 构造写接口（editScriptStep）所需的全量 detail。"""
    d = copy.deepcopy(src_detail)
    old_name = d.get("stepName", "")
    d["stepName"] = renumber_name(old_name, rmap)

    if opening_override:
        d["prologue"] = opening_override
    elif is_header_name(old_name):
        old_mod = module_of(old_name)
        new_mod = rmap.get(old_mod, old_mod)
        if old_mod != new_mod:
            d["prologue"] = (d.get("prologue", "") or "").replace(
                f"关卡{CN[old_mod]}", f"关卡{CN[new_mod]}"
            )

    # 资源：顶层 scriptStepResourceList（读形状）才是真正驱动附件绑定的字段，
    # 必须保留并重映射 task/step；scriptStepResourceId 置空让平台分配新绑定。
    # 同时把写形状塞进 stepExtProperty.resources，供编辑器界面展示。
    src_srl = d.get("scriptStepResourceList") or []
    remapped = []
    for r in src_srl:
        if not r.get("fileId"):
            continue
        nr = copy.deepcopy(r)
        nr["trainTaskId"] = new_task_id
        nr["scriptStepId"] = new_step_id
        nr.pop("scriptStepResourceId", None)
        remapped.append(nr)
    d["scriptStepResourceList"] = remapped
    ext = copy.deepcopy(d.get("stepExtProperty") or {})
    ext["resources"] = convert_resources(src_srl, new_task_id, new_step_id)
    d["stepExtProperty"] = ext

    # 对齐 editScriptStep 载荷形状
    if (d.get("scriptStepCover") or {}).get("fileUrl"):
        d.setdefault("scriptBackgroundType", "image")
    d.setdefault("contentSkip", 0)
    d.pop("createTime", None)
    d.pop("updateTime", None)
    return d


# --- 接口封装 ---


def create_script_node_min(task_id, course_id, step_id, src_detail, rmap):
    """最小创建 SCRIPT_NODE（固定 stepId），随后由 editScriptStep 补全。"""
    url = ability_train_url("createScriptStep")
    payload = {
        "trainTaskId": task_id,
        "stepId": step_id,
        "stepDetailDTO": {
            "nodeType": "SCRIPT_NODE",
            "stepName": renumber_name(src_detail.get("stepName", ""), rmap),
            "description": src_detail.get("description", ""),
            "prologue": "",
            "modelId": src_detail.get("modelId") or "Doubao-Seed-1.6",
            "llmPrompt": "",
            "trainerName": src_detail.get("trainerName", ""),
            "interactiveRounds": src_detail.get("interactiveRounds", 0),
            "scriptStepCover": {},
            "whiteBoardSwitch": 0,
            "agentId": src_detail.get("agentId") or "Tg3LpKo28D",
            "avatarNid": src_detail.get("avatarNid", ""),
            "videoSwitch": 0,
            "scriptStepResourceList": [],
            "knowledgeBaseSwitch": src_detail.get("knowledgeBaseSwitch", 1),
            "searchEngineSwitch": src_detail.get("searchEngineSwitch", 1),
            "historyRecordNum": src_detail.get("historyRecordNum", -1),
            "trainSubType": "ability",
        },
        "positionDTO": {"x": 100, "y": 100},
        "courseId": course_id,
        "libraryFolderId": "",
    }
    resp = requests.post(url, headers=get_headers(), json=payload, timeout=20)
    res = resp.json()
    if res.get("code") == 200 or res.get("success") is True:
        return True
    print(f"❌ createScriptStep 失败 [{step_id}]: {res}")
    return False


def create_script_flow(
    task_id,
    *,
    start_id,
    end_id,
    src_flow=None,
    cond=None,
    transition=None,
    is_default=None,
    flow_config=None,
    hist_num=None,
):
    """创建一条连线，可从源 flow 继承字段，也可逐项覆盖。"""
    url = ability_train_url("createScriptStepFlow")
    flow_id = generate(size=21)

    def pick(value, src_key, default):
        if value is not None:
            return value
        if src_flow is not None and src_key in src_flow:
            return copy.deepcopy(src_flow[src_key])
        return default

    payload = {
        "trainTaskId": task_id,
        "flowId": flow_id,
        "scriptStepStartId": start_id,
        "scriptStepStartHandle": f"{start_id}-source-bottom",
        "scriptStepEndId": end_id,
        "scriptStepEndHandle": f"{end_id}-target-top",
        "flowCondition": pick(cond, "flowCondition", ""),
        "flowConfiguration": pick(flow_config, "flowConfiguration", copy.deepcopy(EMPTY_FLOW_CFG)),
        "flowSettingType": "quick",
        "transitionPrompt": pick(transition, "transitionPrompt", ""),
        "transitionHistoryNum": pick(hist_num, "transitionHistoryNum", -1),
        "isDefault": pick(is_default, "isDefault", 1),
        "isError": False,
    }
    resp = requests.post(url, headers=get_headers(), json=payload, timeout=20)
    res = resp.json()
    if res.get("code") == 200 or res.get("success") is True:
        return True
    print(f"❌ createScriptStepFlow 失败: {res}")
    return False


# --- 分组计算 ---


def select_group_nodes(nodes, spec):
    sel = []
    for node in nodes:
        if not is_business(node):
            continue
        name = detail_of(node).get("stepName", "")
        if module_of(name) in spec["modules"] or name in spec["special"]:
            sel.append(node)
    return sel


def classify_flows(flows, sel_ids):
    internal, boundary_out = [], []
    for fl in flows:
        s = fl.get("scriptStepStartId")
        e = fl.get("scriptStepEndId")
        if s in sel_ids and e in sel_ids:
            internal.append(fl)
        elif s in sel_ids and e not in sel_ids:
            boundary_out.append(fl)
    return internal, boundary_out


def plan_group(group_key, nodes, flows):
    """返回该组的计算结果（不调接口），供 dry-run 与导入共用。"""
    spec = GROUPS[group_key]
    sel = select_group_nodes(nodes, spec)
    sel_ids = {n["stepId"] for n in sel}
    internal, boundary_out = classify_flows(flows, sel_ids)
    first_header = next(
        (n for n in sel if detail_of(n).get("stepName", "").startswith(spec["first_header_prefix"])),
        None,
    )
    return {
        "spec": spec,
        "nodes": sel,
        "sel_ids": sel_ids,
        "internal": internal,
        "boundary_out": boundary_out,
        "first_header": first_header,
    }


# --- dry-run ---


def print_dry_run(group_key, plan, nodes_by_id):
    spec = plan["spec"]
    rmap = spec["renumber"]
    print("\n" + "=" * 72)
    print(f"📦 {group_key}剧本：业务节点 {len(plan['nodes'])} 个（另加 START/END）")
    fh = plan["first_header"]
    print(f"   首关(START指向): {detail_of(fh).get('stepName') if fh else '⚠️ 未找到'}"
          f" -> {renumber_name(detail_of(fh).get('stepName',''), rmap) if fh else ''}")
    print(f"   开场白: {'重写' if spec['opening'] else '沿用原文(仅重编号)'}")
    print(f"   结束语: {'自定义收尾' if spec['closing'] else '沿用源 →END 边'}")
    print("\n   节点(原名 → 新名 | 附件):")
    for n in plan["nodes"]:
        d = detail_of(n)
        files = [r.get("fileName") for r in (d.get("scriptStepResourceList") or []) if r.get("fileId")]
        old = d.get("stepName", "")
        print(f"     · {old[:24]:26} → {renumber_name(old, rmap)[:24]:26} | {files}")
    print(f"\n   组内连线: {len(plan['internal'])} 条")
    print(f"   边界出边(改指向 END): {len(plan['boundary_out'])} 条")
    for fl in plan["boundary_out"]:
        sn = detail_of(nodes_by_id[fl["scriptStepStartId"]]).get("stepName", "")[:18]
        print(f"     · {sn} --[{fl.get('flowCondition')}]--> END")
    print(f"   评分项: {spec['scores']}")


# --- 导入单个组 ---


def query_score_items(task_id):
    url = ability_train_url("queryScoreItemList")
    resp = requests.post(url, headers=get_headers(), json={"trainTaskId": task_id}, timeout=20)
    j = resp.json()
    return j.get("data") or []


def delete_score_item(task_id, item_id):
    url = ability_train_url("delScoreItem")
    resp = requests.post(url, headers=get_headers(), json={"trainTaskId": task_id, "itemId": item_id}, timeout=20)
    j = resp.json()
    if j.get("success") or j.get("code") == 200:
        return True
    print(f"   ❌ 删除评分项失败 {item_id}: {j.get('msg')}")
    return False


def sync_score_items(task_id, keep_names, source_items):
    """让任务只保留 keep_names 对应的评分项：删多余、补缺失（内容取自源）。"""
    live = query_score_items(task_id)
    live_by_name = {it["itemName"]: it for it in live}
    deleted = kept = created = 0
    for it in live:
        if it["itemName"] not in keep_names:
            if delete_score_item(task_id, it["itemId"]):
                deleted += 1
        else:
            kept += 1
    src_by_name = {it["itemName"]: it for it in source_items}
    for name in keep_names:
        if name not in live_by_name:
            item = src_by_name.get(name)
            if item and create_score_item(task_id, item):
                created += 1
            elif not item:
                print(f"   ⚠️ 源中无评分项「{name}」，无法补建")
    print(f"   ✅ 评分项同步：保留 {kept}，删除 {deleted}，补建 {created}（目标 {len(keep_names)} 项）")


def clean_task(task_id):
    """删除目标任务里的全部连线和全部节点（含 START/END），清出干净画布。"""
    flows = query_script_step_flows(task_id)
    for fl in flows:
        if fl.get("flowId"):
            delete_script_step_flow(task_id, fl["flowId"])
    steps = query_script_steps(task_id)
    for st in steps:
        if st.get("stepId"):
            delete_script_step(task_id, st["stepId"])
    print(f"   🧹 已清空任务 {task_id}：删除连线 {len(flows)}，节点 {len(steps)}")
    remaining = query_script_steps(task_id)
    if remaining:
        raise RuntimeError(f"清空后仍残留 {len(remaining)} 个节点，已中止。")


def import_group(group_key, task_id, course_id, nodes, flows, *, write_scores, scores, do_clean=True):
    plan = plan_group(group_key, nodes, flows)
    spec = plan["spec"]
    rmap = spec["renumber"]
    sel = plan["nodes"]
    first_header = plan["first_header"]
    if first_header is None:
        raise RuntimeError(f"{group_key}剧本未找到首关 header（{spec['first_header_prefix']}）")

    print(f"\n🚀 导入 {group_key}剧本 → 任务 {task_id}")
    if do_clean:
        clean_task(task_id)
    start_id, end_id = create_start_end_nodes(task_id, course_id)
    print(f"   ✅ START={start_id} END={end_id}")

    id_map = {n["stepId"]: generate(size=21) for n in sel}

    # 创建业务节点：最小创建 + 全量 edit
    for n in sel:
        src_detail = detail_of(n)
        new_id = id_map[n["stepId"]]
        opening = spec["opening"] if n is first_header else None
        if not create_script_node_min(task_id, course_id, new_id, src_detail, rmap):
            raise RuntimeError(f"创建节点失败: {src_detail.get('stepName')}")
        full_detail = build_clone_detail(src_detail, new_id, task_id, rmap, opening)
        payload = {
            "trainTaskId": task_id,
            "stepId": new_id,
            "stepDetailDTO": full_detail,
            "positionDTO": n.get("positionDTO", {"x": 100, "y": 100}),
            "courseId": course_id,
        }
        if not edit_script_step(payload):
            raise RuntimeError(f"补全节点失败: {full_detail.get('stepName')}")

    # 连线：START -> 首关
    create_script_flow(
        task_id, start_id=start_id, end_id=id_map[first_header["stepId"]],
        cond="", is_default=0, transition="", flow_config=copy.deepcopy(EMPTY_FLOW_CFG), hist_num=0,
    )
    # 组内连线
    for fl in plan["internal"]:
        create_script_flow(
            task_id, src_flow=fl,
            start_id=id_map[fl["scriptStepStartId"]],
            end_id=id_map[fl["scriptStepEndId"]],
        )
    # 边界出边 -> END（结束语覆盖）
    for fl in plan["boundary_out"]:
        create_script_flow(
            task_id, src_flow=fl,
            start_id=id_map[fl["scriptStepStartId"]],
            end_id=end_id,
            transition=spec["closing"] if spec["closing"] else None,
        )
    print(f"   ✅ 连线完成：START 1 + 组内 {len(plan['internal'])} + 边界 {len(plan['boundary_out'])}")

    if write_scores:
        sync_score_items(task_id, spec["scores"], scores)


def verify_task(group_key, task_id, nodes, flows):
    """导入后回采对账：节点数、附件、连线，与计划比对。返回是否通过。"""
    plan = plan_group(group_key, nodes, flows)
    live = query_script_steps(task_id)
    live_flows = query_script_step_flows(task_id)
    biz = [n for n in live if is_business(n)]
    exp_nodes = len(plan["nodes"])
    exp_flows = 1 + len(plan["internal"]) + len(plan["boundary_out"])

    def file_count(node):
        return sum(1 for r in (detail_of(node).get("scriptStepResourceList") or []) if r.get("fileId"))

    live_files = sum(file_count(n) for n in biz)
    src_files = sum(file_count(n) for n in plan["nodes"])
    ok = len(biz) == exp_nodes and len(live_flows) == exp_flows and live_files == src_files
    print(f"   🔎 {group_key} 回采：节点 {len(biz)}/{exp_nodes}，连线 {len(live_flows)}/{exp_flows}，"
          f"附件总数 {live_files}/{src_files} {'✅' if ok else '❌'}")
    sample = next((n for n in biz if file_count(n)), None)
    if sample:
        d = detail_of(sample)
        files = [r.get("fileName") for r in (d.get("scriptStepResourceList") or []) if r.get("fileId")]
        print(f"      抽样：{d.get('stepName','')[:26]} | 附件 {files}")
    return ok


# --- 资源挂载探针 ---


def probe(task_id, course_id, nodes, flows):
    """把关卡1.1克隆进目标任务并连成 START->1.1->END，用于人工验证附件挂载。"""
    node = next(
        (n for n in nodes if detail_of(n).get("stepName", "").startswith("关卡1.1")), None
    )
    if node is None:
        raise RuntimeError("源数据未找到 关卡1.1")
    print(f"🔬 探针：克隆「{detail_of(node).get('stepName')}」到任务 {task_id}")
    start_id, end_id = create_start_end_nodes(task_id, course_id)
    new_id = generate(size=21)
    src_detail = detail_of(node)
    if not create_script_node_min(task_id, course_id, new_id, src_detail, {1: 1}):
        raise RuntimeError("探针节点创建失败")
    full_detail = build_clone_detail(src_detail, new_id, task_id, {1: 1}, None)
    payload = {
        "trainTaskId": task_id, "stepId": new_id, "stepDetailDTO": full_detail,
        "positionDTO": node.get("positionDTO", {"x": 100, "y": 100}), "courseId": course_id,
    }
    if not edit_script_step(payload):
        raise RuntimeError("探针节点 edit 失败")
    create_script_flow(task_id, start_id=start_id, end_id=new_id, cond="", is_default=0,
                       flow_config=copy.deepcopy(EMPTY_FLOW_CFG), hist_num=0)
    create_script_flow(task_id, start_id=new_id, end_id=end_id,
                       cond="接下来我们将进入下一阶段", transition="探针结束")
    print(f"   ✅ 探针节点 {new_id} 已建。请在平台打开该任务，确认 Coordinate.h/.cpp 已挂载、"
          f"封面/知识库/声音/形象/数字人/背景主题与源一致。")


# --- CLI ---


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="按模块拆分能力训练剧本并导入新任务")
    p.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="源 JSON 导出目录")
    p.add_argument("--course-id", default=SOURCE_COURSE_ID, help="目标 courseId（默认与源相同）")
    p.add_argument("--dry-run", action="store_true", help="仅打印拆分计划，不调接口")
    p.add_argument("--probe", metavar="TASK_ID", help="资源挂载探针：克隆关卡1.1到该任务")
    p.add_argument("--import", dest="do_import", action="store_true", help="正式导入三个剧本")
    p.add_argument("--basic", help="基础剧本目标任务 ID")
    p.add_argument("--advanced", help="进阶剧本目标任务 ID")
    p.add_argument("--senior", help="高级剧本目标任务 ID")
    p.add_argument("--no-scores", action="store_true", help="导入时不写评分项")
    return p.parse_args(argv)


def main():
    args = parse_args()
    load_env_config()

    nodes, flows, scores = load_source(args.source_dir)
    nodes_by_id = {n["stepId"]: n for n in nodes}
    print(f"📖 源数据：节点 {len(nodes)}，连线 {len(flows)}，评分项 {len(scores)}")

    if args.dry_run:
        for key in GROUPS:
            print_dry_run(key, plan_group(key, nodes, flows), nodes_by_id)
        # 评分项映射核对
        covered = {n for g in GROUPS.values() for n in g["scores"]}
        missing = [s["itemName"] for s in scores if s["itemName"] not in covered]
        if missing:
            print(f"\n⚠️ 未分配到任何剧本的评分项: {missing}")
        print("\n🧪 Dry-run 完成，未调用任何接口。")
        return

    if args.probe:
        probe(args.probe, args.course_id, nodes, flows)
        return

    if args.do_import:
        targets = {"基础": args.basic, "进阶": args.advanced, "高级": args.senior}
        missing = [k for k, v in targets.items() if not v]
        if missing:
            print(f"❌ 缺少目标任务 ID: {missing}（用 --basic/--advanced/--senior 提供）")
            return
        for key, tid in targets.items():
            import_group(key, tid, args.course_id, nodes, flows,
                         write_scores=not args.no_scores, scores=scores)
        print("\n✅ 三个剧本导入完成。建议回采 queryScriptStepList/FlowList 对账。")
        return

    print("未指定动作。使用 --dry-run / --probe <TASK_ID> / --import。")


if __name__ == "__main__":
    main()
