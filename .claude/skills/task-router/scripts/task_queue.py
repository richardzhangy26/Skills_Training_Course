#!/usr/bin/env python3
"""任務佇列的確定性操作。

Router 和 Worker 只經由這個腳本改 issue 狀態和發布。
設計文檔：docs/superpowers/specs/2026-11-10-agent-task-queue-design.md

stdout 只輸出一個 JSON；拒絕執行時退出碼非 0。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Iterable, Optional

REPO = "richardzhangy26/agent-task-queue"
BOARD_TITLE = "看板"

TRIAGE_LABELS = ["needs-triage", "needs-info", "ready-for-agent", "ready-for-human", "wontfix"]
TYPE_LABELS = ["type:能力训练"]
STATUS_LABELS = [
    "status:in-progress",
    "status:waiting",
    "status:blocked",
    "status:ready",
    "status:published",
]
AGENT_LABELS = ["agent:pi"]

# 名稱 -> (顏色, 說明)
LABEL_SPECS = {
    "needs-triage": ("fbca04", "新分派，等你判斷"),
    "needs-info": ("d876e3", "任務書缺欄位或交付物不清楚"),
    "ready-for-agent": ("0e8a16", "可以派給 worker"),
    "ready-for-human": ("1d76db", "由你自己處理"),
    "wontfix": ("ffffff", "不做"),
    "type:能力训练": ("c5def5", "業務類型：能力訓練"),
    "status:in-progress": ("0052cc", "worker 執行中"),
    "status:waiting": ("e99695", "評測未達標，等你決定重做或接受"),
    "status:blocked": ("b60205", "卡住了，需要你處理"),
    "status:ready": ("bfd4f2", "你已接受，等你說發布"),
    "status:published": ("5319e7", "已發布，等你驗收"),
    "agent:pi": ("ededed", "指定用 pi 執行（不加就是 Claude Code）"),
}

BOARD_PLACEHOLDER = "尚未彙報。對 Router 說「彙報」後，這裡會被重寫。\n"


class GhError(RuntimeError):
    """gh 命令失敗。"""


class Refused(RuntimeError):
    """腳本依規則拒絕執行這個操作。"""


# 連線層的暫時性錯誤才重試。改標籤可以安全重複；重複的留言無害，因為標記行只取最新一條。
_TRANSIENT_HINTS = ("EOF", "timeout", "timed out", "connection reset", "connection refused", "TLS handshake")
_MAX_ATTEMPTS = 3
_RETRY_DELAY = 2.0


def _is_transient(message: str) -> bool:
    return any(hint in message for hint in _TRANSIENT_HINTS)


def _run_gh(argv: list[str], stdin: Optional[str]) -> str:
    proc = subprocess.run(argv, input=stdin, capture_output=True, text=True)
    if proc.returncode != 0:
        raise GhError(f"{' '.join(argv[:4])} … 失敗：{proc.stderr.strip()}")
    return proc.stdout


class Gh:
    """gh CLI 的薄包裝：固定 repo，寫操作串行且間隔至少 min_interval 秒。"""

    def __init__(
        self,
        repo: str = REPO,
        runner: Callable[[list[str], Optional[str]], str] = _run_gh,
        min_interval: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.repo = repo
        self._runner = runner
        self._min_interval = min_interval
        self._sleep = sleep
        self._clock = clock
        self._last_write: Optional[float] = None

    def _call(self, args: tuple, stdin: Optional[str], attempts: int) -> str:
        argv = ["gh", *args, "-R", self.repo]
        for attempt in range(1, attempts + 1):
            try:
                return self._runner(argv, stdin)
            except GhError as exc:
                if attempt == attempts or not _is_transient(str(exc)):
                    raise
                self._sleep(_RETRY_DELAY)
        raise AssertionError("unreachable")

    def read(self, *args: str) -> str:
        return self._call(args, None, _MAX_ATTEMPTS)

    def write(self, *args: str, stdin: Optional[str] = None, retry: bool = True) -> str:
        """retry=False 用於不可重複的寫入（建 issue）：連線中斷時請求可能已經生效。"""
        if self._last_write is not None:
            wait = self._min_interval - (self._clock() - self._last_write)
            if wait > 0:
                self._sleep(wait)
        try:
            return self._call(args, stdin, _MAX_ATTEMPTS if retry else 1)
        finally:
            self._last_write = self._clock()

    def read_json(self, *args: str):
        return json.loads(self.read(*args) or "null")


# ---------------------------------------------------------------- 門禁

GATE_THRESHOLD = 80
MAX_REWORK_ROUNDS = 2


def load_report(path) -> Optional[dict]:
    """讀一份評測報告。檔案缺失或不是合法 JSON 物件時回傳 None。"""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def recompute_total(report: dict):
    """從各維度的 score 重算總分，不採信報告裡的 total_score。"""
    dimensions = report.get("dimensions") if isinstance(report, dict) else None
    if not isinstance(dimensions, list) or not dimensions:
        raise ValueError("報告沒有 dimensions")
    total = 0
    for dimension in dimensions:
        score = dimension.get("score") if isinstance(dimension, dict) else None
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("維度分數不是數字")
        total += score
    return int(total) if float(total).is_integer() else round(total, 2)


def gate(good_report, medium_report, threshold: int = GATE_THRESHOLD) -> dict:
    """兩份報告都達標才通過。報告缺失、解析失敗或一票否決都算不通過。"""
    scores: dict = {}
    reasons: list[str] = []
    notes: list[str] = []
    for profile, report in (("good", good_report), ("medium", medium_report)):
        try:
            total = recompute_total(report)
        except ValueError:
            scores[profile] = None
            reasons.append(f"{profile} 報告缺失或無法解析")
            continue
        scores[profile] = total
        reported = report.get("total_score")
        if reported != total:
            notes.append(f"{profile} 報告總分 {reported} 與子項重算 {total} 不一致，以重算為準")
        if total < threshold:
            reasons.append(f"{profile} 重算總分 {total} 低於 {threshold}")
        vetoed = any(isinstance(d, dict) and d.get("is_veto") for d in report["dimensions"])
        if vetoed or report.get("veto_reasons"):
            reasons.append(f"{profile} 觸發一票否決")
    return {"pass": not reasons, "scores": scores, "reasons": reasons, "notes": notes}


def next_step_after_gate(passed: bool, rounds: int) -> str:
    """門禁之後 worker 該做什麼：publish、waiting 或 blocked。"""
    if passed:
        return "publish"
    return "blocked" if rounds >= MAX_REWORK_ROUNDS else "waiting"


# ---------------------------------------------------------------- 狀態流轉

# 事件 -> (要求的當前狀態, 目標狀態)。表外的流轉一律拒絕。
TRANSITIONS = {
    "claim": (None, "status:in-progress"),
    "retry": ("status:blocked", "status:in-progress"),
    "rework": ("status:waiting", "status:in-progress"),
    "gate-fail": ("status:in-progress", "status:waiting"),
    "block": ("status:in-progress", "status:blocked"),
    "publish": ("status:in-progress", "status:published"),
    "accept": ("status:waiting", "status:ready"),
    "publish-approved": ("status:ready", "status:published"),
}


def current_status(labels: Iterable[str]) -> Optional[str]:
    statuses = [label for label in labels if label.startswith("status:")]
    if len(statuses) > 1:
        raise Refused(f"issue 同時有多個狀態標籤：{', '.join(statuses)}")
    return statuses[0] if statuses else None


def check_transition(labels: Iterable[str], event: str) -> str:
    """檢查事件在當前標籤下是否合法，回傳目標狀態標籤。"""
    labels = list(labels)
    if event not in TRANSITIONS:
        raise Refused(f"未知的事件：{event}")
    required, target = TRANSITIONS[event]
    status = current_status(labels)
    if status != required:
        raise Refused(f"事件 {event} 要求當前狀態為 {required or '無'}，實際是 {status or '無'}")
    if event == "claim" and "ready-for-agent" not in labels:
        raise Refused("只有帶 ready-for-agent 的 issue 可以認領")
    return target


# ---------------------------------------------------------------- 任務書與防重複鍵

_KEY_RE = re.compile(r"<!--\s*key:\s*(.*?)\s*-->")
_FIELD_RE = re.compile(r"^\s*-\s*([^：:]+?)\s*[：:]\s*(.*)$")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_CONVERTED_DATE_RE = re.compile(r"换算\s*(\d{4}-\d{2}-\d{2})")


def _normalize_part(text: str) -> str:
    text = text.replace("（", "(").replace("）", ")")
    return re.sub(r"\s+", "", text)


def normalize_key(key: str) -> str:
    return "|".join(_normalize_part(part) for part in key.split("|"))


def dedup_key(school_course: str, biz_type: str, assigner: str, date: str) -> str:
    """防重複鍵。全角和半角括號、空格視為相同。"""
    return normalize_key("|".join([school_course, biz_type, assigner, date]))


def _key_from_body(body: str) -> Optional[str]:
    """只認第一個二級標題之前的 key，聊天原文裡出現的不算。"""
    header = re.split(r"^## ", body or "", maxsplit=1, flags=re.MULTILINE)[0]
    match = _KEY_RE.search(header)
    return match.group(1) if match else None


def _parse_ddl(value: Optional[str]) -> Optional[dt.date]:
    if not value:
        return None
    match = _CONVERTED_DATE_RE.search(value)
    text = match.group(1) if match else (_DATE_RE.search(value) or [None])[0]
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def parse_task_book(body: str) -> dict:
    """解析 issue 正文裡「## 任务书」一節的欄位。其他小節不解析。"""
    fields: dict[str, str] = {}
    in_book = False
    for line in (body or "").splitlines():
        if line.startswith("## "):
            in_book = line[3:].strip().startswith("任务书")
            continue
        if not in_book:
            continue
        match = _FIELD_RE.match(line)
        if match and match.group(1) not in fields:
            fields[match.group(1)] = match.group(2).strip()
    return {
        "key": _key_from_body(body),
        "school_course": fields.get("学校-课程"),
        "biz_type": fields.get("业务类型"),
        "assigner": fields.get("安排人"),
        "message_date": fields.get("原消息日期"),
        "deliverable": fields.get("交付物"),
        "ddl": _parse_ddl(fields.get("DDL")),
        "local_dir": fields.get("本机目录"),
        "course_id": fields.get("COURSE_ID"),
        "fields": fields,
    }


