"""
从评价标准 Markdown 文件自动创建评分项

支持的 Markdown 格式（评价标准.md）：
    ## 主评分项名称（N分）

    考查描述文字...

    ### 得分点：

    1. **子项名称（n分）**

       子项描述...

       评分要点：
       - 要点1（n分）
       - 要点2（n分）

    2. **子项名称（n分）**
       ...

    ---

每个 ## 二级标题对应一个 createScoreItem 请求。
"""

import os
import re
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# 环境配置（与 create_task_from_markdown.py 保持一致）
# ---------------------------------------------------------------------------


def load_env_config():
    current_dir = Path(__file__).parent
    env_paths = [
        current_dir.parent / ".env",
        current_dir / ".env",
        Path.cwd() / ".env",
    ]
    for path in env_paths:
        if path.exists():
            load_dotenv(path)
            print(f"✅ 已加载环境配置: {path}")
            return
    print("⚠️  未找到 .env 文件，使用系统环境变量。")


def get_headers():
    auth = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not auth or not cookie:
        raise ValueError("缺少 AUTHORIZATION 或 COOKIE 环境变量。")
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": auth,
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
    }


# ---------------------------------------------------------------------------
# Markdown 解析
# ---------------------------------------------------------------------------


def parse_rubric_markdown(md_path: Path) -> list[dict]:
    """
    解析评价标准 Markdown，返回评分项列表。

    每个评分项包含：
      - itemName:      str   主评分项名称（不含分值括号）
      - score:         int   满分值
      - description:   str   考查描述（## 标题下、### 得分点前的段落）
      - requireDetail: str   得分点全文（markdown 格式）
    """
    content = md_path.read_text(encoding="utf-8")

    # 用 ## 切割，每段对应一个主评分项（跳过 # 总标题 和总结说明段）
    # 匹配形如：## 名称（N分） 或 ## 名称(N分)
    section_pattern = re.compile(
        r"^##\s+(.+?)\s*[（(](\d+)\s*分[）)]",
        re.MULTILINE,
    )

    # 找到所有主项标题的位置
    matches = list(section_pattern.finditer(content))
    if not matches:
        return []

    score_items = []

    for i, m in enumerate(matches):
        item_name = m.group(1).strip()
        score = int(m.group(2))

        # 该段的文本范围：从标题行结束到下一个 ## 标题（或文档末尾）
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[body_start:body_end]

        # ---- 提取 description：标题后到 "### 得分点" 之前的段落 ----
        score_point_split = re.split(r"###\s*得分点[：:]?", body, maxsplit=1)
        pre_section = score_point_split[0]

        # 去掉分隔线、空行，取第一段非空文本作为 description
        description_lines = []
        for line in pre_section.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("---"):
                description_lines.append(stripped)
        description = "\n".join(description_lines).strip()

        # ---- 提取 requireDetail：### 得分点 之后的全部内容 ----
        if len(score_point_split) > 1:
            require_raw = score_point_split[1]
        else:
            require_raw = ""

        # 去掉末尾的 --- 分隔线和空行
        require_detail = re.sub(r"\n---\s*$", "", require_raw.strip()).strip()

        score_items.append(
            {
                "itemName": item_name,
                "score": score,
                "description": description,
                "requireDetail": require_detail,
            }
        )

    return score_items


# ---------------------------------------------------------------------------
# API 调用
# ---------------------------------------------------------------------------

CREATE_URL = "https://cloudapi.polymas.com/teacher-course/abilityTrain/createScoreItem"


def create_score_item(train_task_id: str, item: dict) -> str | None:
    """
    调用 createScoreItem 接口，返回 itemId（失败返回 None）。
    """
    payload = {
        "trainTaskId": train_task_id,
        "itemName": item["itemName"],
        "score": item["score"],
        "description": item["description"],
        "requireDetail": item["requireDetail"],
    }

    try:
        resp = requests.post(
            CREATE_URL, headers=get_headers(), json=payload, timeout=20
        )
        result = resp.json()
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")
        return None

    if result.get("success") or result.get("code") == 200:
        item_id = result.get("data", {}).get("itemId")
        return item_id
    else:
        print(f"  ❌ 接口返回错误: {result}")
        return None


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def main():
    load_env_config()

    print("\n" + "=" * 55)
    print("📊  评价标准自动创建工具")
    print("=" * 55)

    # --- 训练任务 ID ---
    train_task_id = os.getenv("TASK_ID", "")
    if len(sys.argv) > 2:
        train_task_id = sys.argv[2]
    if not train_task_id:
        train_task_id = input("\n🔑 请输入训练任务 ID (TASK_ID): ").strip()
    print(f"✅ 训练任务 ID: {train_task_id}")

    # --- Markdown 文件 ---
    target_md: Path | None = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        candidate = Path(sys.argv[1])
        if candidate.exists():
            target_md = candidate

    if not target_md:
        raw = input("\n📄 请输入评价标准 Markdown 文件路径: ").strip()
        raw = raw.strip("'\"")
        if raw:
            target_md = Path(raw)

    if not target_md or not target_md.exists():
        print(f"\n❌ 文件不存在: {target_md}")
        return

    print(f"✅ 配置文件: {target_md}")

    # --- 解析 ---
    print("\n📖 正在解析评价标准...")
    items = parse_rubric_markdown(target_md)
    if not items:
        print("❌ 未解析到任何评分项，请检查 Markdown 格式。")
        return

    print(f"✅ 共解析到 {len(items)} 个评分项：")
    total_score = 0
    for idx, item in enumerate(items, 1):
        print(f"   {idx}. {item['itemName']}  ({item['score']} 分)")
        total_score += item["score"]
    print(f"   {'─' * 35}")
    print(f"   合计：{total_score} 分")

    # --- 确认 ---
    confirm = input(f"\n❓ 确认创建以上 {len(items)} 个评分项？[y/N]: ").strip().lower()
    if confirm not in ("y", "yes"):
        print("⏹️  已取消。")
        return

    # --- 创建 ---
    print("\n" + "═" * 55)
    print("🚀  开始创建评分项")
    print("═" * 55)

    success_count = 0
    for idx, item in enumerate(items, 1):
        print(f"\n[{idx}/{len(items)}]  {item['itemName']}  ({item['score']} 分)")
        item_id = create_score_item(train_task_id, item)
        if item_id:
            print(f"  ✅ 创建成功  itemId: {item_id}")
            success_count += 1
        else:
            print(f"  ❌ 创建失败")

    print("\n" + "=" * 55)
    print("🎉  完成！")
    print("=" * 55)
    print(f"  成功: {success_count} / {len(items)}")
    print(f"  任务 ID: {train_task_id}\n")


if __name__ == "__main__":
    main()
