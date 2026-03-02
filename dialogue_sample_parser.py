"""
模拟对话文档解析器

支持多种格式的对话文档解析：
- AI: / 学生:
- 智能体: / 同学:
- 智能体扮演xxx: / 学生:
- 期望答案: / 期望答案链:
"""

import re
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple


@dataclass
class DialoguePair:
    """对话对数据结构"""
    ai_question: str              # AI/智能体的问题
    student_answer: str           # 学生/同学的回答
    ai_role_hint: str = ""        # 角色提示，如"牧场主"、"质疑专家"
    module: str = ""              # 来源模块，如"模块一：口外检查"
    line_number: int = 0          # 原文行号，便于定位

    def __repr__(self):
        hint = f" ({self.ai_role_hint})" if self.ai_role_hint else ""
        module = f" [{self.module}]" if self.module else ""
        return f"DialoguePair{hint}{module}: AI={self.ai_question[:30]}... -> Student={self.student_answer[:30]}..."


@dataclass
class ParseResult:
    """解析结果"""
    pairs: List[DialoguePair] = field(default_factory=list)
    detected_ai_pattern: str = ""
    detected_student_pattern: str = ""
    modules: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DialogueSampleParser:
    """模拟对话文档解析器"""

    # 常见的 AI 角色标识模式（按优先级排序）
    DEFAULT_AI_PATTERNS = [
        # 精确匹配
        (r'^AI[：:]\s*', 'AI'),
        (r'^智能体[：:]\s*', '智能体'),
        (r'^老师[：:]\s*', '老师'),
        (r'^教师[：:]\s*', '教师'),
        (r'^系统[：:]\s*', '系统'),
        (r'^助手[：:]\s*', '助手'),
        # 带角色描述的智能体
        (r'^智能体扮演[^：:]*[：:]\s*', '智能体扮演'),
        (r'^智能体互动[^：:]*[：:]\s*', '智能体互动'),
        (r'^智能体角色[^：:]*[：:]\s*', '智能体角色'),
    ]

    # 常见的学生角色标识模式
    DEFAULT_STUDENT_PATTERNS = [
        (r'^学生[：:]\s*', '学生'),
        (r'^同学[：:]\s*', '同学'),
        (r'^用户[：:]\s*', '用户'),
        # 期望答案类
        (r'^期望答案链?[：:]\s*', '期望答案'),
        (r'^参考答案[：:]\s*', '参考答案'),
        (r'^标准答案[：:]\s*', '标准答案'),
    ]

    def __init__(
        self,
        ai_patterns: Optional[List[Tuple[str, str]]] = None,
        student_patterns: Optional[List[Tuple[str, str]]] = None,
    ):
        """
        初始化解析器

        Args:
            ai_patterns: 自定义 AI 角色模式列表 [(regex, label), ...]
            student_patterns: 自定义学生角色模式列表
        """
        self.ai_patterns = ai_patterns or self.DEFAULT_AI_PATTERNS
        self.student_patterns = student_patterns or self.DEFAULT_STUDENT_PATTERNS

        # 编译正则表达式
        self._compiled_ai = [(re.compile(p, re.MULTILINE), label) for p, label in self.ai_patterns]
        self._compiled_student = [(re.compile(p, re.MULTILINE), label) for p, label in self.student_patterns]

    def auto_detect_roles(self, content: str) -> Dict[str, str]:
        """
        自动检测文档中使用的角色标识

        Args:
            content: 文档内容

        Returns:
            {'ai': 检测到的AI标识, 'student': 检测到的学生标识, 'ai_count': 次数, 'student_count': 次数}
        """
        result = {
            'ai': '',
            'student': '',
            'ai_count': 0,
            'student_count': 0,
            'ai_candidates': [],
            'student_candidates': [],
        }

        lines = content.split('\n')

        # 统计 AI 模式
        ai_counts: Dict[str, int] = {}
        for pattern, label in self._compiled_ai:
            count = 0
            for line in lines:
                if pattern.match(line.strip()):
                    count += 1
            if count > 0:
                ai_counts[label] = count

        # 统计学生模式
        student_counts: Dict[str, int] = {}
        for pattern, label in self._compiled_student:
            count = 0
            for line in lines:
                if pattern.match(line.strip()):
                    count += 1
            if count > 0:
                student_counts[label] = count

        # 选择频率最高的
        if ai_counts:
            result['ai'] = max(ai_counts, key=ai_counts.get)
            result['ai_count'] = ai_counts[result['ai']]
            result['ai_candidates'] = sorted(ai_counts.items(), key=lambda x: -x[1])

        if student_counts:
            result['student'] = max(student_counts, key=student_counts.get)
            result['student_count'] = student_counts[result['student']]
            result['student_candidates'] = sorted(student_counts.items(), key=lambda x: -x[1])

        return result

    def parse(self, content: str, auto_detect: bool = True) -> ParseResult:
        """
        解析文档内容

        Args:
            content: 文档内容
            auto_detect: 是否自动检测角色标识

        Returns:
            ParseResult 对象，包含解析出的对话对和元信息
        """
        result = ParseResult()

        # 自动检测角色
        if auto_detect:
            detection = self.auto_detect_roles(content)
            result.detected_ai_pattern = detection.get('ai', '')
            result.detected_student_pattern = detection.get('student', '')

            if not result.detected_ai_pattern:
                result.warnings.append("未检测到 AI 角色标识")
            if not result.detected_student_pattern:
                result.warnings.append("未检测到学生角色标识")

        lines = content.split('\n')

        # 状态机解析
        current_module = ""
        current_ai_text = ""
        current_ai_role_hint = ""
        current_ai_line = 0

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 检测模块/章节标题
            module_match = re.match(r'^#{1,3}\s*(.+)$', line)
            if module_match:
                current_module = module_match.group(1).strip()
                if current_module not in result.modules:
                    result.modules.append(current_module)
                i += 1
                continue

            # 检测 AI 角色行
            ai_match, ai_role_hint, ai_content = self._match_ai_line(line)
            if ai_match:
                # 开始新的 AI 内容，重置之前的状态
                current_ai_text = ai_content
                current_ai_role_hint = ai_role_hint
                current_ai_line = i + 1

                # 检查是否需要读取后续行（多行内容）
                current_ai_text = self._collect_multiline_content(lines, i, current_ai_text)

                i += 1
                continue

            # 检测学生角色行
            student_match, student_content = self._match_student_line(line)
            if student_match:
                if current_ai_text:
                    # 收集学生回答（可能跨多行）
                    student_text = student_content
                    student_text = self._collect_multiline_content(lines, i, student_text)

                    # 保存对话对
                    result.pairs.append(DialoguePair(
                        ai_question=current_ai_text.strip(),
                        student_answer=student_text.strip(),
                        ai_role_hint=current_ai_role_hint,
                        module=current_module,
                        line_number=current_ai_line,
                    ))

                    # 重置 AI 状态，等待下一个 AI 问题
                    current_ai_text = ""
                    current_ai_role_hint = ""

                i += 1
                continue

            i += 1

        return result

    def _match_ai_line(self, line: str) -> Tuple[bool, str, str]:
        """
        匹配 AI 角色行

        Returns:
            (是否匹配, 角色提示, 内容)
        """
        for pattern, label in self._compiled_ai:
            match = pattern.match(line)
            if match:
                content = line[match.end():].strip()

                # 提取角色提示（如"智能体扮演推诿的经理"中的"推诿的经理"）
                role_hint = ""
                if '扮演' in label or '互动' in label:
                    hint_match = re.search(r'扮演(.+?)[：:]|互动[（(](.+?)[)）][：:]', line)
                    if hint_match:
                        role_hint = hint_match.group(1) or hint_match.group(2) or ""

                # 处理引号包裹的内容
                content = self._extract_quoted_content(content) or content

                return True, role_hint.strip(), content

        return False, "", ""

    def _match_student_line(self, line: str) -> Tuple[bool, str]:
        """
        匹配学生角色行

        Returns:
            (是否匹配, 内容)
        """
        for pattern, label in self._compiled_student:
            match = pattern.match(line)
            if match:
                content = line[match.end():].strip()
                return True, content

        return False, ""

    def _extract_quoted_content(self, text: str) -> Optional[str]:
        """提取引号内的内容"""
        # 匹配中文引号或英文引号
        match = re.match(r'^["""](.+?)["""]', text)
        if match:
            return match.group(1)
        return None

    def _collect_multiline_content(self, lines: List[str], start_idx: int, initial_content: str) -> str:
        """
        收集可能跨多行的内容

        规则：如果下一行不是新的角色行或标题行，则作为续行内容
        """
        content = initial_content
        i = start_idx + 1

        while i < len(lines):
            line = lines[i].strip()

            # 空行终止
            if not line:
                break

            # 新的角色行终止
            if self._match_ai_line(line)[0] or self._match_student_line(line)[0]:
                break

            # 标题行终止
            if re.match(r'^#{1,3}\s+', line):
                break

            # 数字列表项可能是新的问题，终止
            if re.match(r'^\d+[.、]\s*', line):
                # 但如果是答案中的列表项，继续收集
                if not any(kw in line for kw in ['请', '如何', '为什么', '？', '?']):
                    content += '\n' + line
                    i += 1
                    continue
                break

            # 其他情况，作为续行内容
            content += '\n' + line
            i += 1

        return content

    def parse_file(self, file_path: str) -> ParseResult:
        """
        解析文件

        Args:
            file_path: 文件路径

        Returns:
            ParseResult 对象
        """
        path = Path(file_path)
        if not path.exists():
            result = ParseResult()
            result.warnings.append(f"文件不存在: {file_path}")
            return result

        content = path.read_text(encoding='utf-8')
        return self.parse(content)