def find_duplicates(issues: Iterable[dict], key: str) -> list[int]:
    """在已開和已關的 issue 裡找防重複鍵相同的，回傳編號。"""
    target = normalize_key(key)
    numbers = []
    for issue in issues:
        existing = _key_from_body(issue.get("body") or "")
        if existing and normalize_key(existing) == target:
            numbers.append(issue["number"])
    return sorted(numbers)


# ---------------------------------------------------------------- 留言標記與看板

MARKERS = ("CLAIM", "GATE", "PUBLISHED", "BLOCKED", "COURSE")
_MARKER_RE = re.compile(r"^(%s):\s*(.*)$" % "|".join(MARKERS))

_STATUS_TEXT = {
    "status:in-progress": "進行中",
    "status:waiting": "評測未達標",
    "status:blocked": "卡住了",
    "status:ready": "已接受待發布",
    "status:published": "已發布待驗收",
}
_TRIAGE_TEXT = {
    "needs-triage": "新分派",
    "needs-info": "缺資訊",
    "ready-for-agent": "待派工",
    "ready-for-human": "你自己處理",
    "wontfix": "不做",
}
# 「需要你決定的」區塊：(小標題, 判斷用的標籤, 取哪個留言標記當說明)
_DECIDE_GROUPS = (
    ("評測未達標，請回「重做」或「接受」", "status:waiting", "GATE"),
    ("卡住了", "status:blocked", "BLOCKED"),
    ("新分派，請分診", "needs-triage", None),
    ("缺資訊", "needs-info", None),
    ("已接受，等你說「發布」", "status:ready", "GATE"),
)


