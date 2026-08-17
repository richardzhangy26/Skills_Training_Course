#!/usr/bin/env python3
"""
训练剧本配置 Markdown 格式断言脚本

验证输出的 Markdown 文件是否满足 create_task_from_markdown.py 的导入规则。
用法: python validate_markdown.py <markdown_file> [--strict]
"""

import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationResult:
    """验证结果"""
    errors: list = field(default_factory=list)      # 必须修复的错误
    warnings: list = field(default_factory=list)     # 建议修复的警告
    info: list = field(default_factory=list)         # 信息提示

    @property
    def passed(self):
        return len(self.errors) == 0

    def add_error(self, stage: str, msg: str):
        self.errors.append(f"❌ [{stage}] {msg}")

    def add_warning(self, stage: str, msg: str):
        self.warnings.append(f"⚠️  [{stage}] {msg}")

    def add_info(self, stage: str, msg: str):
        self.info.append(f"ℹ️  [{stage}] {msg}")

    def report(self):
        lines = []
        if self.errors:
            lines.append(f"\n{'='*60}")
            lines.append(f"❌ 错误 ({len(self.errors)}): 会导致导入失败")
            lines.append(f"{'='*60}")
            for e in self.errors:
                lines.append(f"  {e}")
        if self.warnings:
            lines.append(f"\n{'='*60}")
            lines.append(f"⚠️  警告 ({len(self.warnings)}): 建议修复")
            lines.append(f"{'='*60}")
            for w in self.warnings:
                lines.append(f"  {w}")
        if self.info:
            lines.append(f"\n{'='*60}")
            lines.append(f"ℹ️  信息 ({len(self.info)})")
            lines.append(f"{'='*60}")
            for i in self.info:
                lines.append(f"  {i}")
        if not self.errors and not self.warnings:
            lines.append("\n✅ 所有检查通过！Markdown 格式满足导入要求。")
        else:
            lines.append(f"\n{'='*60}")
            status = "❌ 验证失败" if self.errors else "⚠️  验证通过（有警告）"
            lines.append(f"{status}  |  错误: {len(self.errors)}  警告: {len(self.warnings)}")
            lines.append(f"{'='*60}")
        return "\n".join(lines)


