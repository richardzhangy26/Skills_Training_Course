#!/usr/bin/env python3
"""
智能体课程平台自动登录脚本。

使用方式:
    python auto_login.py <训练剧本配置.md路径>
    python auto_login.py --province "福建省区"
    python auto_login.py --account JFFJ1001000000 --password Zhihuishu@000000
    python auto_login.py <训练剧本配置.md路径> --course-name "茶艺学 武夷学院"
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

try:
    from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeout, sync_playwright
except ImportError:
    print("错误: 未安装 Playwright。请运行: pip install playwright")
    print("然后运行: playwright install chromium")
    sys.exit(1)


PROJECT_ROOT = Path("/Users/zhangyichi/工作/能力训练")
SKILL_DIR = PROJECT_ROOT / ".claude" / "skills" / "training-auto-login"
DATA_DIR = SKILL_DIR / "data"
SESSIONS_DIR = SKILL_DIR / "sessions"
ENV_FILE = PROJECT_ROOT / ".env"
COURSE_CENTER_URL = "https://hike-teaching-center.polymas.com/tch-hike/agent-course-hike/ai-course-center"

SCHOOL_SUFFIX_PATTERN = re.compile(
    r"(大学|学院|学校|中学|中德|理工大学|职业学院|职业技术学院|职业技术学校|职业大学|师范大学|师范学院)$"
)
COURSE_NOISE_PATTERNS = [
    r"智能体实训任务",
    r"能力训练",
    r"实训任务\d*",
    r"训练任务\d*",
    r"配置《.*?》\d*个能力训练.*",
    r"选\d+个",
    r"\d+个",
]
COURSE_TRIM_SUFFIXES = ("实践", "实训", "训练")
COURSE_ID_PATTERNS = [
    r"/agent-course-full/([^/?#]+)/",
    r"/resource-hub/([^/?#]+)/",
    r"[?&]courseId=([^&#]+)",
    r"[?&]businessId=([^&#]+)",
]


@dataclass(frozen=True)
class CourseTarget:
    school: str
    province: str
    course_root: str
    course_keyword: str
    search_candidates: Tuple[str, ...]


@dataclass(frozen=True)
class LoginResult:
    success: bool
    authorization: str = ""
    cookie: str = ""
    course_id: str = ""
    matched_course_title: str = ""
    final_url: str = ""


def load_school_province_map() -> Tuple[dict, dict]:
    """加载学校->省区映射和账号信息。"""
    map_file = DATA_DIR / "school_province_map.json"
    if not map_file.exists():
        print(f"错误: 找不到映射文件 {map_file}")
        sys.exit(1)

    with map_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("mappings", {}), data.get("province_accounts", {})


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_match_text(value: str) -> str:
    return re.sub(r"[\s\u3000\-—－–_·•:：,，。、《》【】()（）\[\]\"'“”‘’/\\\\]+", "", value or "").lower()


def split_course_root_parts(course_root: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*[-—－–]+\s*", course_root) if part.strip()]


def extract_course_root_from_path(file_path: str) -> Optional[str]:
    path = Path(file_path).expanduser().resolve()
    parts = path.parts
    try:
        idx = parts.index("skills_training_course")
    except ValueError:
        return None

    if idx + 1 >= len(parts):
        return None

    return normalize_space(parts[idx + 1])


def is_school_like(segment: str, mappings: dict) -> bool:
    normalized = normalize_space(segment)
    if not normalized:
        return False

    mapping_keys = [key for key in mappings if normalize_match_text(key) == normalize_match_text(normalized)]
    if mapping_keys:
        return True

    return bool(SCHOOL_SUFFIX_PATTERN.search(normalized))


def infer_school_from_course_root(course_root: str, mappings: dict) -> Optional[str]:
    normalized_root = normalize_match_text(course_root)
    exact_matches = [
        key for key in mappings
        if normalize_match_text(key) and normalize_match_text(key) in normalized_root
    ]
    if exact_matches:
        return max(exact_matches, key=lambda key: len(normalize_match_text(key)))

    parts = split_course_root_parts(course_root)
    school_parts = [part for part in parts if is_school_like(part, mappings)]
    if school_parts:
        return max(school_parts, key=len)

    return None


def extract_school_from_path(file_path: str, mappings: Optional[dict] = None) -> Optional[str]:
    """从路径中尽量准确提取学校名称。"""
    mappings = mappings or {}
    course_root = extract_course_root_from_path(file_path)
    if course_root:
        school = infer_school_from_course_root(course_root, mappings)
        if school:
            return school

    path = Path(file_path).expanduser().resolve()
    for part in path.parts:
        normalized = normalize_space(part)
        if is_school_like(normalized, mappings):
            return normalized

    for part in path.parts:
        if "-" in part:
            pieces = split_course_root_parts(part)
            if pieces:
                school = next((piece for piece in pieces if is_school_like(piece, mappings)), None)
                if school:
                    return school

    return None


def match_province_by_school(school: str, mappings: dict) -> Optional[str]:
    """根据学校名称匹配省区。"""
    if not school:
        return None

    normalized_school = normalize_match_text(school)
    for key, province in mappings.items():
        normalized_key = normalize_match_text(key)
        if normalized_key == normalized_school:
            return province

    for key, province in mappings.items():
        normalized_key = normalize_match_text(key)
        if normalized_key and (normalized_key in normalized_school or normalized_school in normalized_key):
            return province

    return None


def infer_province_by_llm(school: str, available_provinces: list) -> Optional[str]:
    """当 JSON 映射中找不到学校时，使用 LLM 推断所属省区。"""
    import os

    province_list = "\n".join(f"- {p}" for p in available_provinces)
    prompt = (
        f"请根据学校名称推断其所在省份，并从下列可选省区中选择最匹配的一个。\n"
        f"只返回省区名称本身，不要有任何其他文字。\n\n"
        f"学校名称: {school}\n\n"
        f"可选省区:\n{province_list}"
    )

    def _match_answer(answer: str) -> Optional[str]:
        answer_norm = normalize_space(answer)
        for province in available_provinces:
            p_norm = normalize_space(province)
            if p_norm == answer_norm or p_norm in answer_norm or answer_norm in p_norm:
                return province
        return None

    llm_key = os.environ.get("LLM_API_KEY")
    if llm_key:
        try:
            import requests as _req
            resp = _req.post(
                os.environ.get("LLM_API_URL", "http://llm-service.polymas.com/api/openai/v1/chat/completions"),
                headers={"api-key": llm_key, "Content-Type": "application/json"},
                json={"model": os.environ.get("LLM_MODEL", "Doubao-1.5-pro-32k"),
                      "messages": [{"role": "user", "content": prompt}], "max_tokens": 50},
                timeout=30,
            )
            resp.raise_for_status()
            answer = resp.json()["choices"][0]["message"]["content"].strip()
            matched = _match_answer(answer)
            if matched:
                print(f"  ✓ LLM 推断省区: {matched} (回答: {answer})")
                return matched
        except Exception as e:
            print(f"  LLM 省区推断失败 (Polymas): {e}")

    ark_key = os.environ.get("ARK_API_KEY")
    if ark_key:
        try:
            from openai import OpenAI
            client = OpenAI(base_url="https://ark.cn-beijing.volces.com/api/v3", api_key=ark_key)
            response = client.chat.completions.create(
                model=os.environ.get("DOUBAO_MODEL", "doubao-seed-1-6-251015"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
            )
            answer = response.choices[0].message.content.strip()
            matched = _match_answer(answer)
            if matched:
                print(f"  ✓ LLM 推断省区: {matched} (回答: {answer})")
                return matched
        except Exception as e:
            print(f"  LLM 省区推断失败 (ARK): {e}")

    return None


def get_account_by_province(province: str, province_accounts: dict) -> Optional[Tuple[str, str]]:
    """从省区账号字典查询账号密码。"""
    if province in province_accounts:
        info = province_accounts[province]
        return info["account"], info["password"]
    return None


def infer_province_by_account(account: str, province_accounts: dict) -> str:
    """根据账号反查省区。"""
    normalized_account = normalize_space(account)
    if not normalized_account:
        return ""

    for province, info in province_accounts.items():
        if normalize_space(info.get("account", "")) == normalized_account:
            return province
    return ""


def derive_course_keyword(course_root: str, school: str) -> str:
    course_raw = normalize_space(course_root)

    # 尝试移除完整学校名称（包括后缀）
    if school:
        # 先尝试匹配完整学校名（如"郑州大学"）
        school_pattern = re.escape(school)
        if re.search(r"大学|学院|学校$", school):
            # school 已经包含完整名称，直接移除
            course_raw = normalize_space(re.sub(school_pattern, " ", course_raw, flags=re.IGNORECASE))
        else:
            # school 是缩写（如"郑州"），尝试匹配学校+后缀模式
            expanded_school = re.search(
                re.escape(school) + r"(?:大学|学院|学校|职业学院|职业技术学院)",
                course_raw,
                flags=re.IGNORECASE
            )
            if expanded_school:
                course_raw = normalize_space(
                    course_raw.replace(expanded_school.group(), " ", 1)
                )
            else:
                course_raw = normalize_space(re.sub(school_pattern, " ", course_raw, flags=re.IGNORECASE))

    # 移除噪声词
    for pattern in COURSE_NOISE_PATTERNS:
        course_raw = normalize_space(re.sub(pattern, " ", course_raw))

    # 取分割后的非空部分中，不是纯学校后缀的那部分
    parts = split_course_root_parts(course_raw)
    non_school_parts = [
        p for p in parts
        if p and not re.match(r"^(大学|学院|学校|学院)$", normalize_space(p))
    ]

    if non_school_parts:
        course_raw = normalize_space(non_school_parts[0])
    elif parts:
        course_raw = normalize_space(parts[0])

    course_raw = normalize_space(re.sub(r"\s+", " ", course_raw))
    return course_raw


def build_course_variants(course_keyword: str) -> list[str]:
    variants: list[str] = []

    def add(candidate: str) -> None:
        cleaned = normalize_space(candidate)
        if cleaned and cleaned not in variants:
            variants.append(cleaned)

    add(course_keyword)

    compact = normalize_space(course_keyword)
    for suffix in COURSE_TRIM_SUFFIXES:
        if compact.endswith(suffix) and len(compact) > len(suffix) + 1:
            add(compact[: -len(suffix)])

    if compact:
        for part in re.split(r"\s*[-—－–/|｜]+\s*", compact):
            add(part)

    return variants


def build_search_candidates(course_keyword: str, school: str, course_root: str) -> Tuple[str, ...]:
    candidates: list[str] = []

    def add(candidate: str) -> None:
        cleaned = normalize_space(candidate)
        if cleaned and cleaned not in candidates:
            candidates.append(cleaned)

    for course_variant in build_course_variants(course_keyword):
        if school:
            add(f"{course_variant} {school}")
            add(f"{school} {course_variant}")
        add(course_variant)

    add(course_root)
    return tuple(candidates)


def build_course_target(file_path: str, mappings: dict, explicit_course_name: str = "") -> Optional[CourseTarget]:
    course_root = extract_course_root_from_path(file_path)
    if not course_root:
        return None

    school = extract_school_from_path(file_path, mappings) or ""
    province = match_province_by_school(school, mappings) or ""

    if explicit_course_name:
        course_keyword = normalize_space(explicit_course_name)
    else:
        course_keyword = derive_course_keyword(course_root, school)

    search_candidates = build_search_candidates(course_keyword, school, course_root)
    return CourseTarget(
        school=school,
        province=province,
        course_root=course_root,
        course_keyword=course_keyword,
        search_candidates=search_candidates,
    )


def upsert_env_value(content: str, key: str, value: str) -> str:
    line = f"{key}={value}"
    pattern = re.compile(rf"^{re.escape(key)}=.*$", flags=re.MULTILINE)
    if pattern.search(content):
        return pattern.sub(lambda _match: line, content)

    if content and not content.endswith("\n"):
        content += "\n"
    return f"{content}{line}\n"


def update_env_file(auth: str, cookie: str, course_id: str = "") -> bool:
    """更新 .env 文件中的 AUTHORIZATION、COOKIE 和 COURSE_ID。"""
    if not ENV_FILE.exists():
        print(f"警告: {ENV_FILE} 不存在，将创建新文件")
        content = ""
    else:
        content = ENV_FILE.read_text(encoding="utf-8")

    updates = {
        "AUTHORIZATION": auth,
        "COOKIE": cookie,
    }
    if course_id:
        updates["COURSE_ID"] = course_id

    for key, value in updates.items():
        content = upsert_env_value(content, key, value)

    ENV_FILE.write_text(content, encoding="utf-8")
    return True


def extract_credentials_from_page(page: Page) -> Tuple[str, str]:
    """从 LocalStorage / SessionStorage / Cookie 提取凭证。"""
    token = ""

    try:
        all_storage = page.evaluate(
            """() => {
                const result = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    result[key] = localStorage.getItem(key);
                }
                return result;
            }"""
        )
        print(f"  localStorage keys: {list(all_storage.keys())}")
        for key, value in all_storage.items():
            if value and value.startswith("eyJ"):
                token = value
                print(f"  ✓ 从 localStorage['{key}'] 找到 JWT token")
                break

        if not token:
            for key in ["hike-polymas-identity", "token", "access_token", "Authorization", "authorization"]:
                value = all_storage.get(key)
                if value:
                    token = value
                    print(f"  ✓ 从 localStorage['{key}'] 找到 token")
                    break
    except Exception as exc:
        print(f"  获取 localStorage 时出错: {exc}")

    if not token:
        try:
            all_session = page.evaluate(
                """() => {
                    const result = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        result[key] = sessionStorage.getItem(key);
                    }
                    return result;
                }"""
            )
            for key, value in all_session.items():
                if value and value.startswith("eyJ"):
                    token = value
                    print(f"  ✓ 从 sessionStorage['{key}'] 找到 JWT token")
                    break
        except Exception as exc:
            print(f"  获取 sessionStorage 时出错: {exc}")

    cookies = page.context.cookies()
    if not token:
        preferred_cookie_names = ("ai-poly", "authorization", "Authorization", "token", "access_token")
        for cookie in cookies:
            cookie_name = cookie.get("name", "")
            cookie_value = cookie.get("value", "")
            if not cookie_value:
                continue
            if cookie_name in preferred_cookie_names or cookie_value.startswith("eyJ"):
                token = cookie_value
                print(f"  ✓ 从 Cookie['{cookie_name}'] 找到 token")
                break

    cookie_parts = [f"{cookie['name']}={cookie['value']}" for cookie in cookies if cookie.get("value")]
    cookie_str = "; ".join(cookie_parts)
    print(f"  Cookie 数量: {len(cookies)}")
    return token, cookie_str


def is_logged_in(page: Page) -> bool:
    """检查是否已登录。"""
    url = page.url
    if "login.zhihuishu.com" in url or "oauth" in url:
        return False

    auth_cookie_names = {"ai-poly", "AI-POLY-UINFO", "hike-polymas-user", "CASLOGC"}
    cookie_names = {cookie.get("name") for cookie in page.context.cookies()}
    has_auth_cookie = bool(auth_cookie_names & cookie_names)

    try:
        if page.locator("input[placeholder='请输入课程名称']").first.is_visible(timeout=500):
            return True
    except Exception:
        pass

    if "hike-teaching-center" in url and ("agent-course" in url or "agent-course-full" in url) and has_auth_cookie:
        return True

    return False


def wait_for_portal_state(page: Page, timeout_seconds: int = 12) -> str:
    """等待课程中心跳转稳定后再判断登录态。"""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if "login.zhihuishu.com" in page.url:
            return "login"
        if is_logged_in(page):
            return "logged_in"
        time.sleep(1)
    return "logged_in" if is_logged_in(page) else "login"


def check_for_captcha(page: Page) -> bool:
    """检查是否存在滑块验证码。"""
    captcha_selectors = [
        "button:has-text('向右拖动滑块填充拼图')",
        ".yidun_slider",
        ".yidun--select",
        "[class*='slider']",
        "[class*='captcha']",
        ".verify-slider",
        ".slide-verify",
    ]

    for selector in captcha_selectors:
        try:
            if page.locator(selector).first.is_visible(timeout=500):
                return True
        except Exception:
            continue

    return False


def save_debug_screenshot(page: Page, name: str) -> None:
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SESSIONS_DIR / f"{name}.png"))
    except Exception:
        pass


def read_storage_state(storage_state_path: Path) -> dict:
    if not storage_state_path.exists():
        return {}

    try:
        return json.loads(storage_state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"读取历史会话失败，将忽略并重登: {exc}")
        return {}


def parse_identity_from_cookies(cookies: Sequence[dict]) -> dict:
    """从 cookie 中解析当前会话身份。"""
    cookie_map = {cookie.get("name", ""): cookie.get("value", "") for cookie in cookies}
    identity = {
        "province": "",
        "real_name": "",
        "user_name": "",
    }

    for cookie_name in ("hike-polymas-user", "AI-POLY-UINFO", "CASLOGC"):
        raw_value = urllib.parse.unquote(cookie_map.get(cookie_name, ""))
        if not raw_value:
            continue
        try:
            decoded = json.loads(raw_value)
        except json.JSONDecodeError:
            try:
                decoded = json.loads(re.sub(r"\\x22", '"', raw_value))
            except Exception:
                continue

        identity["province"] = normalize_space(
            decoded.get("realName") or decoded.get("userName") or decoded.get("username") or identity["province"]
        )
        identity["real_name"] = normalize_space(decoded.get("realName") or identity["real_name"])
        identity["user_name"] = normalize_space(
            decoded.get("userName") or decoded.get("username") or identity["user_name"]
        )
        if identity["province"]:
            break

    if not identity["province"]:
        for cookie_name in ("jt-cas", "zhs-jt-cas"):
            raw_value = cookie_map.get(cookie_name, "")
            if not raw_value:
                continue
            payload_parts = raw_value.split(".")
            if len(payload_parts) < 2:
                continue
            payload = payload_parts[1] + "=" * (-len(payload_parts[1]) % 4)
            try:
                decoded = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
            except Exception:
                continue
            identity["province"] = normalize_space(decoded.get("sub") or "")
            if identity["province"]:
                break

    return identity


def get_stored_session_identity(storage_state_path: Path) -> dict:
    data = read_storage_state(storage_state_path)
    cookies = data.get("cookies", []) if isinstance(data, dict) else []
    if not cookies:
        return {}
    return parse_identity_from_cookies(cookies)


def clear_saved_session(storage_state_path: Path, reason: str) -> None:
    if storage_state_path.exists():
        storage_state_path.unlink()
        print(f"已清理历史会话: {reason}")


def should_reset_session(
    storage_state_path: Path,
    expected_province: str = "",
    *,
    force_relogin: bool = False,
) -> bool:
    if force_relogin:
        clear_saved_session(storage_state_path, "显式要求重新登录")
        return True

    if not storage_state_path.exists():
        return False

    if not expected_province:
        return False

    identity = get_stored_session_identity(storage_state_path)
    current_province = normalize_space(identity.get("province", ""))
    if current_province and current_province != normalize_space(expected_province):
        clear_saved_session(
            storage_state_path,
            f"当前会话属于 {current_province}，目标为 {expected_province}，需要重新登录",
        )
        return True

    if current_province:
        print(f"检测到历史会话省区: {current_province}")

    return False


def build_browser_context(browser, storage_state_path: Path) -> BrowserContext:
    context_kwargs = {
        "viewport": {"width": 1440, "height": 960},
    }
    if storage_state_path.exists():
        context_kwargs["storage_state"] = str(storage_state_path)
        print(f"检测到历史会话，优先复用: {storage_state_path}")

    return browser.new_context(**context_kwargs)


def wait_for_course_center_ready(page: Page) -> None:
    page.goto(COURSE_CENTER_URL, timeout=60000)
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    time.sleep(3)
    if "login.zhihuishu.com" in page.url:
        raise RuntimeError("当前仍处于登录页，无法进入课程中心。")

    search_box = page.locator("input[placeholder='请输入课程名称']").first
    search_box.wait_for(timeout=30000)


def click_first_visible(page: Page, selectors: Sequence[str], action_desc: str) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=1500):
                locator.click()
                print(f"  ✓ {action_desc} ({selector})")
                return True
        except Exception:
            continue
    return False


def collect_course_cards(page: Page) -> list[dict]:
    return page.evaluate(
        """() => {
            return Array.from(document.querySelectorAll('.course-card')).map((card, index) => ({
                index,
                title: (card.querySelector('h4')?.innerText || '').trim(),
                text: (card.innerText || '').trim(),
            }));
        }"""
    )


def score_course_card(card: dict, target: CourseTarget) -> int:
    title_norm = normalize_match_text(card.get("title", ""))
    text_norm = normalize_match_text(card.get("text", ""))
    if not title_norm:
        return -1

    score = 0
    school_norm = normalize_match_text(target.school)
    if school_norm and school_norm in text_norm:
        score += 40

    for order, candidate in enumerate(target.search_candidates):
        candidate_norm = normalize_match_text(candidate)
        if not candidate_norm:
            continue
        if candidate_norm == title_norm:
            score = max(score, 120 - order)
        elif candidate_norm in title_norm:
            score = max(score, 95 - order)
        elif candidate_norm in text_norm:
            score = max(score, 70 - order)

    for variant in build_course_variants(target.course_keyword):
        variant_norm = normalize_match_text(variant)
        if variant_norm and variant_norm in title_norm:
            score += 10

    return score


def extract_course_id_from_url(url: str) -> str:
    for pattern in COURSE_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def search_course(page: Page, candidate: str) -> list[dict]:
    search_input = page.locator("input[placeholder='请输入课程名称']").first
    search_input.click()
    search_input.fill("")
    search_input.fill(candidate)
    try:
        search_input.press("Enter")
    except Exception:
        pass

    time.sleep(2.5)
    cards = collect_course_cards(page)
    print(f"  搜索 '{candidate}' 返回 {len(cards)} 张课程卡片")
    return cards


def extract_course_id_from_pages(pages: Iterable[Page]) -> str:
    for target_page in pages:
        course_id = extract_course_id_from_url(target_page.url)
        if course_id:
            return course_id
    return ""


def click_course_card_and_get_id(page: Page, context: BrowserContext, card_index: int) -> Tuple[str, str]:
    cards = page.locator(".course-card")
    if cards.count() <= card_index:
        return "", ""

    course_id = ""
    matched_url = ""
    new_page: Optional[Page] = None

    try:
        with context.expect_page(timeout=15000) as page_info:
            cards.nth(card_index).click()
        new_page = page_info.value
    except PlaywrightTimeout:
        cards.nth(card_index).click()

    deadline = time.time() + 15
    while time.time() < deadline:
        target_pages = [new_page] if new_page else []
        target_pages.extend(page_item for page_item in context.pages if page_item not in target_pages)
        course_id = extract_course_id_from_pages(target_pages)
        if course_id:
            for page_item in target_pages:
                matched_url = page_item.url
                if course_id in matched_url:
                    break
            break
        time.sleep(1)

    return course_id, matched_url


def select_course_and_extract_id(page: Page, context: BrowserContext, target: CourseTarget) -> Tuple[str, str]:
    print("\n开始检索课程...")
    print(f"  学校: {target.school or '未识别'}")
    print(f"  课程目录: {target.course_root}")
    print(f"  课程关键词: {target.course_keyword}")
    print(f"  搜索候选: {', '.join(target.search_candidates)}")

    wait_for_course_center_ready(page)

    for candidate in target.search_candidates:
        cards = search_course(page, candidate)
        if not cards:
            continue

        ranked_cards = sorted(
            (
                {
                    **card,
                    "score": score_course_card(card, target),
                }
                for card in cards
            ),
            key=lambda card: card["score"],
            reverse=True,
        )

        best = ranked_cards[0]
        if best["score"] < 50:
            print(f"  搜索 '{candidate}' 的最佳匹配分数过低，跳过: {best['title']} ({best['score']})")
            continue

        print(f"  ✓ 选中课程: {best['title']} (score={best['score']})")
        course_id, matched_url = click_course_card_and_get_id(page, context, best["index"])
        if course_id:
            print(f"  ✓ 成功进入课程，COURSE_ID={course_id}")
            return course_id, best["title"]

        print("  ! 已点击课程，但未能从跳转 URL 中提取 COURSE_ID，尝试下一个候选词")

    raise RuntimeError("未能自动匹配并进入目标课程。请检查课程目录命名或手动指定 --course-name。")


def run_login(
    account: str,
    password: str,
    headless: bool = False,
    course_target: Optional[CourseTarget] = None,
    expected_province: str = "",
    force_relogin: bool = False,
    keep_open: bool = False,
) -> LoginResult:
    """执行登录流程，并可选自动进入课程。"""
    print(f"\n{'=' * 50}")
    print("开始执行自动登录流程")
    print(f"{'=' * 50}")
    print(f"账号: {account}")
    print(f"目标平台: 智能体课程平台 (Polymas)")
    print()

    storage_state_path = SESSIONS_DIR / "storage_state.json"
    matched_course_title = ""

    with sync_playwright() as p:
        should_reset_session(
            storage_state_path,
            expected_province=expected_province,
            force_relogin=force_relogin,
        )
        try:
            browser = p.chromium.launch(channel="chrome", headless=headless)
            print("使用系统 Chrome 启动浏览器")
        except Exception:
            browser = p.chromium.launch(headless=headless)
            print("系统 Chrome 通道不可用，回退到 Playwright Chromium")
        context = build_browser_context(browser, storage_state_path)
        page = context.new_page()

        try:
            print("[1/6] 打开课程中心...")
            page.goto(COURSE_CENTER_URL, timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            portal_state = wait_for_portal_state(page)

            print("[2/6] 检查登录状态...")
            if portal_state != "logged_in":
                if "login.zhihuishu.com" not in page.url:
                    print("  等待跳转到登录页...")
                    page.wait_for_url(lambda url: "login.zhihuishu.com" in url, timeout=30000)

                print("[3/6] 填写登录表单...")
                page.get_by_role("tab", name="工号登录").click(timeout=10000)
                time.sleep(1)

                school_input = page.locator("input.el-select__input").first
                school_input.wait_for(timeout=10000)
                school_input.click()
                school_input.fill("Polymas")
                time.sleep(1)

                option_selected = click_first_visible(
                    page,
                    [
                        ".el-select-dropdown__item:has-text('Polymas实验室')",
                        ".el-select-dropdown__item:has-text('Polymas')",
                        "li.el-select-dropdown__item:has-text('Polymas实验室')",
                        "li:has-text('Polymas实验室')",
                    ],
                    "选择机构 Polymas实验室",
                )
                if not option_selected:
                    raise RuntimeError("未能自动选择机构 Polymas实验室。")

                page.locator("input[placeholder='请输入您的教工号']").first.fill(account)
                page.locator("input[placeholder='请输入密码']").first.fill(password)

                agreement_checked = click_first_visible(
                    page,
                    [
                        ".el-checkbox__inner",
                        "label .el-checkbox__inner",
                    ],
                    "勾选用户协议",
                )
                if not agreement_checked:
                    try:
                        page.locator("input[type='checkbox']").first.check(force=True)
                        print("  ✓ 已强制勾选用户协议")
                    except Exception as exc:
                        raise RuntimeError(f"未能勾选用户协议: {exc}") from exc

                print("[4/6] 提交登录...")
                page.get_by_text("立即登录", exact=True).click(timeout=10000)
                time.sleep(2)

                if check_for_captcha(page):
                    print("  检测到滑块验证码，等待 60 秒内完成验证或自动通过...")

                try:
                    page.wait_for_url(lambda url: "login.zhihuishu.com" not in url, timeout=60000)
                except PlaywrightTimeout as exc:
                    save_debug_screenshot(page, "login_failed")
                    raise RuntimeError("登录后 60 秒内未跳转出登录页。") from exc
            else:
                print("  ✓ 检测到已登录状态，直接复用当前会话")

            wait_for_course_center_ready(page)

            print("[5/6] 提取认证信息...")
            auth, cookie = extract_credentials_from_page(page)
            if not auth:
                time.sleep(2)
                auth, cookie = extract_credentials_from_page(page)
            if not auth:
                raise RuntimeError("未能提取到 AUTHORIZATION。")

            course_id = ""
            if course_target:
                print("[6/6] 自动检索并进入目标课程...")
                course_id, matched_course_title = select_course_and_extract_id(page, context, course_target)
            else:
                print("[6/6] 未提供课程目标，跳过课程进入")

            print("更新 .env 文件...")
            update_env_file(auth, cookie, course_id)
            print("✓ 已更新环境变量")

            SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(storage_state_path))
            print(f"✓ 会话已保存到 {storage_state_path}")

            final_url = page.url
            print(f"\n{'=' * 50}")
            print("登录成功！")
            print(f"{'=' * 50}")
            print(f"  AUTHORIZATION={auth[:30]}...")
            print(f"  COOKIE={cookie[:50]}...")
            if course_id:
                print(f"  COURSE_ID={course_id}")
                if matched_course_title:
                    print(f"  课程标题={matched_course_title}")

            if keep_open:
                print("\n✓ 登录完成，浏览器保持开启")
                print("  提示: 请手动关闭浏览器窗口以结束脚本")
                try:
                    input("\n按 Enter 键结束脚本（浏览器将保持打开）...")
                except EOFError:
                    pass
                # 不关闭浏览器，直接返回
                return LoginResult(
                    success=True,
                    authorization=auth,
                    cookie=cookie,
                    course_id=course_id,
                    matched_course_title=matched_course_title,
                    final_url=final_url,
                )
            else:
                try:
                    input("\n按 Enter 键关闭浏览器并退出...")
                except EOFError:
                    pass  # 自动化环境无需等待
            return LoginResult(
                success=True,
                authorization=auth,
                cookie=cookie,
                course_id=course_id,
                matched_course_title=matched_course_title,
                final_url=final_url,
            )

        except Exception as exc:
            print(f"\n! 登录过程中出错: {exc}")
            save_debug_screenshot(page, "auto_login_error")

            # 如果已经登录成功但课程匹配失败，仍保存凭证到 .env
            try:
                if auth and cookie:
                    print("\n登录凭证已获取，正在更新 .env 文件...")
                    update_env_file(auth, cookie, course_id)
                    print("✓ 已更新 AUTHORIZATION 和 COOKIE（COURSE_ID 可能需要手动配置）")

                    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
                    context.storage_state(path=str(storage_state_path))
                    print(f"✓ 会话已保存到 {storage_state_path}")
            except NameError:
                pass  # auth/cookie 未定义，说明登录未成功

            if keep_open:
                print("\n! 登录部分成功（凭证已保存），浏览器保持开启以供调试")
                print("  提示: 请手动关闭浏览器窗口以结束脚本")
                try:
                    input("\n按 Enter 键结束脚本（浏览器将保持打开）...")
                except EOFError:
                    pass
                # 如果有凭证，返回成功状态（尽管课程匹配失败）
                if 'auth' in locals() and auth and 'cookie' in locals() and cookie:
                    return LoginResult(
                        success=True,
                        authorization=auth,
                        cookie=cookie,
                        course_id=course_id,
                        matched_course_title=matched_course_title if 'matched_course_title' in locals() else "",
                        final_url=page.url,
                    )
                return LoginResult(success=False)
            else:
                try:
                    input("\n按 Enter 键关闭浏览器并退出...")
                except EOFError:
                    pass  # 自动化环境无需等待
            # 如果有凭证，返回成功状态
            if 'auth' in locals() and auth and 'cookie' in locals() and cookie:
                return LoginResult(
                    success=True,
                    authorization=auth,
                    cookie=cookie,
                    course_id=course_id,
                    matched_course_title=matched_course_title if 'matched_course_title' in locals() else "",
                    final_url=page.url,
                )
            return LoginResult(success=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="智能体课程平台自动登录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 通过文件路径自动识别学校并进入课程
  python auto_login.py /path/to/训练剧本配置.md

  # 直接指定省区
  python auto_login.py --province "福建省区"

  # 直接指定账号密码
  python auto_login.py --account JFFJ1001000000 --password Zhihuishu@000000
        """,
    )

    parser.add_argument("file_path", nargs="?", help="训练剧本配置文件路径（用于自动识别学校和课程）")
    parser.add_argument("--province", "-p", help="直接指定省区名称（如：福建省区）")
    parser.add_argument("--account", "-a", help="直接指定教工号")
    parser.add_argument("--password", "-w", help="直接指定密码")
    parser.add_argument("--course-name", help="直接指定课程名称（用于检索并进入课程）")
    parser.add_argument("--force-relogin", action="store_true", help="忽略历史会话，强制重新登录")
    parser.add_argument("--headless", action="store_true", help="使用无头模式（不显示浏览器窗口）")
    parser.add_argument("--keep-open", action="store_true", help="保持浏览器开启，不自动关闭（需手动关闭浏览器窗口）")

    args = parser.parse_args()

    mappings, province_accounts = load_school_province_map()

    account = None
    password = None
    province = None
    course_target = None

    if args.file_path:
        # 处理 @/path/to/file 格式（Claude Code 文件引用格式）
        file_path = args.file_path
        if file_path.startswith('@'):
            file_path = file_path[1:]
        course_target = build_course_target(file_path, mappings, explicit_course_name=args.course_name or "")
        if course_target:
            print(f"识别到课程目录: {course_target.course_root}")
            if course_target.school:
                print(f"识别到学校: {course_target.school}")
            if course_target.course_keyword:
                print(f"识别到课程关键词: {course_target.course_keyword}")

    if args.account and args.password:
        account = args.account
        password = args.password
        province = infer_province_by_account(account, province_accounts)
        print(f"使用指定账号: {account}")
        if province:
            print(f"根据账号识别省区: {province}")

    elif args.province:
        province = args.province
        result = get_account_by_province(province, province_accounts)
        if result:
            account, password = result
            print(f"省区: {province}")
            print(f"账号: {account}")
        else:
            print(f"错误: 找不到省区 '{province}' 的账号信息")
            print(f"可用省区: {', '.join(province_accounts.keys())}")
            sys.exit(1)

    elif args.file_path:
        file_path = args.file_path
        if file_path.startswith('@'):
            file_path = file_path[1:]
        school = extract_school_from_path(file_path, mappings)
        if school:
            print(f"从路径识别到学校: {school}")
            province = match_province_by_school(school, mappings)

        if not province and course_target and course_target.province:
            province = course_target.province

        if not province:
            print(f"  JSON 映射未找到 '{school or file_path}'，尝试 LLM 推断省区...")
            province = infer_province_by_llm(school or file_path, list(province_accounts.keys()))

        if not province:
            print("! 无法从路径自动识别省区")
            print(f"  路径: {file_path}")
            print("\n可用选项:")
            print("  1. 使用 --province 参数指定省区")
            print("  2. 使用 --account 和 --password 直接指定账号")
            print(f"\n支持的省区: {', '.join(province_accounts.keys())}")
            sys.exit(1)

        print(f"匹配到省区: {province}")
        result = get_account_by_province(province, province_accounts)
        if result:
            account, password = result
            print(f"账号: {account}")
        else:
            print(f"错误: 找不到省区 '{province}' 的账号信息")
            sys.exit(1)
    else:
        parser.print_help()
        print("\n错误: 请提供文件路径、省区名称或账号密码")
        sys.exit(1)

    result = run_login(
        account,
        password,
        headless=args.headless,
        course_target=course_target,
        expected_province=province or "",
        force_relogin=args.force_relogin,
        keep_open=args.keep_open,
    )
    if result.success:
        print("\n✓ 自动登录完成，现在可以使用其他技能进行部署和测试")
        sys.exit(0)

    print("\n✗ 登录失败，请检查错误信息")
    sys.exit(1)


if __name__ == "__main__":
    main()
