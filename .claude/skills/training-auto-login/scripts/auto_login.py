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
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

try:
    from yidun_slider import captcha_visible as yidun_visible, solve_yidun as yidun_solve
except Exception:  # 模块缺失时退化为人工
    yidun_visible = None
    yidun_solve = None

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
ACCOUNTS_XLSX = PROJECT_ROOT / "智能体课程配置账号情况.xlsx"
ACCOUNTS_SESSION_DIR = SESSIONS_DIR / "accounts"
DEFAULT_SESSION_TTL_HOURS = 72.0
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


_XLSX_CACHE: dict = {"path": "", "rows": []}


def xlsx_rows(path: Optional[Path] = None) -> list:
    """账号表（唯一账号来源），带进程内缓存。"""
    target = Path(path) if path else ACCOUNTS_XLSX
    if _XLSX_CACHE["rows"] and _XLSX_CACHE["path"] == str(target):
        return _XLSX_CACHE["rows"]
    rows = load_accounts_from_xlsx(target)
    _XLSX_CACHE["path"] = str(target)
    _XLSX_CACHE["rows"] = rows
    return rows


def xlsx_provinces() -> list:
    seen = []
    for r in xlsx_rows():
        key = r.get("province_key") or ""
        if key and key not in seen:
            seen.append(key)
    return seen


def normalize_name(value: str) -> str:
    """学校/机构名归一化：去空白、全半角括号、校名后缀差异。"""
    text = re.sub(r"[\s\u3000]", "", value or "")
    text = text.replace("（", "(").replace("）", ")").replace("·", "")
    return text.upper()


def load_accounts_from_xlsx(xlsx_path: Optional[Path] = None) -> list:
    """解析《智能体课程配置账号情况.xlsx》，返回账号条目列表。

    表格是多段式的，这里做通用解析：
      - B 列（教工号）必须是账号形态 ^[A-Za-z0-9_-]{6,}$
      - 密码取 D/E 列中第一个以 Zhihuishu@ 开头或含 @ 的值（不同小表格列序不一样）
      - C 列作为学校/机构名，A 列作为省份（可能为空）
    """
    path = Path(xlsx_path) if xlsx_path else ACCOUNTS_XLSX
    if not path.exists():
        return []
    try:
        import openpyxl
    except ImportError:
        print("! 未安装 openpyxl，无法读取账号表（pip install openpyxl）")
        return []

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as exc:
        print(f"! 读取账号表失败: {exc}")
        return []

    account_re = re.compile(r"^[A-Za-z0-9_-]{6,}$")
    rows = []
    seen = set()
    for sheet in wb.worksheets:
        for raw in sheet.iter_rows(values_only=True):
            if not raw or len(raw) < 5:
                continue
            cells = [("" if v is None else str(v).strip()) for v in raw[:7]]
            cells += [""] * (7 - len(cells))
            province, account, name, col_d, col_e, phone, note = cells[:7]

            if not account_re.match(account):
                continue
            password = ""
            for cand in (col_d, col_e):
                if cand.startswith("Zhihuishu@") or ("@" in cand and len(cand) <= 40 and " " not in cand):
                    password = cand
                    break
            if not password:
                continue

            key = (account.upper(), password)
            if key in seen:
                continue
            seen.add(key)

            province_key = province
            if province and not province.endswith("省区") and re.fullmatch(r"[\u4e00-\u9fa5]{2,6}", province):
                province_key = province + "省区"

            rows.append({
                "province": province,
                "province_key": province_key,
                "account": account,
                "name": name,
                "org": col_d if "@" not in col_d else name,
                "password": password,
                "phone": phone,
                "note": note,
            })
    return rows


def school_candidates(school: str, course_root: str = "") -> list:
    """构造用于匹配账号表的学校候选名：识别出的学校 > 目录 '-' 前缀 > 整个目录名。"""
    cands = []
    for raw in (school, re.split(r"[-—_\s]", course_root or "")[0], course_root or ""):
        val = (raw or "").strip()
        if val and val not in cands:
            cands.append(val)
    return cands


