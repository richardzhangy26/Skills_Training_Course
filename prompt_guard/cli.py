# -*- coding: utf-8 -*-
"""prompt_guard 命令行入口。

python3 -m prompt_guard.cli scan    -f 剧本.md
python3 -m prompt_guard.cli rewrite -f 剧本.md -m terms,abbr,abstract,framing -o out/
python3 -m prompt_guard.cli split   -f 剧本.md -o out/
python3 -m prompt_guard.cli variants -f 剧本.md -o out/
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import shield as SH


def _read(args) -> str:
    if args.text:
        return args.text
    with open(args.file, "r", encoding="utf-8") as f:
        return f.read()


def _write(args, name: str, content: str) -> str:
    outdir = args.out or "."
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def cmd_scan(args) -> int:
    text = _read(args)
    r = SH.scan(text)
    if args.json:
        print(SH.to_json(r))
        return 0
    band_cn = {"safe": "安全", "mid": "中风险（语义层可能拦）", "high": "高风险（基本必拦）"}[r["band"]]
    print("风险分: %d   档位: %s" % (r["score"], band_cn))
    if not r["hits"] and not r["intent_hits"]:
        print("未命中本地词表。若平台仍拒收 → 问题在语义层或运行时层，见 README「三层定位」。")
        return 0
    print("\n%-14s %-10s %-4s %s" % ("命中词", "分类", "风险", "建议替代"))
    print("-" * 56)
    for h in r["hits"]:
        print("%-14s %-10s %-4d %s" % (h["term"], h["category_label"], h["risk"], h["replacement"] or "（无等价词→编号外置）"))
    if r["intent_hits"]:
        print("\n高危意图短语（语义审核重点）:")
        for i in r["intent_hits"]:
            print("  - %s  @%d" % (i["pattern"], i["start"]))
    return 0


def cmd_rewrite(args) -> int:
    text = _read(args)
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    new, log = SH.rewrite(text, modes)
    after = SH.scan(new)
    if args.json:
        print(SH.to_json({"modes": modes, "before": SH.scan(text)["score"],
                          "after": after["score"], "changes": log, "output": new}))
        return 0
    print("改写模式: %s" % ",".join(modes))
    print("风险分: %d → %d" % (SH.scan(text)["score"], after["score"]))
    print("变更条数: %d" % len(log))
    for c in log[:40]:
        print("  [%s] %s → %s ×%s" % (c["kind"], c["from"] or "-", c["to"], c["count"]))
    if len(log) > 40:
        print("  ... 共 %d 条" % len(log))
    if after["high_risk_terms"]:
        print("\n仍残留高风险词（需编号外置或人工改）: %s" % "、".join(after["high_risk_terms"]))
    if args.out:
        p = _write(args, "rewritten.md", new)
        print("\n已写出: %s" % p)
    else:
        print("\n--- 改写结果 ---\n" + new)
    return 0


def cmd_split(args) -> int:
    text = _read(args)
    skeleton, payload = SH.split_payload(text)
    lines = ["# 外置载荷清单（不进平台提示词字段）", "",
             "| 编号 | 原表述 | 分类 | 载体位置 |", "|---|---|---|---|"]
    for p in payload:
        lines.append("| %s | %s | %s | %s |" % (p["id"], p["term"], p["category"], p["slot"]))
    payload_md = "\n".join(lines) + "\n"
    hint = ("\n\n---\n## 运行时注入约定\n"
            "骨架中的 `{{Txx}}` 由以下任一渠道在实际对话时补齐：\n"
            "1. 知识库文档检索片段（推荐，审核只扫提示词字段）\n"
            "2. 首轮 user 输入（教师端/测试脚本下发）\n"
            "3. 资源附件 OCR/摘要\n"
            "未注入时提示词本身仍可读通，不阻断导入。\n")
    if args.out:
        p1 = _write(args, "skeleton.md", skeleton)
        p2 = _write(args, "payload.md", payload_md + hint)
        print("骨架: %s\n载荷: %s\n抽出条目: %d" % (p1, p2, len(payload)))
    else:
        print(skeleton)
        print("\n" + payload_md)
    return 0


def cmd_variants(args) -> int:
    text = _read(args)
    vs = SH.variants(text)
    print("原始风险分: %d\n" % SH.scan(text)["score"])
    for name, t in vs.items():
        print("%-14s 风险分 %d" % (name, SH.scan(t)["score"]))
        if args.out:
            _write(args, name + ".md", t)
    if args.out:
        print("\n已写出到 %s/" % args.out)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="prompt_guard", description="提示词审核对抗：扫描/改写/骨架拆分")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("-f", "--file", help="输入文件")
        g.add_argument("-t", "--text", help="直接输文本")
        p.add_argument("-o", "--out", help="输出目录")
        p.add_argument("--json", action="store_true")

    p = sub.add_parser("scan"); common(p); p.set_defaults(fn=cmd_scan)
    p = sub.add_parser("rewrite"); common(p)
    p.add_argument("-m", "--modes", default="terms,abbr,verbs,intent,abstract,framing",
                   help="terms/abbr/verbs/abstract/framing/cfw，逗号分隔")
    p.set_defaults(fn=cmd_rewrite)
    p = sub.add_parser("split"); common(p); p.set_defaults(fn=cmd_split)
    p = sub.add_parser("variants"); common(p); p.set_defaults(fn=cmd_variants)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
