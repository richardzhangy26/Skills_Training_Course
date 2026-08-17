#!/usr/bin/env python3
"""
Export current Polymas digital-human options for training-prompt-expert.

The script only reads platform configuration. It does not create or update
digital humans, voices, avatars, tasks, or script steps.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


DEFAULT_API_BASE = "https://cloudapi.polymas.com"
DEFAULT_VOICE_TEMPLATE_TYPE = "ONLINE_DOUBAO"


def text(value):
    if value is None:
        return ""
    return str(value).strip()


def first_non_empty(*values):
    for value in values:
        value_text = text(value)
        if value_text:
            return value_text
    return ""


def markdown_cell(value):
    return text(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(markdown_cell(cell) for cell in row) + " |")
    return "\n".join(lines)


def build_headers():
    auth = os.getenv("AUTHORIZATION")
    cookie = os.getenv("COOKIE")
    if not auth or not cookie:
        raise RuntimeError("缺少 AUTHORIZATION 或 COOKIE，请先在 .env 中配置平台登录态。")
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": auth,
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }


def post_json(api_base, endpoint, payload, headers):
    url = f"{api_base.rstrip('/')}/{endpoint.lstrip('/')}"
    response = requests.post(url, headers=headers, json=payload, timeout=20)
    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError(f"{endpoint} 返回非 JSON 响应: HTTP {response.status_code}") from exc
    if not (data.get("code") == 200 or data.get("code") == "200" or data.get("success") is True):
        raise RuntimeError(f"{endpoint} 请求失败: {data}")
    return data.get("data")


def fetch_catalog(api_base, course_id=""):
    headers = build_headers()
    user_detail = post_json(api_base, "console/v1/get-current-user-detail", {}, headers) or {}
    user_nid = first_non_empty(os.getenv("POLYMAS_USER_NID"), os.getenv("USER_NID"), user_detail.get("userNid"))
    if not user_nid:
        raise RuntimeError(f"当前用户信息缺少 userNid: {user_detail}")

    voice_payload = {"voiceTemplateType": DEFAULT_VOICE_TEMPLATE_TYPE}
    if course_id:
        voice_payload["courseId"] = course_id

    owner_payload = {"userNid": user_nid, "sort": 2, "type": "NORMAL"}
    avatar_payload = {"userNid": user_nid}
    if course_id:
        owner_payload["courseId"] = course_id
        avatar_payload["courseId"] = course_id

    return {
        "digital_humans": post_json(api_base, "ai-profile/digital_human/owner/list", owner_payload, headers) or [],
        "voices": post_json(api_base, "ai-profile/ai_voice/list", voice_payload, headers) or [],
        "avatars": post_json(api_base, "ai-profile/ai_avatar/getOwnerAvatar", avatar_payload, headers) or [],
    }


def build_selection_hints():
    return "\n".join(
        [
            "## 选择规则",
            "",
            "1. 优先复用已有数字人：若阶段角色能匹配“已创建数字人”的名称、身份或语气，直接填写 `**数字人**: <customNid>`，并同步填写 `**声音**: <voiceNid>`、`**形象**: <avatarNid>`。",
            "2. 教师/导师/专家/评委/考官：优先选择沉稳、专业、可信的中青年或教授型数字人；音色优先选“擎苍”“儒雅青年”“霸气青叔”等。",
            "3. 患者/客户/居民/学生/普通群众：优先选择与年龄、性别、情绪状态贴近的数字人；焦虑、求助、投诉场景可选择更有情绪表现力的音色。",
            "4. 儿童/青少年角色：优先使用童声或年轻音色，避免使用成熟专家音色。",
            "5. 英语口语或涉外角色：优先使用英语或双语音色；没有合适英语音色时再退回中文通用音色。",
            "6. 如果没有可复用数字人，但有合适音色和形象，填写 `**数字人名称**`、`**声音**`、`**形象**`，导入脚本会自动创建数字人。",
            "7. 如果没有明显匹配项，教学引导类默认选专业教师/引导助手；模拟人物类默认选最贴近角色身份的人物，而不是固定使用教师形象。",
            "",
            "输出阶段字段时保持以下顺序：",
            "`**数字人**`、`**数字人名称**`、`**声音**`、`**形象**`。已有数字人至少填写 `**数字人**`；新建数字人至少填写 `**数字人名称**`、`**声音**`、`**形象**`。",
        ]
    )


def render_catalog_markdown(catalog, *, max_digital_humans=120, max_voices=120, max_avatars=120):
    digital_humans = list(catalog.get("digital_humans") or [])[:max_digital_humans]
    voices = list(catalog.get("voices") or [])[:max_voices]
    avatars = list(catalog.get("avatars") or [])[:max_avatars]

    lines = [
        "# 平台数字人资源清单",
        "",
        build_selection_hints(),
        "",
        "## 已创建数字人（优先复用）",
        "",
        markdown_table(
            ["customNid", "名称", "voiceNid", "avatarNid", "音色名", "音色说明"],
            [
                [
                    item.get("customNid"),
                    item.get("digitalHumanName"),
                    item.get("voiceNid"),
                    item.get("avatarNid"),
                    item.get("voiceName"),
                    item.get("voiceIntroduce"),
                ]
                for item in digital_humans
            ],
        ),
        "",
        "## 可选音色（创建新数字人时使用）",
        "",
        markdown_table(
            ["voiceNid", "音色", "音色说明", "适用场景", "语言", "bigModelVoiceParam"],
            [
                [
                    item.get("nid"),
                    item.get("voiceTone"),
                    item.get("toneType"),
                    item.get("fitScene"),
                    item.get("language"),
                    item.get("bigModelVoiceParam"),
                ]
                for item in voices
            ],
        ),
        "",
        "## 可选形象（创建新数字人时使用）",
        "",
        markdown_table(
            ["avatarNid", "名称", "scope"],
            [
                [
                    item.get("nid"),
                    first_non_empty(item.get("name"), item.get("digitalHumanNid")),
                    item.get("scope"),
                ]
                for item in avatars
            ],
        ),
        "",
    ]
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="导出 Polymas 数字人、音色和形象资源清单。")
    parser.add_argument("--env-file", default="", help="可选 .env 路径，默认自动查找当前目录和项目根目录。")
    parser.add_argument("--api-base", default=os.getenv("POLYMAS_API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--course-id", default=os.getenv("COURSE_ID", ""))
    parser.add_argument("--output", default="", help="输出 Markdown 文件路径；为空时打印到 stdout。")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON 而不是 Markdown。")
    return parser.parse_args(argv)


def load_env(env_file=""):
    if env_file:
        load_dotenv(env_file, override=True)
        return
    cwd = Path.cwd()
    script_dir = Path(__file__).resolve().parent
    for path in (cwd / ".env", cwd.parent / ".env", script_dir.parents[3] / ".env"):
        if path.exists():
            load_dotenv(path, override=True)
            return


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    load_env(args.env_file)
    catalog = fetch_catalog(args.api_base, args.course_id)
    output = json.dumps(catalog, ensure_ascii=False, indent=2) if args.json else render_catalog_markdown(catalog)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ 已导出数字人资源清单: {args.output}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