def extract_markers(comments: Iterable[str]) -> dict:
    """從留言裡取每種標記行的最新一條，例如「GATE: PASS good=88 medium=83」。"""
    markers: dict[str, str] = {}
    for comment in comments:
        for line in (comment or "").splitlines():
            match = _MARKER_RE.match(line.strip())
            if match:
                markers[match.group(1)] = match.group(2).strip()
    return markers


def _board_group(labels: list[str]) -> str:
    """一張 issue 在看板上歸哪一類：有狀態標籤看狀態，否則看分診標籤。"""
    for label in labels:
        if label in _STATUS_TEXT:
            return label
    for label in _TRIAGE_TEXT:
        if label in labels:
            return label
    return ""


def _remaining_text(ddl: Optional[dt.date], today: dt.date) -> str:
    if ddl is None:
        return "未定"
    days = (ddl - today).days
    if days < 0:
        return f"逾期 {-days} 天"
    return "今天" if days == 0 else f"剩 {days} 天"


def _board_line(issue: dict, marker: Optional[str]) -> str:
    detail = issue.get("markers", {}).get(marker) if marker else None
    line = f"- #{issue['number']} {issue['title']}"
    return f"{line} — {detail}" if detail else line


def render_board(issues: Iterable[dict], today: dt.date, updated_at: str) -> str:
    """產生看板正文。issues 不含看板 issue 本身。"""
    issues = sorted(issues, key=lambda issue: issue["number"])
    grouped: dict[str, list[dict]] = {}
    for issue in issues:
        grouped.setdefault(_board_group(issue["labels"]), []).append(issue)

    out = ["## 需要你決定的", ""]
    any_decision = False
    for heading, label, marker in _DECIDE_GROUPS:
        if grouped.get(label):
            any_decision = True
            out.append(f"**{heading}**")
            out.extend(_board_line(issue, marker) for issue in grouped[label])
            out.append("")
    if not any_decision:
        out.extend(["（無）", ""])

    for heading, label, marker in (
        ("## 進行中", "status:in-progress", "CLAIM"),
        ("## 已發布待驗收", "status:published", "PUBLISHED"),
    ):
        out.extend([heading, ""])
        rows = [_board_line(issue, marker) for issue in grouped.get(label, [])]
        out.extend(rows or ["（無）"])
        out.append("")

    out.extend(["## DDL 一覽", ""])
    if issues:
        out.extend(["| 任務 | DDL | 剩餘 | 狀態 |", "|---|---|---|---|"])
        by_ddl = sorted(issues, key=lambda i: (i.get("ddl") is None, i.get("ddl") or dt.date.max, i["number"]))
        for issue in by_ddl:
            group = _board_group(issue["labels"])
            status = _STATUS_TEXT.get(group) or _TRIAGE_TEXT.get(group) or "未分類"
            ddl = issue.get("ddl")
            out.append(
                f"| #{issue['number']} {issue['title']} | {ddl.isoformat() if ddl else '—'} "
                f"| {_remaining_text(ddl, today)} | {status} |"
            )
    else:
        out.append("（無）")
    out.extend(["", "## 最後更新", "", updated_at, ""])
    return "\n".join(out)