class DialogueSampleMatcher:
    """对话样本匹配器"""

    def __init__(
        self,
        pairs: List[DialoguePair],
        similarity_threshold: float = 0.4,
        max_candidates: int = 5,
    ):
        """
        初始化匹配器

        Args:
            pairs: 对话对列表
            similarity_threshold: 相似度阈值，低于此值不返回
            max_candidates: 最多返回的候选数量
        """
        self.pairs = pairs
        self.threshold = similarity_threshold
        self.max_candidates = max_candidates

    def find_candidates(
        self,
        ai_question: str,
        module_filter: Optional[str] = None,
    ) -> List[Tuple[DialoguePair, float]]:
        """
        查找匹配的候选回答

        Args:
            ai_question: 当前 AI 的问题
            module_filter: 可选，只在指定模块中查找

        Returns:
            [(DialoguePair, 相似度), ...] 按相似度降序排列
        """
        if not self.pairs:
            return []

        candidates = self.pairs
        if module_filter:
            # 优先在指定模块中查找
            filtered = [p for p in self.pairs if module_filter in p.module]
            if filtered:
                candidates = filtered

        # 计算相似度
        scored: List[Tuple[DialoguePair, float]] = []
        for pair in candidates:
            similarity = self.calculate_similarity(ai_question, pair.ai_question)
            if similarity >= self.threshold:
                scored.append((pair, similarity))

        # 按相似度降序排列
        scored.sort(key=lambda x: -x[1])

        return scored[:self.max_candidates]

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0

        # 预处理：去除多余空格和换行符
        text1_clean = ' '.join(text1.split())
        text2_clean = ' '.join(text2.split())

        # 使用 difflib 计算相似度
        return difflib.SequenceMatcher(None, text1_clean, text2_clean).ratio()

    def get_best_match(self, ai_question: str) -> Optional[Tuple[DialoguePair, float]]:
        """
        获取最佳匹配

        Args:
            ai_question: AI 问题

        Returns:
            (DialoguePair, 相似度) 或 None
        """
        candidates = self.find_candidates(ai_question)
        if candidates:
            return candidates[0]
        return None


