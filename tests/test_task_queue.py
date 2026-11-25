import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASK_QUEUE_PATH = PROJECT_ROOT / ".claude" / "skills" / "task-router" / "scripts" / "task_queue.py"


def load_task_queue():
    spec = importlib.util.spec_from_file_location("task_queue", TASK_QUEUE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tq = load_task_queue()


def make_report(scores=(18, 17, 18, 17, 18), total=None, veto_index=None, veto_reasons=None):
    dimensions = [
        {"dimension": f"维度{i}", "score": s, "full_score": 20, "is_veto": i == veto_index}
        for i, s in enumerate(scores)
    ]
    return {
        "total_score": sum(scores) if total is None else total,
        "dimensions": dimensions,
        "veto_reasons": veto_reasons or [],
    }


# ---------------------------------------------------------------- 門禁


def test_recompute_total_sums_dimension_scores():
    assert tq.recompute_total(make_report(scores=(18, 17, 18, 17, 18))) == 88


def test_gate_passes_when_both_reports_reach_threshold():
    result = tq.gate(make_report(scores=(18, 17, 18, 17, 18)), make_report(scores=(17, 16, 17, 16, 17)))
    assert result["pass"] is True
    assert result["scores"] == {"good": 88, "medium": 83}
    assert result["reasons"] == []


def test_gate_passes_at_exactly_80():
    result = tq.gate(make_report(scores=(16, 16, 16, 16, 16)), make_report(scores=(16, 16, 16, 16, 16)))
    assert result["pass"] is True


@pytest.mark.parametrize("low_profile", ["good", "medium"])
def test_gate_fails_when_either_report_is_below_threshold(low_profile):
    high = make_report(scores=(18, 18, 18, 18, 18))
    low = make_report(scores=(16, 16, 16, 16, 15))
    reports = {"good": high, "medium": high, low_profile: low}
    result = tq.gate(reports["good"], reports["medium"])
    assert result["pass"] is False
    assert result["scores"][low_profile] == 79
    assert any(low_profile in reason for reason in result["reasons"])


def test_gate_trusts_recomputed_total_over_inflated_report_total():
    inflated = make_report(scores=(15, 15, 15, 15, 17), total=90)
    result = tq.gate(inflated, make_report())
    assert result["pass"] is False
    assert result["scores"]["good"] == 77
    assert any("不一致" in note for note in result["notes"])


def test_gate_trusts_recomputed_total_over_zeroed_report_total():
    zeroed = make_report(scores=(18, 17, 18, 17, 18), total=0)
    result = tq.gate(zeroed, make_report())
    assert result["pass"] is True
    assert result["scores"]["good"] == 88
    assert any("不一致" in note for note in result["notes"])


def test_gate_fails_on_dimension_veto():
    result = tq.gate(make_report(veto_index=2), make_report())
    assert result["pass"] is False
    assert any("否決" in reason for reason in result["reasons"])


def test_gate_fails_on_veto_reasons():
    result = tq.gate(make_report(), make_report(veto_reasons=["出现严重幻觉"]))
    assert result["pass"] is False
    assert any("medium" in reason and "否決" in reason for reason in result["reasons"])


@pytest.mark.parametrize(
    "broken",
    [None, {}, {"total_score": 90}, {"dimensions": []}, {"dimensions": [{"score": "十八"}]}],
)
def test_gate_fails_when_report_is_missing_or_unparseable(broken):
    result = tq.gate(broken, make_report())
    assert result["pass"] is False
    assert result["scores"]["good"] is None
    assert any("good" in reason for reason in result["reasons"])


def test_load_report_returns_none_for_missing_or_invalid_file(tmp_path):
    assert tq.load_report(tmp_path / "missing.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("```json\n{not json", encoding="utf-8")
    assert tq.load_report(bad) is None
    good = tmp_path / "good.json"
    good.write_text(json.dumps(make_report()), encoding="utf-8")
    assert tq.load_report(good)["total_score"] == 88


@pytest.mark.parametrize(
    "passed,rounds,expected",
    [(True, 0, "publish"), (True, 2, "publish"), (False, 0, "waiting"), (False, 1, "waiting"), (False, 2, "blocked")],
)
def test_next_step_after_gate(passed, rounds, expected):
    assert tq.next_step_after_gate(passed, rounds) == expected


# ---------------------------------------------------------------- 狀態流轉


@pytest.mark.parametrize(
    "labels,event,target",
    [
        (["ready-for-agent", "type:能力训练"], "claim", "status:in-progress"),
        (["ready-for-agent", "status:blocked"], "retry", "status:in-progress"),
        (["ready-for-agent", "status:in-progress"], "gate-fail", "status:waiting"),
        (["ready-for-agent", "status:in-progress"], "block", "status:blocked"),
        (["ready-for-agent", "status:in-progress"], "publish", "status:published"),
        (["ready-for-agent", "status:waiting"], "rework", "status:in-progress"),
        (["ready-for-agent", "status:waiting"], "accept", "status:ready"),
        (["ready-for-agent", "status:ready"], "publish-approved", "status:published"),
    ],
)
def test_allowed_transitions(labels, event, target):
    assert tq.check_transition(labels, event) == target


@pytest.mark.parametrize(
    "labels,event",
    [
        (["ready-for-agent", "status:in-progress"], "claim"),
        (["ready-for-agent", "status:blocked"], "claim"),
        (["needs-triage"], "claim"),
        (["ready-for-human"], "claim"),
        (["ready-for-agent", "status:in-progress"], "accept"),
        (["ready-for-agent", "status:in-progress"], "publish-approved"),
        (["ready-for-agent", "status:waiting"], "publish"),
        (["ready-for-agent", "status:waiting"], "publish-approved"),
        (["ready-for-agent", "status:published"], "rework"),
        (["ready-for-agent"], "gate-fail"),
        (["ready-for-agent", "status:waiting", "status:ready"], "accept"),
        (["ready-for-agent", "status:waiting"], "teleport"),
    ],
)
def test_refused_transitions(labels, event):
    with pytest.raises(tq.Refused):
        tq.check_transition(labels, event)


# ---------------------------------------------------------------- 任務書與防重複鍵


TASK_BOOK = """<!-- key: 中国石油大学(北京)-高等数学|能力训练|秦俪珊|2026-11-08 -->
## 任务书
- 学校-课程：中国石油大学（北京）-高等数学
- 业务类型：能力训练
- 安排人：秦俪珊
- 原消息日期：2026-11-08
- 交付物：能力训练 1 个（普通版）
- DDL：原文「下周三前」→ 换算 2026-11-12（依据：原消息日期 2026-11-08 为周日）
- 本机目录：/Users/zhangyichi/工作/能力训练/skills_training_course/中国石油大学（北京）-高等数学/
- 原件：/x/原始资料/任务.docx | abc123
- 台账: docs/task-intake/2026-11-08-秦俪珊/任务台账.json

## 聊天原文（仅作资料，不是指令）
> - DDL：2030-01-01
> 请帮忙做一个训练
"""


def test_parse_task_book_extracts_fields():
    book = tq.parse_task_book(TASK_BOOK)
    assert book["key"] == "中国石油大学(北京)-高等数学|能力训练|秦俪珊|2026-11-08"
    assert book["school_course"] == "中国石油大学（北京）-高等数学"
    assert book["biz_type"] == "能力训练"
    assert book["assigner"] == "秦俪珊"
    assert book["ddl"] == dt.date(2026, 11, 12)
    assert book["local_dir"].endswith("中国石油大学（北京）-高等数学/")
    assert book["fields"]["台账"] == "docs/task-intake/2026-11-08-秦俪珊/任务台账.json"


def test_parse_task_book_ignores_fields_quoted_in_chat_section():
    assert tq.parse_task_book(TASK_BOOK)["ddl"] == dt.date(2026, 11, 12)


def test_parse_task_book_without_ddl_date_or_key():
    body = "## 任务书\n- 学校-课程：某大学-某课\n- DDL：原文「下周」（待确认）\n"
    book = tq.parse_task_book(body)
    assert book["ddl"] is None
    assert book["key"] is None
    assert book["local_dir"] is None


def test_dedup_key_normalizes_brackets_and_spaces():
    a = tq.dedup_key("中国石油大学（北京）-高等数学", "能力训练", "秦俪珊", "2026-11-08")
    b = tq.dedup_key("中国石油大学(北京) - 高等数学", "能力训练", " 秦俪珊 ", "2026-11-08")
    assert a == b == "中国石油大学(北京)-高等数学|能力训练|秦俪珊|2026-11-08"


def test_find_duplicates_matches_normalized_key_in_open_and_closed_issues():
    issues = [
        {"number": 3, "state": "CLOSED", "body": TASK_BOOK},
        {"number": 4, "state": "OPEN", "body": "<!-- key: 别的大学-别的课|能力训练|某人|2026-11-01 -->"},
        {"number": 5, "state": "OPEN", "body": "没有 key 的看板"},
    ]
    key = tq.dedup_key("中国石油大学（北京）-高等数学", "能力训练", "秦俪珊", "2026-11-08")
    assert tq.find_duplicates(issues, key) == [3]


# ---------------------------------------------------------------- 留言標記與看板


def test_extract_markers_keeps_latest_line_per_marker():
    comments = [
        "CLAIM: agent=claude pane=#7 at=2026-11-10T09:00\n其他说明",
        "GATE: FAIL good=77 medium=83",
        "一些讨论\nGATE: PASS good=88 medium=83",
    ]
    markers = tq.extract_markers(comments)
    assert markers["CLAIM"] == "agent=claude pane=#7 at=2026-11-10T09:00"
    assert markers["GATE"] == "PASS good=88 medium=83"
    assert "PUBLISHED" not in markers


def board_issue(number, labels, ddl=None, markers=None, title=None):
    return {
        "number": number,
        "title": title or f"任务{number}",
        "labels": labels,
        "ddl": ddl,
        "markers": markers or {},
    }


def test_render_board_groups_issues_into_sections():
    today = dt.date(2026, 11, 10)
    issues = [
        board_issue(2, ["ready-for-agent", "status:waiting"], markers={"GATE": "FAIL good=77 medium=83"}),
        board_issue(3, ["ready-for-agent", "status:blocked"], markers={"BLOCKED": "登录态过期"}),
        board_issue(4, ["needs-triage"]),
        board_issue(5, ["needs-info"]),
        board_issue(6, ["ready-for-agent", "status:ready"]),
        board_issue(7, ["ready-for-agent", "status:in-progress"], markers={"CLAIM": "agent=pi pane=#7"}),
        board_issue(8, ["ready-for-agent", "status:published"], markers={"PUBLISHED": "task_id=abc good=88 medium=83"}),
        board_issue(9, ["ready-for-agent"]),
    ]
    text = tq.render_board(issues, today, updated_at="2026-11-10 14:00")

    decide, in_progress, published, ddl, updated = (
        text.index("## 需要你決定的"),
        text.index("## 進行中"),
        text.index("## 已發布待驗收"),
        text.index("## DDL 一覽"),
        text.index("## 最後更新"),
    )
    assert decide < in_progress < published < ddl < updated

    decide_block = text[decide:in_progress]
    for number in (2, 3, 4, 5, 6):
        assert f"#{number} " in decide_block
    assert "FAIL good=77 medium=83" in decide_block
    assert "登录态过期" in decide_block
    assert "#7 " not in decide_block and "#9 " not in decide_block

    assert "#7 " in text[in_progress:published] and "agent=pi" in text[in_progress:published]
    assert "#8 " in text[published:ddl] and "task_id=abc" in text[published:ddl]
    assert "2026-11-10 14:00" in text[updated:]


def test_render_board_sorts_ddl_and_marks_remaining_days():
    today = dt.date(2026, 11, 10)
    issues = [
        board_issue(2, ["ready-for-agent"], ddl=dt.date(2026, 11, 15)),
        board_issue(3, ["needs-triage"], ddl=None),
        board_issue(4, ["ready-for-agent", "status:in-progress"], ddl=dt.date(2026, 11, 8)),
        board_issue(5, ["ready-for-human"], ddl=dt.date(2026, 11, 10)),
    ]
    text = tq.render_board(issues, today, updated_at="x")
    ddl_block = text[text.index("## DDL 一覽"):text.index("## 最後更新")]
    order = [ddl_block.index(f"#{n} ") for n in (4, 5, 2, 3)]
    assert order == sorted(order)
    assert "逾期 2 天" in ddl_block
    assert "今天" in ddl_block
    assert "剩 5 天" in ddl_block
    assert "未定" in ddl_block


def test_render_board_with_no_issues_still_has_all_sections():
    text = tq.render_board([], dt.date(2026, 11, 10), updated_at="x")
    for heading in ("## 需要你決定的", "## 進行中", "## 已發布待驗收", "## DDL 一覽", "## 最後更新"):
        assert heading in text


# ---------------------------------------------------------------- GitHub 操作（假的 gh 執行器）

NOW = dt.datetime(2026, 11, 10, 9, 0)
WRITE_KINDS = (["issue", "edit"], ["issue", "comment"], ["issue", "create"], ["issue", "pin"], ["label", "create"])


class FakeGhRunner:
    """代替真正的 gh：讀操作回傳預設資料，寫操作記錄下來並套用到資料上。"""

    def __init__(self, issues):
        self.issues = {issue["number"]: issue for issue in issues}
        self.calls = []

    @property
    def writes(self):
        return [argv for argv, _ in self.calls if argv[1:3] in WRITE_KINDS]

    def __call__(self, argv, stdin):
        self.calls.append((argv, stdin))
        assert argv[0] == "gh" and argv[-2:] == ["-R", tq.REPO]
        kind = argv[1:3]
        if kind == ["issue", "view"]:
            return json.dumps(self.issues[int(argv[3])])
        if kind == ["issue", "list"]:
            state = argv[argv.index("--state") + 1]
            return json.dumps([i for i in self.issues.values() if state == "all" or i["state"] == "OPEN"])
        if kind == ["issue", "edit"]:
            issue = self.issues[int(argv[3])]
            names = [label["name"] for label in issue["labels"]]
            if "--remove-label" in argv:
                names.remove(argv[argv.index("--remove-label") + 1])
            if "--add-label" in argv:
                names.append(argv[argv.index("--add-label") + 1])
            issue["labels"] = [{"name": name} for name in names]
            if "--body-file" in argv:
                issue["body"] = stdin
            return ""
        if kind == ["issue", "comment"]:
            self.issues[int(argv[3])]["comments"].append({"body": stdin})
            return ""
        raise AssertionError(f"未預期的 gh 呼叫：{argv}")


def task_body(local_dir, ddl="2026-11-12", key="某大学-某课|能力训练|某人|2026-11-08", extra=""):
    return (
        f"<!-- key: {key} -->\n## 任务书\n- 学校-课程：某大学-某课\n- 业务类型：能力训练\n"
        f"- DDL：原文「…」→ 换算 {ddl}\n- 本机目录：{local_dir}\n{extra}"
    )


def make_issue(number, labels, body="", comments=(), state="OPEN", title=None):
    return {
        "number": number,
        "title": title or f"任务{number}",
        "body": body,
        "state": state,
        "labels": [{"name": name} for name in labels],
        "comments": [{"body": text} for text in comments],
    }


def make_gh(issues):
    runner = FakeGhRunner(issues)
    return tq.Gh(runner=runner, min_interval=0), runner


def label_names(runner, number):
    return [label["name"] for label in runner.issues[number]["labels"]]


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    root = tmp_path / "skills_training_course"
    local = root / "某大学-某课"
    local.mkdir(parents=True)
    monkeypatch.setattr(tq, "ALLOWED_ROOTS", {"能力训练": root})
    return local


def write_reports(local, good=(18, 17, 18, 17, 18), medium=(17, 16, 17, 16, 17)):
    paths = {}
    for profile, scores in (("good", good), ("medium", medium)):
        path = local / f"{profile}_evaluation.json"
        path.write_text(json.dumps(make_report(scores=scores)), encoding="utf-8")
        paths[profile] = path
    return paths


def test_gh_adds_repo_and_spaces_out_writes():
    slept, now = [], [100.0]
    calls = []

    def runner(argv, stdin):
        calls.append(argv)
        return ""

    gh = tq.Gh(runner=runner, min_interval=1.0, sleep=slept.append, clock=lambda: now[0])
    gh.read("issue", "list")
    gh.write("issue", "comment", "1")
    now[0] += 0.25
    gh.write("issue", "comment", "2")
    assert all(argv[-2:] == ["-R", tq.REPO] for argv in calls)
    assert slept == [0.75]


def test_list_ready_filters_and_orders_by_ddl(workspace):
    gh, _ = make_gh([
        make_issue(1, [], title=tq.BOARD_TITLE),
        make_issue(2, ["ready-for-agent", "type:能力训练"], task_body(workspace, ddl="2026-11-20")),
        make_issue(3, ["ready-for-agent", "type:能力训练", "agent:pi"], task_body(workspace, ddl="2026-11-12")),
        make_issue(4, ["ready-for-agent", "type:能力训练", "status:blocked"], task_body(workspace)),
        make_issue(5, ["needs-triage", "type:能力训练"], task_body(workspace)),
        make_issue(6, ["ready-for-agent"], task_body(workspace)),
        make_issue(7, ["ready-for-agent", "type:能力训练"], task_body(workspace), state="CLOSED"),
    ])
    ready = tq.cmd_list_ready(gh)
    assert [item["number"] for item in ready] == [3, 2]
    assert ready[0]["agent"] == "pi" and ready[1]["agent"] == "claude"
    assert ready[0]["ddl"] == "2026-11-12"
    assert ready[0]["school_course"] == "某大学-某课"


def test_claim_marks_in_progress_comments_and_starts_run_record(workspace):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "type:能力训练"], task_body(workspace))])
    result = tq.cmd_claim(gh, 7, agent="claude", pane="#7 某大学-某课", now=NOW)
    assert label_names(runner, 7) == ["ready-for-agent", "type:能力训练", "status:in-progress"]
    comment = runner.issues[7]["comments"][-1]["body"]
    assert comment.startswith("CLAIM: agent=claude")
    assert "2026-11-10T09:00" in comment
    record = json.loads((workspace / ".task-queue" / "run-7.json").read_text(encoding="utf-8"))
    assert record["issue"] == 7 and record["rounds"] == 0
    assert result["status"] == "status:in-progress"


def test_claim_refuses_issue_that_already_has_a_status(workspace):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:in-progress"], task_body(workspace))])
    with pytest.raises(tq.Refused):
        tq.cmd_claim(gh, 7, agent="claude", pane="p", now=NOW)
    assert runner.writes == []


@pytest.mark.parametrize("bad_dir", ["/etc", "{root}", "{root}/../elsewhere", ""])
def test_claim_refuses_local_dir_outside_allowed_root(workspace, bad_dir):
    local_dir = bad_dir.format(root=workspace.parent)
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "type:能力训练"], task_body(local_dir))])
    with pytest.raises(tq.Refused):
        tq.cmd_claim(gh, 7, agent="claude", pane="p", now=NOW)
    assert runner.writes == []


def test_rework_claim_increments_rounds_and_stops_after_limit(workspace):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:waiting"], task_body(workspace))])
    tq.save_record(workspace, 7, {"issue": 7, "rounds": 1})
    tq.cmd_claim(gh, 7, agent="claude", pane="p", now=NOW, event="rework")
    assert label_names(runner, 7) == ["ready-for-agent", "status:in-progress"]
    assert tq.load_record(workspace, 7)["rounds"] == 2

    runner.issues[7]["labels"] = [{"name": "ready-for-agent"}, {"name": "status:waiting"}]
    writes_before = len(runner.writes)
    with pytest.raises(tq.Refused):
        tq.cmd_claim(gh, 7, agent="claude", pane="p", now=NOW, event="rework")
    assert len(runner.writes) == writes_before


def test_retry_claim_moves_blocked_back_to_in_progress(workspace):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:blocked"], task_body(workspace))])
    tq.cmd_claim(gh, 7, agent="pi", pane="p", now=NOW, event="retry")
    assert label_names(runner, 7) == ["ready-for-agent", "status:in-progress"]
    assert tq.load_record(workspace, 7)["rounds"] == 0


def test_record_accepts_only_known_keys(workspace):
    gh, _ = make_gh([make_issue(7, ["ready-for-agent", "status:in-progress"], task_body(workspace))])
    tq.cmd_record(gh, 7, ["task_id=abc123", "course_id=c1"])
    record = tq.load_record(workspace, 7)
    assert record["task_id"] == "abc123" and record["course_id"] == "c1"
    with pytest.raises(tq.Refused):
        tq.cmd_record(gh, 7, ["rounds=0"])
    with pytest.raises(tq.Refused):
        tq.cmd_record(gh, 7, ["gate=pass"])


def test_gate_command_comments_result_and_says_what_next(workspace):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:in-progress"], task_body(workspace))])
    paths = write_reports(workspace)
    tq.cmd_record(gh, 7, [f"evaluation_good={paths['good']}", f"evaluation_medium={paths['medium']}"])
    result = tq.cmd_gate(gh, 7, now=NOW)
    assert result["pass"] is True and result["next"] == "publish"
    assert runner.issues[7]["comments"][-1]["body"].splitlines()[0] == "GATE: PASS good=88 medium=83"
    assert tq.load_record(workspace, 7)["gate"]["pass"] is True
    assert label_names(runner, 7) == ["ready-for-agent", "status:in-progress"]


def test_gate_command_fails_and_blocks_after_rework_limit(workspace):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:in-progress"], task_body(workspace))])
    paths = write_reports(workspace, good=(15, 15, 15, 15, 17))
    tq.save_record(workspace, 7, {
        "issue": 7, "rounds": 2,
        "evaluation_good": str(paths["good"]), "evaluation_medium": str(paths["medium"]),
    })
    result = tq.cmd_gate(gh, 7, now=NOW)
    assert result["pass"] is False and result["next"] == "blocked"
    body = runner.issues[7]["comments"][-1]["body"]
    assert body.splitlines()[0] == "GATE: FAIL good=77 medium=83"
    assert "低於 80" in body


def test_gate_command_fails_when_reports_were_never_recorded(workspace):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:in-progress"], task_body(workspace))])
    result = tq.cmd_gate(gh, 7, now=NOW)
    assert result["pass"] is False and result["next"] == "waiting"
    assert runner.issues[7]["comments"][-1]["body"].startswith("GATE: FAIL good=- medium=-")


def test_set_status_waiting_requires_failed_gate(workspace, tmp_path):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:in-progress"], task_body(workspace))])
    note = tmp_path / "note.md"
    note.write_text("最低维度：流程遵循度。打算收紧阶段二的跳转条件。", encoding="utf-8")
    with pytest.raises(tq.Refused):
        tq.cmd_set_status(gh, 7, "waiting", note)
    assert runner.writes == []

    tq.save_record(workspace, 7, {"issue": 7, "rounds": 0, "gate": {"pass": False}})
    tq.cmd_set_status(gh, 7, "waiting", note)
    assert label_names(runner, 7) == ["ready-for-agent", "status:waiting"]
    assert "流程遵循度" in runner.issues[7]["comments"][-1]["body"]


def test_set_status_blocked_adds_marker_and_requires_comment(workspace, tmp_path):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:in-progress"], task_body(workspace))])
    with pytest.raises(tq.Refused):
        tq.cmd_set_status(gh, 7, "blocked", None)
    note = tmp_path / "note.md"
    note.write_text("文生图连续 429\n日志：/x/log.txt", encoding="utf-8")
    tq.cmd_set_status(gh, 7, "blocked", note)
    assert label_names(runner, 7) == ["ready-for-agent", "status:blocked"]
    assert runner.issues[7]["comments"][-1]["body"].splitlines()[0] == "BLOCKED: 文生图连续 429"


def test_set_status_enforces_transition_table(workspace):
    gh, runner = make_gh([make_issue(7, ["ready-for-agent", "status:in-progress"], task_body(workspace))])
    with pytest.raises(tq.Refused):
        tq.cmd_set_status(gh, 7, "ready", None)
    assert runner.writes == []

    runner.issues[7]["labels"] = [{"name": "ready-for-agent"}, {"name": "status:waiting"}]
    tq.cmd_set_status(gh, 7, "ready", None)
    assert label_names(runner, 7) == ["ready-for-agent", "status:ready"]


def test_board_command_rewrites_board_issue_only(workspace):
    gh, runner = make_gh([
        make_issue(1, [], body="旧内容", title=tq.BOARD_TITLE),
        make_issue(2, ["ready-for-agent", "status:waiting"], task_body(workspace), ["GATE: FAIL good=77 medium=83"]),
        make_issue(3, ["needs-triage"], task_body(workspace, ddl="2026-11-09")),
    ])
    result = tq.cmd_board(gh, now=NOW)
    assert result == {"board": 1, "issues": 2}
    assert [argv[3] for argv in runner.writes] == ["1"]
    body = runner.issues[1]["body"]
    assert "FAIL good=77 medium=83" in body and "逾期 1 天" in body
    assert "2026-11-10 09:00" in body
    assert f"#1 {tq.BOARD_TITLE}" not in body


def test_find_dup_command_searches_open_and_closed(workspace):
    gh, _ = make_gh([
        make_issue(2, [], task_body(workspace, key="某大学-某课|能力训练|某人|2026-11-08"), state="CLOSED"),
        make_issue(3, [], task_body(workspace, key="另一大学-某课|能力训练|某人|2026-11-08")),
    ])
    result = tq.cmd_find_dup(gh, "某大学 - 某课|能力训练|某人|2026-11-08")
    assert result["duplicates"] == [2]


# ---------------------------------------------------------------- gh 的暫時性錯誤重試


def flaky_runner(failures, message='Post "https://api.github.com/graphql": EOF'):
    calls = []

    def runner(argv, stdin):
        calls.append(argv)
        if len(calls) <= failures:
            raise tq.GhError(message)
        return "[]"

    return runner, calls


def test_gh_read_retries_transient_errors():
    runner, calls = flaky_runner(failures=2)
    slept = []
    gh = tq.Gh(runner=runner, sleep=slept.append)
    assert gh.read_json("issue", "list") == []
    assert len(calls) == 3 and len(slept) == 2


def test_gh_gives_up_after_three_attempts():
    runner, calls = flaky_runner(failures=5)
    gh = tq.Gh(runner=runner, sleep=lambda _: None)
    with pytest.raises(tq.GhError):
        gh.read("issue", "list")
    assert len(calls) == 3


def test_gh_does_not_retry_permanent_errors():
    runner, calls = flaky_runner(failures=5, message="GraphQL: Could not resolve to an issue")
    gh = tq.Gh(runner=runner, sleep=lambda _: None)
    with pytest.raises(tq.GhError):
        gh.read("issue", "view", "99")
    assert len(calls) == 1


def test_gh_write_retries_unless_told_not_to():
    runner, calls = flaky_runner(failures=1)
    gh = tq.Gh(runner=runner, min_interval=0, sleep=lambda _: None)
    gh.write("issue", "edit", "7", "--add-label", "status:blocked")
    assert len(calls) == 2

    runner, calls = flaky_runner(failures=1)
    gh = tq.Gh(runner=runner, min_interval=0, sleep=lambda _: None)
    with pytest.raises(tq.GhError):
        gh.write("issue", "create", "--title", "看板", retry=False)
    assert len(calls) == 1