# ---------------------------------------------------------------- init


def find_board(gh: Gh) -> Optional[dict]:
    """找標題恰為 BOARD_TITLE 的開啟中 issue。不用搜尋接口，避免索引延遲。"""
    issues = gh.read_json(
        "issue", "list", "--state", "open", "--limit", "1000", "--json", "number,title,isPinned"
    )
    for issue in issues or []:
        if issue["title"] == BOARD_TITLE:
            return issue
    return None


def cmd_init(gh: Gh) -> dict:
    for name, (color, description) in LABEL_SPECS.items():
        gh.write("label", "create", name, "--color", color, "--description", description, "--force")

    board = find_board(gh)
    created = False
    if board is None:
        url = gh.write(
            "issue", "create", "--title", BOARD_TITLE, "--body-file", "-", stdin=BOARD_PLACEHOLDER, retry=False
        )
        number = int(url.strip().rstrip("/").rsplit("/", 1)[-1])
        board = {"number": number, "title": BOARD_TITLE, "isPinned": False}
        created = True
    if not board.get("isPinned"):
        gh.write("issue", "pin", str(board["number"]))
    return {
        "labels": list(LABEL_SPECS),
        "board": board["number"],
        "board_created": created,
        "pinned": True,
    }


# ---------------------------------------------------------------- issue 讀取與運行記錄

