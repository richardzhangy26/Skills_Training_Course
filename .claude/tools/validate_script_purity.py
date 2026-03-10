#!/usr/bin/env python3
"""
训练剧本"纯净跳转"验证工具

用于检测训练剧本配置中的非纯净跳转问题，确保满足跳转条件时
仅输出跳转关键词，不包含任何其他字符。

使用方法:
    python validate_script_purity.py <markdown_file>     # 验证单个文件
    python validate_script_purity.py --batch <dir>       # 批量验证目录
    python validate_script_purity.py --check-git         # 验证git staged文件
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Violation:
    """违规记录"""
    file_path: str
    line_number: int
    line_content: str
    violation_type: str
    suggestion: str
    context: str = ""  # 上下文内容


class ScriptPurityValidator:
    """训练剧本纯净跳转验证器"""

    # 跳转关键词模式
    JUMP_KEYWORDS = [
        r'NEXT_TO_\w+',
        r'TASK_COMPLETE',
        r'JUMP_TO_\w+',
        r'STAGE_\w+',
    ]

    # 违规模式定义
    VIOLATION_PATTERNS = {
        'prefix_dialogue': {
            'name': '前缀对话违规',
            'description': '跳转关键词前有对话内容',
            'pattern': r'[\u4e00-\u9fa5a-zA-Z].*(?:NEXT_TO_\w+|TASK_COMPLETE)',
            'suggestion': '移除跳转关键词前的所有文字，仅保留纯跳转关键词'
        },
        'suffix_dialogue': {
            'name': '后缀对话违规',
            'description': '跳转关键词后有对话内容',
            'pattern': r'(?:NEXT_TO_\w+|TASK_COMPLETE).*[\u4e00-\u9fa5a-zA-Z]',
            'suggestion': '移除跳转关键词后的所有文字，仅保留纯跳转关键词'
        },
        'with_punctuation': {
            'name': '标点符号违规',
            'description': '跳转关键词包含标点符号',
            'pattern': r'(?:NEXT_TO_\w+|TASK_COMPLETE)[。，！？、；："\'\(\)\[\]{}]',
            'suggestion': '移除跳转关键词后的所有标点符号'
        },
        'multi_action_pattern': {
            'name': '组合动作违规',
            'description': '操作字段包含"先输出X,再跳转"模式',
            'pattern': r'先.*(?:输出|回复|评价|说).*再.*(?:跳转|输出).*NEXT_TO',
            'suggestion': '将评价/回复与跳转拆分为两个独立分支，评价分支使用"回复策略"，跳转分支使用"操作"'
        },
        'evaluation_then_jump': {
            'name': '评价后跳转违规',
            'description': '同一分支中先评价再跳转',
            'pattern': r'(?:评价|回复|说).*(?:然后|再|之后).*跳转',
            'suggestion': '评价和跳转必须在不同分支中处理：评价分支单独输出评价内容，跳转分支仅输出跳转关键词'
        },
        'output_then_jump': {
            'name': '输出后跳转违规',
            'description': '操作描述包含"输出X,然后跳转"',
            'pattern': r'(?:输出|回复).*(?:然后|再|之后).*?(?:NEXT_TO_\w+|TASK_COMPLETE)',
            'suggestion': '跳转操作必须独立，不允许在跳转前输出任何内容'
        },
        'quotes_around_jump': {
            'name': '引号包裹违规',
            'description': '跳转关键词被引号包裹',
            'pattern': r'["\'].*NEXT_TO_\w+.*["\']',
            'suggestion': '跳转关键词不应被引号包裹，直接输出纯文本'
        },
    }

    def __init__(self):
        self.violations: List[Violation] = []
        self.current_file: str = ""
        self.lines: List[str] = []

    def validate_file(self, file_path: str) -> List[Violation]:
        """验证单个文件"""
        self.current_file = file_path
        self.violations = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
        except Exception as e:
            print(f"错误: 无法读取文件 {file_path}: {e}")
            return []

        # 检查各种违规模式
        self._check_jump_purity()
        self._check_action_patterns()
        self._check_response_constraints()

        return self.violations

    def _get_context(self, line_idx: int, radius: int = 3) -> str:
        """获取指定行的上下文"""
        start = max(0, line_idx - radius)
        end = min(len(self.lines), line_idx + radius + 1)
        context_lines = []
        for i in range(start, end):
            marker = ">>> " if i == line_idx else "    "
            context_lines.append(f"{marker}{i+1:4d}: {self.lines[i].rstrip()}")
        return "\n".join(context_lines)

    def _should_skip_line(self, line: str, context_lines: List[str] = None, current_idx: int = 0) -> bool:
        """判断是否应该跳过该行（减少误报）"""
        stripped = line.strip()

        # 跳过 Markdown 标题
        if stripped.startswith('#'):
            return True

        # 跳过 flowCondition 字段（这是配置文件格式，不是提示词内容）
        if 'flowCondition' in stripped:
            return True

        # 跳过包含 "不要输出任何对话内容" 的行（这是正确的写法）
        if '不要输出任何对话内容' in stripped:
            return True

        # 跳过阶段跳转关系说明（如 "阶段1 → 阶段2：跳转关键词"）
        if '→' in stripped and ('阶段' in stripped or '跳转' in stripped):
            return True

        # 跳过配置说明中的跳转示例
        if stripped.startswith('-') and '跳转关键词' in stripped and '：' in stripped:
            return True

        # 跳过表格行（| 列1 | 列2 |）
        if stripped.startswith('|') and stripped.endswith('|'):
            return True

        # 跳过代码块标记
        if stripped.startswith('```'):
            return True

        # 跳过文档说明中的跳转描述（非实际提示词内容）
        if '输出跳转指令' in stripped or '跳转指令' in stripped:
            return True

        # 跳过流程示例中的描述（如"智能体：（执行步骤0...）"）
        if stripped.startswith('- 智能体：') and '执行步骤' in stripped:
            return True

        # 跳过设计文档中的分支说明（非实际提示词）
        if '分支' in stripped and ('→' in stripped or '：' in stripped):
            # 检查是否是配置说明部分
            if context_lines:
                for i in range(current_idx - 1, max(-1, current_idx - 20), -1):
                    if i < 0:
                        break
                    if '配置说明' in context_lines[i] or '判断逻辑' in context_lines[i] or '阶段跳转关系' in context_lines[i]:
                        return True
                    if context_lines[i].strip().startswith('#') and '示例' in context_lines[i]:
                        break

        # 跳过"输出"字段的说明（如"- **输出**：`TASK_COMPLETE`"）
        if '**输出**' in stripped and 'TASK_COMPLETE' in stripped:
            return True

        # 跳过设计文档中的分支说明（如"- **分支A（学生回答准确完整）**: 2项诊断都有"）
        if '**分支' in stripped and ('→' in stripped or '2项' in stripped or '都有' in stripped):
            return True

        # 检查上下文：如果在 "❌ 错误写法" 或 "实际输出结果" 块中，跳过
        if context_lines:
            # 向上查找最近的上下文标记
            for i in range(current_idx - 1, max(-1, current_idx - 10), -1):
                if i < 0:
                    break
                prev_line = context_lines[i].strip()
                if '❌ 错误写法' in prev_line or '❌ 实际输出结果' in prev_line:
                    return True
                if '```' in prev_line and prev_line.startswith('```'):
                    # 遇到了代码块开始，检查这个代码块是否包含错误示例
                    for j in range(i - 1, max(-1, i - 5), -1):
                        if j < 0:
                            break
                        check_line = context_lines[j].strip()
                        if '❌' in check_line:
                            return True
                        if check_line.startswith('#'):
                            break
                    break

        return False

    def _check_jump_purity(self):
        """检查跳转纯净性"""
        for i, line in enumerate(self.lines):
            line_num = i + 1

            # 检查是否有跳转关键词
            jump_pattern = r'NEXT_TO_\w+|TASK_COMPLETE'
            if not re.search(jump_pattern, line):
                continue

            # 跳过不应检查的行
            if self._should_skip_line(line, self.lines, i):
                continue

            # 检查前缀对话（中文或英文单词在跳转前）
            # 排除配置字段和正确写法
            prefix_pattern = r'[\u4e00-\u9fa5]{2,}.*(?:NEXT_TO_\w+|TASK_COMPLETE)'
            if re.search(prefix_pattern, line):
                # 进一步确认不是 "跳转关键词 XXX" 这种说明性文字
                if not re.search(r'跳转关键词[\s`]*NEXT_TO', line):
                    self._add_violation(
                        line_num, line, 'prefix_dialogue',
                        '检测到跳转关键词前有文字内容'
                    )
                    continue

            # 检查后缀对话（跳转后有中文或英文单词）
            suffix_pattern = r'(?:NEXT_TO_\w+|TASK_COMPLETE).*[\u4e00-\u9fa5]{2,}'
            if re.search(suffix_pattern, line):
                self._add_violation(
                    line_num, line, 'suffix_dialogue',
                    '检测到跳转关键词后有文字内容'
                )
                continue

            # 检查标点符号（紧跟在跳转关键词后的标点）
            punc_pattern = r'(?:NEXT_TO_\w+|TASK_COMPLETE)[。，！？、；：\.\,\!\?]'
            if re.search(punc_pattern, line):
                self._add_violation(
                    line_num, line, 'with_punctuation',
                    '检测到跳转关键词后有标点符号'
                )

            # 检查引号包裹（排除代码块和配置字段的引号）
            quote_pattern = r'^\s*["\']+.*?NEXT_TO_\w+.*?["\']+\s*$'
            if re.search(quote_pattern, line):
                self._add_violation(
                    line_num, line, 'quotes_around_jump',
                    '检测到跳转关键词被引号包裹'
                )

    def _check_action_patterns(self):
        """检查操作字段中的违规模式"""
        in_workflow = False
        current_section = ""

        for i, line in enumerate(self.lines):
            line_num = i + 1
            stripped = line.strip()

            # 追踪 Workflow 区域
            if re.search(r'#{1,3}\s+(?:Workflow|Interaction Rules)', stripped):
                in_workflow = True
                continue
            elif re.search(r'#{1,3}\s+\w+', stripped) and in_workflow:
                if 'Response Constraints' in stripped or 'Opening Line' in stripped:
                    in_workflow = False

            if not in_workflow:
                continue

            # 检查"先...再跳转"模式
            multi_pattern = r'先.*(?:输出|回复|评价|说|确认).*再.*(?:跳转|输出.*NEXT_TO)'
            if re.search(multi_pattern, line, re.IGNORECASE):
                self._add_violation(
                    line_num, line, 'multi_action_pattern',
                    '检测到"先X再跳转"的组合模式'
                )

            # 检查"输出...然后跳转"模式
            output_jump_pattern = r'(?:输出|回复|说).*(?:然后|再|之后).*NEXT_TO_\w+'
            if re.search(output_jump_pattern, line, re.IGNORECASE):
                self._add_violation(
                    line_num, line, 'output_then_jump',
                    '检测到"输出内容后再跳转"的描述'
                )

    def _check_response_constraints(self):
        """检查 Response Constraints 中的跳转纯净性声明"""
        in_constraints = False

        for i, line in enumerate(self.lines):
            line_num = i + 1
            stripped = line.strip()

            if re.search(r'#{1,3}\s+Response Constraints', stripped):
                in_constraints = True
                continue
            elif re.search(r'#{1,3}\s+\w+', stripped) and in_constraints:
                in_constraints = False

            if not in_constraints:
                continue

            # 检查是否有跳转纯净性约束
            purity_pattern = r'跳转.*纯净|纯净.*跳转|不要输出任何对话'
            if re.search(purity_pattern, line):
                # 找到了约束声明，这是好事
                pass

    def _add_violation(self, line_number: int, line_content: str,
                       violation_type: str, detail: str = ""):
        """添加违规记录"""
        pattern_info = self.VIOLATION_PATTERNS.get(violation_type, {})

        violation = Violation(
            file_path=self.current_file,
            line_number=line_number,
            line_content=line_content.rstrip(),
            violation_type=pattern_info.get('name', violation_type),
            suggestion=pattern_info.get('suggestion', detail),
            context=self._get_context(line_number - 1)
        )
        self.violations.append(violation)

    def print_report(self, violations: List[Violation]) -> bool:
        """打印验证报告，返回是否通过"""
        if not violations:
            print("\n✅ 验证通过！未发现非纯净跳转问题。\n")
            return True

        # 按文件分组
        by_file: Dict[str, List[Violation]] = {}
        for v in violations:
            by_file.setdefault(v.file_path, []).append(v)

        print("\n" + "=" * 80)
        print("❌ 发现非纯净跳转问题")
        print("=" * 80)

        for file_path, file_violations in by_file.items():
            print(f"\n📄 文件: {file_path}")
            print("-" * 60)

            for i, v in enumerate(file_violations, 1):
                print(f"\n  问题 #{i}: {v.violation_type}")
                print(f"  行号: {v.line_number}")
                print(f"  内容: {v.line_content[:100]}{'...' if len(v.line_content) > 100 else ''}")
                print(f"  建议: {v.suggestion}")
                print(f"\n  上下文:\n{v.context}")
                print("-" * 60)

        print(f"\n总计: {len(violations)} 个问题需要修复\n")
        return False


def find_training_scripts(directory: str) -> List[str]:
    """查找目录中的所有训练剧本配置文件"""
    scripts = []
    path = Path(directory)

    for pattern in ['**/训练剧本配置.md', '**/*剧本*.md']:
        scripts.extend([str(p) for p in path.glob(pattern)])

    return list(set(scripts))


def main():
    parser = argparse.ArgumentParser(
        description='训练剧本"纯净跳转"验证工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s script.md                    # 验证单个文件
  %(prog)s --batch ./scripts            # 批量验证目录
  %(prog)s --check-git                  # 验证 git staged 文件
        """
    )

    parser.add_argument('path', nargs='?',
                        help='要验证的 Markdown 文件或目录')
    parser.add_argument('--batch', '-b', action='store_true',
                        help='批量验证目录中的所有训练剧本')
    parser.add_argument('--check-git', '-g', action='store_true',
                        help='验证 git staged 的训练剧本文件')
    parser.add_argument('--strict', '-s', action='store_true',
                        help='严格模式（将警告视为错误）')

    args = parser.parse_args()

    validator = ScriptPurityValidator()
    all_violations = []

    if args.check_git:
        # 获取 git staged 文件
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, check=True
            )
            staged_files = [
                f for f in result.stdout.strip().split('\n')
                if f and ('剧本' in f or '训练' in f) and f.endswith('.md')
            ]

            if not staged_files:
                print("未发现 staged 的训练剧本文件")
                return 0

            for f in staged_files:
                print(f"验证: {f}")
                violations = validator.validate_file(f)
                all_violations.extend(violations)

        except subprocess.CalledProcessError:
            print("错误: 无法获取 git staged 文件")
            return 1
        except FileNotFoundError:
            print("错误: 未找到 git 命令")
            return 1

    elif args.batch:
        if not args.path:
            print("错误: 批量模式需要指定目录路径")
            return 1

        scripts = find_training_scripts(args.path)
        if not scripts:
            print(f"在 {args.path} 中未找到训练剧本文件")
            return 0

        print(f"找到 {len(scripts)} 个训练剧本文件")
        for script in scripts:
            print(f"\n验证: {script}")
            violations = validator.validate_file(script)
            all_violations.extend(violations)

    elif args.path:
        if not Path(args.path).exists():
            print(f"错误: 文件不存在: {args.path}")
            return 1

        all_violations = validator.validate_file(args.path)

    else:
        parser.print_help()
        return 0

    # 打印报告
    passed = validator.print_report(all_violations)

    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
