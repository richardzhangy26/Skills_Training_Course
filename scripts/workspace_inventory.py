#!/usr/bin/env python3
"""重新生成 docs/agents/workspace-map.md 中的清单段落：扫描各项目的 AGENTS.md / skills / agents。

用法:
    python3 scripts/workspace_inventory.py           # 写回 workspace-map.md 的标记段
    python3 scripts/workspace_inventory.py --print   # 只打印，不写文件
"""
import argparse
import datetime
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_FILE = ROOT / "docs" / "agents" / "workspace-map.md"
BEGIN, END = "<!-- BEGIN GENERATED -->", "<!-- END GENERATED -->"

# (显示名, 相对根目录路径, 是否深度扫描散落的 SKILL.md / 子 AGENTS.md)
PROJECTS = [
    ("能力训练（根）", ".", False),
    ("skills_training_course", "skills_training_course", True),
    ("HTML", "HTML", True),
    ("polymas_v5", "polymas_v5", True),
    ("homework_review", "homework_review", False),
    ("agent_microcourse", "agent_microcourse", False),
]
SKILL_DIRS = [".claude/skills", ".agents/skills", ".qoder/skills", ".codex/skills"]
AGENT_DIRS = [".claude/agents", ".agents/agents", ".codex/agents"]
PRUNE = {"node_modules", "__pycache__", "output", "outputs", "log", "logs", "tmp", "dist"}
MAX_DEPTH = 4      # 深度扫描的目录层数
COMPACT_OVER = 30  # 超过该数量的 skills 只列名称


def mark(p):
    """R=实体目录 L=有效软链接 X=失效软链接 ·=不存在"""
    if p.is_symlink():
        return "L" if p.exists() else "X"
    return "R" if p.is_dir() else "·"


def skills_of(proj):
    names = {}
    for sd in SKILL_DIRS:
        d = proj / sd
        if not d.is_dir():
            continue
        for e in sorted(d.iterdir()):
            if e.name.startswith((".", "__")):
                continue
            if e.is_symlink():
                if e.exists() and not e.is_dir():
                    continue  # 指向文件的链接（如 AGENTS.md）
            elif not e.is_dir():
                continue  # zip / png 等
            names.setdefault(e.name, {})[sd] = mark(e)
    return names


def describe(proj, name):
    for sd in SKILL_DIRS:
        f = proj / sd / name / "SKILL.md"
        if f.is_file():
            for line in f.read_text(encoding="utf-8", errors="ignore").splitlines()[:20]:
                m = re.match(r"\s*description:\s*(.*)", line)
                if m:
                    t = m.group(1).strip().strip("\"'").replace("|", "/")
                    if t in ("", ">", "|", ">-", "|-"):
                        return ""
                    return t[:40] + "…" if len(t) > 40 else t
            return ""
    return "（无 SKILL.md）"


def agents_of(proj):
    found = []
    for ad in AGENT_DIRS:
        d = proj / ad
        if d.is_dir():
            found += [f"{ad}/{e.name}" for e in sorted(d.iterdir())
                      if e.suffix in (".md", ".toml") and e.name.lower() != "readme.md"]
    return found


def scattered(proj):
    skills, docs = [], []
    for dirpath, dirnames, filenames in os.walk(proj):
        rel = Path(dirpath).relative_to(proj)
        dirnames[:] = sorted(d for d in dirnames if d not in PRUNE and not d.startswith("."))
        if len(rel.parts) >= MAX_DEPTH:
            dirnames[:] = []
        if "SKILL.md" in filenames:
            skills.append(str(rel))
        if "AGENTS.md" in filenames and rel.parts:
            docs.append(str(rel / "AGENTS.md"))
    return skills, docs


def git_info(proj):
    if not (proj / ".git").exists():
        return "无独立 repo"
    r = subprocess.run(["git", "-C", str(proj), "config", "--get", "remote.origin.url"],
                       capture_output=True, text=True, timeout=10)
    url = re.sub(r"//[^/@]+@", "//", r.stdout.strip())  # 去掉可能内嵌的凭证
    return url or "独立 repo（无 origin）"


