#!/usr/bin/env python3
"""
将指定文件夹下所有子文件夹中的 docx 文件转换为 markdown 并合并
使用 python-docx 库，不依赖 pandoc
"""

from pathlib import Path
from typing import List
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.table import Table


def table_to_markdown(table):
    """将 docx 表格转换为 markdown 表格"""
    rows = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            text = cell.text.replace("\n", " ").strip()
            cells.append(text)
        rows.append(cells)

    if not rows:
        return ""

    header = "| " + " | ".join(rows[0]) + " |"
    sep = "| " + " | ".join(["---"] * len(rows[0])) + " |"
    body_lines = []
    for r in rows[1:]:
        body_lines.append("| " + " | ".join(r) + " |")

    return "\n".join([header, sep] + body_lines)


def docx_to_markdown_content(docx_path: Path) -> str:
    """
    将 docx 文件转换为 Markdown 字符串（不提取图片）

    Args:
        docx_path: docx 文件路径

    Returns:
        Markdown 字符串
    """
    if not docx_path.exists():
        raise FileNotFoundError(f"文件不存在: {docx_path}")

    document = Document(docx_path)
    lines = []

    body = document._element.body
    for child in body.iterchildren():
        tag = child.tag

        if tag == qn("w:p"):
            paragraph = Paragraph(child, document)
            text = paragraph.text.strip()

            # 判断该段落是否包含图片
            has_drawing = any(elem.tag == qn("w:drawing") for elem in child.iter())

            if has_drawing and not text:
                lines.append("[图片]")
                continue

            if not text:
                lines.append("")
                continue

            style_name = ((paragraph.style.name or "") if paragraph.style else "").lower()

            if "heading 1" in style_name:
                lines.append(f"# {text}")
            elif "heading 2" in style_name:
                lines.append(f"## {text}")
            elif "heading 3" in style_name:
                lines.append(f"### {text}")
            else:
                lines.append(text)

        elif tag == qn("w:tbl"):
            tbl = Table(child, document)
            md_table = table_to_markdown(tbl)
            if md_table:
                lines.append(md_table)
                lines.append("")

    return "\n".join(lines)


def merge_folder_docx_to_markdown(base_dir: str, skip_folders: List[str] = []):
    """
    将每个子文件夹下的 docx 文件分别合并为独立的 markdown 文件

    Args:
        base_dir: 基础文件夹路径
        skip_folders: 需要跳过的文件夹列表
    """
    if skip_folders is None:
        skip_folders = []

    base_path = Path(base_dir)
    print(f"正在扫描文件夹: {base_dir}\n")

    # 遍历每个子文件夹
    processed_count = 0
    for subfolder in sorted(base_path.iterdir()):
        if not subfolder.is_dir() or subfolder.name.startswith('.'):
            continue

        folder_name = subfolder.name

        # 跳过指定的文件夹
        if folder_name in skip_folders:
            print(f"⏭️  跳过文件夹: {folder_name}\n")
            continue

        # 查找该文件夹下的所有 docx 文件
        docx_files = []
        for docx_file in sorted(subfolder.glob('*.docx')):
            if not docx_file.name.startswith('~'):  # 忽略临时文件
                docx_files.append(docx_file)

        if not docx_files:
            print(f"⚠️  {folder_name}: 未找到 docx 文件\n")
            continue

        # 输出文件名：子文件夹名.md
        output_file = base_path / f"{folder_name}.md"
        print(f"📁 正在处理: {folder_name} (共 {len(docx_files)} 个文件)")

        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write(f"# {folder_name}\n\n")
            f.write(f"本文档由 {len(docx_files)} 个案例文档合并而成\n\n")
            f.write("---\n\n")

            # 转换每个 docx 文件
            for idx, docx_path in enumerate(docx_files, 1):
                file_name = docx_path.name
                print(f"  [{idx}/{len(docx_files)}] {file_name}")

                # 添加二级标题（文件名）
                f.write(f"## {file_name.replace('.docx', '')}\n\n")

                # 转换并写入内容
                try:
                    markdown_content = docx_to_markdown_content(docx_path)
                    f.write(markdown_content)
                except Exception as e:
                    print(f"    ⚠️  转换失败: {e}")
                    f.write(f"\n\n**[转换失败: {e}]**\n\n")

                # 添加分隔符（最后一个文件不需要）
                if idx < len(docx_files):
                    f.write("\n\n---\n\n")

        print(f"  ✅ 已生成: {output_file.name}\n")
        processed_count += 1

    print(f"\n🎉 全部完成！共处理 {processed_count} 个文件夹")


if __name__ == "__main__":
    base_directory = "/Users/richardzhang/工作/能力训练/skills_training_course/医学微生物学-中南大学"

    # 跳过"其他*17"文件夹
    skip_folders = ["其他*17"]

    merge_folder_docx_to_markdown(base_directory, skip_folders)