class DialogueSampleIndex:
    """对话样本索引，用于快速查找和交互选择"""

    def __init__(
        self,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        similarity_threshold: float = 0.4,
        max_candidates: int = 5,
    ):
        """
        初始化索引

        Args:
            file_path: 文件路径（与 content 二选一）
            content: 文档内容
            similarity_threshold: 相似度阈值
            max_candidates: 最多返回的候选数量
        """
        self.file_path = file_path
        self.similarity_threshold = similarity_threshold
        self.max_candidates = max_candidates

        self.parser = DialogueSampleParser()
        self.parse_result: Optional[ParseResult] = None
        self.matcher: Optional[DialogueSampleMatcher] = None
        self.loaded = False

        # 加载内容
        if file_path:
            self.load_file(file_path)
        elif content:
            self.load_content(content)

    def load_file(self, file_path: str) -> bool:
        """加载文件"""
        self.file_path = file_path
        self.parse_result = self.parser.parse_file(file_path)
        return self._finalize_load()

    def load_content(self, content: str) -> bool:
        """加载内容"""
        self.parse_result = self.parser.parse(content)
        return self._finalize_load()

    def _finalize_load(self) -> bool:
        """完成加载"""
        if not self.parse_result or not self.parse_result.pairs:
            print("⚠️  未解析到有效的对话对")
            self.loaded = False
            return False

        self.matcher = DialogueSampleMatcher(
            self.parse_result.pairs,
            similarity_threshold=self.similarity_threshold,
            max_candidates=self.max_candidates,
        )
        self.loaded = True

        # 打印解析结果摘要
        print(f"✅ 解析完成，共 {len(self.parse_result.pairs)} 个对话对")
        if self.parse_result.detected_ai_pattern:
            print(f"   AI 角色标识: {self.parse_result.detected_ai_pattern}")
        if self.parse_result.detected_student_pattern:
            print(f"   学生角色标识: {self.parse_result.detected_student_pattern}")
        if self.parse_result.modules:
            print(f"   模块: {', '.join(self.parse_result.modules[:3])}{'...' if len(self.parse_result.modules) > 3 else ''}")
        if self.parse_result.warnings:
            for warn in self.parse_result.warnings:
                print(f"   ⚠️  {warn}")

        return True

    def find_candidates(self, ai_question: str) -> List[Tuple[DialoguePair, float]]:
        """查找候选回答"""
        if not self.loaded or not self.matcher:
            return []
        return self.matcher.find_candidates(ai_question)

    def format_candidates_for_display(
        self,
        candidates: List[Tuple[DialoguePair, float]],
        max_answer_len: int = 60,
    ) -> str:
        """
        格式化候选回答用于终端显示

        Args:
            candidates: 候选列表
            max_answer_len: 回答最大显示长度

        Returns:
            格式化的字符串
        """
        if not candidates:
            return ""

        lines = ["🎯 找到相似的预设回答："]
        for i, (pair, score) in enumerate(candidates, 1):
            answer = pair.student_answer
            if len(answer) > max_answer_len:
                answer = answer[:max_answer_len] + "..."

            # 单行显示，包含来源信息
            source_hint = ""
            if pair.ai_role_hint:
                source_hint = f" [{pair.ai_role_hint}]"
            elif pair.module:
                # 提取模块名称的简短版本
                short_module = pair.module.split('：')[-1] if '：' in pair.module else pair.module
                if len(short_module) > 15:
                    short_module = short_module[:15] + "..."
                source_hint = f" [{short_module}]"

            lines.append(f"  [{i}] {answer} (相似度: {score:.2f}){source_hint}")

        return '\n'.join(lines)

    def interactive_select(
        self,
        ai_question: str,
        show_ai_question: bool = False,
    ) -> Optional[str]:
        """
        交互式选择候选回答

        Args:
            ai_question: AI 问题
            show_ai_question: 是否显示匹配的 AI 问题

        Returns:
            选中的回答，或 None 表示用户跳过
        """
        candidates = self.find_candidates(ai_question)

        if not candidates:
            return None

        # 显示候选
        print(self.format_candidates_for_display(candidates))

        if show_ai_question:
            print("\n匹配的原始问题：")
            for i, (pair, _) in enumerate(candidates, 1):
                q = pair.ai_question[:80] + "..." if len(pair.ai_question) > 80 else pair.ai_question
                print(f"  [{i}] {q}")

        print()

        # 等待用户选择
        while True:
            choice = input("选择预设回答 (数字) 或直接回车跳过: ").strip()

            if not choice:
                return None

            try:
                idx = int(choice)
                if 1 <= idx <= len(candidates):
                    return candidates[idx - 1][0].student_answer
                else:
                    print(f"⚠️  请输入 1-{len(candidates)} 之间的数字")
            except ValueError:
                # 不是数字，可能是用户想直接输入回答
                return None