def validate_markdown(filepath: str, strict: bool = False) -> ValidationResult:
    """验证 Markdown 文件格式"""
    result = ValidationResult()
    path = Path(filepath)

    if not path.exists():
        result.add_error("全局", f"文件不存在: {filepath}")
        return result

    if not path.suffix.lower() == '.md':
        result.add_warning("全局", f"文件扩展名不是 .md: {path.suffix}")

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # ============================================================
    # 1. 全局结构检查
    # ============================================================
    has_basic_config = False
    for line in lines:
        normalized = line.strip().replace('：', ':')
        if normalized.startswith('## ') and '基础配置' in normalized:
            has_basic_config = True
            break

    if not has_basic_config:
        result.add_error("全局", "缺少 '## 基础配置' 或 '## 📋 基础配置' 章节")

    # 检查是否有训练阶段
    stage_headers = [i for i, l in enumerate(lines) if l.strip().replace('：', ':').startswith('### 阶段')]
    if not stage_headers:
        result.add_error("全局", "未找到任何 '### 阶段' 标题，至少需要一个训练阶段")
        return result

    result.add_info("全局", f"共发现 {len(stage_headers)} 个训练阶段")

    # ============================================================
    # 2. 逐阶段检查
    # ============================================================
    # 定义每个阶段的范围
    stage_ranges = []
    for idx, line_num in enumerate(stage_headers):
        end = stage_headers[idx + 1] if idx + 1 < len(stage_headers) else len(lines)
        stage_ranges.append((line_num, end))

    for stage_idx, (start, end) in enumerate(stage_ranges):
        stage_name = f"阶段{stage_idx + 1}"
        stage_lines = lines[start:end]
        stage_text = '\n'.join(stage_lines)

        # 提取阶段标题
        header = stage_lines[0].strip()
        result.add_info(stage_name, f"标题: {header}")

        # --- 2.1 必需字段检查 ---
        REQUIRED_FIELDS = [
            ('**虚拟训练官名字**:', '虚拟训练官名字'),
            ('**模型**:', '模型'),
            ('**阶段描述**:', '阶段描述'),
            ('**互动轮次**:', '互动轮次'),
            ('**flowCondition**:', 'flowCondition'),
        ]

        for field_pattern, field_name in REQUIRED_FIELDS:
            found = False
            for line in stage_lines:
                normalized = line.strip().replace('：', ':')
                if normalized.startswith(field_pattern.replace('：', ':')):
                    found = True
                    # 检查字段值是否为空
                    value = normalized.split(':', 1)[1].strip() if ':' in normalized else ''
                    if not value:
                        result.add_warning(stage_name, f"字段 '{field_name}' 值为空")
                    break
            if not found:
                result.add_error(stage_name, f"缺少必需字段 '{field_name}'")

        # --- 2.2 代码块字段检查 ---
        CODE_BLOCK_FIELDS = ['**开场白**:', '**提示词**:', '**transitionPrompt**:']

        for field_pattern in CODE_BLOCK_FIELDS:
            field_name = field_pattern.replace('**', '').replace(':', '')
            normalized_pattern = field_pattern.replace('：', ':')

            field_line_idx = None
            for i, line in enumerate(stage_lines):
                normalized = line.strip().replace('：', ':')
                if normalized.startswith(normalized_pattern):
                    field_line_idx = i
                    break

            if field_line_idx is None:
                # transitionPrompt 可以是行内值
                if 'transitionPrompt' in field_pattern:
                    result.add_info(stage_name, "transitionPrompt 未找到（可能为行内值或省略）")
                else:
                    result.add_error(stage_name, f"缺少代码块字段 '{field_name}'")
                continue

            # 检查字段后面是否有代码块
            # 找到该字段之后的下一个非空行
            next_content_idx = None
            for i in range(field_line_idx + 1, len(stage_lines)):
                if stage_lines[i].strip():
                    next_content_idx = i
                    break

            if next_content_idx is None:
                result.add_error(stage_name, f"字段 '{field_name}' 后没有代码块内容")
                continue

            next_line = stage_lines[next_content_idx].strip()

            # transitionPrompt 特殊处理：可以是行内值
            if 'transitionPrompt' in field_pattern:
                if not next_line.startswith('```'):
                    # 行内值模式 - 检查是否有内容
                    if len(next_line) > 0:
                        result.add_info(stage_name, "transitionPrompt 使用行内值模式")
                        # 行内值不需要代码块，跳过后续代码块检查
                        continue
                    else:
                        result.add_error(stage_name, "transitionPrompt 既没有代码块也没有行内值")
                        continue

            # 检查是否是代码块开始
            if not next_line.startswith('```'):
                result.add_error(stage_name, f"字段 '{field_name}' 后必须紧跟代码块 (```), 当前行为: {next_line[:50]}")
                continue

            # 检查代码块是否有语言标记（解析器不支持）
            if len(next_line) > 3:
                lang_tag = next_line[3:].strip()
                if lang_tag and lang_tag not in ['', 'markdown']:
                    result.add_warning(stage_name, f"代码块带有语言标记 '{lang_tag}'，解析器会将其当作内容")
                elif lang_tag == 'markdown':
                    result.add_error(stage_name, f"代码块带有 'markdown' 语言标记，解析器会误判为代码块结束符，必须移除")

            # 查找代码块结束位置
            code_block_start = next_content_idx
            code_block_end = None
            for i in range(code_block_start + 1, len(stage_lines)):
                if stage_lines[i].strip().startswith('```'):
                    code_block_end = i
                    break

            if code_block_end is None:
                result.add_error(stage_name, f"字段 '{field_name}' 的代码块未闭合（缺少结束 ```）")
                continue

            # 检查代码块内容
            code_content = '\n'.join(stage_lines[code_block_start + 1:code_block_end])

            # 检查代码块内部是否包含三反引号（会导致解析器误判）
            if '```' in code_content:
                result.add_error(stage_name, f"字段 '{field_name}' 的代码块内容中包含三反引号 (```)，会导致解析器截断。请使用单反引号 (`) 替代")

            # 检查代码块是否为空
            if not code_content.strip():
                result.add_warning(stage_name, f"字段 '{field_name}' 的代码块内容为空")

            # 提示词专项检查
            if '提示词' in field_pattern:
                # 检查是否包含 Role 标记
                if '# Role' not in code_content and '# 角色' not in code_content:
                    result.add_warning(stage_name, "提示词中未找到 '# Role' 或 '# 角色' 标记")
                # 检查是否包含 Workflow
                if 'Workflow' not in code_content and '步骤' not in code_content:
                    result.add_warning(stage_name, "提示词中未找到 'Workflow' 或 '步骤' 标记")

        # --- 2.3 flowCondition 格式检查 ---
        for line in stage_lines:
            normalized = line.strip().replace('：', ':')
            if normalized.startswith('**flowCondition**:'):
                value = normalized.split(':', 1)[1].strip()
                if value:
                    # 检查是否是合法的 flowCondition 格式
                    if not (value.startswith('NEXT_TO_') or value.startswith('TASK_COMPLETE') or value.startswith('"')):
                        result.add_warning(stage_name, f"flowCondition 值 '{value}' 不符合预期格式 (NEXT_TO_xxx 或 TASK_COMPLETE)")
                break

        # --- 2.4 互动轮次格式检查 ---
        for line in stage_lines:
            normalized = line.strip().replace('：', ':')
            if normalized.startswith('**互动轮次**:'):
                value = normalized.split(':', 1)[1].strip()
                if value and not re.search(r'\d+', value):
                    result.add_error(stage_name, f"互动轮次值 '{value}' 中未找到数字")
                break

    # ============================================================
    # 3. 严格模式额外检查
    # ============================================================
    if strict:
        # 检查阶段编号连续性
        stage_numbers = []
        for line in lines:
            match = re.match(r'###\s*阶段(\d+)', line.strip().replace('：', ':'))
            if match:
                stage_numbers.append(int(match.group(1)))

        if stage_numbers:
            expected = list(range(1, len(stage_numbers) + 1))
            if stage_numbers != expected:
                result.add_warning("全局", f"阶段编号不连续: {stage_numbers}, 期望: {expected}")

        # 检查基础配置中的必需字段
        in_basic_config = False
        basic_config_fields = set()
        for line in lines:
            normalized = line.strip().replace('：', ':')
            if normalized.startswith('## ') and '基础配置' in normalized:
                in_basic_config = True
                continue
            if normalized.startswith('## ') and in_basic_config:
                break
            if in_basic_config:
                if '任务名称' in normalized:
                    basic_config_fields.add('任务名称')
                if '任务描述' in normalized:
                    basic_config_fields.add('任务描述')

        for required in ['任务名称', '任务描述']:
            if required not in basic_config_fields:
                result.add_error("基础配置", f"缺少必需字段 '{required}'")

    return result


def main():
    parser = argparse.ArgumentParser(
        description='验证训练剧本配置 Markdown 格式是否满足导入要求'
    )
    parser.add_argument('markdown_file', help='Markdown 文件路径')
    parser.add_argument('--strict', action='store_true', help='严格模式：额外检查阶段编号连续性和基础配置字段')
    parser.add_argument('--quiet', '-q', action='store_true', help='安静模式：仅输出错误')

    args = parser.parse_args()
    result = validate_markdown(args.markdown_file, strict=args.strict)

    if args.quiet:
        if result.errors:
            for e in result.errors:
                print(e)
            sys.exit(1)
        sys.exit(0)

    print(f"\n📋 验证文件: {args.markdown_file}")
    print(result.report())

    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
