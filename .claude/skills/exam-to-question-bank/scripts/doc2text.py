#!/usr/bin/env python3
"""试卷文档 → 纯文本提取。

支持 .doc / .docx / .pdf / .txt / .md 输入，输出 UTF-8 纯文本。
提取链（按可用性自动选择）：
  Word:   macOS textutil → LibreOffice headless → antiword(.doc)/python-docx(.docx)
  PDF:    pdftotext(poppler) → PyMuPDF(fitz) → pypdf

用法:
  python3 doc2text.py <输入文档> [输出txt路径]
  未指定输出路径时，写到输入文件同目录下的 <同名>.extracted.txt
"""
import shutil
import subprocess
import sys
from pathlib import Path

SUPPORTED = {".doc", ".docx", ".pdf", ".txt", ".md"}


def run(cmd: list[str]) -> bool:
    """执行命令，成功返回 True。"""
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def extract_with_textutil(src: Path, dst: Path) -> bool:
    return run(["textutil", "-convert", "txt", str(src), "-output", str(dst)])


def extract_with_libreoffice(src: Path, dst: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return False
    if not run([soffice, "--headless", "--convert-to", "txt:Text",
                "--outdir", str(dst.parent), str(src)]):
        return False
    produced = dst.parent / (src.stem + ".txt")
    if produced.exists() and produced != dst:
        produced.replace(dst)
    return dst.exists()


def extract_with_antiword(src: Path, dst: Path) -> bool:
    if shutil.which("antiword") is None:
        return False
    try:
        text = subprocess.run(["antiword", str(src)],
                              capture_output=True, timeout=120).stdout
        dst.write_bytes(text)
        return bool(text.strip())
    except (OSError, subprocess.TimeoutExpired):
        return False


def extract_with_python_docx(src: Path, dst: Path) -> bool:
    try:
        from docx import Document
    except ImportError:
        return False
    try:
        doc = Document(str(src))
        lines = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            lines.extend("\t".join(c.text for c in row.cells)
                         for row in table.rows)
        dst.write_text("\n".join(lines), encoding="utf-8")
        return True
    except Exception:
        return False


def extract_pdf_with_pdftotext(src: Path, dst: Path) -> bool:
    # -layout 保留选项/表格的原始排版，利于后续结构识别
    return shutil.which("pdftotext") is not None and \
        run(["pdftotext", "-layout", str(src), str(dst)]) and \
        dst.exists() and dst.read_text(errors="replace").strip() != ""


def extract_pdf_with_fitz(src: Path, dst: Path) -> bool:
    try:
        import fitz
    except ImportError:
        return False
    try:
        doc = fitz.open(str(src))
        text = "\n".join(page.get_text() for page in doc)
        dst.write_text(text, encoding="utf-8")
        return bool(text.strip())
    except Exception:
        return False


def extract_pdf_with_pypdf(src: Path, dst: Path) -> bool:
    try:
        from pypdf import PdfReader
    except ImportError:
        return False
    try:
        reader = PdfReader(str(src))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        dst.write_text(text, encoding="utf-8")
        return bool(text.strip())
    except Exception:
        return False


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = Path(sys.argv[1]).expanduser()
    if not src.exists():
        print(f"错误: 文件不存在: {src}", file=sys.stderr)
        return 1
    if src.suffix.lower() not in SUPPORTED:
        print(f"错误: 不支持的格式 {src.suffix}，仅支持 {sorted(SUPPORTED)}",
              file=sys.stderr)
        return 1

    dst = (Path(sys.argv[2]).expanduser() if len(sys.argv) > 2
           else src.with_name(src.stem + ".extracted.txt"))

    if src.suffix.lower() in {".txt", ".md"}:
        shutil.copyfile(src, dst)
    elif src.suffix.lower() == ".pdf":
        extractors = [extract_pdf_with_pdftotext,
                      extract_pdf_with_fitz,
                      extract_pdf_with_pypdf]
        for extract in extractors:
            if extract(src, dst):
                break
        else:
            print("错误: 无可用 PDF 提取工具。请安装 poppler "
                  "(brew install poppler) 或 pypdf (pip install pypdf)。\n"
                  "提示: 若 PDF 为扫描图片版，文本提取会为空，"
                  "需改用 OCR 或让模型直接读图。", file=sys.stderr)
            return 1
    else:
        extractors = [extract_with_textutil, extract_with_libreoffice]
        if src.suffix.lower() == ".doc":
            extractors.append(extract_with_antiword)
        else:
            extractors.append(extract_with_python_docx)
        for extract in extractors:
            if extract(src, dst):
                break
        else:
            print("错误: 无可用提取工具。请安装 LibreOffice，"
                  "macOS 自带 textutil 无需额外安装。", file=sys.stderr)
            return 1

    text = dst.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        if src.suffix.lower() == ".pdf":
            print(f"错误: 提取结果为空，{src} 可能是扫描图片版 PDF（无可提取文本层）。\n"
                  f"请改用 OCR，或让模型直接读取 PDF 图像。", file=sys.stderr)
        else:
            print(f"错误: 提取结果为空: {src}", file=sys.stderr)
        return 1
    print(f"✅ 已提取 {len(text.splitlines())} 行 → {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
