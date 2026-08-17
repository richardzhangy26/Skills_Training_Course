# Polymas Skill V5参考手册

---

## 一、Skill 本质

Skill = Markdown 文档 + Python 脚本 + 格式规范。本质是写给 Agent 的"操作说明书"

---

## 二、协作平台与资源

| 资源 | 地址 | 说明 |
|------|------|------|
| Git 仓库 | https://git.zhihuishu.com/polymas/polymas-agent-ext-component/tree/release-branch/skills | Skill 源码 |
| 技能表格 | https://doc.weixin.qq.com/sheet/e3_AV4ArAaBAJoCNCdCLqy1ESO2K84g1?scode=ACwAUgfxABEonXZrpv | Sheet 页说明：`Agent与Skill列表`（上期）、`SKILL开发方向划分`（本期任务）、`SKILL开发日报`（日报） |
| 技能库平台 | https://pds.polymas.com/skills | Skill 发布与管理 |
| 数据平台 | https://daas.polymas.com/actionApp/projectMgt | Skill 接口统一写在：项目管理 > skill技能库 |

**平台登录（预发账号）：**

```
手机号：19990000001
验证码：5556
学校：上海大学
角色：数据平台角色
```

---

## 三、目录结构

```
skill-name/
├── SKILL.md                    # 入口文档（功能定位 + 执行流程 + 约束）
├── references/                 # 详细参考（子技能流程 / 工具参数定义）
├── output_format/              # 输出格式模板（Agent 返回用户的 Markdown/JSON 格式）
└── scripts/
    ├── base/                   # 通用基础模块（各 Skill 共享）
    │   ├── workflow_client.py    工作流 HTTP 客户端（唯一域名硬编码点）
    │   ├── get_token.py          Token 鉴权（走 workflow_client）
    │   ├── load_context.py       运行时上下文（userId/toNid/traceId）
    │   └── academic_tool.py      学期计算工具
    └── *.py                    # 业务脚本
```

---

## 四、两种开发模式

业界（参考 Anthropic《Building Effective Agents》）将 Agent 系统分为两类：

- **Workflow** — 预定义路径编排，确定性高
- **Agent** — LLM 自主决策工具组合，灵活性高

我们目前的 Skill 开发实践中对应为两种模式（还在演进中）：

### 模式A：编排型路由（Workflow Routing）

SKILL.md 作为路由器，意图识别后分发到子技能，每个子技能按固定 Step 串行执行。

**结构特征：**

- SKILL.md：意图识别表 → 子技能映射
- references/ 下每个子技能独立一份流程文档（Step 1 → Step 2 → ... → BUILD）
- Agent 严格按路径执行，无自主判断空间

**参考：** `polymas-teacher-homework-skills`（7 个子技能，覆盖作业全生命周期）

---

### 模式B：工具注册自主型（Tool-Use Agent）

将脚本注册为工具，描述用途/参数/依赖，给出推荐流程，Agent 自主编排。

**结构特征：**
- SKILL.md：工具清单表 + 参数依赖关系图 + 推荐流程 + 强制约束
- references/ 放工具的详细参数和返回结构
- Agent 可跳过非必要步骤，但不得违反强制约束

**参考：** `polymas-teacher-file-import-questions`（7 个工具，线性主流程 + 条件分支）

---

### 对比

| 维度 | 编排型路由 | 工具注册自主型 |
|------|-----------|--------------|
| 确定性 | 高 | 中 |
| 灵活性 | 低 | 高 |
| 典型场景 | 多子功能、CRUD 全覆盖 | 单主线、有条件跳转 |
| Agent 角色 | 执行者 | 决策者 |
| 调试体验 | 按 Step 定位 | 需理解 Agent 决策 |

两种模式各有适用场景，根据业务特征自行判断。也欢迎探索新的模式。

---

## 五、SKILL.md 编写约定

**原则：** 文档描述"干什么"，不描述"怎么干"（实现细节放 references 和 output_format）。

**必含章节：**

```markdown
---
name: "skill-name"
description: "一句话功能描述"
---

## 技能说明
## 触发条件 / 不触发条件
## 项目结构
## 执行流程
## 暂停确认规则（如有）
## 执行流程强制约束
```

**步骤标记约定：** `[CALL]` 调用脚本、`[FILTER]` 过滤、`[BUILD]` 构建输出、`[CONFIRM]` 暂停确认、`[DETERMINE]` 意图识别。

---

## 六、通用基础脚本

以下脚本位于 `scripts/base/`，各 Skill 共享同一份代码。

**强制规则：** 全 Skill 内所有 HTTP 接口调用必须走 `workflow_client.py`，确保整个 Skill 只有 `workflow_client.py` 一处硬编码域名。换域名时只改这一个文件。

### workflow_client.py（唯一域名入口）

全 Skill 唯一硬编码工作流域名的位置。所有业务脚本、`get_token.py` 均通过 `call_workflow` 发起调用。

```python
#!/usr/bin/env python3
"""工作流调用公共模块 — 本技能内所有工作流接口的唯一入口。

本文件是本技能内 **唯一** 硬编码工作流域名与前置路径的位置，
后续换域名只需修改 `WORKFLOW_BASE_URL`。所有业务脚本、鉴权脚本
（get_token.py）都通过 `call_workflow` 发起 HTTP 调用。

网关侧所有 workflow 接口**统一使用 POST**，本客户端不再暴露 method 参数。

bridge 认证机制（兼容两种模式，同时写入以确保最大兼容性）：
  1. 请求体 `userCloudToken` 字段 — bridge StartNode 的 header.authorization 映射到
     `${流程开始/userCloudToken}`，由 bridge 自动提取并转发给下游服务的 Authorization 头。
  2. 请求头 `Authorization` — 直接通过 HTTP 头传递 token，兼容不走 bridge StartNode 映射的旧路由。

调用示例：
  from base.workflow_client import call_workflow
  result = call_workflow("agentClassCreateClass", {"data": payload}, token=token)
  result = call_workflow("oauthGetToken", {"userNid": user_nid})

返回值：解析后的 JSON dict；网络异常或解析失败返回 None（错误详情打印到 stderr）。
"""

import requests
import sys
from typing import Optional, Dict, Any

WORKFLOW_BASE_URL = "https://cloudapi.polymas.com/bridge/service/main/skill/"
TIMEOUT = 60


def call_workflow(
    route: str,
    payload: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    timeout: int = TIMEOUT,
) -> Optional[Dict[str, Any]]:
    url = f"{WORKFLOW_BASE_URL}{route}"
    headers = {"Content-Type": "application/json"}
    body = dict(payload or {})
    if token:
        # 兼容两种认证模式：请求体 userCloudToken + 请求头 Authorization
        body["userCloudToken"] = token
        headers["Authorization"] = token

    try:
        response = requests.post(url, json=body, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"工作流 [{route}] 网络错误：{e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"工作流 [{route}] 调用异常：{e}", file=sys.stderr)
        return None
```

---

### get_token.py

通过 `workflow_client` 调用 `oauthGetToken` 路由获取 Token。**不直接使用 requests**，保持域名唯一入口。

