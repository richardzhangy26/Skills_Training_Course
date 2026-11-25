#!/usr/bin/env python3
"""组装"物流岗位实训（三岗选考）"路由合并版训练剧本。

结构：阶段1 岗位选择中枢 + 分拣分支(原1-6→新2-7) + 客服分支(原1-5→新8-12)
     + 管理分支(原1-5→新13-17)，共17个业务阶段。

来源：
- 仓库分拣岗_拣货员/训练剧本配置.md
- 客户服务岗_快递投诉处理/训练剧本配置.md
- 管理岗_数据分析/训练剧本配置.md

变换（仿 build_trauma_router_md.py）：
- 阶段重编号（只改标题行）
- 跳转关键词全局唯一化改写（内链加岗位前缀；终阶段 训练完成→分拣/客服/管理训练完成，直达END）
- 背景图绝对路径改为相对课程目录的路径
- HEADER 手写中枢阶段，FOOTER 手写跳转关系与配置说明
"""
import re
import subprocess
import sys
from pathlib import Path

BASE = Path("/Users/zhangyichi/工作/能力训练/skills_training_course/四川交通职技术大学-物流专业实习四维智能体课程")
OUT_MD = BASE / "训练剧本配置（路由合并版）.md"

SOURCES = [
    # (目录, 编号偏移, 关键词替换表: 旧→新)
    ("仓库分拣岗_拣货员", 1, {
        "进入方法判定阶段": "进入分拣方法判定阶段",
        "进入流程演练阶段": "进入分拣流程演练阶段",
        "进入异常处置阶段": "进入分拣异常处置阶段",
        "进入单证填写阶段": "进入分拣单证填写阶段",
        "进入复盘反思阶段": "进入分拣复盘反思阶段",
        "训练完成": "分拣训练完成",
    }),
    ("客户服务岗_快递投诉处理", 7, {
        "进入模拟接听阶段": "进入客服模拟接听阶段",
        "进入工单填写阶段": "进入客服工单填写阶段",
        "进入处理方案阶段": "进入客服处理方案阶段",
        "进入总结阶段": "进入客服总结阶段",
        "训练完成": "客服训练完成",
    }),
    ("管理岗_数据分析", 12, {
        "进入总结反思阶段": "进入管理总结反思阶段",
        "训练完成": "管理训练完成",
    }),
]

EXPECTED_COUNTS = {"仓库分拣岗_拣货员": 6, "客户服务岗_快递投诉处理": 5, "管理岗_数据分析": 5}

KW_HUB_TO_SORT = "进入仓库分拣岗训练"
KW_HUB_TO_SERVICE = "进入客户服务岗训练"
KW_HUB_TO_DATA = "进入管理岗训练"
KW_HUB_TO_END = "训练完成"
KW_SORT_END = "分拣训练完成"
KW_SERVICE_END = "客服训练完成"
KW_DATA_END = "管理训练完成"