def doc_info(proj):
    a, c = proj / "AGENTS.md", proj / "CLAUDE.md"
    a_s = f"{sum(1 for _ in a.open(encoding='utf-8', errors='ignore'))} 行" if a.is_file() else "无"
    if c.is_symlink():
        c_s = "→ " + os.readlink(c)
    else:
        c_s = "独立文件" if c.is_file() else "无"
    return a_s, c_s


def render():
    rows, parts = [], []
    for label, rel, deep in PROJECTS:
        proj = ROOT / rel
        if not proj.is_dir():
            rows.append(f"| {label} | （目录不存在） | | | | | |")
            continue
        git, (a_s, c_s) = git_info(proj), doc_info(proj)
        names, agents = skills_of(proj), agents_of(proj)
        sk, docs = scattered(proj) if deep else ([], [])
        rows.append(f"| {label} | {git} | {a_s} | {c_s} | {len(names)} | {len(agents)} | {len(sk)} |")

        p = [f"### {label}（`{rel}/`）", f"- Git：{git}", f"- AGENTS.md：{a_s}；CLAUDE.md：{c_s}"]
        dirs = [sd for sd in SKILL_DIRS if (proj / sd).is_dir()]
        if names and len(names) <= COMPACT_OVER:
            p += ["", "| skill | " + " | ".join(dirs) + " | 说明 |", "|---|" + "---|" * (len(dirs) + 1)]
            for n in sorted(names):
                p.append(f"| `{n}` | " + " | ".join(names[n].get(sd, "·") for sd in dirs)
                         + f" | {describe(proj, n)} |")
        elif names:
            stat = "；".join(f"`{sd}` {sum(1 for v in names.values() if sd in v)} 个" for sd in dirs)
            p += ["", f"- Skills 共 {len(names)} 个（{stat}）",
                  "<details><summary>名称列表</summary>", "", ", ".join(f"`{n}`" for n in sorted(names)),
                  "", "</details>"]
        warn = [n for n, v in names.items() if list(v.values()).count("R") > 1 or "X" in v.values()]
        if warn:
            p += ["", "- ⚠ 多处实体或失效链接：" + ", ".join(f"`{n}`" for n in sorted(warn))]
        if agents:
            p += ["", "- Agents：" + ", ".join(f"`{a}`" for a in agents)]
        if sk:
            p += ["", f"- 散落的 SKILL.md（{len(sk)}）：" + ", ".join(f"`{s}`" for s in sk[:40])]
        if docs:
            p += ["", f"- 子目录 AGENTS.md（{len(docs)}）：" + ", ".join(f"`{d}`" for d in docs[:40])]
        parts.append("\n".join(p))

    head = [f"_生成于 {datetime.date.today().isoformat()}，由 `scripts/workspace_inventory.py` 写入，勿手改。_", "",
            "| 目录 | Git | AGENTS.md | CLAUDE.md | skills | agents | 散落 SKILL.md |",
            "|---|---|---|---|---|---|---|", *rows, "",
            "Skill 表图例：R=实体目录 L=有效软链接 X=失效软链接 ·=不存在。", ""]
    return "\n".join(head) + "\n" + "\n\n".join(parts) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--print", action="store_true", dest="dry", help="只打印，不写文件")
    args = ap.parse_args()
    body = render()
    if args.dry:
        print(body)
        return
    text = MAP_FILE.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit(f"{MAP_FILE} 缺少 {BEGIN} / {END} 标记")
    pre, rest = text.split(BEGIN, 1)
    post = rest.split(END, 1)[1]
    MAP_FILE.write_text(f"{pre}{BEGIN}\n{body}{END}{post}", encoding="utf-8")
    print(f"已更新 {MAP_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