```python
#!/usr/bin/env python3
"""Token 获取公共模块 — 通过工作流接口 oauthGetToken 换取 Token。

本模块内部走 `workflow_client.call_workflow`，不直接调 requests，
以保持整个技能内工作流域名/前置路径的唯一硬编码点在 workflow_client.py。
"""

import sys
from typing import Optional

from base.workflow_client import call_workflow

GET_TOKEN_ROUTE = "oauthGetToken"


def get_token(user_nid: str) -> Optional[str]:
    if not user_nid:
        print("获取Token失败：user_nid 为空", file=sys.stderr)
        return None

    response_data = call_workflow(
        GET_TOKEN_ROUTE,
        {"userNid": user_nid},
    )

    if not response_data:
        return None

    if response_data.get("success") and response_data.get("code") == 200:
        token = response_data.get("data")
        if isinstance(token, str) and token:
            return token
        print("获取Token失败：响应 data 为空或类型异常", file=sys.stderr)
        return None

    msg = response_data.get("msg", "未知原因")
    print(f"获取Token失败：{msg}", file=sys.stderr)
    return None
```

---

### load_context.py

从环境变量加载运行时上下文。平台运行时自动注入 `metadata`、`userId`、`toNid`、`traceId`、`schoolId`、`appCategory`。

```python
#!/usr/bin/env python3
"""
运行时上下文加载工具 — 从环境变量中加载并打印当前用户与会话上下文。

用法:
  python3 load_context.py

依赖环境变量:
  metadata — JSON 字符串（可空对象 `{}`）
  userId   — 当前操作用户 ID
  toNid    — 目标用户 ID
  traceId  — 会话链路追踪 ID
  schoolId — 学校/机构ID
  appCategory — 应用类别
"""
import sys
import json
import os
from typing import Dict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    
# stdin 使用 utf-8-sig：能自动剥离 BOM（PowerShell 管道 / Windows 记事本文件常见），
# 无 BOM 时也兼容普通 UTF-8。注意仅对使用 sys.stdin.read() 的文本模式生效；
# 若脚本使用 sys.stdin.buffer.read()，则需在业务脚本内自行 .decode('utf-8-sig')。
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8-sig')


def load_runtime_context() -> Dict[str, str]:
    metadata_raw = os.getenv("metadata", "{}")
    if not metadata_raw:
        raise RuntimeError("缺少环境变量 metadata（应为 JSON 字符串）")

    try:
        metadata = json.loads(metadata_raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"环境变量 metadata 不是合法 JSON：{e}") from e

    if not isinstance(metadata, dict):
        raise RuntimeError("环境变量 metadata 必须是 JSON 对象")

    user_id = os.getenv("userId")
    to_nid = os.getenv("toNid")
    trace_id = os.getenv("traceId")
    school_id = os.getenv("schoolId")
    app_category = os.getenv("appCategory")

    missing = []
    if not user_id:
        missing.append("userId")
    if not to_nid:
        missing.append("toNid")
    if not trace_id:
        missing.append("traceId")
    if not school_id:
        missing.append("schoolId")
    if not app_category:
        missing.append("appCategory")

    if missing:
        missing_text = "、".join(missing)
        raise RuntimeError(f"缺少必要环境变量字段：{missing_text}")

    return {
        "userId": user_id,
        "toNid": to_nid,
        "traceId": trace_id,
        "schoolId": school_id,
        "appCategory": app_category
    }


def main():
    try:
        context = load_runtime_context()
        print(json.dumps(context, ensure_ascii=False))
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

```



---

### academic_tool.py

学期计算工具类。编号规则：5 位整数，前 4 位结束年份 + 第 5 位学期序号（1=秋冬，2=春夏）。

主要接口：
- `AcademicTool.get_current_term()` → 当前学期编号（如 `20262`）
- `AcademicTool.get_term_name(term)` → 可读名称（如 `"2026年春夏学期"`）
- `AcademicTool.get_all_terms()` → 系统初始化至今所有学期