PROJECT_ROOT = Path(__file__).resolve().parents[4]
# 業務類型 -> worker 可以寫的根目錄。任務書的「本机目录」必須在它之下。
ALLOWED_ROOTS = {"能力训练": PROJECT_ROOT / "skills_training_course"}
# worker 可以經 record 子命令寫入的欄位。rounds、gate、claims 只由腳本自己寫。
RECORD_KEYS = (
    "task_id",
    "course_id",
    "script_md",
    "teacher_doc",
    "dialogue_good",
    "dialogue_medium",
    "evaluation_good",
    "evaluation_medium",
)
_ISSUE_FIELDS = "number,title,body,state,labels,comments"
_STATUS_EVENTS = {"waiting": "gate-fail", "blocked": "block", "ready": "accept"}


def _labels(issue: dict) -> list[str]:
    return [label["name"] for label in issue.get("labels") or []]


def _comments(issue: dict) -> list[str]:
    return [comment.get("body") or "" for comment in issue.get("comments") or []]


def fetch_issue(gh: Gh, number: int) -> dict:
    return gh.read_json("issue", "view", str(number), "--json", _ISSUE_FIELDS)


def fetch_issues(gh: Gh, state: str) -> list[dict]:
    """state 是 open 或 all。直接列出再在本機篩選，不用搜尋接口。"""
    return gh.read_json("issue", "list", "--state", state, "--limit", "1000", "--json", _ISSUE_FIELDS) or []


def resolve_local_dir(book: dict) -> Path:
    """任務書的本機目錄必須是允許根目錄下的子目錄，否則拒絕。"""
    root = ALLOWED_ROOTS.get(book.get("biz_type") or "")
    if root is None:
        raise Refused(f"任務書的业务类型缺失或不支援：{book.get('biz_type')!r}")
    raw = (book.get("local_dir") or "").strip()
    if not raw:
        raise Refused("任務書缺少本机目录")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise Refused(f"本机目录必須是絕對路徑：{raw}")
    path, root = path.resolve(), root.resolve()
    if path == root or not path.is_relative_to(root):
        raise Refused(f"本机目录必須在 {root} 之下：{raw}")
    return path


def record_path(local_dir, number: int) -> Path:
    return Path(local_dir) / ".task-queue" / f"run-{number}.json"


def load_record(local_dir, number: int) -> dict:
    path = record_path(local_dir, number)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"issue": number, "rounds": 0}


