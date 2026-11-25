#!/usr/bin/env python3
"""把三个岗位的资源图（docx 表格/图片渲染的 PNG）上传并绑定到合并任务的对应阶段。

绑定采用实战验证过的双写形状（参照 update_remote_sensing_tasks._apply_resource_write_shape
与 split_script_into_tasks.build_clone_detail）：
- 顶层 scriptStepResourceList（读形状，真正驱动附件绑定的字段）
- stepExtProperty.resources（编辑器分组写形状）
经 editScriptStep 提交；提交后回查对账每个阶段的附件数。

用法：
    python bind_resource_images.py <train_task_id>           # dry-run 预览
    python bind_resource_images.py <train_task_id> --apply   # 实际执行
"""
import argparse
import copy
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from create_task_from_markdown import (  # noqa: E402
    load_env_config,
    query_script_steps,
    get_business_script_steps,
    upload_basic_resource_file,
    edit_script_step,
)

try:
    from create_task_from_markdown import require_course_id
except ImportError:  # 兼容旧版本
    import os

    def require_course_id():
        cid = os.getenv("COURSE_ID", "")
        if not cid:
            raise ValueError("缺少 COURSE_ID")
        return cid

ROOT = Path("/Users/zhangyichi/工作/能力训练/skills_training_course/四川交通职技术大学-物流专业实习四维智能体课程")

# 资源文件（只用下划线新版命名；"各板块要做的事"为设计依据不面向学生，不绑定）
# 映射：合并后阶段号 -> 资源文件相对 ROOT 路径
STAGE_RESOURCES = {
    2: ["仓库分拣岗_拣货员/资源图/表1_出库订单1.png",
        "仓库分拣岗_拣货员/资源图/表2_出库订单2.png"],
    3: ["仓库分拣岗_拣货员/资源图/拣选方式判定参考表.png",
        "仓库分拣岗_拣货员/资源图/表3_A超市采购订单.png",
        "仓库分拣岗_拣货员/资源图/表4_B超市采购订单.png",
        "仓库分拣岗_拣货员/资源图/表5_C超市采购订单.png"],
    4: ["仓库分拣岗_拣货员/资源图/图1_储位分布图.png"],
    6: ["仓库分拣岗_拣货员/资源图/表1_出库订单1.png",
        "仓库分拣岗_拣货员/资源图/图1_储位分布图.png",
        "仓库分拣岗_拣货员/资源图/表6_播种法拣货单.png",
        "仓库分拣岗_拣货员/资源图/表7_摘果法拣货单.png"],
    8: ["客户服务岗_快递投诉处理/资源图/表1_投诉案例.png",
        "客户服务岗_快递投诉处理/资源图/表3_投诉处理时限与级别.png"],
    9: ["客户服务岗_快递投诉处理/资源图/表1_投诉案例.png"],
    10: ["客户服务岗_快递投诉处理/资源图/表1_投诉案例.png",
         "客户服务岗_快递投诉处理/资源图/表2_投诉工单字段说明.png"],
    11: ["客户服务岗_快递投诉处理/资源图/表1_投诉案例.png",
         "客户服务岗_快递投诉处理/资源图/表3_投诉处理时限与级别.png"],
    12: ["客户服务岗_快递投诉处理/资源图/表4_投诉处理考核评价.png"],
    14: ["管理岗_数据分析/资源图/表1_源数据3-14库存数据.png",
         "管理岗_数据分析/资源图/表2_库存分析指标与判定标准.png"],
    15: ["管理岗_数据分析/资源图/表1_源数据3-14库存数据.png",
         "管理岗_数据分析/资源图/表2_库存分析指标与判定标准.png"],
    16: ["管理岗_数据分析/资源图/表1_源数据3-14库存数据.png",
         "管理岗_数据分析/资源图/表2_库存分析指标与判定标准.png"],
    17: ["管理岗_数据分析/资源图/表3_参考分析结论.png"],
}

EXPECTED_STEP_COUNT = 17


def step_name(step):
    return step.get("stepDetailDTO", {}).get("stepName") or step.get("stepName") or ""


def build_resource_rows(train_task_id, step_id, file_infos):
    """file_infos: [(fileId, fileName, fileUrl), ...]"""
    rows = []
    for sort, (file_id, file_name, file_url) in enumerate(file_infos, start=1):
        rows.append({
            "type": "resource",
            "fileId": file_id,
            "fileName": file_name,
            "thumbnail": file_url,
            "fileUrl": file_url,
            "isRequired": False,
            "description": "",
            "trainTaskId": train_task_id,
            "scriptStepId": step_id,
            "sort": sort,
        })
    return rows


