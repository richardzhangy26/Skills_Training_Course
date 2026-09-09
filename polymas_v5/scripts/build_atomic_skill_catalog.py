#!/usr/bin/env python3
"""只读解析 XLSX 原始 XML，构建来源可追溯的 Polymas 能力目录。"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import posixpath
import re
import sys
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
PLACEHOLDERS = re.compile(r"待补|待分配|暂无|待确定|CAND-|^TODO$|^[-—/]$", re.I)
SKILL_TOKEN = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)*(?![A-Za-z0-9_-])")
READ_WORDS = re.compile(r"检索|搜索|查询|search|lookup|rag", re.I)
WRITE_WORDS = re.compile(r"上传|创建|编辑|删除|发布|打回|催交|导入|提交|修改|发送|安装|同步|取消")
COURSE_WORDS = re.compile(r"课程|教学|课堂|班级|作业|考试|题库|学情|学习资源|course|teaching|homework|classroom|student|teacher|questionbank", re.I)


def _column(cell):
    return re.match(r"[A-Z]+", cell).group()


def _column_number(column):
    value = 0
    for letter in column:
        value = value * 26 + ord(letter) - 64
    return value


def _read_sheets(path):
    """不加载样式、不求值公式；保留原始字符串及公式缓存。"""
    with ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(t.text or "" for t in si.findall(".//m:t", NS))
                      for si in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        relations = {r.get("Id"): r for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            relationship = relations[sheet.get(REL_ID)]
            if relationship.get("TargetMode") == "External":
                raise ValueError("EXTERNAL_WORKSHEET_UNSUPPORTED")
            target = relationship.get("Target", "")
            member = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
            if not member.startswith("xl/"):
                raise ValueError("INVALID_WORKSHEET_PATH")
            root = ET.fromstring(archive.read(member))
            rows = []
            cells = {}
            for row in root.findall("m:sheetData/m:row", NS):
                raw = {}
                for cell in row.findall("m:c", NS):
                    reference = cell.get("r")
                    value_node = cell.find("m:v", NS)
                    value = "" if value_node is None else value_node.text or ""
                    if cell.get("t") == "s":
                        value = shared[int(value)] if value else ""
                    elif cell.get("t") == "inlineStr":
                        value = "".join(t.text or "" for t in cell.findall(".//m:t", NS))
                    formula = cell.find("m:f", NS)
                    if value or formula is not None:
                        field = {"cell": reference, "value": value, "type": cell.get("t", "n")}
                        if formula is not None:
                            field["formula"] = formula.text or ""
                        raw[_column(reference)] = field
                        cells[reference] = field
                if raw:
                    rows.append({"row": int(row.get("r")), "raw_fields": raw, "merged_fields": {}})
            merges = [m.get("ref") for m in root.findall("m:mergeCells/m:mergeCell", NS)]
            # 仅传播 Excel 显式合并范围；普通空白不进行向下填充。
            for merge in merges:
                start, end = merge.split(":") if ":" in merge else (merge, merge)
                if start not in cells:
                    continue
                a, b = _column(start), _column(end)
                first, last = int(start[len(a):]), int(end[len(b):])
                for row in rows:
                    if first <= row["row"] <= last:
                        for number in range(_column_number(a), _column_number(b) + 1):
                            # 原始单元格是唯一真实值；横向大标题无需扩散为多个字段。
                            if a != b:
                                continue
                            if a not in row["raw_fields"]:
                                row["merged_fields"][a] = {"value": cells[start]["value"], "source_cell": start, "range": merge}
            yield {"sheet": sheet.get("name"), "visibility": sheet.get("state", "visible"), "rows": rows, "merged_ranges": merges}


def _values(row):
    return {key: value["value"] for key, value in {**row["merged_fields"], **row["raw_fields"]}.items()}


def _headers(rows):
    for row in rows[:3]:
        values = _values(row)
        if any(v.strip().lower() in {"技能名称", "skill名称", "技能nid", "附属技能", "技能", "名称"} for v in values.values()):
            return row["row"], values
    return rows[0]["row"], _values(rows[0]) if rows else {}


def _field(values, headers, *labels):
    labels = {label.lower() for label in labels}
    return next((values[column] for column, label in headers.items() if label.strip().lower() in labels and values.get(column, "").strip()), "")


def _row_content(sheet, row, headers, header_row):
    """显式区分能力记录与专家、问题和日志上下文，不从日志生成可挂载技能。"""
    values = _values(row)
    if row["row"] <= header_row:
        return None
    if sheet in {"专家推荐列表", "推广问题修复", "SKILL开发日报"}:
        return None
    name_value = _field(values, headers, "技能名称", "skill名称", "技能", "附属技能")
    if sheet == "应用广场数据整理":
        if values.get("A") != "技能":
            return None
        name_value = values.get("C", "")
    if sheet == "模版推荐":
        if not 26 <= row["row"] <= 46:
            return None
        name_value = "\n".join(values.get(column, "") for column in ["A", "B"])
    if sheet in {"专家", "业务-专家"} and not name_value.strip():
        return None
    if sheet == "专家" and name_value.strip() == "代替处理":
        return None
    if sheet == "SKILL开发方向划分":
        if not values.get("M", "").strip() and not re.fullmatch(r"[ABC]\d+", values.get("B", "")):
            return None
        name_value = values.get("M", "")
    if sheet == "技能一览" and row["row"] >= 30:
        if row["row"] != 31:
            return None
    description = _field(values, headers, "描述", "技能说明", "技能简介", "技能解释", "Skill描述", "技能的实现说明")
    feature = _field(values, headers, "功能点（英文）", "功能列表", "功能点（中文）", "要求")
    chinese_name = _field(values, headers, "技能中文名", "中文名", "SKILL")
    fallback = chinese_name or feature or description or values.get("B", "")
    if not name_value.strip() and not (description.strip() or feature.strip() or chinese_name.strip()):
        return None
    names = []
    for line in name_value.splitlines():
        if not PLACEHOLDERS.search(line) and SKILL_TOKEN.fullmatch(line.strip()):
            names.append(line.strip())
    names = list(dict.fromkeys(names))
    title = name_value.strip() or fallback.strip()
    return title, names, chinese_name, feature, description


def _make_entry(file, sheet, row, headers, content):
    title, names, chinese_name, feature, description = content
    values = _values(row)
    nid_value = _field(values, headers, "技能nid", "nid").strip()
    version_value = _field(values, headers, "版本", "技能版本", "version").strip()
    nid = nid_value if nid_value and not PLACEHOLDERS.search(nid_value) else None
    version = version_value if version_value and not PLACEHOLDERS.search(version_value) else None
    source = {"file": file, "sheet": sheet, "row": row["row"]}
    identifier = "entry-" + hashlib.sha256(json.dumps(source, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:20]
    text = "\n".join([title, chinese_name, feature, description, _field(values, headers, "技能详情")])
    # 分类仅用于候选检索，不能推出权限。否定写入词从写入候选判断中移除。
    positive_text = re.split(r"不支持|禁止|不允许", text)[0]
    flags = ["online_unverified"]
    if not nid:
        flags.append("missing_nid")
    if not version:
        flags.append("missing_version")
    if not names:
        flags.append("missing_exact_skill_name")
    if "待" in title or "CAND-" in title:
        flags.append("planned_or_placeholder")
    return {
        "id": identifier, "name": names[0] if len(names) == 1 else title,
        "skill_name": names[0] if len(names) == 1 else None, "skill_names": names,
        "chinese_name": chinese_name or None, "function": feature or None,
        "description": description or None, "nid": nid, "version": version,
        "source_refs": [source], "raw_fields": row["raw_fields"], "merged_fields": row["merged_fields"],
        "classification": {"inferred": True, "method": "名称和本行能力描述关键词；不代表角色权限或在线能力",
                           "retrieval": bool(READ_WORDS.search(text)), "course": bool(COURSE_WORDS.search(text)),
                           "write_candidate": bool(WRITE_WORDS.search(positive_text)),
                           "explicit_read_only_restriction": bool(re.search(r"仅用于.{0,40}(查询|搜索)|纯搜索|不支持.{0,50}(上传|编辑|删除)", text))},
        "verification_flags": flags,
    }


def build_catalog(sources):
    paths = [Path(source) for source in sources]
    if not paths:
        raise ValueError("INVALID_ARGUMENTS")
    if len({path.name for path in paths}) != len(paths):
        raise ValueError("DUPLICATE_SOURCE_NAME")
    catalog = {"schema_version": 1, "sources": [], "entries": [], "conflicts": [], "reuse_index": {"retrieval": [], "course": []}}
    for path in paths:
        source = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "sheets": []}
        for sheet in _read_sheets(path):
            rows = sheet.pop("rows")
            header_row, headers = _headers(rows) if rows else (0, {})
            summary = {**sheet, "headers": headers, "header_row": header_row, "nonempty_rows": len(rows), "entry_count": 0, "context_rows": []}
            for row in rows:
                for column, field in row["raw_fields"].items():
                    field["header"] = headers.get(column, f"未命名列 {column}")
                content = _row_content(sheet["sheet"], row, headers, header_row)
                if content:
                    catalog["entries"].append(_make_entry(path.name, sheet["sheet"], row, headers, content))
                    summary["entry_count"] += 1
                else:
                    summary["context_rows"].append(row)
            source["sheets"].append(summary)
        source["entry_count"] = sum(sheet["entry_count"] for sheet in source["sheets"])
        catalog["sources"].append(source)
    grouped = defaultdict(list)
    for entry in catalog["entries"]:
        for category in catalog["reuse_index"]:
            if entry["classification"][category]:
                catalog["reuse_index"][category].append(entry["id"])
        for name in entry["skill_names"]:
            grouped[name].append(entry)
    for name, entries in sorted(grouped.items()):
        nids = sorted({entry["nid"] for entry in entries if entry["nid"]})
        if len(nids) > 1:
            catalog["conflicts"].append({"kind": "same_name_different_nids", "name": name, "nids": nids, "entry_ids": [entry["id"] for entry in entries], "status": "待核对"})
        restricted = [entry["id"] for entry in entries if entry["classification"]["explicit_read_only_restriction"]]
        writers = [entry["id"] for entry in entries if entry["classification"]["write_candidate"] and not entry["classification"]["explicit_read_only_restriction"]]
        if restricted and writers:
            catalog["conflicts"].append({"kind": "scope_conflict_needs_check", "name": name, "entry_ids": list(dict.fromkeys(restricted + writers)), "status": "待核对", "note": "同名记录同时出现只读约束与写入能力描述；可能为版本、功能点或角色差异，须核对平台。"})
    catalog["counts"] = {"entries": len(catalog["entries"]), "distinct_skill_names": len(grouped), "sheets": sum(len(s["sheets"]) for s in catalog["sources"]), "conflicts": len(catalog["conflicts"])}
    return catalog


def _md(value):
    return str(value if value is not None else "待核对").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>")


def _reference(entry):
    ref = entry["source_refs"][0]
    return f'{ref["file"]} / {ref["sheet"]} / 第 {ref["row"]} 行'


def _raw_table(row):
    lines = ["| 单元格 | 原始表头 | 原始值 |", "| --- | --- | --- |"]
    for column, field in row["raw_fields"].items():
        value = _md(field["value"])
        if "formula" in field:
            value += "；原公式：" + _md(field["formula"])
        lines.append(f'| {field["cell"]} | {_md(field.get("header", column))} | {value} |')
    for column, field in row["merged_fields"].items():
        lines.append(f'| {column}（合并继承自 {field["source_cell"]}；{field["range"]}） | 原值见锚点 | {_md(field["value"])} |')
    return lines


def render_markdown(catalog):
    lines = ["# Polymas 原子 Skill 复用目录", "", "本目录由 atomic-skill-catalog.json 渲染；JSON 是权威数据。表格记录不等同于当前线上可用。", "",
             "先查目录中的检索类、课程读写类及既有功能点，再核对 PDS/SkillHub 的精确名称、NID、版本与角色权限。已有技能临时失败不能作为新建同职责技能的理由。", "",
             "一条记录对应一条来源表格行；功能点并不等于独立可挂载 Skill。同一行可能列出多个 Skill。空白 NID/版本保持 null，候选占位名不当作真实技能；跨行仅承接 Excel 显式合并单元格。原始日期序号、状态和错别字保持原样。", "",
             "关键词分类与职责差异是选型提示，属于推断；并不授予读写权限。线上状态、提测状态与测试结论均为原表历史快照。专家配置、问题、日志等非能力行保留在来源上下文，不计入能力条目。", "",
             "## 来源覆盖", "", "| 文件 | 工作表 | 能力记录 | 上下文记录 | 非空行 |", "| --- | --- | ---: | ---: | ---: |"]
    for source in catalog["sources"]:
        for sheet in source["sheets"]:
            lines.append(f'| {_md(source["file"])} | {_md(sheet["sheet"])} | {sheet["entry_count"]} | {len(sheet["context_rows"])} | {sheet["nonempty_rows"]} |')
    lines += ["", f'共 {catalog["counts"]["entries"]} 条来源能力记录，{catalog["counts"]["distinct_skill_names"]} 个按原文提取的不同技能名称。名称数包含历史独立功能名与推荐模板候选，不等于线上 Skill 数量。', ""]
    for category, title in [("retrieval", "检索类优先复用索引"), ("course", "课程读写类优先复用索引")]:
        lines += [f"## {title}", "", "按名称合并展示；引用指向原始记录，挂载前仍需核对各功能点、来源差异和权限。", "", "| 名称 | 代表功能 / 描述 | 写入候选（推断） | 来源条目 |", "| --- | --- | --- | --- |"]
        groups = defaultdict(list)
        for entry in catalog["entries"]:
            if entry["id"] in catalog["reuse_index"][category]:
                for name in entry["skill_names"]:
                    groups[name].append(entry)
        for name, entries in sorted(groups.items()):
            representative = next((entry for entry in entries if entry["description"] or entry["function"]), entries[0])
            excerpt = representative["function"] or representative["description"] or representative["chinese_name"] or "见原表"
            refs = "、".join(f'[{entry["id"]}](#{entry["id"]})' for entry in entries[:3])
            if len(entries) > 3:
                refs += f'（共 {len(entries)} 条，完整记录见下文）'
            lines.append(f'| {_md(name)} | {_md(excerpt[:180])} | {"有" if any(e["classification"]["write_candidate"] for e in entries) else "未从文本识别"} | {refs} |')
    lines += ["", "## 待核对的名称与职责差异", ""]
    if not catalog["conflicts"]:
        lines.append("未在本次表格快照中识别同名不同 NID 或只读/写入差异；这不证明线上名称或职责一致。")
    for conflict in catalog["conflicts"]:
        lines += [f'- **{_md(conflict["name"])}**：{conflict["kind"]}；待核对。' + _md(conflict.get("note", "NID：" + "、".join(conflict.get("nids", [])))), "  " + "、".join(f'[{i}](#{i})' for i in conflict["entry_ids"])]
    lines += ["", "## 全部能力来源记录", ""]
    for entry in catalog["entries"]:
        lines += [f'<a id="{entry["id"]}"></a>', f'### {entry["id"]} · {_md(entry["name"])}', "", _reference(entry), "", f'NID：{_md(entry["nid"])}；版本：{_md(entry["version"])}；线上：未核对。', "", *_raw_table(entry), ""]
    lines += ["## 非能力行来源上下文", "", "保留表头、专家说明、问题、开发日志和无法确认的记录，以供追溯；不能据此直接挂载 Skill。", ""]
    for source in catalog["sources"]:
        for sheet in source["sheets"]:
            lines += [f'### {_md(source["file"])} / {_md(sheet["sheet"])}', ""]
            for row in sheet["context_rows"]:
                lines += [f'第 {row["row"]} 行', "", *_raw_table(row), ""]
    return "\n".join(lines).rstrip() + "\n"


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("INVALID_ARGUMENTS")


def main(argv=None):
    try:
        parser = _Parser(description=__doc__)
        parser.add_argument("sources", nargs="+")
        parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "docs")
        args = parser.parse_args(argv)
        catalog = build_catalog(args.sources)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = args.output_dir / "atomic-skill-catalog.json"
        markdown_path = args.output_dir / "atomic-skill-catalog.md"
        json_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        markdown_path.write_text(render_markdown(json.loads(json_path.read_text(encoding="utf-8"))), encoding="utf-8")
        print(json.dumps({"entry_count": len(catalog["entries"]), "source_count": len(catalog["sources"]), "outputs": [json_path.name, markdown_path.name]}, ensure_ascii=False))
        return 0
    except (FileNotFoundError, PermissionError):
        error = "SOURCE_NOT_READABLE"
    except (BadZipFile, ET.ParseError, KeyError, IndexError):
        error = "INVALID_XLSX"
    except ValueError as exc:
        error = str(exc) if re.fullmatch(r"[A-Z_]+", str(exc)) else "INVALID_XLSX"
    except OSError:
        error = "FILE_OPERATION_FAILED"
    print(json.dumps({"error": error}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    sys.exit(main())
