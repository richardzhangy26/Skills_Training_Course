"""原子能力目录的只读解析、来源与机器合同回归。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from xml.sax.saxutils import escape
from zipfile import ZipFile

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_atomic_skill_catalog.py"


def api():
    assert SCRIPT.exists(), "缺少目录构建能力 build_atomic_skill_catalog.py"
    spec = importlib.util.spec_from_file_location("atomic_catalog", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_book(path, *, nid="nid-example-1", absolute=False, restricted=False):
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    def cell(ref, value):
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    headers = ["类型", "场景标签", "技能名称", "技能中文名", "功能点（英文）", "描述", "技能nid", "版本"]
    header = ''.join(cell(f'{chr(65+i)}1', value) for i, value in enumerate(headers))
    description = "仅用于查询课程资源。不支持上传、删除" if restricted else "查询课程资源与上传课程文件"
    rows = (
        f'<row r="1">{header}</row>'
        '<row r="2"><c r="A2" t="s"><v>0</v></c>'
        '<c r="B2" t="s"><v>1</v></c><c r="C2" t="s"><v>2</v></c>'
        + cell("D2", "课程资源技能") + cell("E2", "course_search")
        + cell("F2", description) + cell("G2", nid)
        + '<c r="I2"><f>1+1</f><v>2</v></c></row>'
        '<row r="3">' + cell("E3", "course_upload") + cell("F3", "上传课程文件") + '</row>'
        '<row r="4">' + cell("C4", "#82（待分配）") + cell("D4", "学生群聊查询") + '</row>'
    )
    target = "/xl/worksheets/custom.xml" if absolute else "worksheets/custom.xml"
    with ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="技能" sheetId="8" r:id="customRel"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="customRel" Target="{target}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{ns}"><si><t>业务</t></si><si><t>课程检索</t></si><si><r><t>polymas-</t></r><r><t>course-resource</t></r></si></sst>')
        z.writestr("xl/worksheets/custom.xml", f'<worksheet xmlns="{ns}"><sheetData>{rows}</sheetData><mergeCells><mergeCell ref="A2:A3"/><mergeCell ref="B2:B3"/><mergeCell ref="C2:C3"/><mergeCell ref="D2:D3"/></mergeCells></worksheet>')
    return path


@pytest.mark.parametrize("absolute", [False, True])
def test_xml_reads_relationships_shared_inline_merged_groups_without_modifying_source(tmp_path, absolute):
    source = make_book(tmp_path / "源表.xlsx", absolute=absolute)
    before = source.read_bytes()
    catalog = api().build_catalog([source])
    assert catalog["schema_version"] == 1
    assert len(catalog["entries"]) == 3
    first, second, pending = catalog["entries"]
    assert first["name"] == second["name"] == "polymas-course-resource"
    assert first["raw_fields"]["I"]["value"] == "2"
    assert first["raw_fields"]["I"]["formula"] == "1+1"
    assert "C" not in second["raw_fields"]
    assert second["merged_fields"]["C"]["source_cell"] == "C2"
    assert second["source_refs"] == [{"file": "源表.xlsx", "sheet": "技能", "row": 3}]
    assert first["nid"] == "nid-example-1"
    assert second["nid"] is None and first["version"] is None
    assert pending["skill_name"] is None
    assert "missing_nid" in pending["verification_flags"]
    assert source.read_bytes() == before
    assert catalog["sources"][0]["sha256"] == hashlib.sha256(before).hexdigest()


def test_identical_names_with_different_nids_remain_separate_and_flagged(tmp_path):
    a = make_book(tmp_path / "a.xlsx")
    b = make_book(tmp_path / "b.xlsx", nid="nid-example-2")
    catalog = api().build_catalog([a, b])
    conflicts = [x for x in catalog["conflicts"] if x["kind"] == "same_name_different_nids"]
    assert len(conflicts) == 1
    assert set(conflicts[0]["nids"]) == {"nid-example-1", "nid-example-2"}
    assert len(catalog["entries"]) == 6


def test_missing_nid_placeholder_never_becomes_identifier_and_ids_survive_reorder(tmp_path):
    a = make_book(tmp_path / "a.xlsx", nid="待补")
    b = make_book(tmp_path / "b.xlsx")
    module = api()
    forward = module.build_catalog([a, b])
    reverse = module.build_catalog([b, a])
    assert forward["entries"][0]["nid"] is None
    assert {x["id"] for x in forward["entries"]} == {x["id"] for x in reverse["entries"]}


def test_scope_conflicts_and_inferred_reuse_index_link_actual_entries(tmp_path):
    source = make_book(tmp_path / "a.xlsx", restricted=True)
    catalog = api().build_catalog([source])
    assert any(x["kind"] == "scope_conflict_needs_check" for x in catalog["conflicts"])
    entry_ids = {x["id"] for x in catalog["entries"]}
    assert catalog["reuse_index"]["retrieval"]
    assert catalog["reuse_index"]["course"]
    assert set(catalog["reuse_index"]["course"]) <= entry_ids
    assert all(x["classification"]["inferred"] for x in catalog["entries"])


def test_markdown_preserves_every_entry_id_reference_and_does_not_claim_online_verified(tmp_path):
    catalog = api().build_catalog([make_book(tmp_path / "a.xlsx")])
    rendered = api().render_markdown(catalog)
    assert all(x["id"] in rendered for x in catalog["entries"])
    assert "a.xlsx / 技能 / 第 3 行" in rendered
    assert "表格记录不等同于当前线上可用" in rendered
    assert "待核对" in rendered


@pytest.mark.parametrize("args,error", [([], "INVALID_ARGUMENTS"), (["missing.xlsx"], "SOURCE_NOT_READABLE")])
def test_cli_failure_is_one_stable_json_without_traceback(args, error):
    api()
    result = subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True)
    assert result.returncode != 0
    assert json.loads(result.stdout)["error"] == error
    assert "Traceback" not in result.stderr


def test_cli_writes_json_authority_and_derived_markdown(tmp_path):
    source = make_book(tmp_path / "a.xlsx")
    output = tmp_path / "output"
    api()
    result = subprocess.run([sys.executable, str(SCRIPT), str(source), "--output-dir", str(output)], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)["entry_count"] == 3
    catalog = json.loads((output / "atomic-skill-catalog.json").read_text())
    assert (output / "atomic-skill-catalog.md").read_text() == api().render_markdown(catalog)


def test_duplicate_source_basename_rejected_to_prevent_reference_collision(tmp_path):
    (tmp_path / "other").mkdir()
    a = make_book(tmp_path / "a.xlsx")
    b = make_book(tmp_path / "other" / "a.xlsx")
    with pytest.raises(ValueError, match="DUPLICATE_SOURCE_NAME"):
        api().build_catalog([a, b])


def test_blank_english_function_falls_back_to_chinese_function():
    module = api()
    row = {"row": 2, "raw_fields": {"G": {"value": "查询课程教学计划"}}, "merged_fields": {}}
    content = module._row_content("技能(学生测)", row, {"C": "技能名称", "F": "功能点（英文）", "G": "功能点（中文）"}, 1)
    assert content is not None
    assert content[3] == "查询课程教学计划"


@pytest.mark.parametrize("label", ["教学AIGC生成", "OBE管理", "大明白V5帮助文档", "TODO"])
def test_chinese_capability_labels_and_todo_are_not_fragmented_into_skill_names(label):
    row = {"row": 2, "raw_fields": {"C": {"value": label}}, "merged_fields": {}}
    content = api()._row_content("技能", row, {"C": "技能名称"}, 1)
    assert content[0] == label
    assert content[1] == []


def test_expert_placeholder_is_context_not_atomic_skill():
    row = {"row": 2, "raw_fields": {"D": {"value": "代替处理"}}, "merged_fields": {}}
    assert api()._row_content("专家", row, {"D": "附属技能"}, 1) is None
