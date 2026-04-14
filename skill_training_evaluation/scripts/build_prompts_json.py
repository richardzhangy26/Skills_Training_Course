"""
One-shot converter: prompts.ts -> skill_training_evaluation/prompts.json

Reads the TypeScript template-literal prompts defined in the top-level
`prompts.ts` and emits a JSON file keyed as {dimension: {sub_dimension: template}}
that matches the shape expected by `skill_training_evaluation/evaluator.py`.

Usage:
    python skill_training_evaluation/scripts/build_prompts_json.py
    python skill_training_evaluation/scripts/build_prompts_json.py \
        --source prompts.ts --output skill_training_evaluation/prompts.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Expected rubric shape (see prompts.ts STANDARD_SCORES and
# skill_training_evaluation/config.py DEFAULT_SUB_SCORES).
EXPECTED_DIMENSIONS = {
    "目标达成度": ["知识点覆盖率", "能力覆盖率"],
    "流程遵循度": ["环节准入条件", "环节内部顺序", "全局环节流转", "环节准出检查", "非线性跳转处理"],
    "交互体验性": ["人设语言风格", "表达自然度", "上下文衔接", "循环僵局", "回复长度控制"],
    "幻觉与边界": ["事实正确性", "逻辑自洽性", "未知承认", "安全围栏", "干扰抵抗"],
    "教学策略": ["启发式提问频率", "正向激励机制", "纠错引导路径", "深度追问技巧"],
}


def unescape_ts_template(src: str) -> str:
    """
    Reverse the TypeScript template-literal escapes so the string matches what
    the TS runtime would emit.

    The prompts.ts templates escape three things:
      \\\\  -> \\      (literal backslash)
      \\`   -> `      (literal backtick)
      \\$   -> $      (prevent interpolation)

    We process `\\\\` first via a sentinel so that a subsequent `\\`` or `\\$`
    does not match a backslash that was part of an already-unescaped pair.
    """
    sentinel = "\x00"
    out = src.replace("\\\\", sentinel)
    out = out.replace("\\`", "`")
    out = out.replace("\\$", "$")
    out = out.replace(sentinel, "\\")
    return out


def parse_prompts_ts(source: str) -> dict:
    """
    Walk prompts.ts line-by-line, collecting template literals between
    the markers `"sub_name": \`` ... `\`,` (or closing `` ` ``).
    """
    # Anchor on the declaration so we skip the `buildSubDimensionPrompt` header.
    anchor = re.search(
        r"const prompts: Record<string, Record<string, string>> = \{",
        source,
    )
    if anchor is None:
        raise SystemExit(
            "Could not locate `const prompts: Record<string, ...>` in prompts.ts"
        )

    body = source[anchor.end():]
    lines = body.split("\n")

    dim_open_re = re.compile(r'^    "([^"]+)":\s*\{\s*$')
    sub_open_re = re.compile(r'^      "([^"]+)":\s*`\s*$')
    sub_close_re = re.compile(r"^`,?\s*$")
    outer_close_re = re.compile(r"^\s*\};\s*$")

    result: dict[str, dict[str, str]] = {}
    current_dim: str | None = None
    current_sub: str | None = None
    template_buf: list[str] = []
    in_template = False

    for line in lines:
        if in_template:
            if sub_close_re.match(line):
                assert current_dim is not None and current_sub is not None
                raw_tpl = "\n".join(template_buf)
                result[current_dim][current_sub] = unescape_ts_template(raw_tpl)
                template_buf = []
                current_sub = None
                in_template = False
            else:
                template_buf.append(line)
            continue

        dim_match = dim_open_re.match(line)
        if dim_match and current_dim is None:
            current_dim = dim_match.group(1)
            result.setdefault(current_dim, {})
            continue
        if dim_match and current_dim is not None:
            # Already inside a dim block; treat as dim switch after close.
            current_dim = dim_match.group(1)
            result.setdefault(current_dim, {})
            continue

        sub_match = sub_open_re.match(line)
        if sub_match:
            if current_dim is None:
                raise SystemExit(
                    f"Found sub-dim `{sub_match.group(1)}` before any dim header"
                )
            current_sub = sub_match.group(1)
            template_buf = []
            in_template = True
            continue

        # Close of a dim block: `    },` or `    }`. Only reset when we're not in a template.
        if re.match(r"^    \},?\s*$", line):
            current_dim = None
            continue

        if outer_close_re.match(line):
            break

    return result


def validate(result: dict) -> None:
    errors: list[str] = []
    if list(result.keys()) != list(EXPECTED_DIMENSIONS.keys()):
        errors.append(
            f"Dimension keys mismatch.\n  got:      {list(result.keys())}\n"
            f"  expected: {list(EXPECTED_DIMENSIONS.keys())}"
        )
    for dim, expected_subs in EXPECTED_DIMENSIONS.items():
        got_subs = list(result.get(dim, {}).keys())
        if got_subs != expected_subs:
            errors.append(
                f"Sub-dim mismatch for 『{dim}』:\n  got:      {got_subs}\n"
                f"  expected: {expected_subs}"
            )
        for sub in expected_subs:
            tpl = result.get(dim, {}).get(sub, "")
            if "${teacherDoc}" not in tpl:
                errors.append(f"Template 『{dim}/{sub}』 missing ${{teacherDoc}} placeholder")
            if "${dialogueText}" not in tpl:
                errors.append(f"Template 『{dim}/{sub}』 missing ${{dialogueText}} placeholder")
    if errors:
        msg = "\n\n".join(errors)
        raise SystemExit(f"❌ Validation failed:\n{msg}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=str(repo_root / "prompts.ts"),
        help="Path to prompts.ts (default: <repo>/prompts.ts)",
    )
    parser.add_argument(
        "--output",
        default=str(repo_root / "skill_training_evaluation" / "prompts.json"),
        help="Path to prompts.json (default: <repo>/skill_training_evaluation/prompts.json)",
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)

    if not source_path.exists():
        print(f"❌ Source not found: {source_path}", file=sys.stderr)
        return 1

    source = source_path.read_text(encoding="utf-8")
    result = parse_prompts_ts(source)
    validate(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total_subs = sum(len(v) for v in result.values())
    print(
        f"✅ Wrote {total_subs} sub-dimensions across {len(result)} dimensions → {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