def extract_stage_chunks(text):
    """按 ### 阶段N 标题切分，返回 [(原编号, 正文)]。

    注意：不能用 ^## 通用匹配截断——提示词代码块内部就有 `## 步骤 0` 这类行。
    中间 chunk 以下一个 ### 阶段 为界；最后一个 chunk 以文件级 `## 🔄` 标题为界。
    """
    marks = [(m.start(), int(m.group(1))) for m in re.finditer(r"^### 阶段(\d+):[^\n]*$", text, re.M)]
    footer = re.search(r"^## 🔄", text, re.M)
    footer_pos = footer.start() if footer else len(text)
    chunks = []
    for i, (pos, num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else footer_pos
        body = text[pos:end].rstrip()
        body = re.sub(r"\n+---\s*$", "", body).rstrip()
        chunks.append((num, body))
    return chunks


def renumber(body, old_num, new_num):
    return body.replace(f"### 阶段{old_num}:", f"### 阶段{new_num}:", 1)


def rewrite_background_paths(body):
    """绝对背景图路径 → 相对课程目录。"""
    return body.replace(str(BASE) + "/", "")


def transform(folder, offset, keyword_map):
    src = BASE / folder / "训练剧本配置.md"
    text = src.read_text(encoding="utf-8")
    chunks = extract_stage_chunks(text)
    assert len(chunks) == EXPECTED_COUNTS[folder], f"{folder}: 阶段数 {len(chunks)} != {EXPECTED_COUNTS[folder]}"
    out = []
    for old_num, body in chunks:
        # 关键词改写（chunk 内全文替换；各词只出现在部分阶段，全局计数在 main 校验）
        for old_kw, new_kw in keyword_map.items():
            body = body.replace(old_kw, new_kw)
        body = rewrite_background_paths(body)
        body = renumber(body, old_num, old_num + offset)
        out.append(body)
    return out


HEADER = f"""# 物流岗位实训（分拣/客服/数据分析三岗选考） - 训练剧本配置

## 📋 基础配置
- **任务名称**：物流岗位实训（分拣/客服/数据分析三岗选考）
- **任务描述**：物流专业实习学生进入实训后，先在岗位选择中枢从仓库分拣岗（拣货员）、客户服务岗（快递投诉处理）、管理岗（数据分析）三个岗位中自主选择其一，进入对应岗位的完整训练链路；训练结束后返回中枢，可继续选择其他岗位训练或结束实训。
- **智能体角色**：实训导学助手（中枢）/ 王师傅（分拣）/ 林晓棠（客服）/ 林老师（管理）
- **目标受众**：物流管理/现代物流专业实习学生
- **背景图**：仓库分拣岗_拣货员/backgrounds/训练剧本配置_cover.png

## 📝 训练阶段

### 阶段1: 岗位选择

**虚拟训练官名字**: 实训导学助手

**模型**: Doubao-Seed-1.6

**数字人**: ls4ucixfWP

**数字人名称**: 王师傅

**声音**: Tg3LpKo28D

**形象**: KwLGLpvRyF

**阶段描述**: 实训总入口。欢迎学生并引导其在仓库分拣岗、客户服务岗、管理岗三个岗位中选择一个开始训练；选定后直接进入对应岗位训练链路，训练完成后结束整个实训。

**背景图**: 仓库分拣岗_拣货员/backgrounds/训练剧本配置_cover.png

**互动轮次**: 4轮

**flowCondition**: "{KW_HUB_TO_SORT}"

**transitionPrompt**:
```
【输入参数】
- 下一阶段原始开场白 ${{next_stage_opening}}

【整体生成目标】
直接输出下一阶段原始开场白，不做额外改写。
```

**开场白**:
```
你好，欢迎来到物流岗位实训！我是你的实训导学助手。
今天有三个岗位的训练等你选：
1. 仓库分拣岗（拣货员）——跟王师傅学摘果法/播种法拣选与出库全流程；
2. 客户服务岗（快递投诉处理）——跟晓棠姐学投诉接听、工单填写与处理方案；
3. 管理岗（数据分析）——跟林老师学库存数量、健康度与结构分析。
你想从哪个岗位开始？直接告诉我岗位名称就行。
```

**提示词**:
```
# Role

你是"物流岗位实训"的导学助手，亲切、专业、不啰嗦。

**当前情境**：学生刚进入实训，尚未开始任何岗位训练。

**当前任务**：引导学生从三个岗位中选择一个进入训练；或在学生明确要求时结束实训。

**三个岗位选项**：
1. 仓库分拣岗（拣货员）
2. 客户服务岗（快递投诉处理）
3. 管理岗（数据分析）

# Opening Line (你已经在上一轮输出过这句话，请基于此进行回复)

# Workflow & Interaction Rules

## Step 0 状态判定
- 学生处于岗位选择环节：按开场白思路引导学生在三个岗位中做选择。

## Step 1 分支判定（按优先级从上到下，命中即停止）

- **分支Z（兜底，最高优先级）**：学生话题与岗位选择完全无关（闲聊、问无关知识等）→ 礼貌拉回话题，重新列出三个岗位选项请学生选择。

- **分支A**：学生明确选择仓库分拣岗/分拣/拣货员/拣货（等类似意思）→ **不要输出任何对话内容**。**仅输出**跳转关键词：`{KW_HUB_TO_SORT}`

- **分支B**：学生明确选择客户服务岗/客服/投诉处理/快递投诉（等类似意思）→ **不要输出任何对话内容**。**仅输出**跳转关键词：`{KW_HUB_TO_SERVICE}`

- **分支C**：学生明确选择管理岗/数据分析/管理（等类似意思）→ **不要输出任何对话内容**。**仅输出**跳转关键词：`{KW_HUB_TO_DATA}`

- **分支D**：学生明确表示要结束/退出/不练了/下次再说（等类似意思）→ **不要输出任何对话内容**。**仅输出**跳转关键词：`{KW_HUB_TO_END}`

- **分支E**：学生选择不明确、同时提到多个岗位、或询问"选哪个好"→ 澄清确认：简要说明三个岗位各自训练什么（每个岗位一句话），请学生自己决定。**严禁替学生决定，严禁默认进入某一个岗位。**

# Response Constraints

1. **【跳转纯净性】**分支A/B/C/D 命中时只输出对应跳转关键词，严禁任何标点、空格、寒暄或解释。
2. **【严禁替学生决定】**选择不明确时必须走分支E澄清，不得自行假定学生要选某个岗位。
3. **【反剧透】**不得提前透露各岗位训练的具体题目、数据或标准答案。
4. **【字数】**非跳转回复不超过150字，口语化、自然。
5. **【称呼】**称呼学生用"你"或"同学"，严禁出现"学生"二字。
6. **【跳转关键词清单】**`{KW_HUB_TO_SORT}`、`{KW_HUB_TO_SERVICE}`、`{KW_HUB_TO_DATA}`、`{KW_HUB_TO_END}`，仅限分支命中时原样输出。
```

"""

FOOTER = f"""
## 🔄 阶段跳转关系

- START → 阶段1（岗位选择中枢）
- 阶段1 → 阶段2（分拣·情境导入）：**默认边**，条件 `{KW_HUB_TO_SORT}`
- 阶段1 → 阶段8（客服·投诉类型判断）：条件 `{KW_HUB_TO_SERVICE}`（布线脚本补建，非默认边）
- 阶段1 → 阶段13（管理·导入）：条件 `{KW_HUB_TO_DATA}`（布线脚本补建，非默认边）
- 阶段1 → END：条件 `{KW_HUB_TO_END}`（布线脚本补建，非默认边；学生在选择环节要求结束时使用）
- 阶段2→3→4→5→6→7：分拣分支内链，条件依次为 `进入分拣方法判定阶段` / `进入分拣流程演练阶段` / `进入分拣异常处置阶段` / `进入分拣单证填写阶段` / `进入分拣复盘反思阶段`
- 阶段7 → END：条件 `{KW_SORT_END}`（布线脚本补建，默认边）
- 阶段8→9→10→11→12：客服分支内链，条件依次为 `进入客服模拟接听阶段` / `进入客服工单填写阶段` / `进入客服处理方案阶段` / `进入客服总结阶段`
- 阶段12 → END：条件 `{KW_SERVICE_END}`（布线脚本补建，默认边）
- 阶段13→14→15→16→17：管理分支内链，条件依次为 `进入库存数量分析阶段` / `进入库存健康度分析阶段` / `进入库存结构分析阶段` / `进入管理总结反思阶段`
- 阶段17 → END：条件 `{KW_DATA_END}`（布线脚本补建，默认边）
- 注：线性导入会产生 阶段7→8、阶段12→13、阶段17→END（带误连条件）三条误连边，由布线脚本 wire_three_posts_hub.py 删除/修正。

## 📖 配置说明

- **阶段划分原因**：按老师要求将仓库分拣岗、客户服务岗、管理岗三个能力训练合并为一个任务；阶段1为岗位选择路由中枢，学生三选一进入对应岗位训练链路，复盘总结完成后直接结束实训。
- **拓扑**：中枢分流型（仿创伤路由合并版）。同一起点仅一条默认边：中枢默认边为→阶段2（分拣）；三个分支收尾阶段各自唯一出边直达 END，结束关键词互斥（{KW_SORT_END}/{KW_SERVICE_END}/{KW_DATA_END}，与中枢的 {KW_HUB_TO_END} 分离）。
- **模板类型选择理由**：中枢阶段为自定义路由提示词（状态判定+三选一+跳转纯净性）；三个分支沿用原剧本的循序过关型（前段）+总结模块型（收尾）结构，内容不变。
- **数字人配置选择理由**：分拣岗复用王师傅（customNid=ls4ucixfWP 精确匹配）、管理岗复用林老师（customNid=ElrZoowrgf）、客服岗林晓棠按"名称+声音+形象"新建（阶段9虚拟训练官为客户A，单独声音/形象）；中枢复用王师傅数字人资源，人设为导学助手。
- **关键考核点**：见合并版评价标准（分拣20分/客服50分/管理20分）。

### 素材放置说明（合并后全局阶段号）

| 素材 | 放置阶段 |
|---|---|
| 分拣·表1 出库订单（1） | 阶段2（开场核对）、阶段6（单证再引用） |
| 分拣·表2 出库订单（2） | 阶段2 |
| 分拣·图1 某仓库的储位分布图 | 阶段4（路径规划）、阶段6（填储位号码） |
| 分拣·拣选方式判定参考表 | 阶段3（判定知识库） |
| 分拣·表3/表4/表5 A/B/C超市采购订单 | 阶段3（拓展关卡） |
| 分拣·表6 播种法拣货单（示例） | 阶段6 |
| 分拣·表7 摘果法拣货单 | 阶段6 |
| 分拣·"各板块要做的事"表 | 设计依据，不面向学生展示 |
| 客服·表1 投诉案例（客户A–E） | 阶段8、9、10、11 |
| 客服·表2 投诉工单字段说明 | 阶段10 |
| 客服·表3 投诉处理时限与级别 | 阶段8、阶段11 |
| 客服·表4 投诉处理考核评价 | 阶段12 |
| 管理·表1 源数据3-14库存数据 | 阶段14、15、16 |
| 管理·表2 库存分析指标与判定标准 | 阶段14、15、16 |
| 管理·表3 参考分析结论 | 阶段17 |
"""


def main():
    parts = [HEADER]
    for folder, offset, kwmap in SOURCES:
        chunks = transform(folder, offset, kwmap)
        parts.append("\n\n---\n\n".join(chunks))
    merged = "\n\n---\n\n".join([parts[0]] + parts[1:]) + FOOTER
    OUT_MD.write_text(merged, encoding="utf-8")
    print(f"✅ 已写入 {OUT_MD}")

    # 断言1：关键词全局计数
    counts = {
        KW_HUB_TO_SORT: merged.count(KW_HUB_TO_SORT),
        KW_HUB_TO_SERVICE: merged.count(KW_HUB_TO_SERVICE),
        KW_HUB_TO_DATA: merged.count(KW_HUB_TO_DATA),
        KW_SORT_END: merged.count(KW_SORT_END),
        KW_SERVICE_END: merged.count(KW_SERVICE_END),
        KW_DATA_END: merged.count(KW_DATA_END),
        KW_HUB_TO_END: merged.count(KW_HUB_TO_END),
    }
    for kw, n in counts.items():
        print(f"  关键词 [{kw}] 出现 {n} 次")
    assert counts[KW_HUB_TO_SORT] >= 4, "分拣入口关键词出现次数不足（含flowCondition应≥4）"
    assert counts[KW_HUB_TO_SERVICE] >= 3, "客服入口关键词出现次数不足"
    assert counts[KW_HUB_TO_DATA] >= 3, "管理入口关键词出现次数不足"
    assert counts[KW_SORT_END] >= 3, "分拣结束关键词不足"
    assert counts[KW_SERVICE_END] >= 3, "客服结束关键词不足"
    assert counts[KW_DATA_END] >= 3, "管理结束关键词不足"
    assert counts[KW_HUB_TO_END] >= 4, "中枢结束关键词缺失"
    # 断言2a：旧内链关键词必须全部清零（含近似词逐一检查）
    OLD_KEYWORDS = [
        "进入方法判定阶段", "进入流程演练阶段", "进入异常处置阶段", "进入单证填写阶段", "进入复盘反思阶段",
        "进入模拟接听阶段", "进入工单填写阶段", "进入处理方案阶段", "进入总结阶段",
        "进入总结反思阶段", "返回岗位选择",
    ]
    for old_kw in OLD_KEYWORDS:
        assert merged.count(old_kw) == 0, f"旧关键词未清零: {old_kw} 残留 {merged.count(old_kw)} 处"
    # 断言2b：分支正文区不得残留裸"训练完成"（去掉三个带前缀结束词后检查）
    body_region = merged.split("### 阶段2:", 1)[1].split("## 🔄 阶段跳转关系", 1)[0]
    stripped = body_region.replace(KW_SORT_END, "").replace(KW_SERVICE_END, "").replace(KW_DATA_END, "")
    assert "训练完成" not in stripped, "分支中仍残留裸 训练完成 关键词！"

    # 断言3：导入器解析恰好17阶段
    sys.path.insert(0, str(Path(__file__).parent))
    from create_task_from_markdown import parse_markdown
    steps = parse_markdown(OUT_MD)
    print(f"  parse_markdown 解析阶段数: {len(steps)}")
    assert len(steps) == 17, f"解析阶段数 {len(steps)} != 17"
    names = [s.get("stepName", "") for s in steps]
    print("  阶段列表:", " / ".join(f"{i+1}.{n}" for i, n in enumerate(names)))

    # 断言4：validate_markdown.py --strict
    validator = Path(__file__).parent.parent / ".claude/skills/training-prompt-expert/scripts/validate_markdown.py"
    r = subprocess.run([sys.executable, str(validator), str(OUT_MD), "--strict"], capture_output=True, text=True)
    tail = "\n".join(r.stdout.splitlines()[-3:])
    print(tail)
    assert "所有检查通过" in r.stdout, f"格式断言未通过:\n{r.stdout[-2000:]}"
    print("✅ 全部断言通过")


if __name__ == "__main__":
    main()
