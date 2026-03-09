"""
文件解析器 - 读取教师文档和对话记录
"""

import os
import json
from typing import Tuple, Optional
from txt_converter import parse_txt_dialogue
from types_def import DialogueData, DialogueMetadata, DialogueStage, DialogueMessage



def read_file_content(file_path: str) -> str:
    """读取文件内容"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_dialogue_file(file_path: str) -> DialogueData:
    """解析对话记录文件 (.txt, .json)"""
    ext = os.path.splitext(file_path)[1].lower()
    content = read_file_content(file_path)

    if ext == ".txt":
        return parse_txt_dialogue(content)

    if ext == ".json":
        data = json.loads(content)
        return DialogueData(
            metadata=DialogueMetadata(**data.get("metadata", {})),
            stages=[
                DialogueStage(
                    stage_name=stage.get("stage_name", ""),
                    messages=[DialogueMessage(**msg) for msg in stage.get("messages", [])]
                )
                for stage in data.get("stages", [])
            ],
        )

    raise ValueError(f"不支持的对话记录格式: {ext}")


def parse_teacher_doc_file(file_path: str) -> str:
    """解析教师文档 (.md, .txt, .docx)"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".md", ".txt"]:
        return read_file_content(file_path)

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            raise ValueError("读取 .docx 需要安装: pip install python-docx")

    raise ValueError(f"不支持的教师文档格式: {ext}")


def parse_workflow_config_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".md", ".docx"]:
        return parse_teacher_doc_file(file_path)

    raise ValueError(f"不支持的工作流配置格式: {ext}")


def parse_input_files(
    teacher_doc_path: str,
    dialogue_record_path: str,
    workflow_config_path: Optional[str] = None,
) -> Tuple[str, DialogueData, Optional[str]]:
    """解析输入文件"""
    print(f"正在读取教师文档: {teacher_doc_path}")
    teacher_doc = parse_teacher_doc_file(teacher_doc_path)
    print(f"已加载教师文档: {len(teacher_doc)} 字符")

    print(f"正在读取对话记录: {dialogue_record_path}")
    dialogue_data = parse_dialogue_file(dialogue_record_path)
    print(f"已加载对话记录: {dialogue_data.metadata.total_rounds} 轮")

    workflow_config = None
    if workflow_config_path:
        print(f"正在读取工作流配置: {workflow_config_path}")
        workflow_config = parse_workflow_config_file(workflow_config_path)
        print(f"已加载工作流配置: {len(workflow_config)} 字符")

    return teacher_doc, dialogue_data, workflow_config