```python
"""
用途：学期工具类，提供学期编号与名称的互转、当前学期计算等能力
供 polymas-teacher-agent-teaching-gen 及其他需要学期计算的 Skill 调用

对外使用的主要函数：
  - get_current_term() -> int          获取当前学期编号
  - get_term_name(term) -> str         学期编号转可读名称（如 20262 → "2026年春夏学期"）
  - get_all_terms() -> list[Term]      获取从系统初始化至今的所有学期列表

学期编号规则：
  格式为 5 位整数，前 4 位为结束年份，第 5 位为学期序号（1=秋冬，2=春夏）
  示例：20261 = 2025-2026学年秋冬学期，20262 = 2026年春夏学期
"""

from datetime import date, timedelta
from typing import List, Tuple, Optional


class AcademicTool:
    SEMESTER_ONE_START_MONTH = 7
    SEMESTER_ONE_START_DAY = 19
    SEMESTER_ONE_END_MONTH = 2
    SEMESTER_ONE_END_DAY = 13
    SEMESTER_TWO_START_MONTH = 2
    SEMESTER_TWO_START_DAY = 14
    SEMESTER_TWO_END_MONTH = 7
    SEMESTER_TWO_END_DAY = 18
    INIT_YEAR = date(2024, 7, 19)

    NUMER_MAP = {
        1: "一",
        2: "二",
        3: "三",
        4: "四"
    }

    class Term:
        def __init__(self, start_year: Optional[int] = None, end_year: Optional[int] = None, semester: Optional[int] = None):
            self.start_year = start_year
            self.end_year = end_year
            self.semester = semester
            self.start_date = None
            self.end_date = None
            self.term = None

            if start_year and end_year and semester:
                if semester == 1:
                    self.start_date = date(start_year, AcademicTool.SEMESTER_ONE_START_MONTH, AcademicTool.SEMESTER_ONE_START_DAY)
                else:
                    self.start_date = date(end_year, AcademicTool.SEMESTER_TWO_START_MONTH, AcademicTool.SEMESTER_TWO_START_DAY)

                if semester == 1:
                    self.end_date = date(end_year, AcademicTool.SEMESTER_ONE_END_MONTH, AcademicTool.SEMESTER_ONE_END_DAY)
                else:
                    self.end_date = date(end_year, AcademicTool.SEMESTER_TWO_END_MONTH, AcademicTool.SEMESTER_TWO_END_DAY)

                self.term = int(f"{end_year}{semester}")

    @staticmethod
    def get_term_name(term: Optional[int]) -> Optional[str]:
        """
        输入：term(int) — 学期编号，如 20262
        输出：str — 可读学期名称，如 "2026年春夏学期"；term 为 None 时返回 None
        """
        if term is None:
            return None

        year_str = str(term)[:4]
        term_str = str(term)[4:]
        year = int(year_str)

        if term_str == "1":
            year -= 1

        term_type = "秋冬" if term_str == "1" else "春夏"
        return f"{year}年{term_type}学期"

    @staticmethod
    def get_current_term() -> int:
        """
        输入：无
        输出：int — 当前日期所在的学期编号
        """
        term = AcademicTool.get_academic_term(date.today()).term
        return term

    @staticmethod
    def get_yesterday_term() -> int:
        """
        输入：无
        输出：int — 昨天所在的学期编号
        """
        yesterday = date.today() - timedelta(days=1)
        return AcademicTool.get_academic_term(yesterday).term

    @staticmethod
    def get_all_terms() -> List['AcademicTool.Term']:
        """
        输入：无
        输出：list[Term] — 从系统初始化日期至今的所有学期列表，按 term 降序排列
        """
        return AcademicTool.list_all_terms(AcademicTool.INIT_YEAR, date.today())

    @staticmethod
    def get_system_term_date_range(term: str) -> Tuple[date, date]:
        """
        输入：term(str) — 学期编号字符串
        输出：tuple(start_date, end_date) — 该学期的起止日期
        """
        year = int(term[:4])
        semester = int(term[4:5])

        if semester == 1:
            start_date = date(year - 1, AcademicTool.SEMESTER_ONE_START_MONTH, AcademicTool.SEMESTER_ONE_START_DAY)
            end_date = date(year, AcademicTool.SEMESTER_ONE_END_MONTH, AcademicTool.SEMESTER_ONE_END_DAY)
        else:
            start_date = date(year, AcademicTool.SEMESTER_TWO_START_MONTH, AcademicTool.SEMESTER_TWO_START_DAY)
            end_date = date(year, AcademicTool.SEMESTER_TWO_END_MONTH, AcademicTool.SEMESTER_TWO_END_DAY)

        return (start_date, end_date)

    @staticmethod
    def get_academic_term(current_date: date) -> 'AcademicTool.Term':
        """
        输入：current_date(date) — 任意日期
        输出：Term — 该日期所属的学期对象
        """
        second_term_start = date(current_date.year, AcademicTool.SEMESTER_TWO_START_MONTH, AcademicTool.SEMESTER_TWO_START_DAY)
        second_term_end = date(current_date.year, AcademicTool.SEMESTER_TWO_END_MONTH, AcademicTool.SEMESTER_TWO_END_DAY)
        first_term_start = date(current_date.year, AcademicTool.SEMESTER_ONE_START_MONTH, AcademicTool.SEMESTER_ONE_START_DAY)
        first_term_end = date(current_date.year + 1, AcademicTool.SEMESTER_ONE_END_MONTH, AcademicTool.SEMESTER_ONE_END_DAY)

        if not (current_date >= second_term_start and current_date < second_term_end):
            if not (current_date >= first_term_start and current_date < first_term_end):
                if current_date < first_term_start:
                    return AcademicTool.Term(current_date.year - 1, current_date.year, 1)
                else:
                    return AcademicTool.Term()
            else:
                return AcademicTool.Term(current_date.year, current_date.year + 1, 1)
        else:
            return AcademicTool.Term(current_date.year - 1, current_date.year, 2)

    @staticmethod
    def get_academic_term_next(current_date: date) -> 'AcademicTool.Term':
        """
        输入：current_date(date)
        输出：Term — 下一个学期对象
        """
        term_info = AcademicTool.get_academic_term(current_date)

        if term_info.semester == 2:
            return AcademicTool.Term(term_info.start_year + 1, term_info.end_year + 1, 1)
        else:
            return AcademicTool.Term(term_info.start_year, term_info.end_year, 2)

    @staticmethod
    def list_all_terms(start_date: date, end_date: date) -> List['AcademicTool.Term']:
        """
        输入：start_date(date), end_date(date)
        输出：list[Term] — 该时间范围内所有学期，按 term 降序排列
        """
        terms = []
        current_date = start_date

        while current_date <= end_date:
            term_info = AcademicTool.get_academic_term(current_date)

            exists = any(
                t.start_year == term_info.start_year and
                t.end_year == term_info.end_year and
                t.semester == term_info.semester
                for t in terms
            )

            if not exists:
                terms.append(term_info)

            if term_info.semester == 2:
                current_date = date(current_date.year, AcademicTool.SEMESTER_TWO_END_MONTH, AcademicTool.SEMESTER_TWO_END_DAY + 1)
            elif term_info.semester == 1:
                current_date = date(current_date.year + 1, AcademicTool.SEMESTER_ONE_END_MONTH, AcademicTool.SEMESTER_ONE_END_DAY + 1)
            else:
                break

        terms.sort(key=lambda x: x.term, reverse=True)
        return terms

    @staticmethod
    def get_current_term_list() -> List[int]:
        """
        输入：无
        输出：list[int] — 当前有效的学期编号列表（秋冬学期返回单个，春夏学期返回同年多个）
        """
        academic_term = AcademicTool.get_academic_term(date.today())
        term = academic_term.term

        if str(term).endswith("1"):
            return [term]
        else:
            year = str(term)[:4]
            return [int(f"{year}2"), int(f"{year}3"), int(f"{year}4")]

    @staticmethod
    def spoc_conver_ai(start_year: str, end_year: str, term: int) -> str:
        """SPOC 学期格式转 AI 学期编号"""
        return f"{end_year}{term}"

    @staticmethod
    def ai_conver_spoc(term_str: str) -> str:
        """AI 学期编号转 SPOC 可读格式，如 20262 → '2025-2026学年第二学期'"""
        end_year = int(term_str[:4])
        term = int(term_str[4:5])
        return f"{end_year - 1}-{end_year}学年第{AcademicTool.NUMER_MAP.get(term)}学期"


def main():
    term = AcademicTool.get_current_term()
    print(f"当前学期: {term}")
    print(f"当前学期名称: {AcademicTool.get_term_name(term)}")

if __name__ == "__main__":
    main()

```



---

## 七、常用复用脚本

> ⚠️ **课程搜索脚本分教师端 / 学生端两个版本，结构一致但路由不同，不可混用**：
> - **教师端**：`course_search.py`（路由 `courseSearch`）→ 见 7.1
> - **学生端**：`course_search.py`（路由 `studentCourseSearch`）→ 见 7.2

### 7.1 course_search.py【教师端】

> 🟦 **教师端脚本**：路由 `courseSearch`，面向教师关联课程。学生端技能请勿使用本版本，改用 7.2。

多个 Skill 共用的课程搜索能力（作业、活动、成绩等 Skill 都需要先定位课程）。注意：已改为走 `call_workflow`，不直接 requests。

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --name, -n | string | 否 | 课程名称关键词，模糊搜索；不传则查询所有课程 |
| --term, -t | int | 否 | 学期编号，5位整数。格式：`{年份}{学期序号}`，前4位为学年结束年份，第5位为 `1`（秋冬学期）或 `2`（春夏学期）。示例：`20262` = 2025-2026学年春夏学期，`20271` = 2026-2027学年秋冬学期。不传时查询所有学期的课程 |

#### 输出格式（结构化 JSON）

| 场景 | 输出结构 | 说明 |
|------|---------|------|
| 有课程（指定学期） | `{"courses": [...], "term": 20271, "termName": "2026年秋冬学期"}` | courses 为课程对象数组 |
| 有课程（所有学期） | `{"courses": [...], "term": null, "termName": "所有学期"}` | term 为 null 表示查询所有学期 |
| 无课程（指定学期） | `{"courses": [], "term": 20271, "termName": "...", "availableTerms": [...]}` | 自动附带可选学期列表 |
| 无课程（所有学期） | `{"courses": [], "term": null, "termName": "所有学期"}` | 不返回 availableTerms |
| 智能体代表课程 | `{"courses": [{...}], "term": 20262, "termName": null}` | appCategory=AI_COURSE_REPRESENTATIVE 时走专用接口，忽略学期/模糊搜索，返回单课程 |
| 错误 | `{"error": "课程搜索失败：xxx"}` | 接口异常或 Token 获取失败 |

`availableTerms` 数组每项格式：`{"term": 20271, "name": "2026年秋冬学期", "isCurrent": true}`