def find_account_in_xlsx(query: str, rows: list, strict: bool = False) -> Optional[dict]:
    """按学校名 / 机构名 / 省区名匹配账号。优先级：精确 > 归一化精确 > 包含。

    strict=True 时，包含匹配必须双向包含（避免 "广州" 命中 "广州软件学院"）。
    """
    if not query or not rows:
        return None
    q = normalize_name(query)

    for r in rows:
        if r["name"] == query:
            return r
    for r in rows:
        if normalize_name(r["name"]) == q:
            return r
    if not strict:
        for r in rows:
            if normalize_name(r["province_key"]) == q and "省区" in (r["name"] or ""):
                return r
        for r in rows:
            if normalize_name(r["province"]) == q:
                return r

    # 包含匹配：优先名字最长的（更具体）
    if strict:
        hits = [r for r in rows if q and normalize_name(r["name"]) in q]
    else:
        hits = [r for r in rows
                if q and (q in normalize_name(r["name"]) or normalize_name(r["name"]) in q)]
    if hits:
        hits.sort(key=lambda r: -len(r["name"] or ""))
        return hits[0]

    # 去掉学校后缀再试一次
    stripped = re.sub(r"(大学|学院|学校|中学|分校|校区)$", "", query)
    if stripped and stripped != query:
        q2 = normalize_name(stripped)
        hits = [r for r in rows if q2 in normalize_name(r["name"])]
        if hits:
            hits.sort(key=lambda r: -len(r["name"] or ""))
            return hits[0]
    return None


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


def is_school_like(segment: str, mappings: Optional[dict] = None) -> bool:
    normalized = normalize_space(segment)
    if not normalized:
        return False
    target = normalize_match_text(normalized)
    if any(normalize_match_text(r["name"]) == target for r in xlsx_rows()):
        return True
    return bool(SCHOOL_SUFFIX_PATTERN.search(normalized))


def infer_school_from_course_root(course_root: str, mappings: Optional[dict] = None) -> Optional[str]:
    normalized_root = normalize_match_text(course_root)
    hits = [r["name"] for r in xlsx_rows()
            if r["name"] and normalize_match_text(r["name"]) in normalized_root]
    if hits:
        return max(hits, key=len)

    parts = split_course_root_parts(course_root)
    school_parts = [part for part in parts if is_school_like(part)]
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


def match_province_by_school(school: str, mappings: Optional[dict] = None) -> Optional[str]:
    """根据学校名称从账号表反查省区。"""
    if not school:
        return None
    hit = find_account_in_xlsx(school, xlsx_rows(), strict=True)
    if hit:
        return hit["province_key"] or None
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


def get_account_by_province(province: str, province_accounts: Optional[dict] = None) -> Optional[Tuple[str, str]]:
    """按省区名从账号表查账号密码（优先省区行）。"""
    if not province:
        return None
    hit = find_account_in_xlsx(province, xlsx_rows(), strict=False)
    if hit:
        return hit["account"], hit["password"]
    return None


def infer_province_by_account(account: str, province_accounts: Optional[dict] = None) -> str:
    """根据账号在账号表里反查省区。"""
    normalized_account = normalize_space(account).upper()
    if not normalized_account:
        return ""
    for r in xlsx_rows():
        if (r["account"] or "").upper() == normalized_account:
            return r["province_key"] or ""
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


def build_course_target(file_path: str, mappings: Optional[dict] = None,
                        explicit_course_name: str = "") -> Optional[CourseTarget]:
    course_root = extract_course_root_from_path(file_path)
    if not course_root:
        return None

    # 目录名首段像学校名（…大学/学院/学校）时直接采用，避免被截断成城市名
    parts = split_course_root_parts(course_root)
    school = ""
    if len(parts) >= 2 and re.search(r"(大学|学院|学校|校区|分校)$", parts[0]):
        school = parts[0]
    if not school:
        school = extract_school_from_path(file_path, mappings) or ""
    province = match_province_by_school(school, mappings) or ""

    if explicit_course_name:
        course_keyword = normalize_space(explicit_course_name)
    elif school and parts and parts[0] == school and len(parts) >= 2:
        course_keyword = normalize_space(" ".join(parts[1:]))
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


LOGIN_URL = "https://login.zhihuishu.com/"


