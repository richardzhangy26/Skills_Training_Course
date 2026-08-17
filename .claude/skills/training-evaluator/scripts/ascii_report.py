"""ASCII 评分汇总表渲染器"""
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

DIM_ORDER = ["目标达成度", "流程遵循度", "交互体验性", "幻觉与边界", "教学策略"]
DIM_SHORT = {"目标达成度":"目标", "流程遵循度":"流程", "交互体验性":"交互", "幻觉与边界":"幻觉", "教学策略":"教学"}


def _row_key(path: Path) -> Tuple[str, str, int]:
    """从路径推出 (task, label, run_idx)"""
    try:
        parts = path.parts
        idx_log = next(i for i, p in enumerate(parts) if p.lower() == "log")
        task = parts[idx_log + 2] if len(parts) > idx_log + 2 else path.parent.name
        # label = 任务下所有中间目录的 /joined
        label_parts = parts[idx_log + 3 : -1]
        label = "/".join(label_parts) if label_parts else path.parent.name
    except StopIteration:
        task = path.parent.name
        label = path.parent.name

    stem = path.stem
    run_idx = 1
    if "_run" in stem:
        try:
            run_idx = int(stem.rsplit("_run", 1)[1].split("_")[0])
        except (ValueError, IndexError):
            pass
    return task, label, run_idx


def render(report_paths: List[str]) -> str:
    """读取多份 *_evaluation.json 并渲染 ASCII 汇总表"""
    rows = []
    for p in report_paths:
        path = Path(p)
        if not path.exists():
            continue
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            rows.append((path, None, f"读取失败: {e}"))
            continue
        task, label, run_idx = _row_key(path)
        rows.append((path, d, (task, label, run_idx)))

    if not rows:
        return "(无可渲染的评测报告)"

    # 表头
    lines = []
    sep = "=" * 116
    lines.append(sep)
    header = f"{'任务':22s}{'档位/run':16s}{'总分':>7s}  {'等级':>10s}  "
    header += "  ".join(f"{DIM_SHORT[k]:>7s}" for k in DIM_ORDER)
    lines.append(header)
    lines.append(sep)

    prev_task = None
    # 按 (task, label, run_idx) 排序
    rows_sorted = [r for r in rows if r[1] is not None]
    rows_sorted.sort(key=lambda r: (r[2][0], r[2][1], r[2][2]))

    for path, d, key in rows_sorted:
        task, label, run_idx = key
        if prev_task and prev_task != task:
            lines.append("-" * 116)
        dims = {x["dimension"]: x for x in d.get("dimensions", [])}
        label_col = f"{label}  r{run_idx}" if run_idx > 1 else label
        row = f"{task[:20]:22s}{label_col[:14]:16s}{d.get('total_score', 0):7.1f}  {d.get('final_level',''):>10s}  "
        for k in DIM_ORDER:
            dim = dims.get(k)
            if not dim:
                row += f"{'-':>7s}  "
                continue
            veto_mark = "⚠" if dim.get("is_veto") else " "
            row += f"{dim['score']:4.0f}/{dim['full_score']}{veto_mark}  "
        lines.append(row)
        prev_task = task

    lines.append(sep)

    # 多次运行时: 每个对话的均值+极差
    grouped: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for _, d, key in rows_sorted:
        if d:
            grouped[(key[0], key[1])].append(d.get("total_score", 0))
    multi = {k: v for k, v in grouped.items() if len(v) > 1}
    if multi:
        lines.append("\n### 多次评测稳定性（N≥2）")
        lines.append(f"{'任务':22s}{'档位':16s}{'N':>3s}{'均值':>8s}{'最低':>8s}{'最高':>8s}{'极差':>8s}")
        for (task, label), vals in multi.items():
            mn, mx = min(vals), max(vals)
            avg = sum(vals) / len(vals)
            lines.append(f"{task[:20]:22s}{label[:14]:16s}{len(vals):>3d}{avg:>8.1f}{mn:>8.1f}{mx:>8.1f}{mx-mn:>8.1f}")

    # 一票否决 / 失败块
    vetoes = [(p, d, k) for p, d, k in rows_sorted if d and d.get("veto_reasons")]
    fails = []
    for p, d, k in rows_sorted:
        if not d:
            continue
        for dim in d.get("dimensions", []):
            for sub in dim.get("sub_scores", []):
                if sub.get("rating") in ("解析失败", "评估失败"):
                    fails.append((k, dim["dimension"], sub.get("sub_dimension", "?"), sub.get("judgment_basis", "")[:80]))

    if vetoes:
        lines.append("\n### ⚠ 一票否决")
        for p, d, k in vetoes:
            task, label, run_idx = k
            run_tag = f" r{run_idx}" if run_idx > 1 else ""
            lines.append(f"  ▸ {task} / {label}{run_tag}: " + "; ".join(d["veto_reasons"]))

    if fails:
        lines.append("\n### 🐛 子维度解析/评估失败")
        for k, dim, sub, basis in fails:
            task, label, run_idx = k
            run_tag = f" r{run_idx}" if run_idx > 1 else ""
            lines.append(f"  ▸ {task}/{label}{run_tag} → {dim}/{sub}: {basis}")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ASCII 评分汇总表渲染器")
    parser.add_argument("paths", nargs="+", help="一个或多个 *_evaluation.json 路径，或包含它们的目录")
    args = parser.parse_args()

    all_paths = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            all_paths.extend(sorted(path.rglob("*_evaluation*.json")))
        elif path.is_file():
            all_paths.append(path)

    if not all_paths:
        print("(未找到任何 *_evaluation*.json)", file=sys.stderr)
        sys.exit(1)

    print(render([str(p) for p in all_paths]))


if __name__ == "__main__":
    main()