`courses` 数组每项主要字段：`courseId`（课程ID）、`courseName`（课程名称）、`courseType`（课程类型标识，如 agent、spoc 等）、`courseTypeDesc`（课程类型中文描述，与 courseType 对应）

#### 调用示例

```bash
# 查询所有学期所有课程
python3 scripts/course_search.py

# 查询所有学期包含"数学"的课程
python3 scripts/course_search.py --name 数学

# 查询指定学期的所有课程
python3 scripts/course_search.py --term 20262

# 查询指定学期包含"英语"的课程
python3 scripts/course_search.py --name 英语 --term 20271

# 查看帮助
python3 course_search.py --help
```

#### Agent 调用约束（参考）

1. **学期参数处理**：用户未指定学期时不传 `--term`（查询所有学期的课程，不默认取当前学期）；用户指定了学期时，尝试提取为合法的 5 位整数（前4位年份 + 第5位 1 或 2），若提取失败则先调用 `academic_tool.py` 获取所有学期列表供用户选择。

2. **空结果引导**：仅在查询**指定学期**且输出中包含 `availableTerms` 字段时（即 `courses` 为空列表），Agent 应直接从该字段提取学期列表，引导用户切换学期；查询所有学期仍为空说明确实没有课程，直接提示用户即可。

3. **错误处理**：当脚本输出中包含 `error` 字段时，将错误消息以自然语言提示给用户。

4. **智能体代表课程分支**：当运行时上下文 `appCategory == "AI_COURSE_REPRESENTATIVE"` 时，脚本自动走专用接口（`getCourseInfoByAgentCode`），忽略 `--name`/`--term` 参数，直接返回该 toNid 对应的单门智能体课程。Agent 无需引导学期选择或模糊搜索。


> **设计要点**：仅在查询指定学期且结果为空时，脚本才返回 `availableTerms` 字段供 Agent 引导用户切换学期；查询所有学期为空时不返回该字段，Agent 直接提示用户没有课程即可。

#### 脚本源码

```python
#!/usr/bin/env python3
"""
课程搜索工具 — 搜索教师关联课程信息。

用法:
  python3 scripts/course_search.py [--name 课程名] [--term 学期]

参数:
  --name, -n  — 课程名称关键词（可选，模糊搜索，不传则查询所有课程）
  --term, -t  — 学期编号（可选，5位整数：前4位为学年结束年份，
                第5位为 1=秋冬 或 2=春夏；不传则查询所有学期的课程）
                示例：20262 = 2025-2026学年春夏学期

输出格式（结构化 JSON）:
  有课程(指定学期): {"courses": [...], "term": 20271, "termName": "2026年秋冬学期"}
  有课程(所有学期): {"courses": [...], "term": null, "termName": "所有学期"}
  无课程(指定学期): {"courses": [], "term": 20271, "termName": "...", "availableTerms": [...]}
  无课程(所有学期): {"courses": [], "term": null, "termName": "所有学期"}
  错误:   {"error": "课程搜索失败：xxx"}

  term 为 null 表示查询所有学期；仅在查询指定学期且结果为空时才返回
  availableTerms 引导用户切换学期；查询所有学期仍为空说明确实没有课程，
  不返回 availableTerms。

  courses 数组每项主要字段：
    courseId       — 课程ID
    courseName     — 课程名称
    courseType     — 课程类型标识（如 agent、spoc 等）
    courseTypeDesc — 课程类型中文描述（与 courseType 对应）

依赖环境变量:
  userId, toNid, traceId, appCategory — 由运行时上下文自动注入

特殊分支:
  当 appCategory == "AI_COURSE_REPRESENTATIVE" 时，绕过 courseSearch 接口，
  改用 getCourseInfoByAgentCode 接口（传参 agentCode=toNid）查询智能体代表课程，
  忽略 --name/--term 参数，直接返回单课程结果的 courses 数组。
"""
import sys
import json
import argparse
from typing import Optional, Dict, Any, List

from base.academic_tool import AcademicTool
from base.load_context import load_runtime_context
from base.get_token import get_token
from base.workflow_client import call_workflow

COURSE_SEARCH_ROUTE = "courseSearch"
AGENT_COURSE_QUERY_ROUTE = "getCourseInfoByAgentCode"
AI_COURSE_REPRESENTATIVE = "AI_COURSE_REPRESENTATIVE"


def _build_available_terms(current_term: int) -> List[Dict[str, Any]]:
    """构建可选学期列表，标注当前学期。"""
    all_terms = AcademicTool.get_all_terms()
    result = []
    for t in all_terms:
        result.append({
            "term": t.term,
            "name": AcademicTool.get_term_name(t.term),
            "isCurrent": t.term == current_term
        })
    return result


def _query_agent_course(to_nid: str, token: str) -> Dict[str, Any]:
    """通过 getCourseInfoByAgentCode 接口按 agentCode 查询智能体代表课程。

    传参仅 agentCode（取 toNid），返回单个课程对象，按原 courses 数组项
    字段结构构建后放入 courses 数组返回。忽略学期与模糊搜索。
    """
    response_data = call_workflow(AGENT_COURSE_QUERY_ROUTE, {"agentCode": to_nid}, token=token)
    if not response_data:
        return {"error": "课程搜索失败：接口无响应"}

    if response_data.get("data"):
        course_data = response_data.get("data")
        course = {
            "courseId": course_data.get("courseId"),
            "courseName": course_data.get("courseName"),
            "courseType": course_data.get("courseType"),
            "courseTypeDesc": course_data.get("courseTypeDesc")
        }
        return {
            "courses": [course],
            "term": course_data.get("term"),
            "termName": None
        }

    msg = response_data.get("msg", "未知原因")
    return {"error": f"课程搜索失败：{msg}"}


def course_search(user_nid: str, to_nid: str, course_name: str, term: Optional[int] = None, app_category: Optional[str] = None) -> Dict[str, Any]:
    """执行课程搜索，返回结构化结果字典。

    term 为 None 时不传学期字段，查询所有学期的课程；
    term 不为 None 时查询指定学期的课程。

    当 app_category == AI_COURSE_REPRESENTATIVE 时，绕过常规搜索，
    直接通过 getCourseInfoByAgentCode 接口按 agentCode(=toNid) 查询智能体代表课程，
    忽略 course_name/term 参数，返回单课程结果。
    """
    token = get_token(user_nid)
    if not token:
        return {"error": "课程搜索失败：无法获取 Token"}

    # appCategory 为智能体课程代表时，走专用接口，忽略学期与模糊搜索
    if app_category == AI_COURSE_REPRESENTATIVE:
        return _query_agent_course(to_nid, token)

    # term 为 None 时查询所有学期，不传 term 字段给接口
    if term is not None:
        term_name = AcademicTool.get_term_name(term)
        payload = {
            "userNid": user_nid,
            "term": term,
            "toNid": to_nid,
            "courseName": course_name or ""
        }
    else:
        term_name = "所有学期"
        payload = {
            "userNid": user_nid,
            "toNid": to_nid,
            "courseName": course_name or ""
        }

    response_data = call_workflow(COURSE_SEARCH_ROUTE, payload, token=token)
    if not response_data:
        return {"error": "课程搜索失败：接口无响应"}

    if response_data.get("data") is not None:
        courses = response_data.get("data")
        result = {
            "courses": courses,
            "term": term,
            "termName": term_name
        }
        # 仅在查询指定学期且结果为空时，才返回可选学期列表引导用户切换学期
        # 查询所有学期仍为空说明确实没有课程，无需引导切换
        if not courses and term is not None:
            result["availableTerms"] = _build_available_terms(term)
        return result

    msg = response_data.get("msg", "未知原因")
    return {"error": f"课程搜索失败：{msg}"}


def main() -> None:
    parser = argparse.ArgumentParser(description='课程搜索工具')
    parser.add_argument('--name', '-n', dest='courseName', default='',
                        help='课程名称关键词（模糊搜索，不传查所有）')
    parser.add_argument('--term', '-t', dest='term', type=int, default=None,
                        help='学期编号（5位整数，不传则查询所有学期）')
    args = parser.parse_args()

    context = load_runtime_context()
    result = course_search(context["userId"], context["toNid"], args.courseName, args.term, context.get("appCategory"))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

```