def open_course_center(page: Page, attempts: int = 3) -> None:
    """打开课程中心；网络抖动(ERR_CONNECTION_CLOSED)时重试，仍失败则直接进登录页。"""
    last_exc = None
    for i in range(1, attempts + 1):
        try:
            page.goto(COURSE_CENTER_URL, timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            return
        except Exception as exc:
            last_exc = exc
            print(f"  打开课程中心失败（第 {i} 次）: {str(exc).splitlines()[0][:90]}")
            time.sleep(3)
    print("  回退：直接打开登录页")
    page.goto(LOGIN_URL, timeout=60000)
    time.sleep(2)


AUTH_COOKIE_NAMES = ("jt-cas", "zhs-jt-cas", "CASLOGC", "polymas-token", "AI-POLY-UINFO")


def has_auth_cookie(context: BrowserContext) -> bool:
    try:
        names = {c.get("name", "") for c in context.cookies()}
    except Exception:
        return False
    return bool(names & set(AUTH_COOKIE_NAMES))


def wait_for_auth_cookie(context: BrowserContext, page: Page, timeout: float = 30.0) -> bool:
    """重定向可能因网络失败，但登录成功时 cookie 一定会落下 -> 以 cookie 为准。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if has_auth_cookie(context):
            return True
        if "login.zhihuishu.com" not in getattr(page, "url", ""):
            return True
        time.sleep(0.5)
    return has_auth_cookie(context)


def ensure_login_page(page: Page, timeout: float = 40.0) -> None:
    """确保当前在登录页：轮询 URL / 登录表单，超时就直接打开登录页。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if "login.zhihuishu.com" in page.url:
                return
            if page.locator("input[placeholder='请输入密码']").count():
                return
        except Exception:
            pass
        time.sleep(1)
    print("  页面未自动跳转，直接打开登录页")
    try:
        page.goto(LOGIN_URL, timeout=60000)
    except Exception as exc:
        raise RuntimeError(f"打开登录页失败: {str(exc).splitlines()[0][:80]}") from exc
    time.sleep(2)


def wait_until_leaves_login(page: Page, timeout: float = 60.0) -> bool:
    """轮询 URL 是否已离开登录页。

    跳转瞬间可能抛 net::ERR_ABORTED / frame detached，这里全部吞掉按"已跳转"处理。
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            url = page.url
        except Exception:
            time.sleep(0.5)
            if not page.is_closed():
                continue
            return True
        if "login.zhihuishu.com" not in url:
            return True
        try:
            for other in page.context.pages:
                if "login.zhihuishu.com" not in other.url:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


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


def sanitize_account_key(account: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", (account or "unknown").strip().upper())


def session_path_for(account: str) -> Path:
    ACCOUNTS_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return ACCOUNTS_SESSION_DIR / f"{sanitize_account_key(account)}.json"


def meta_path_for(session_path: Path) -> Path:
    return session_path.with_suffix(".meta.json")


def read_session_meta(session_path: Path) -> dict:
    mp = meta_path_for(session_path)
    if mp.exists():
        try:
            return json.loads(mp.read_text(encoding="utf-8"))
        except Exception:
            return {}
    ident = get_stored_session_identity(session_path)
    return {"real_name": ident.get("real_name", ""), "user_name": ident.get("user_name", "")}


def session_age_hours(session_path: Path) -> Optional[float]:
    if not session_path.exists():
        return None
    saved_at = read_session_meta(session_path).get("saved_at")
    if saved_at:
        try:
            return (datetime.now() - datetime.fromisoformat(saved_at)).total_seconds() / 3600.0
        except Exception:
            pass
    return (time.time() - session_path.stat().st_mtime) / 3600.0


def session_is_usable(session_path: Path, ttl_hours: float, account: str) -> Tuple[bool, str]:
    if not session_path.exists():
        return False, "无历史会话，将新建网页登录"
    age = session_age_hours(session_path)
    if age is None:
        return False, "无法读取会话时间，将重新登录"
    if ttl_hours > 0 and age > ttl_hours:
        return False, f"会话已过期（{age:.1f}h > {ttl_hours:g}h），将重新登录"
    meta = read_session_meta(session_path)
    stored = str(meta.get("account", "")).upper()
    if stored and stored != account.upper():
        return False, f"该会话属于 {stored}，与目标账号 {account} 不一致，将重新登录"
    who = meta.get("real_name") or meta.get("user_name") or ""
    return True, f"复用已保存的登录态（{age:.1f}h 前保存{('，' + who) if who else ''}）"


def save_session_state(context: BrowserContext, page: Page, account: str,
                       school: str = "", province: str = "", note: str = "") -> Path:
    """按账号落盘 storage_state + meta，同时刷新全局 storage_state.json（兼容其他技能）。"""
    session_path = session_path_for(account)
    context.storage_state(path=str(session_path))
    cookies = context.cookies()
    identity = parse_identity_from_cookies(cookies)
    meta = {
        "account": account.upper(),
        "school": school,
        "province": province,
        "real_name": identity.get("real_name", ""),
        "user_name": identity.get("user_name", ""),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "url": page.url,
        "note": note,
        "cookie_count": len(cookies),
    }
    meta_path_for(session_path).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    global_path = SESSIONS_DIR / "storage_state.json"
    try:
        context.storage_state(path=str(global_path))
    except Exception:
        pass
    return session_path


def credentials_from_storage_state(session_path: Path) -> Tuple[str, str]:
    """从 storage_state 离线还原 (AUTHORIZATION, COOKIE)，不需要启动浏览器。"""
    data = read_storage_state(session_path)
    if not data:
        return "", ""

    cookies = data.get("cookies", []) or []
    token = ""
    for origin in data.get("origins", []) or []:
        for item in origin.get("localStorage", []) or []:
            value = str(item.get("value", ""))
            if value.startswith("eyJ"):
                token = value
                break
        if token:
            break

    if not token:
        for c in cookies:
            name, value = c.get("name", ""), c.get("value", "")
            if not value:
                continue
            if name in ("ai-poly", "token", "access_token", "Authorization") or value.startswith("eyJ"):
                token = value
                break

    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies if c.get("value"))
    return token, cookie_str


def list_saved_sessions() -> list[dict]:
    if not ACCOUNTS_SESSION_DIR.exists():
        return []
    rows = []
    for f in sorted(ACCOUNTS_SESSION_DIR.glob("*.json")):
        if f.name.endswith(".meta.json"):
            continue
        meta = read_session_meta(f)
        rows.append({
            "account": meta.get("account", f.stem),
            "school": meta.get("school", ""),
            "real_name": meta.get("real_name", ""),
            "saved_at": meta.get("saved_at", ""),
            "age_h": round(session_age_hours(f) or 0, 1),
            "path": str(f),
        })
    return rows


def build_browser_context(browser, storage_state_path: Path) -> BrowserContext:
    context_kwargs = {
        "viewport": {"width": 1440, "height": 960},
        "locale": "zh-CN",
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    }
    if storage_state_path is not None and Path(storage_state_path).exists():
        context_kwargs["storage_state"] = str(storage_state_path)
        print(f"检测到历史会话，优先复用: {storage_state_path}")

    context = browser.new_context(**context_kwargs)
    try:
        context.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            "window.chrome={runtime:{}};"
            "Object.defineProperty(navigator,'languages',{get:()=>['zh-CN','zh']});"
            "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});"
        )
    except Exception:
        pass
    return context


def wait_for_course_center_ready(page: Page) -> None:
    open_course_center(page)
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
    reuse_session: bool = True,
    session_ttl_hours: float = DEFAULT_SESSION_TTL_HOURS,
    school: str = "",
) -> LoginResult:
    """执行登录流程，并可选自动进入课程。

    会话策略（按账号隔离）：
      1. ``sessions/accounts/<账号>.json`` 存在且未过期 -> 直接复用，不弹登录/滑块
      2. 不存在、过期、或复用后发现已失效 -> 新开一个干净网页用账号密码登录，然后落盘
    """
    print(f"\n{'=' * 50}")
    print("开始执行自动登录流程")
    print(f"{'=' * 50}")
    print(f"账号: {account}")
    print(f"目标平台: 智能体课程平台 (Polymas)")
    print()

    storage_state_path = session_path_for(account)
    matched_course_title = ""

    with sync_playwright() as p:
        reusable, reason = session_is_usable(storage_state_path, session_ttl_hours, account)
        if force_relogin:
            reusable, reason = False, "显式 --force-relogin，丢弃旧会话"
        if not reuse_session:
            reusable, reason = False, "显式 --no-reuse-session，强制新建登录"
        print(f"[会话] {reason}")

        try:
            browser = p.chromium.launch(channel="chrome", headless=headless, args=["--no-proxy-server"])
            print("使用系统 Chrome 启动浏览器（直连，绕过系统代理）")
        except Exception:
            browser = p.chromium.launch(headless=headless, args=["--no-proxy-server"])
            print("系统 Chrome 通道不可用，回退到 Playwright Chromium（直连）")
        context = build_browser_context(browser, storage_state_path if reusable else None)
        page = context.new_page()

        try:
            print("[1/6] 打开课程中心...")
            open_course_center(page)
            portal_state = wait_for_portal_state(page)

            print("[2/6] 检查登录状态...")
            if portal_state == "logged_in" and reusable:
                print("  ✓ 复用登录态成功，跳过登录与滑块")
            elif portal_state != "logged_in":
                if reusable:
                    print("  ! 已保存的登录态失效（过期/被踢下线），新建干净网页重新登录")
                    try:
                        context.close()
                    except Exception:
                        pass
                    context = build_browser_context(browser, None)
                    page = context.new_page()
                    open_course_center(page)
                    wait_for_portal_state(page, timeout_seconds=8)
                if "login.zhihuishu.com" not in page.url:
                    print("  等待跳转到登录页...")
                    ensure_login_page(page)

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
                submit_clicked = click_first_visible(
                    page,
                    [
                        ".btn-block__grandient_login:has-text('登录')",
                        "div:has-text('登录').btn-block__grandient_login",
                        "text=立即登录",
                        "button:has-text('立即登录')",
                        "button:has-text('登录')",
                    ],
                    "点击登录提交按钮",
                )
                if not submit_clicked:
                    page.get_by_text("立即登录", exact=True).click(timeout=10000)
                time.sleep(2)

                if check_for_captcha(page) or (yidun_visible and yidun_visible(page)):
                    solved = False
                    if yidun_solve:
                        print("  检测到易盾滑块，自动破解中（缺口定位 + 拟人轨迹）...")
                        try:
                            solved = yidun_solve(page, max_retry=4)
                        except Exception as exc:
                            print(f"  自动破解异常，转人工: {exc}")
                    if solved:
                        print("  ✓ 滑块已通过")
                    else:
                        print("  ✗ 自动破解未通过，请在弹出的浏览器窗口里手动拖动滑块（60 秒内）")

                # 验证通过后站点通常会自动重发登录；若仍停留在登录页则补一次提交
                if not wait_for_auth_cookie(context, page, timeout=18):
                    if not (yidun_visible and yidun_visible(page)):
                        print("  页面未跳转，补一次登录提交...")
                        click_first_visible(
                            page,
                            [
                                ".btn-block__grandient_login:has-text('登录')",
                                "button:has-text('登录')",
                            ],
                            "补提交登录",
                        )
                    if yidun_visible and yidun_visible(page) and yidun_solve:
                        print("  补提交后又出现滑块，继续破解...")
                        try:
                            if yidun_solve(page, max_retry=4):
                                print("  ✓ 第二张滑块已通过")
                            else:
                                print("  ✗ 第二张滑块未通过")
                        except Exception as exc:
                            print(f"  第二张滑块破解异常: {exc}")
                    if not wait_for_auth_cookie(context, page, timeout=45):
                        save_debug_screenshot(page, "login_failed")
                        raise RuntimeError("登录后 60 秒内未拿到登录 Cookie。")
            else:
                print("  ✓ 检测到已登录状态，直接复用当前会话")

            try:
                wait_for_course_center_ready(page)
            except Exception as exc:
                if has_auth_cookie(context):
                    print(f"  ! 课程中心暂时打不开（{str(exc).splitlines()[0][:60]}），"
                          f"但登录 Cookie 已在，继续提取凭证")
                else:
                    raise

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

            saved = save_session_state(
                context, page, account,
                school=school, province=expected_province, note="login",
            )
            print(f"✓ 登录态已保存（按账号隔离）: {saved}")

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

                    saved = save_session_state(
                        context, page, account,
                        school=school, province=expected_province, note="login(partial)",
                    )
                    print(f"✓ 登录态已保存（按账号隔离）: {saved}")
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
    parser.add_argument("--force-relogin", action="store_true", help="忽略已保存登录态，强制重新登录")
    parser.add_argument("--headless", action="store_true", help="使用无头模式（不显示浏览器窗口）")
    parser.add_argument("--keep-open", action="store_true", help="保持浏览器开启，不自动关闭（需手动关闭浏览器窗口）")
    parser.add_argument("--school", help="按学校名取账号（如：天津大学 / 西南交通大学）")
    parser.add_argument("--no-reuse-session", action="store_true", help="不复用已保存登录态，强制新开网页登录")
    parser.add_argument("--session-ttl", type=float, default=DEFAULT_SESSION_TTL_HOURS,
                        help=f"登录态有效期（小时），默认 {DEFAULT_SESSION_TTL_HOURS:g}；设为 0 表示不按时间过期")
    parser.add_argument("--accounts-xlsx", help="账号表路径（默认 能力训练/智能体课程配置账号情况.xlsx）")
    parser.add_argument("--list-accounts", nargs="?", const="", metavar="关键字",
                        help="列出账号表里的账号（可按学校/省份关键字过滤）")
    parser.add_argument("--list-sessions", action="store_true", help="列出已保存登录态的账号")
    parser.add_argument("--export-headers", metavar="ACCOUNT",
                        help="离线导出某账号的 AUTHORIZATION/COOKIE（JSON），给其他 agent 直接复用")
    parser.add_argument("--export-env", metavar="ACCOUNT",
                        help="离线导出某账号的 AUTHORIZATION/COOKIE（shell 变量形式，可直接 eval）")
    parser.add_argument("--forget-session", metavar="ACCOUNT", help="删除某账号已保存的登录态")

    args = parser.parse_args()

    xlsx_rows = load_accounts_from_xlsx(Path(args.accounts_xlsx) if args.accounts_xlsx else None)

    if args.list_accounts is not None:
        kw = normalize_name(args.list_accounts)
        hits = [r for r in xlsx_rows
                if not kw or kw in normalize_name(r["name"]) or kw in normalize_name(r["province"])]
        if not hits:
            print("账号表里没有匹配的条目")
        else:
            print(f"{'省份':<8}{'学校/机构':<26}{'教工号':<20}{'密码':<22}")
            for r in hits:
                print(f"{r['province'] or '-':<8}{r['name'][:24]:<26}{r['account']:<20}{r['password']:<22}")
            print(f"\n共 {len(hits)} 条（账号表总计 {len(xlsx_rows)} 条）")
        sys.exit(0)

    if args.export_headers or args.export_env:
        target_account = args.export_headers or args.export_env
        sp = session_path_for(target_account)
        if not sp.exists():
            print(f"错误: {target_account} 没有已保存的登录态，先跑 --school/--account 登录一次")
            sys.exit(1)
        token, cookie_str = credentials_from_storage_state(sp)
        if not token:
            print(f"错误: {sp} 里没有可用的 JWT，请重新登录")
            sys.exit(1)
        meta = read_session_meta(sp)
        if args.export_headers:
            print(json.dumps({"Authorization": token, "Cookie": cookie_str}, ensure_ascii=False))
        else:
            print(f"AUTHORIZATION={token}")
            print(f"COOKIE={cookie_str}")
            print(f"# account={meta.get('account','')} saved_at={meta.get('saved_at','')}", file=sys.stderr)
        sys.exit(0)

    if args.list_sessions:
        rows = list_saved_sessions()
        if not rows:
            print("暂无已保存的登录态")
        else:
            print(f"{'账号':<18}{'学校':<16}{'姓名':<10}{'保存时间':<22}{'已存(h)':>8}")
            for r in rows:
                print(f"{r['account']:<18}{r['school'] or '-':<16}{r['real_name'] or '-':<10}"
                      f"{r['saved_at'] or '-':<22}{r['age_h']:>8}")
        sys.exit(0)

    if args.forget_session:
        target = session_path_for(args.forget_session)
        removed = []
        for f in (target, meta_path_for(target)):
            if f.exists():
                f.unlink()
                removed.append(f.name)
        print("已删除: " + (", ".join(removed) if removed else f"{args.forget_session} 无已保存登录态"))
        sys.exit(0)

    account = None
    password = None
    province = None
    course_target = None

    if args.file_path:
        # 处理 @/path/to/file 格式（Claude Code 文件引用格式）
        file_path = args.file_path
        if file_path.startswith('@'):
            file_path = file_path[1:]
        course_target = build_course_target(file_path, explicit_course_name=args.course_name or "")
        if course_target:
            print(f"识别到课程目录: {course_target.course_root}")
            if course_target.school:
                print(f"识别到学校: {course_target.school}")
            if course_target.course_keyword:
                print(f"识别到课程关键词: {course_target.course_keyword}")

    if args.school and not (args.account and args.password):
        hit = find_account_in_xlsx(args.school, xlsx_rows)
        if hit:
            account = hit["account"]
            password = hit["password"]
            province = hit["province_key"] or ""
            print(f"学校: {args.school}（来自账号表《智能体课程配置账号情况.xlsx》）")
            print(f"账号: {account}  省区: {province or '-'}")
        if not hit:
            print(f"错误: 账号表里找不到学校 '{args.school}'")
            print(f"提示: 用 --list-accounts 关键字 查看账号表，或用 --account/--password 直传")
            sys.exit(1)

    if account and password:
        pass

    elif args.account and args.password:
        account = args.account
        password = args.password
        province = infer_province_by_account(account)
        print(f"使用指定账号: {account}")
        if province:
            print(f"根据账号识别省区: {province}")

    elif args.province:
        province = args.province
        hit = find_account_in_xlsx(province, xlsx_rows)
        if hit:
            province = hit["province_key"] or province
            account, password = hit["account"], hit["password"]
            print(f"省区: {province}（来自账号表）")
            print(f"账号: {account}")
        else:
            print(f"错误: 账号表里找不到省区 '{province}' 的账号")
            print(f"可用省区: {', '.join(xlsx_provinces())}")
            sys.exit(1)

    elif args.file_path:
        file_path = args.file_path
        if file_path.startswith('@'):
            file_path = file_path[1:]
        school = (course_target.school if course_target and course_target.school
                  else extract_school_from_path(file_path))
        if school:
            print(f"从路径识别到学校: {school}")
            province = match_province_by_school(school) or ""

        if not province and course_target and course_target.province:
            province = course_target.province

        if not province:
            print(f"  账号表里没找到 '{school or file_path}' 的省区，尝试 LLM 推断...")
            province = infer_province_by_llm(school or file_path, xlsx_provinces())

        if not province:
            print("! 无法从路径自动识别省区")
            print(f"  路径: {file_path}")
            print("\n可用选项:")
            print("  1. 使用 --province 参数指定省区")
            print("  2. 使用 --account 和 --password 直接指定账号")
            print(f"\n支持的省区: {', '.join(xlsx_provinces())}")
            sys.exit(1)

        print(f"匹配到省区: {province}")

        # 账号来源优先级：账号表(按学校候选名) > 账号表(按省区) > 本地 JSON 映射
        hit = None
        for cand in school_candidates(school or "", course_target.course_root if course_target else ""):
            hit = find_account_in_xlsx(cand, xlsx_rows, strict=True)
            if hit:
                break
        if not hit and province:
            hit = find_account_in_xlsx(province, xlsx_rows, strict=False)
            if hit:
                print(f"  ! 账号表里没有该学校的专属账号，改用省区账号 {hit['account']}")
        if hit:
            account, password = hit["account"], hit["password"]
            province = hit["province_key"] or province
            print(f"账号: {account}（来自账号表：{hit['name']}）")
        else:
            result = get_account_by_province(province)
            if result:
                account, password = result
                print(f"账号: {account}（账号表省区账号）")
            else:
                print(f"错误: 账号表里找不到 '{school or province}' 的账号")
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
        reuse_session=not args.no_reuse_session,
        session_ttl_hours=args.session_ttl,
        school=args.school or "",
    )
    if result.success:
        print("\n✓ 自动登录完成，现在可以使用其他技能进行部署和测试")
        sys.exit(0)

    print("\n✗ 登录失败，请检查错误信息")
    sys.exit(1)


if __name__ == "__main__":
    main()
