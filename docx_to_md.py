from pathlib import Path
from docx import Document
import zipfile
import shutil
import os
import sys
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.table import Table


def extract_images(docx_path: Path, media_output_dir: Path):
    """
    从 docx 中提取图片到 media_output_dir，返回 {原始路径: 新路径} 映射
    """
    media_map = {}
    media_output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx_path, "r") as zf:
        for name in zf.namelist():
            if not name.startswith("word/media/"):
                continue

            # 目录项（以 / 结尾）跳过，只处理真正的文件
            if name.endswith("/"):
                continue

            filename = name.split("/")[-1]
            if not filename:
                continue

            out_path = media_output_dir / filename
            with zf.open(name) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            media_map[name] = out_path
    return media_map


def table_to_markdown(table):
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


def docx_to_markdown_content(docx_path: Path, extract_images: bool = False) -> str:
    """
    将 docx 文件转换为 Markdown 字符串（不保存文件）

    Args:
        docx_path: docx 文件路径
        extract_images: 是否提取图片（会保存到 media/<docx_stem>/ 目录）

    Returns:
        Markdown 字符串
    """
    if not docx_path.exists():
        raise FileNotFoundError(f"文件不存在: {docx_path}")

    # 可选：提取图片
    media_output_dir = None
    image_paths = []
    if extract_images:
        media_output_dir = docx_path.parent / "media" / docx_path.stem
        media_map = extract_images(docx_path, media_output_dir)
        image_paths = list(media_map.values())
    else:
        # 仍然需要提取图片信息来确定图片位置，但不保存
        media_map = extract_images(docx_path, docx_path.parent / ".temp_media")
        image_paths = list(media_map.values())
        # 清理临时目录
        shutil.rmtree(docx_path.parent / ".temp_media", ignore_errors=True)

    document = Document(docx_path)
    image_index = 0
    lines = []

    body = document._element.body
    for child in body.iterchildren():
        tag = child.tag

        if tag == qn("w:p"):
            paragraph = Paragraph(child, document)
            text = paragraph.text.strip()

            # 判断该段落是否包含图片（w:drawing）
            has_drawing = any(elem.tag == qn("w:drawing") for elem in child.iter())

            if has_drawing and not text and image_index < len(image_paths):
                if extract_images:
                    rel = os.path.relpath(image_paths[image_index], docx_path.parent)
                    lines.append(f"![]({rel})")
                else:
                    lines.append("[图片]")
                image_index += 1
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

    # 如果还有剩余未插入的图片，统一放在文末
    if image_index < len(image_paths):
        lines.append("")
        lines.append("## 其他图片")
        for remaining_path in image_paths[image_index:]:
            if extract_images:
                rel = os.path.relpath(remaining_path, docx_path.parent)
                lines.append(f"![]({rel})")
            else:
                lines.append("[图片]")

    return "\n".join(lines)


def docx_to_md(docx_file: Path):
    docx_path = docx_file
    if not docx_path.exists():
        print(f"文件不存在: {docx_path}")
        return

    md_path = docx_path.with_suffix(".md")
    # 每个 docx 使用独立的图片子目录：media/<docx_stem>/
    media_output_dir = docx_path.parent / "media" / docx_path.stem

    document = Document(docx_path)
    media_map = extract_images(docx_path, media_output_dir)

    # 按文件名顺序记录图片路径，用于在正文中依次插入
    image_paths = list(media_map.values())
    image_index = 0

    lines = []

    body = document._element.body
    for child in body.iterchildren():
        tag = child.tag

        if tag == qn("w:p"):
            paragraph = Paragraph(child, document)
            text = paragraph.text.strip()

            # 判断该段落是否包含图片（w:drawing），如果只有图片没有文本，则在此位置插入图片
            has_drawing = any(elem.tag == qn("w:drawing") for elem in child.iter())

            if has_drawing and not text and image_index < len(image_paths):
                rel = os.path.relpath(image_paths[image_index], md_path.parent)
                lines.append(f"![]({rel})")
                image_index += 1
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

    # 如果还有剩余未插入的图片，统一放在文末作为补充
    if image_index < len(image_paths):
        lines.append("")
        lines.append("## 其他图片")
        for remaining_path in image_paths[image_index:]:
            rel = os.path.relpath(remaining_path, md_path.parent)
            lines.append(f"![]({rel})")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"转换完成: {docx_path} -> {md_path}")


def main():
    if len(sys.argv) < 2:
        print("用法: python docx_to_md.py file1.docx [file2.docx ...]")
        return

    for arg in sys.argv[1:]:
        docx_to_md(Path(arg))


if __name__ == "__main__":
    main()