---

### 7.2 course_search.py【学生端】

> 🟩 **学生端脚本**：路由 `studentCourseSearch`，面向学生关联课程。教师端技能请勿使用本版本，改用 7.1。

与 7.1 教师端同构的课程搜索能力（学生版教学计划、讨论、成绩等 Skill 先定位课程）。**参数说明、输出格式、调用示例、Agent 调用约束与 7.1 完全一致**，差异仅在：

| 差异点 | 教师端（7.1） | 学生端（7.2） |
|--------|--------------|--------------|
| 课程搜索路由 | `courseSearch` | `studentCourseSearch` |
| 适用技能 | 教师端 Skill | 学生端 Skill |

`appCategory=AI_COURSE_REPRESENTATIVE` 智能体代表课程分支两端一致（均走 `getCourseInfoByAgentCode`）。

#### 脚本源码

```python
#!/usr/bin/env python3
"""课程搜索工具 — 搜索学生关联课程信息。

用法:
  python3 scripts/course_search.py [--name 课程名] [--term 学期]

参数:
  --name, -n  — 课程名称关键词（可选，模糊搜索，不传则查询所有课程）
  --term, -t  — 学期编号（可选，5位整数：前4位为学年结束年份，
                第5位为 1=秋冬 或 2=春夏；不传则查询所有学期的课程）
                示例：20262 = 2025-2026学年春夏学期

输出格式（结构化 JSON）:
  有课程(指定学期): {"courses": [...], "term": 20271, "termName": "2026年秋冬学期"}
  有课程(所有学期): {"courses": [...], "term": null, "termName": "所有学期"}
  无课程(指定学期): {"courses": [], "term": 20271, "termName": "...", "availableTerms": [...]}
  无课程(所有学期): {"courses": [], "term": null, "termName": "所有学期"}
  错误:   {"error": "课程搜索失败：xxx"}

  term 为 null 表示查询所有学期；仅在查询指定学期且结果为空时才返回
  availableTerms 引导用户切换学期；查询所有学期仍为空说明确实没有课程，
  不返回 availableTerms。

  courses 数组每项主要字段：
    courseId       — 课程ID
    courseName     — 课程名称
    courseType     — 课程类型标识（如 agent、spoc 等）
    courseTypeDesc — 课程类型中文描述（与 courseType 对应）

依赖环境变量:
  userId, toNid, metadata — 由运行时上下文自动注入

特殊分支:
  当 appCategory == "AI_COURSE_REPRESENTATIVE" 时，绕过 studentCourseSearch 接口，
  改用 getCourseInfoByAgentCode 接口（传参 agentCode=toNid）查询智能体代表课程，
  忽略 --name/--term 参数，直接返回单课程结果的 courses 数组。
"""
import json
import argparse
from typing import Optional, Dict, Any, List

from base.academic_tool import AcademicTool
from base.load_context import load_runtime_context
from base.get_token import get_token
from base.workflow_client import call_workflow

COURSE_SEARCH_ROUTE = "studentCourseSearch"
AGENT_COURSE_QUERY_ROUTE = "getCourseInfoByAgentCode"
AI_COURSE_REPRESENTATIVE = "AI_COURSE_REPRESENTATIVE"


def _build_available_terms(current_term: int) -> List[Dict[str, Any]]:
    """构建可选学期列表，标注当前学期。"""
    all_terms = AcademicTool.get_all_terms()
    result = []
    for t in all_terms:
        result.append({
            "term": t.term,
            "name": AcademicTool.get_term_name(t.term),
            "isCurrent": t.term == current_term
        })
    return result


def _query_agent_course(to_nid: str, token: str) -> Dict[str, Any]:
    """通过 getCourseInfoByAgentCode 接口按 agentCode 查询智能体代表课程。

    传参仅 agentCode（取 toNid），返回单个课程对象，按原 courses 数组项
    字段结构构建后放入 courses 数组返回。忽略学期与模糊搜索。
    """
    response_data = call_workflow(AGENT_COURSE_QUERY_ROUTE, {"agentCode": to_nid}, token=token)
    if not response_data:
        return {"error": "课程搜索失败：接口无响应"}

    if response_data.get("data"):
        course_data = response_data.get("data")
        course = {
            "courseId": course_data.get("courseId"),
            "courseName": course_data.get("courseName"),
            "courseType": course_data.get("courseType"),
            "courseTypeDesc": course_data.get("courseTypeDesc")
        }
        return {
            "courses": [course],
            "term": course_data.get("term"),
            "termName": None
        }

    msg = response_data.get("msg", "未知原因")
    return {"error": f"课程搜索失败：{msg}"}


def course_search(user_nid: str, to_nid: str, course_name: str, term: Optional[int] = None, app_category: Optional[str] = None) -> Dict[str, Any]:
    """执行课程搜索，返回结构化结果字典。

    term 为 None 时不传学期字段，查询所有学期的课程；
    term 不为 None 时查询指定学期的课程。

    当 app_category == AI_COURSE_REPRESENTATIVE 时，绕过常规搜索，
    直接通过 getCourseInfoByAgentCode 接口按 agentCode(=toNid) 查询智能体代表课程，
    忽略 course_name/term 参数，返回单课程结果。
    """
    token = get_token(user_nid)
    if not token:
        return {"error": "课程搜索失败：无法获取 Token"}

    # appCategory 为智能体课程代表时，走专用接口，忽略学期与模糊搜索
    if app_category == AI_COURSE_REPRESENTATIVE:
        return _query_agent_course(to_nid, token)

    # term 为 None 时查询所有学期，不传 term 字段给接口
    if term is not None:
        term_name = AcademicTool.get_term_name(term)
        payload = {
            "userNid": user_nid,
            "term": term,
            "toNid": to_nid,
            "courseName": course_name or ""
        }
    else:
        term_name = "所有学期"
        payload = {
            "userNid": user_nid,
            "toNid": to_nid,
            "courseName": course_name or ""
        }

    response_data = call_workflow(COURSE_SEARCH_ROUTE, payload, token=token)
    if not response_data:
        return {"error": "课程搜索失败：接口无响应"}

    if response_data.get("data") is not None:
        courses = response_data.get("data")
        result = {
            "courses": courses,
            "term": term,
            "termName": term_name
        }
        # 仅在查询指定学期且结果为空时，才返回可选学期列表引导用户切换学期
        # 查询所有学期仍为空说明确实没有课程，无需引导切换
        if not courses and term is not None:
            result["availableTerms"] = _build_available_terms(term)
        return result

    msg = response_data.get("msg", "未知原因")
    return {"error": f"课程搜索失败：{msg}"}


def main() -> None:
    parser = argparse.ArgumentParser(description='课程搜索工具')
    parser.add_argument('--name', '-n', dest='courseName', default='',
                        help='课程名称关键词（模糊搜索，不传查所有）')
    parser.add_argument('--term', '-t', dest='term', type=int, default=None,
                        help='学期编号（5位整数，不传则查询所有学期）')
    args = parser.parse_args()

    context = load_runtime_context()
    result = course_search(context["userId"], context["toNid"], args.courseName, args.term, context.get("appCategory"))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

```