def save_record(local_dir, number: int, record: dict) -> Path:
    path = record_path(local_dir, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _issue_local_dir(issue: dict) -> Path:
    return resolve_local_dir(parse_task_book(issue.get("body") or ""))


def _move_status(gh: Gh, number: int, labels: list[str], target: str) -> None:
    args = ["issue", "edit", str(number), "--add-label", target]
    current = current_status(labels)
    if current:
        args += ["--remove-label", current]
    gh.write(*args)


def _comment(gh: Gh, number: int, text: str) -> None:
    gh.write("issue", "comment", str(number), "--body-file", "-", stdin=text)


# ---------------------------------------------------------------- 子命令


def cmd_find_dup(gh: Gh, key: str) -> dict:
    return {"key": normalize_key(key), "duplicates": find_duplicates(fetch_issues(gh, "all"), key)}


def cmd_list_ready(gh: Gh) -> list[dict]:
    """可以派的任務：開啟中、ready-for-agent、有業務類型、沒有任何狀態標籤。DDL 早的排前面。"""
    ready = []
    for issue in fetch_issues(gh, "open"):
        labels = _labels(issue)
        if issue["title"] == BOARD_TITLE or "ready-for-agent" not in labels:
            continue
        if not any(label in TYPE_LABELS for label in labels):
            continue
        if any(label.startswith("status:") for label in labels):
            continue
        book = parse_task_book(issue.get("body") or "")
        markers = extract_markers(_comments(issue))
        ready.append(
            {
                "number": issue["number"],
                "title": issue["title"],
                "agent": next((l.split(":", 1)[1] for l in labels if l.startswith("agent:")), "claude"),
                "school_course": book["school_course"],
                "local_dir": book["local_dir"],
                "ddl": book["ddl"].isoformat() if book["ddl"] else None,
                "course_id": book["course_id"] or markers.get("COURSE"),
            }
        )
    return sorted(ready, key=lambda item: (item["ddl"] is None, item["ddl"] or "", item["number"]))


def cmd_claim(gh: Gh, number: int, agent: str, pane: str, now: dt.datetime, event: str = "claim") -> dict:
    """認領一張任務。event 是 claim（新派）、retry（重派卡住的）或 rework（重做）。"""
    if event not in ("claim", "retry", "rework"):
        raise Refused(f"claim 不接受事件：{event}")
    issue = fetch_issue(gh, number)
    labels = _labels(issue)
    target = check_transition(labels, event)
    local_dir = _issue_local_dir(issue)
    record = load_record(local_dir, number)
    rounds = record.get("rounds", 0)
    if event == "rework":
        if rounds >= MAX_REWORK_ROUNDS:
            raise Refused(f"#{number} 已重做 {rounds} 輪，達到上限")
        rounds += 1
    at = now.isoformat(timespec="minutes")
    record["rounds"] = rounds
    record.setdefault("claims", []).append({"event": event, "agent": agent, "pane": pane, "at": at})

    _move_status(gh, number, labels, target)
    _comment(gh, number, f"CLAIM: agent={agent} pane={pane} at={at} event={event} round={rounds}\n")
    path = save_record(local_dir, number, record)
    return {"number": number, "status": target, "rounds": rounds, "record": str(path), "local_dir": str(local_dir)}


def cmd_record(gh: Gh, number: int, sets: list[str]) -> dict:
    updates = {}
    for item in sets:
        key, sep, value = item.partition("=")
        if not sep or key not in RECORD_KEYS:
            raise Refused(f"record 不接受的欄位：{key}（可用：{', '.join(RECORD_KEYS)}）")
        updates[key] = value
    local_dir = _issue_local_dir(fetch_issue(gh, number))
    record = load_record(local_dir, number)
    record.update(updates)
    path = save_record(local_dir, number, record)
    return {"number": number, "record": str(path), "updated": sorted(updates)}


def _gate_from_record(record: dict) -> dict:
    reports = {
        profile: load_report(record[f"evaluation_{profile}"]) if record.get(f"evaluation_{profile}") else None
        for profile in ("good", "medium")
    }
    return gate(reports["good"], reports["medium"])


def _gate_line(result: dict) -> str:
    def fmt(score):
        return "-" if score is None else str(score)

    verdict = "PASS" if result["pass"] else "FAIL"
    return f"GATE: {verdict} good={fmt(result['scores']['good'])} medium={fmt(result['scores']['medium'])}"


def cmd_gate(gh: Gh, number: int, now: dt.datetime) -> dict:
    """讀運行記錄裡的兩份評測報告，判定門禁，留言，並告訴 worker 下一步。不改狀態標籤。"""
    local_dir = _issue_local_dir(fetch_issue(gh, number))
    record = load_record(local_dir, number)
    result = _gate_from_record(record)
    result["next"] = next_step_after_gate(result["pass"], record.get("rounds", 0))

    lines = [_gate_line(result), ""]
    lines += [f"- 不通過：{reason}" for reason in result["reasons"]]
    lines += [f"- 註：{note}" for note in result["notes"]]
    lines.append(f"- 下一步：{result['next']}（已重做 {record.get('rounds', 0)} 輪）")
    _comment(gh, number, "\n".join(lines) + "\n")

    record["gate"] = {**result, "at": now.isoformat(timespec="minutes")}
    save_record(local_dir, number, record)
    return result


def cmd_set_status(gh: Gh, number: int, status: str, comment_file) -> dict:
    """worker 標 waiting 或 blocked；Router 在你說「接受」時標 ready。"""
    if status not in _STATUS_EVENTS:
        raise Refused(f"set-status 不接受：{status}")
    issue = fetch_issue(gh, number)
    labels = _labels(issue)
    target = check_transition(labels, _STATUS_EVENTS[status])
    comment = Path(comment_file).read_text(encoding="utf-8").strip() if comment_file else ""
    if status in ("waiting", "blocked") and not comment:
        raise Refused(f"標 {status} 必須附說明（--comment-file）")
    if status == "waiting":
        record = load_record(_issue_local_dir(issue), number)
        if record.get("gate", {}).get("pass") is not False:
            raise Refused("只有門禁不通過之後才能標 waiting，先跑 gate")
    if status == "blocked":
        comment = f"BLOCKED: {comment}"

    _move_status(gh, number, labels, target)
    if comment:
        _comment(gh, number, comment + "\n")
    return {"number": number, "status": target}


def cmd_board(gh: Gh, now: dt.datetime) -> dict:
    issues = fetch_issues(gh, "open")
    board = next((issue for issue in issues if issue["title"] == BOARD_TITLE), None)
    if board is None:
        raise Refused("找不到看板 issue，先跑 init")
    rows = [
        {
            "number": issue["number"],
            "title": issue["title"],
            "labels": _labels(issue),
            "ddl": parse_task_book(issue.get("body") or "")["ddl"],
            "markers": extract_markers(_comments(issue)),
        }
        for issue in issues
        if issue["number"] != board["number"]
    ]
    body = render_board(rows, now.date(), now.strftime("%Y-%m-%d %H:%M"))
    gh.write("issue", "edit", str(board["number"]), "--body-file", "-", stdin=body)
    return {"board": board["number"], "issues": len(rows)}


# ---------------------------------------------------------------- main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="任務佇列的確定性操作")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="建標籤、建並置頂看板 issue（可重複執行）")

    p = sub.add_parser("find-dup", help="用防重複鍵找已有的 issue（含已關閉）")
    p.add_argument("--key", required=True)

    sub.add_parser("list-ready", help="列出可以派的任務")

    p = sub.add_parser("claim", help="認領任務並標 status:in-progress")
    p.add_argument("number", type=int)
    p.add_argument("--agent", required=True)
    p.add_argument("--pane", required=True)
    p.add_argument("--event", choices=("claim", "retry", "rework"), default="claim")

    p = sub.add_parser("record", help="把產出路徑和 ID 寫進運行記錄")
    p.add_argument("number", type=int)
    p.add_argument("--set", dest="sets", nargs="+", required=True, metavar="KEY=VALUE")

    p = sub.add_parser("gate", help="判定評測門禁並留言")
    p.add_argument("number", type=int)

    p = sub.add_parser("set-status", help="標 waiting、blocked 或 ready")
    p.add_argument("number", type=int)
    p.add_argument("status", choices=tuple(_STATUS_EVENTS))
    p.add_argument("--comment-file")

    sub.add_parser("board", help="重寫看板 issue")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    gh = Gh()
    now = dt.datetime.now()
    try:
        if args.command == "init":
            result = cmd_init(gh)
        elif args.command == "find-dup":
            result = cmd_find_dup(gh, args.key)
        elif args.command == "list-ready":
            result = cmd_list_ready(gh)
        elif args.command == "claim":
            result = cmd_claim(gh, args.number, args.agent, args.pane, now, args.event)
        elif args.command == "record":
            result = cmd_record(gh, args.number, args.sets)
        elif args.command == "gate":
            result = cmd_gate(gh, args.number, now)
        elif args.command == "set-status":
            result = cmd_set_status(gh, args.number, args.status, args.comment_file)
        elif args.command == "board":
            result = cmd_board(gh, now)
        else:  # pragma: no cover - argparse 已擋掉
            raise Refused(f"未知的子命令：{args.command}")
    except Refused as exc:
        print(json.dumps({"error": str(exc), "refused": True}, ensure_ascii=False))
        return 2
    except GhError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