# 便捷函数
def parse_dialogue_file(file_path: str) -> ParseResult:
    """解析对话文件的便捷函数"""
    parser = DialogueSampleParser()
    return parser.parse_file(file_path)


def create_dialogue_index(
    file_path: Optional[str] = None,
    content: Optional[str] = None,
    **kwargs
) -> DialogueSampleIndex:
    """创建对话索引的便捷函数"""
    return DialogueSampleIndex(file_path=file_path, content=content, **kwargs)


# 测试代码
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python dialogue_sample_parser.py <markdown文件路径>")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"\n📄 解析文件: {file_path}\n")
    print("=" * 60)

    # 解析文件
    index = create_dialogue_index(file_path)

    if not index.loaded:
        print("❌ 解析失败")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("📋 解析到的对话对：\n")

    for i, pair in enumerate(index.parse_result.pairs[:10], 1):
        print(f"{i}. [AI] {pair.ai_question[:60]}...")
        print(f"   [学生] {pair.student_answer[:60]}...")
        if pair.ai_role_hint:
            print(f"   [角色] {pair.ai_role_hint}")
        print()

    if len(index.parse_result.pairs) > 10:
        print(f"... 共 {len(index.parse_result.pairs)} 个对话对\n")

    # 交互测试
    print("=" * 60)
    print("🔍 测试匹配功能（输入问题查找相似回答，输入 quit 退出）\n")

    while True:
        question = input("输入测试问题: ").strip()
        if question.lower() == 'quit':
            break

        candidates = index.find_candidates(question)
        if candidates:
            print(index.format_candidates_for_display(candidates))
        else:
            print("❌ 未找到相似回答")
        print()