---

## 八、交互设计：意图澄清与暂停确认

> **本章定位**：技能与用户交互设计的统一规范。8.1–8.8 为通用交互规范（含改造自检清单），8.9 为全局强制的学期前置校验。各技能的 SKILL.md 应引用本章而非重复定义。

### 8.1 交互总原则

**工具铁律**：一套任务流程在结束前需要用户提供信息时，**必须调用 `ask_user_question` 工具**当场发起交互，禁止"输出一段提示文本然后结束本轮对话、等用户下一轮自己回复"。

**三条递进原则**：

1. **能让用户点选的，绝不让用户打字**——凡是候选集有限且已知，全部渲染为选项
2. **必须由用户主观输入的，先给推荐再留出口**——生成至少 3 个符合当前上下文的推荐选项，同时在调用中**显式要求提供一个可自定义输入的选项**，让用户既能一键选中推荐，也能自己填写
3. **不替用户做主观决定**——凡是影响结果且取决于用户偏好的取值，都要问，不允许用"默认全选""默认第一个""自动生成"静默略过

**意图澄清的两条裁量**：

1. **能推断就不追问**——上下文足以确定意图时（如当前只有一门课程），直接执行
2. **必须追问时，给出选项而非开放提问**——按 [8.2](#82-四种交互模式不限于这四种) 模式 4 渲染可能意图供用户点选

### 8.2 四种交互模式（不限于这四种）

按交互的**性质**选择模式，不要按场景名称机械对应：

| 模式 | 适用场景 | 自定义输入项 | 选项要求 |
|------|---------|------------|---------|
| **模式 1 · 二选一确认** | 执行前的最后一道闸门（写入、发布、删除、修改等写操作；触发时机按 [8.7](#87-确认环节的条件化免确认判定) 判定） | 不提供 | 两个选项，文本用**具体动作动词**而非泛化的"是/否"，如"发布 / 我再改改"、"确认删除 / 取消"。待确认的完整信息写进问题文本 |
| **模式 2 · 已知候选集选择** | 从接口返回数据、枚举值、已有列表中选择 | 不提供 | 有多少项就渲染多少项，不做截断。选项文本必须是人类可读的业务标识，**技术 ID 一律不出现在选项里**；用户选定后由模型从缓存数据中回查对应 ID。单个字段不足以区分时，拼接关键区分字段，用多个空格分隔。语义上允许选多项时，开启多选 |
| **模式 3 · 推荐 + 自定义** | 需要用户主观产出内容或取值的场景（如定标题、定分值、写描述） | 必须提供 | 生成至少 3 个贴合当前上下文、彼此有实际区分度的推荐项。**必须显式要求提供可自定义输入的选项**。推荐内容较长时可用 Markdown 列表先输出候选（标 A/B/C），再用工具渲染"选择 A··""选择 B··"等选项 + 自定义输入项 |
| **模式 4 · 意图澄清** | 请求不明确、存在多种合理解释时 | 必须提供 | 把可能的意图全部渲染为选项，配简短说明帮用户区分。**必须显式要求提供可自定义输入的选项** |

> **布尔/枚举类参数的特别要求**：不要用"是否 XX"提问，把每个取值翻译成自然语言的完整表述作为选项。例如"允许多次回复 / 仅回复一次"，而不是"是否允许多次回复：是 / 否"。这类参数候选已穷尽，不开启自定义输入项。多个相关参数可在单次调用中并行提问。

### 8.3 是否提供自定义输入项：统一判据

自定义输入入口**不会自动出现**，需要在调用时明确要求。是否要求，取决于一个判断：**已列出的候选项能否穷尽用户的合理意图？**

- **能穷尽 → 不提供**。如二选一确认、从接口返回的数据中选一条。此时开启自定义输入反而会让用户填出系统无法处理的内容（如手写一个不存在的班级名），或让确认语义变得模糊
- **不能穷尽 → 必须提供**。如让用户定标题、定分值、写内容、澄清意图。推荐项再多也只是示例，用户真实需求可能都不在其中

### 8.4 选项字段拼接规范

当选项需要拼接多个字段时，遵循以下方法：

- **主标识字段**（用户认知中的名字）+ **最能消除歧义的辅助字段**（类型、时间、规模、状态等），用多个空格分隔
- 辅助字段为空时省略，只保留主字段
- **技术 ID 一律不出现在选项文本中**

### 8.5 暂停确认（CONFIRM 步骤）的执行语义

技能文档中标注 **[CONFIRM]** 的步骤 = 必须在此处调用 `ask_user_question` 工具发起交互并等待返回。两条执行要求：

1. **真正等待**——工具调用发出后，必须等用户作出选择再继续；⛔ 严禁 Agent 自行假设用户决策（如默认"用户会选确认"）而跳过等待直接推进
2. **尊重选择**——以用户选择的结果继续后续步骤，不可忽略或覆盖用户的选择

### 8.6 业务目标定位：精确匹配校验（路径 A/B）

很多流程存在「先查询业务列表 → 再确定目标」的环节（课程、班级、题库、课次、文件夹等）。这类环节的交互量取决于一个前置判断：**用户是否已经告诉了你要操作哪个目标？**

**核心思想**：用户已明确给出目标时，「选择环节」的本质就变成了「校验环节」——用用户提供的数据在可操作数据里做**存在校验**，而不是把列表原样摆回去让用户再选一遍。用户说"把文件放到 A 课程的 B 课次"时，再让他从课程列表里选一次 A，是对用户已提供信息的浪费。

**路径 A：用户已提供精确名称或 ID（或上下文明确正在操作该业务）**

1. **照常查询**：调用查询脚本获取可操作数据全集（查询仍要执行，因为校验需要全集、后续传参需要 ID）
2. **精确匹配校验**：用用户提供的名称/ID 在返回全集中做精确匹配——ID 全等优先，其次名称全字符相等；**不做模糊/包含匹配**（匹配越宽松，"替用户认错目标"的风险越大）
   - **唯一命中** → 直接静默采用，无需用户确认或选择，在结果中回显该业务名称
   - **多个命中**（同名不同实例，如不同学期的同名课程）→ 调用 `ask_user_question`（模式 2）**仅渲染命中的候选项**供用户选择
   - **未命中** → 如实告知「未找到 {名称/ID} 对应的{业务}」，**并将查询到的全集数据渲染为选项（模式 2）供用户重新选择**——告知与兜底选择缺一不可，只告知不重选会把用户堵死
3. **黑盒铁律**：查询脚本一律当作黑盒执行，**绝对禁止因未查到/未命中而自行篡改参数重复查询**（如去掉过滤条件、更换关键字、切换学期重试）。正常流程没查到就代表不存在，按「未命中」处理。篡改参数重查会破坏"查不到即不存在"这一结论的可信度，也让失败原因变得不可解释

**路径 B：用户未提供前置信息**

维持原流程：查询后直接渲染全集选项供用户选择（模式 2），不做任何预匹配。

**两个推论**：

- **自行匹配优先于脚本筛选参数**：若查询脚本的筛选参数（如模糊搜索关键字）后端实现不可靠（过滤被忽略、规则不透明），应放弃该参数，改为查全集后自行精确匹配。只有匹配逻辑在自己手里，"查不到即不存在"的结论才成立
- **用户直接给了 ID 也要校验**：ID 可能过期、可能不属于当前用户。校验同时附带拿到名称等展示字段，一举两得

**上下文复用判定（跨任务场景）**：历史任务操作过的业务对象是否算「上下文明确正在操作该业务」，按信号强度分级，**指代性语言是分水岭**：

| 信号档位 | 特征 | 处理方式 |
|---------|------|--------|
| 强信号 | 指代性语言（"这个课程""刚才那个""继续"）、同一业务链的紧邻子任务（创建合集→发布合集）、用户再次报出精确名称/ID | 属「上下文明确」，走路径 A：校验后静默采用并回显（如"沿用《高等数学》"） |
| 弱信号 | 近期操作过某对象，但新请求没有任何指代（如创建合集后只说"帮我备课"） | **不静默复用**（读操作同样不静默）——走模式 2 全集选择，但将最近操作对象**置顶为推荐项**（label 前加"最近操作"标注） |
| 无信号 | 话题已切换、中间隔了其他任务、或请求中提到了其他对象 | 纯路径 B，不考虑历史 |

三条护栏：

1. **复用候选必须过精确匹配校验**——历史对象可能已删除或已无权访问；校验不过走未命中分支，不能因"是上下文里的"就放行
2. **复用按业务维度独立判定**——复用课程不等于复用课次；上一任务未涉及的维度照常选择，不把上一任务的对象整包继承
3. **静默复用必须回显**——一句话说明沿用了哪个对象，给用户可打断的机会

> 宽严取向的依据：误复用的代价（写错位置需清理、读错数据需纠正）高于误重选的代价（多一轮点选），故弱信号一律「存疑即问」，读写操作对齐。

### 8.7 确认环节的条件化：免确认判定

模式 1 确认是写操作的常规闸门，但**不应无条件触发**。判断标准是看确认环节还有没有"信息量"：

**确认环节的价值 = 让用户审阅他没见过、没拍板的信息。** 如果一路走来所有关键参数都是用户自己提供、自己选定、或经校验命中的，确认页面上没有任何新信息，再确认一遍就是纯摩擦。

- **免确认**：全部关键参数可溯源到用户（明确提供 / 交互选定 / 校验命中）→ 以普通文本输出**非阻塞计划概要**（写清将要执行的内容与推断值）后直接执行。信息透明依然保留——用户看到概要有异议可以随时打断，但不强制他再点一次"确认"
- **需确认**：核心要素缺失、由 Agent 代为设计/组装方案时（如用户只说"出一套练习"，题型分布与数量由 Agent 自行设计）→ 保留模式 1 确认。Agent 替用户做的**实质性设计**必须经用户拍板

**三个边界**：

- **文档既定规则的机械映射不算"替用户做主观决定"**（如按题型映射表确定考核目标、未指定难度默认中等）。这类推断值不需要确认，但必须在计划概要或结果中**透明展示**，让用户事后可追溯
- **要写入数据库的名称类取值不受免确认保护**：名称（题目本名、文件夹名等）即使用户没提，也必须经模式 3（推荐+自定义）由用户选定，禁止模型静默生成后直接写入
- **不可逆操作不适用免确认**：删除、发布等不可逆操作即使参数全部可溯源到用户，仍须保留模式 1 确认作为最后闸门（与 9.5 一致）；免确认仅适用于轻量可逆的写操作

**调用链传递（附采信条件）**：多层架构（专家 → 技能 → 子技能）中，同一份信息在链路任一环节被用户**明确批准**过后，下游环节不再重复确认，下游只对自身新增/变更的部分发起确认。采信需同时满足：

1. **可见可核对**：上游的确认过程在当前对话上下文中可见，且能逐项核对确认内容（单项选择、推荐采纳不等于对整体计划的确认）
2. **逐项一致**：下游将执行的内容与上游确认的内容逐项一致；下游新增/变更的取值仍需确认，或在非阻塞概要中显著标注
3. **轻量可逆**：删除、发布等不可逆操作不受此规则豁免，仍须本层确认

**存疑即确认**——免确认是例外，采信条件全部由下游举证满足；任何一个条件不满足或无法判定时，回退为正常确认。

### 8.8 改造完成后自检

- 全文检索并清零旧式交互残留：提示格式、请输入、输入"确认"、输入其他内容取消、等待用户回复、让用户选择、展示列表供用户选择，以及任何自定义的表单 JSON 结构
- 确认每个子技能文档都已引用统一规范章节
- 确认每个写操作前都有模式 1 确认环节，或满足免确认判定条件时以非阻塞计划概要替代
- 确认每个模式 3 / 模式 4 交互点都标注了需提供自定义输入项，每个模式 1 / 模式 2 交互点都标注了不提供
- 确认没有任何选项文本里裸露技术 ID
- 确认文档中没有出现工具的底层字段名或参数结构

### 8.9 学期前置校验（全局强制）

所有**新业务增删改操作**（写入服务端数据的操作）执行前，必须校验上下文中的学期是否为**本学期**，如果是对已有数据进行删改或增加其子数据那么学期应来自于母数据本身的学期。纯查询操作不受此规则限制，支持任意学期（包括历史学期）。

#### 校验逻辑

1. 在执行写入操作前，调用 `AcademicTool.get_current_term()` 获取本学期编号
2. 将本学期与上下文中的学期（用户传入或 Step 2 选定的学期）对比
3. 根据对比结果处理：

| 上下文学期 | 校验结果 | 处理方式 |
|-----------|---------|----------|
| = 本学期 | ✅ 通过 | 静默通过，正常执行写入操作 |
| ≠ 本学期 | ❌ 拦截 | 调用 `ask_user_question` 工具（模式 1，不提供自定义输入项）告知用户该操作仅支持本学期，询问是否切换 |

#### 拦截交互方式

调用 `ask_user_question` 工具（按 [8.2 四种交互模式](#82-四种交互模式不限于这四种) 模式 1，不提供自定义输入项），问题文本为「当前上下文学期为 {上下文学期名称}，{操作描述}仅支持对本学期（{本学期名称}）数据进行操作。是否切换到本学期执行？」，选项为：
- 「切换到本学期执行」（description: 将学期更新为本学期后继续执行）
- 「取消操作」（description: 终止当前操作）

- 用户选「切换到本学期执行」 → 将上下文学期更新为 `get_current_term()` 返回值，后续所有操作（含查询链路）均使用本学期
- 用户选「取消操作」 → 终止当前操作，告知用户已取消

#### 适用操作范围

所有**写入服务端的操作**（增删改）都必须进行学期前置校验。各技能应在自己的 SKILL.md 中明确列出需要校验的具体操作清单。

**配置指导**：
- 在 SKILL.md 的「学期前置校验规则」章节中，使用表格列出该技能所有需要校验的写入操作
- 按子技能分组，清晰标注每个操作对应的写入类型（创建/修改/删除/导入等）
- 参考格式：

```markdown
### 适用操作范围

| 子技能 | 需校验的写入操作 |
|--------|----------------|
| 子技能A | 操作1（类型）、操作2（类型）、操作3（类型） |
| 子技能B | 操作1（类型）、操作2（类型） |
```

#### 不受影响的操作

所有**纯查询**操作（查询列表、详情、统计数据等）支持任意学期，包括历史学期，**无需校验**。

#### 实现要求

- 在 SKILL.md 中添加「学期前置校验规则（全局强制）」章节
- 在执行流程强制约束中添加对应约束项
- 在各子技能的写入操作步骤中引用该规则

---

## 九、通用经验沉淀（AI 参考语料）

> **本章定位**：本章是从历次 Skill 开发中沉淀的泛化经验，供编写新 Skill 时参考，也可作为 AI 语料直接投喂。
>
> **优先级约定**：本章内容为经验性建议，非强制规范。**当用户（需求方）对某方面给出明确说明时，一律以用户说明为准，本章优先级次之**；若用户说明与本章经验存在较大冲突、难以调和，应先向用户确认后再执行，不要自行取舍。
>
> 各节只给思路与判断方法，不给唯一答案——具体实现形态留给编写者按业务实际发挥。

### 9.1 学期（term）处理经验

学期是多数业务接口的必传参数，核心不是背规则，而是先给操作**分类**：

1. **先问一句："换了学期，这个请求还成立吗？"**
   - 不成立（如发布通知、创建话题）→ 该操作是**根实体创建**，学期锚定当前学期，不是用户可选变量。实现上可以让脚本内部直接取当前学期、甚至不提供 `--term` 参数，从结构上杜绝历史学期写入，比文档约束更可靠
   - 成立但作用于已有数据（如给某话题回帖、删除某条记录）→ **依附操作**，学期沿用宿主数据自身的学期（数据自治）。实现上可把 `--term` 设为必传、缺失即报错（fail fast），迫使调用方显式带上定位数据时所用的学期
   - 成立且纯读取 → **查询操作**，尊重用户指定；未指定时默认当前学期
2. **空结果的引导方向取决于分类**：查询空结果可以附 `availableTerms` 引导切换学期；但根实体创建场景禁止引导切换（应告知"当前学期下无可操作对象"，引导用户先创建前置数据）
3. **term 的类型以接口为准**：有的接口要求 int，传 string 可能出现"HTTP 200 但空响应"的静默失败。脚本侧用 `type=int` 的 argparse 定义把好类型关，比事后排查省心
4. 课程搜索是特例：用户未指定学期时**不传** term 查全部学期，而不是默认当前学期（详见 9.4）

### 9.2 分页接口处理经验

- **pageSize 跟随页面抓包值**（如列表 20、 10），在脚本内固定，不暴露为自由参数，减少调用方决策负担
- 脚本返回建议带 `totalCount`、`pageNum`、`hasMore` 等字段，**把翻页决策留给 Agent/用户**：还有更多时由 Agent 引导"下一页/展开更多"，脚本不擅自循环拉全量
- 例外：当脚本内部需要完整性扫描时（如在列表中定位某条记录做归属校验），逐页循环是合理的——这类循环属于脚本内部实现，不改变对外的分页语义
- 分页参数（pageNum 等）注意与接口原文对齐，有的接口从 1 开始，个别从 0 开始，以抓包为准

### 9.3 带筛选条件的列表查询经验

- **筛选条件以可选参数暴露，用户未指定就不加条件**：脚本保持"查全部"的初始行为，不擅自设置默认筛选，把缩小范围的选择权交给用户
- **查询结果下方，把筛选能力翻译成"你还可以这样问"**：推荐少量（3 条左右）具体、可直接照说的自然语言问法，每条问法背后对应一种筛选/排序/搜索条件。用户往往不知道接口支持什么——推荐问法是最轻量的能力曝光，比罗列参数说明有效得多
- **推荐要结合当前结果上下文**：结果较多时推荐收敛类问法（如"只看精华帖""按发布时间排"）；结果为空时改为引导换条件/换范围，而不是继续推更多筛选
- **枚举型筛选的"口语 → 参数值"映射写在文档里**（SKILL.md 或 references），由 Agent 完成映射；脚本侧保持宽松校验（见 9.6 校验边界）
- 排序、关键字搜索等可选能力同样按此处理：不默认启用，而是作为可被推荐的问法

### 9.4 课程搜索脚本使用经验

- 教师端与学生端各有一份课程搜索（路由分别为 `courseSearch` / `studentCourseSearch`），结构与语义一致，按技能角色选用
- **未指定学期不传 term**（查全部学期）是刻意设计：先帮用户找到课，再谈学期；指定学期查不到时才返回 `availableTerms` 引导切换
- 运行时上下文 `appCategory=AI_COURSE_REPRESENTATIVE` 时脚本自动走智能体代表课程专用接口，调用方无需感知
- 空结果引导用自然语言与可选学期列表，不要把"空数组""data 为空"这类技术措辞抛给用户

### 9.5 写操作的权限与确认经验

- **双保险思路**：查询类脚本返回中带上当前用户标识（如 `myNid`），Agent 据此预判权限、提前拦截越权请求；脚本内部再独立校验一次（先查到目标记录、比对归属字段，不一致直接拒绝、不发起写请求）。Agent 层是体验，脚本层是底线
- 不可逆操作（删除等）执行前走一次确认交互（模式 1）；轻量可逆操作（围观、点赞、等）不必确认，避免交互疲劳（确认触发时机的完整判定规则见 [8.7](#87-确认环节的条件化免确认判定)）
- 脚本因权限拒绝时，Agent 应原样转告原因，不得换参数重试或绕过——这是权限体系的一部分

### 9.6 脚本工程习惯

- **校验边界**：脚本只做轻量校验——复杂嵌套参数（如 toolInfo）只查存在性与基本类型，字段规则交给后端按业务类型统一校验；枚举类参数（如 type）只查非空、不限制取值，后端扩枚举时脚本无需跟着改
- 对外契约统一：成功结果以 JSON 打印到 stdout；错误以 `{"error": "..."}` 返回，详情打印到 stderr；脚本 docstring 写清用法、参数、返回结构、依赖环境变量与接口契约
- CLI 设计上，必填且语义核心的标识用位置参数，可选筛选用命名参数；可选位置参数要谨慎（历史上有过因位置顺序歧义导致的调用失败），并在文档中写明调用示例
- HTTP 调用带超时、区分网络异常与业务失败，给 Agent 留出可转述的错误信息
- `scripts/base/` 下的基础脚本各技能共享同一份副本，改动时注意全局同步（未来会收敛为公共库，见第十章）

---

## 十、未来演进

- 所有脚本调用接口的域名通过`load_context.py`从环境变量获取，不再硬编码在脚本中
- `scripts/base/` 的通用脚本将迁移至公共脚本库，届时 Skill 内只保留业务脚本
- `course_search.py` 等高频复用脚本同理
- 当前阶段仍需在每个 Skill 中放置 base 副本，注意多处修改时保持同步