def apply_write_shape(detail, rows):
    """顶层 scriptStepResourceList（读形状）+ stepExtProperty.resources（分组写形状）双写。"""
    detail["scriptStepResourceList"] = [
        {
            "trainTaskId": r["trainTaskId"],
            "scriptStepId": r["scriptStepId"],
            "sort": r["sort"],
            "fileId": r["fileId"],
            "fileName": r["fileName"],
            "fileUrl": r["fileUrl"],
            "thumbnail": r["fileUrl"],
        }
        for r in rows
    ]
    ext = copy.deepcopy(detail.get("stepExtProperty") or {})
    ext["resources"] = [{
        "nid": "default",
        "category": "未分类",
        "list": [
            {
                "type": "resource",
                "fileId": r["fileId"],
                "fileName": r["fileName"],
                "thumbnail": r["fileUrl"],
                "fileUrl": r["fileUrl"],
                "isRequired": False,
                "description": "",
                "trainTaskId": r["trainTaskId"],
                "scriptStepId": r["scriptStepId"],
                "sort": r["sort"],
                "scriptStepResourceId": uuid.uuid4().hex[:20],
            }
            for r in rows
        ],
    }]
    detail["stepExtProperty"] = ext


def main():
    parser = argparse.ArgumentParser(description="上传并绑定三岗资源图到合并任务各阶段")
    parser.add_argument("train_task_id")
    parser.add_argument("--apply", action="store_true", help="实际执行（默认 dry-run）")
    args = parser.parse_args()

    load_env_config()
    course_id = require_course_id()

    step_list = query_script_steps(args.train_task_id)
    business_steps = get_business_script_steps(step_list)
    if len(business_steps) != EXPECTED_STEP_COUNT:
        print(f"❌ 业务阶段数 {len(business_steps)} != {EXPECTED_STEP_COUNT}，中止。")
        return 1

    # 按画布 x 坐标排序还原阶段顺序（x 是字符串，须 int 化）
    ordered = sorted(
        business_steps,
        key=lambda s: int((s.get("positionDTO") or {}).get("x") or 0),
    )
    stage_steps = {i + 1: s for i, s in enumerate(ordered)}

    # 预检：文件存在性 + 打印计划
    unique_files = sorted({p for files in STAGE_RESOURCES.values() for p in files})
    print(f"📦 共 {len(unique_files)} 个资源文件，绑定到 {len(STAGE_RESOURCES)} 个阶段：")
    for rel in unique_files:
        p = ROOT / rel
        if not p.exists():
            print(f"❌ 文件不存在: {p}")
            return 1
        bound = [st for st, files in STAGE_RESOURCES.items() if rel in files]
        print(f"  - {rel} → 阶段{bound}")

    if not args.apply:
        print("\n🧪 Dry-run 完成。确认无误后加 --apply 执行。")
        return 0

    # 上传（同一文件只传一次）
    uploaded = {}
    for rel in unique_files:
        p = ROOT / rel
        print(f"⬆️  上传 {rel} ...")
        res = upload_basic_resource_file(str(p))
        if not res or not res.get("fileId"):
            print(f"❌ 上传失败: {rel} -> {res}")
            return 1
        uploaded[rel] = (res["fileId"], p.name, res.get("fileUrl") or res.get("ossUrl") or "")
        print(f"   fileId={uploaded[rel][0]}")

    # 绑定
    for stage_no, rel_files in sorted(STAGE_RESOURCES.items()):
        step = stage_steps[stage_no]
        step_id = step["stepId"]
        file_infos = [uploaded[rel] for rel in rel_files]
        payload = copy.deepcopy(step)
        payload["trainTaskId"] = args.train_task_id
        payload["stepId"] = step_id
        payload["courseId"] = course_id
        detail = payload.setdefault("stepDetailDTO", {})
        rows = build_resource_rows(args.train_task_id, step_id, file_infos)
        apply_write_shape(detail, rows)
        if not edit_script_step(payload):
            print(f"❌ 阶段{stage_no} ({step_name(step)}) 绑定失败，中止。")
            return 1
        print(f"✅ 阶段{stage_no} ({step_name(step)}) 绑定 {len(rows)} 个资源")

    # 回查对账
    print("\n🔎 回查对账：")
    fresh = get_business_script_steps(query_script_steps(args.train_task_id))
    fresh_ordered = sorted(fresh, key=lambda s: int((s.get("positionDTO") or {}).get("x") or 0))
    ok = True
    for i, s in enumerate(fresh_ordered, start=1):
        resources = (s.get("stepDetailDTO") or {}).get("scriptStepResourceList") or []
        bound = [r for r in resources if r.get("fileId")]
        expected = len(STAGE_RESOURCES.get(i, []))
        mark = "✅" if len(bound) == expected else "❌"
        if len(bound) != expected:
            ok = False
        print(f"  {mark} 阶段{i} ({step_name(s)}): 期望{expected} 实际{len(bound)}")
    print("\n" + ("✅ 全部绑定完成并对账通过" if ok else "❌ 存在对账不符，请检查"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
