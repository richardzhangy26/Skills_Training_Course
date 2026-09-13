# 原子能力选型

选型权威源：`技能一览表.xlsx`、`技能  - 专家整理.xlsx`、由其生成的 `docs/atomic-skill-catalog.json`。xlsx 里有的名称即可进入设计挂载清单。不打开 PDS/SkillHub 也不能阻断交付。

## 检索顺序

1. 把需求点收成可搜索词：检索/知识库/课程/作业/文件/日程/消息。
2. 打开 `docs/atomic-skill-catalog.md` 的检索类、课程读写类索引，记下候选 `name`。
3. 在 `docs/atomic-skill-catalog.json` 用 `name` 或中文名过滤 `entries[]`。
4. 读该条 `source_refs`（文件、工作表、行），需要时打开 xlsx 原行。
5. 看 `conflicts[]` 是否点名该 `name`。
6. 填选型表。空 `nid` / `version` 留空，写入 `verification_flags` 原文。

```bash
python - <<'PY'
import json, sys
from pathlib import Path
q = sys.argv[1].lower()
data = json.loads(Path("docs/atomic-skill-catalog.json").read_text())
for e in data["entries"]:
    blob = " ".join(str(e.get(k) or "") for k in ("name","skill_name","chinese_name","function","description"))
    if q in blob.lower():
        print(e["id"], e.get("name"), e.get("nid"), e.get("version"), e.get("source_refs"))
PY
```

`reuse_index.retrieval` / `reuse_index.course` 只是候选入口，不是挂载许可。

## 选型表列

每行必须能指回一条来源：

- 需求点
- 表中名称（`name` 或中文名，保持原文）
- 来源：`file` / `sheet` / `row`
- 角色范围（表中师生/公共原文；表没有就留空）
- 读写：只读 / 写入候选 / 冲突
- `nid`、`version`（空则空）
- `verification_flags`
- 拟挂载顺序（整数，可空直到 grilling 后）
- 备注：功能点而非独立 Skill、目录指纹过期、冲突缩小路径等

## 硬规则

功能点 ≠ 独立可挂载 Skill。同一 `name` 多行只记来源差异，不合并成一个虚构超集。

`classification.*` 是关键词推断，不授予权限。`write_candidate` 为真仍须看原行是否真有写入功能点。

师生角色不能互换：学生技能不写进教师专家的默认挂载，反之亦然，除非原表写明两者。

表中不存在的英文名、占位名、`CAND-`、待补，不当作可挂载 Skill。

官方技能临时失败、缺版本、缺 NID，不是新建同职责 Skill 的理由。在备注写「依赖待观察」，继续用该名称。

## 冲突

`docs/atomic-skill-catalog.md` 已标 `scope_conflict_needs_check` 的名称（当前包括 `polymas-teacher-resource-skills`、`polymas-tool-skills`）：

1. 能缩小到单一功能点（例如只查询不写入）就缩小，并在 Agent.md 写明只用该功能点。
2. 不能缩小就报告冲突，撤下该候选，grilling 是否改需求。
3. 不要默认克隆官方 Skill 做兼容副本。

## 缺口

同时满足才算领域缺口：

1. 选型表没有任何名称覆盖该需求点的核心输出合同。
2. 缺口是专业对象、证据分层、版本发布或领域校验，不是「再做一个检索器」。
3. 工程师在 grilling 中确认要做新平台 Skill。

否则结论为「零新 Skill」。
