#!/usr/bin/env python3
"""合并三份岗位评价标准为一份（供三合一路由任务部署评分项）。

规则：
- 主评分项标题加岗位前缀【分拣岗】/【客服岗】/【管理岗】
- 去掉各自的 # 评价标准 与 ## 总分 行，统一为总分90分
- 用 create_score_items_from_rubric.parse_rubric_markdown 验证解析出13项、总分90
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BASE = Path("/Users/zhangyichi/工作/能力训练/skills_training_course/四川交通职技术大学-物流专业实习四维智能体课程")
OUT = BASE / "评价标准（合并）.md"

SOURCES = [
    ("仓库分拣岗_拣货员/评价标准.md", "分拣岗"),
    ("客户服务岗_快递投诉处理/评价标准.md", "客服岗"),
    ("管理岗_数据分析/评价标准.md", "管理岗"),
]


def main():
    parts = [
        "# 评价标准",
        "",
        "## 总分：90分",
        "",
        "> 本任务为三岗选考（仓库分拣岗/客户服务岗/管理岗）。评分项按岗位分组并加前缀，"
        "评判时以学生实际选择并完成的岗位对应评分组为主。",
        "",
    ]
    for rel, prefix in SOURCES:
        text = (BASE / rel).read_text(encoding="utf-8")
        # 去掉文件级标题与总分行
        lines = [
            ln for ln in text.splitlines()
            if not re.match(r"^#\s+评价标准\s*$", ln) and not re.match(r"^##\s+总分", ln)
        ]
        body = "\n".join(lines).strip()
        # 主评分项标题加岗位前缀（兼容全角/半角括号）
        body = re.sub(r"^##\s+(?![#])(.+?[（(]\d+\s*分[）)])", rf"## 【{prefix}】\1", body, flags=re.M)
        parts.append(body)
    merged = "\n\n---\n\n".join(parts) + "\n"
    OUT.write_text(merged, encoding="utf-8")
    print(f"✅ 已写入 {OUT}")

    from create_score_items_from_rubric import parse_rubric_markdown
    items = parse_rubric_markdown(OUT)
    total = sum(int(it["score"]) for it in items)
    print(f"  解析出 {len(items)} 个主评分项，总分 {total}")
    for it in items:
        print(f"   - {it['itemName']}（{it['score']}分）")
    assert len(items) == 13, f"评分项数 {len(items)} != 13"
    assert total == 90, f"总分 {total} != 90"
    print("✅ 校验通过")


if __name__ == "__main__":
    main()
