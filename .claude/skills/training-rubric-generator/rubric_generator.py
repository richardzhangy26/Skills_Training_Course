#!/usr/bin/env python3
"""
Training Rubric Generator
生成详细的评价标准，包括评分项、评价要求、正反例
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv


@dataclass
class ScoringLogic:
    """评分逻辑"""
    fullScore: str = ""
    goodScore: str = ""
    mediumScore: str = ""
    lowScore: str = ""
    poorScore: str = ""


@dataclass
class Example:
    """示例"""
    answer: str
    explanation: str


@dataclass
class ScoringItem:
    """评分项"""
    id: str
    name: str
    maxScore: int
    userDescription: str
    aiGuidelines: Dict
    examples: Dict


class RubricGenerator:
    """评价标准生成器"""

    def __init__(self):
        """初始化"""
        load_dotenv()

    def extract_rubric_from_markdown(self, md_content: str) -> Optional[List[Dict]]:
        """
        从markdown文档中提取评价标准表格

        Args:
            md_content: markdown文件内容

        Returns:
            评分项列表，如果未找到则返回None
        """
        # 查找评价标准表格
        lines = md_content.split('\n')
        rubric_start = None

        for i, line in enumerate(lines):
            if '评价标准' in line or '评分' in line:
                # 查找表格开始
                for j in range(i + 1, min(i + 10, len(lines))):
                    if '|' in lines[j]:
                        rubric_start = j
                        break
                if rubric_start:
                    break

        if rubric_start is None:
            return None

        # 解析表格
        items = []
        for i in range(rubric_start + 2, len(lines)):  # 跳过表头和分隔线
            line = lines[i].strip()
            if not line or not line.startswith('|'):
                break

            # 提取表格单元格
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(cells) >= 3:
                items.append({
                    'name': cells[0],
                    'description': cells[1],
                    'maxScore': self._parse_score(cells[2])
                })

        return items if items else None

    def _parse_score(self, score_str: str) -> int:
        """解析分值字符串"""
        match = re.search(r'\d+', score_str)
        return int(match.group()) if match else 5

    def extract_task_info(self, md_content: str) -> Tuple[str, str, str]:
        """
        从markdown文档中提取任务信息

        Args:
            md_content: markdown文件内容

        Returns:
            (任务目标, 任务描述, 评价标准部分)
        """
        lines = md_content.split('\n')
        task_goal = ""
        task_desc = ""
        rubric_section = ""

        current_section = None
        for i, line in enumerate(lines):
            if '任务目标' in line:
                current_section = 'goal'
            elif '任务描述' in line:
                current_section = 'desc'
            elif '评价标准' in line:
                current_section = 'rubric'
            elif line.startswith('#') and current_section:
                current_section = None
            else:
                if current_section == 'goal' and line.strip():
                    task_goal += line + "\n"
                elif current_section == 'desc' and line.strip():
                    task_desc += line + "\n"
                elif current_section == 'rubric' and line.strip():
                    rubric_section += line + "\n"

        return task_goal.strip()[:500], task_desc.strip()[:500], rubric_section.strip()

    def generate_default_rubric(self, task_goal: str, task_desc: str) -> List[Dict]:
        """
        根据任务信息生成默认的评价标准

        Args:
            task_goal: 任务目标
            task_desc: 任务描述

        Returns:
            评分项列表
        """
        # 基于任务类型生成不同的评价标准
        default_rubrics = {
            '离心泵': [
                {'name': '故障识别', 'description': '能否准确识别泵的故障现象', 'maxScore': 3},
                {'name': '原因分析', 'description': '能否正确分析故障产生的根本原因', 'maxScore': 4},
                {'name': '解决方案', 'description': '能否提出合理可行的解决方案', 'maxScore': 3},
            ],
            '精馏': [
                {'name': '原理理解', 'description': '是否理解精馏的基本原理和操作步骤', 'maxScore': 3},
                {'name': '操作规范', 'description': '是否能按照规范进行精馏操作', 'maxScore': 4},
                {'name': '结果分析', 'description': '是否能正确分析和解释实验结果', 'maxScore': 3},
            ],
            '沟通': [
                {'name': '倾听能力', 'description': '是否能有效倾听对方的需求和感受', 'maxScore': 3},
                {'name': '表达清晰', 'description': '是否能清晰、准确地表达自己的观点', 'maxScore': 3},
                {'name': '问题解决', 'description': '是否能通过沟通找到有效的解决方案', 'maxScore': 4},
            ],
            '电力': [
                {'name': '知识掌握', 'description': '是否掌握电力系统的基本知识和概念', 'maxScore': 3},
                {'name': '理论应用', 'description': '是否能将理论知识应用到实际场景', 'maxScore': 4},
                {'name': '分析能力', 'description': '是否能进行深入的分析和推理', 'maxScore': 3},
            ],
            '默认': [
                {'name': '知识理解', 'description': '是否正确理解了核心知识点', 'maxScore': 3},
                {'name': '内容完整', 'description': '是否全面、准确地陈述了相关内容', 'maxScore': 3},
                {'name': '逻辑清晰', 'description': '表述是否逻辑清晰、思路连贯', 'maxScore': 4},
            ],
        }

        # 查找关键词匹配
        combined_text = (task_goal + task_desc).lower()
        for keyword, rubric_template in default_rubrics.items():
            if keyword.lower() in combined_text:
                return rubric_template

        return default_rubrics['默认']

    def enrich_rubric_item(self, item: Dict, task_context: str) -> Dict:
        """
        为评分项增加详细的评判指南和示例

        Args:
            item: 评分项基本信息
            task_context: 任务背景信息

        Returns:
            增强后的评分项
        """
        enriched = {
            'id': f"item_{item.get('id', '')or self._generate_id()}",
            'name': item['name'],
            'maxScore': item.get('maxScore', 5),
            'userDescription': item.get('description', ''),
            'aiGuidelines': {
                'description': self._generate_ai_guideline(
                    item['name'],
                    item.get('description', ''),
                    task_context
                ),
                'keyPoints': self._generate_key_points(item['name']),
                'commonMistakes': self._generate_common_mistakes(item['name']),
                'scoringLogic': self._generate_scoring_logic(item.get('maxScore', 5))
            },
            'examples': {
                'excellent': self._generate_excellent_example(item['name'], task_context),
                'poor': self._generate_poor_examples(item['name'], task_context)
            }
        }
        return enriched

    def _generate_id(self) -> str:
        """生成唯一ID"""
        import random
        return f"{random.randint(1000, 9999)}"

    def _generate_ai_guideline(self, item_name: str, description: str, context: str) -> str:
        """生成大模型评判指南"""
        guidelines = {
            '故障识别': f"评判学生是否能准确识别{description}。需要检查学生是否提到了关键特征、现象表现以及与其他故障的区别。评估学生对现象的观察是否细致、描述是否准确。",
            '原因分析': f"评判学生是否能深入分析{description}。需要检查学生的分析逻辑是否正确、是否考虑了所有相关因素、是否能从表面现象推导到根本原因。",
            '解决方案': f"评判学生是否能提出合理的{description}。需要检查方案的可行性、是否考虑了实际操作的约束条件、是否有循序渐进的步骤。",
            '知识理解': f"评判学生是否正确理解了{description}。需要检查学生能否准确解释核心概念，区分不同概念之间的联系和区别。",
            '知识掌握': f"评判学生是否掌握了{description}。需要检查学生对关键知识点的理解深度，是否能准确陈述，是否理解了知识之间的逻辑关系。",
            '表达清晰': f"评判学生的{description}。需要检查表述是否逻辑清晰、思路是否连贯、是否使用了准确的专业术语、是否避免了模糊和歧义。",
            '默认': f"评判学生在'{item_name}'方面的表现，参考描述为：{description}。需要根据学生的实际表述内容，从准确性、完整性和逻辑性三个维度进行评估。"
        }

        for key, template in guidelines.items():
            if key.lower() in item_name.lower():
                return template

        return guidelines['默认']

    def _generate_key_points(self, item_name: str) -> List[str]:
        """生成关键评判点"""
        key_points = {
            '故障识别': [
                '是否准确描述了故障现象的具体表现',
                '是否识别了关键特征',
                '是否能将现象与故障类型正确关联'
            ],
            '原因分析': [
                '分析逻辑是否清晰和正确',
                '是否考虑了所有相关的因素',
                '是否能够从现象推导到根本原因',
                '是否有理论依据支持分析'
            ],
            '知识掌握': [
                '对核心概念的理解是否准确',
                '是否能准确陈述关键知识点',
                '是否理解了不同知识点之间的逻辑关系',
                '是否能举例说明'
            ],
            '表达清晰': [
                '表述的逻辑顺序是否合理',
                '是否使用了准确的专业术语',
                '是否避免了冗余和重复',
                '是否涵盖了所有必要的信息'
            ],
            '默认': [
                '核心内容是否准确',
                '表述是否完整和清晰',
                '逻辑是否合理和连贯'
            ]
        }

        for key, points in key_points.items():
            if key.lower() in item_name.lower():
                return points

        return key_points['默认']

    def _generate_common_mistakes(self, item_name: str) -> List[str]:
        """生成常见错误"""
        mistakes = {
            '故障识别': [
                '只描述了现象的一个方面，缺少系统性分析',
                '混淆了不同的故障现象',
                '无法准确描述现象的具体表现',
                '凭感觉判断，缺少事实依据'
            ],
            '原因分析': [
                '只停留在现象层面，没有深入分析',
                '分析不够严谨，有逻辑漏洞',
                '忽视了重要的因素',
                '分析方向错误'
            ],
            '知识掌握': [
                '对概念理解不准确，存在混淆',
                '知识点记住了但不理解其含义',
                '无法区分相似的概念',
                '不能用自己的话解释'
            ],
            '表达清晰': [
                '表述不完整，遗漏了关键信息',
                '逻辑混乱，思路不清',
                '使用了不准确的专业术语',
                '表述过于简洁或过于复杂'
            ],
            '默认': [
                '内容不准确或有错误',
                '表述不清晰或不完整',
                '逻辑不清或有矛盾',
                '偏离了主题'
            ]
        }

        for key, items_list in mistakes.items():
            if key.lower() in item_name.lower():
                return items_list

        return mistakes['默认']

    def _generate_scoring_logic(self, max_score: int) -> Dict[str, str]:
        """生成评分逻辑"""
        if max_score == 5:
            return {
                'fullScore': f'{max_score}分：完全满足要求，表述准确、完整、清晰',
                'goodScore': f'{max_score-1}分：基本满足要求，表述基本准确，少量不足',
                'mediumScore': f'{max_score-2}分：部分满足要求，有一定的理解和表述',
                'lowScore': f'{max_score-3}分：不太满足要求，理解或表述有较大不足',
                'poorScore': f'{max_score-4}分：严重不足或完全不满足要求'
            }
        elif max_score == 4:
            return {
                'fullScore': f'{max_score}分：完全满足要求，表述准确、完整、清晰',
                'goodScore': f'{max_score-1}分：基本满足要求，少量表述不足',
                'mediumScore': f'{max_score-2}分：部分满足要求',
                'lowScore': f'1分：不太满足要求',
                'poorScore': f'0分：严重不足或未能满足'
            }
        elif max_score == 3:
            return {
                'fullScore': f'{max_score}分：完全满足要求',
                'goodScore': f'2分：基本满足要求',
                'mediumScore': f'1分：部分满足要求',
                'lowScore': f'0分：不满足要求',
                'poorScore': f'0分：严重不足'
            }
        else:
            return {
                'fullScore': f'{max_score}分：完全满足要求',
                'goodScore': f'{max(1, max_score//2)}分：基本满足要求',
                'mediumScore': f'中等水平',
                'lowScore': f'较低水平',
                'poorScore': f'0分：完全不满足'
            }

    def _generate_excellent_example(self, item_name: str, context: str) -> Dict[str, str]:
        """生成优秀示例"""
        examples = {
            '故障识别': {
                'answer': '泵发出"咔咔"的异常声音，出口压力表指针剧烈波动，这些都是汽蚀的典型特征。与其他故障（如密封泄漏）不同，汽蚀会产生气泡坍塌的冲击噪音。',
                'explanation': '此回答准确指出了多个关键特征（声音、压力波动），能够与其他故障区分，证明学生对故障现象有深入的理解。'
            },
            '原因分析': {
                'answer': '汽蚀发生是因为进口处液体压力低于其饱和蒸汽压，导致液体在泵进口处汽化。这可能是因为吸入管路堵塞、液面过低或吸入阀未完全打开导致进口压力不足。',
                'explanation': '此回答从热力学原理出发，准确解释了汽蚀的根本原因，并列举了可能导致进口压力不足的具体因素，展现了深层的因果分析能力。'
            },
            '知识掌握': {
                'answer': '电力系统由发电、输电、变电、配电和用电五个环节组成。发电厂将原始能量转化为电能，不同类型的发电厂工作原理不同，如火电厂通过燃烧煤炭产生蒸汽驱动汽轮机。',
                'explanation': '此回答系统地阐述了电力系统的基本结构，能够准确列举核心概念，并能用具体例子说明，表明学生对知识有完整的理解。'
            },
            '表达清晰': {
                'answer': '故障排查的步骤包括：第一，观察现象并记录；第二，初步判断可能的故障类型；第三，制定检修方案；第四，实施检修；第五，验证效果。',
                'explanation': '此回答结构清晰，使用了编号列表，逻辑关系明确，每一步都阐述了要点，便于理解和记忆。'
            },
            '默认': {
                'answer': '学生准确理解了核心概念，能够清晰地表述要点，逻辑清晰，论证严密，使用了恰当的专业术语。',
                'explanation': '此回答体现了深入的理解和优秀的表达能力。'
            }
        }

        for key, example in examples.items():
            if key.lower() in item_name.lower():
                return example

        return examples['默认']

    def _generate_poor_examples(self, item_name: str, context: str) -> List[Dict[str, str]]:
        """生成不足示例"""
        examples = {
            '故障识别': [
                {
                    'answer': '泵声音不对，肯定是坏了。',
                    'explanation': '描述过于笼统，没有具体说明是什么声音，缺少诊断依据和特征描述。'
                },
                {
                    'answer': '应该是密封圈坏了，因为有声音。',
                    'explanation': '混淆了不同的故障类型，用错误的故障解释现象，证明对故障特征的理解不足。'
                }
            ],
            '原因分析': [
                {
                    'answer': '泵坏了所以就出现故障了。',
                    'explanation': '分析过于简单且循环论证，没有提供实际的原因分析，逻辑严重不足。'
                },
                {
                    'answer': '可能是很多原因，比如操作不当、设备老化等。',
                    'explanation': '列举了太多泛化的原因，但没有针对具体现象做出深入分析，缺乏逻辑严密性。'
                }
            ],
            '知识掌握': [
                {
                    'answer': '电力系统很重要，我们要学好。',
                    'explanation': '没有具体的知识内容，无法判断学生是否真正掌握了核心概念。'
                },
                {
                    'answer': '有发电厂和变电站，发电的和改变的。',
                    'explanation': '虽然提到了组件，但描述不准确，"改变的"表述不专业，说明对概念理解不深。'
                }
            ],
            '表达清晰': [
                {
                    'answer': '故障排查就是看看有什么问题然后修，这样就行了。',
                    'explanation': '表述过于简化，遗漏了重要步骤，逻辑不够严密，不够专业。'
                },
                {
                    'answer': '可能是这个或者那个或者另外一个，反正要仔细检查。',
                    'explanation': '模糊不清，思路混乱，没有提供明确的指导或逻辑框架。'
                }
            ],
            '默认': [
                {
                    'answer': '不太清楚，可能是这样吧。',
                    'explanation': '缺乏确定性，表述不清晰，无法判断学生是否真正掌握。'
                },
                {
                    'answer': '这个我不太了解。',
                    'explanation': '完全没有尝试回答，无法评估学生的理解水平。'
                }
            ]
        }

        for key, examples_list in examples.items():
            if key.lower() in item_name.lower():
                return examples_list

        return examples['默认']

    def process(self, md_content: str, doc_path: str, output_dir: Optional[str] = None) -> Tuple[Dict, str]:
        """
        完整处理流程

        Args:
            md_content: markdown文件内容
            doc_path: 文档路径
            output_dir: 输出目录（如果为None，则自动创建）

        Returns:
            (配置字典, 输出目录路径)
        """
        print("📖 分析任务文档...")

        # 提取任务信息
        task_goal, task_desc, existing_rubric = self.extract_task_info(md_content)
        print(f"   ✓ 任务目标提取完成")
        print(f"   ✓ 任务描述提取完成")

        # 尝试从文档中提取评价标准
        print("\n🔍 查找文档中的评价标准...")
        rubric_items = self.extract_rubric_from_markdown(md_content)

        if rubric_items:
            print(f"   ✓ 从文档中提取了 {len(rubric_items)} 个评分项")
            generation_method = 'extracted'
        else:
            print("   ℹ  文档中未找到评价标准，自动生成...")
            rubric_items = self.generate_default_rubric(task_goal, task_desc)
            print(f"   ✓ 自动生成了 {len(rubric_items)} 个评分项")
            generation_method = 'generated'

        # 为每个评分项增强信息
        print("\n📝 生成详细的评判指南和示例...")
        context = f"{task_goal}\n{task_desc}"
        enriched_items = []
        for item in rubric_items:
            enriched = self.enrich_rubric_item(item, context)
            enriched_items.append(enriched)
            print(f"   ✓ 完成：{item['name']}")

        # 计算总分
        total_score = sum(item.get('maxScore', 5) for item in rubric_items)

        # 创建输出目录
        if output_dir is None:
            # 自动创建以任务名称命名的目录
            doc_dir = Path(doc_path).parent
            # 从文档名称提取任务名
            task_name = Path(doc_path).stem
            task_name = task_name.replace("实训任务文档", "").replace("实训任务-", "").strip()
            if task_name.startswith("-"):
                task_name = task_name[1:].strip()
            output_dir = doc_dir / task_name
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 输出目录: {output_dir}")

        # 创建配置结构
        config = {
            'rubricName': '训练评价标准',
            'totalScore': total_score,
            'description': f'针对"{Path(doc_path).stem}"的详细评价标准',
            'scoringItems': enriched_items,
            'metadata': {
                'createdAt': datetime.now().isoformat() + 'Z',
                'source': str(doc_path),
                'generationMethod': generation_method
            }
        }

        # 保存JSON配置
        config_path = output_dir / "评价标准.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"   ✓ 配置已保存: {config_path}")

        # 生成Markdown版本
        md_path = output_dir / "评价标准.md"
        self._save_markdown_version(config, md_path)
        print(f"   ✓ Markdown已保存: {md_path}")

        return config, str(output_dir)

    def _save_markdown_version(self, config: Dict, md_path: Path):
        """保存Markdown格式的评价标准"""
        md_content = f"""# {config['rubricName']}

**总满分**: {config['totalScore']} 分
**生成时间**: {config['metadata']['createdAt']}
**生成方式**: {'从文档提取' if config['metadata']['generationMethod'] == 'extracted' else '自动生成'}

---

## 评分项汇总

| 评分项 | 满分 | 说明 |
|------|------|------|
"""
        for item in config['scoringItems']:
            md_content += f"| {item['name']} | {item['maxScore']}分 | {item['userDescription'][:50]}... |\n"

        md_content += "\n---\n\n"

        # 详细的评分项说明
        for i, item in enumerate(config['scoringItems'], 1):
            md_content += f"""## 评分项 {i}: {item['name']}

**满分值**: {item['maxScore']} 分

### 评价描述
{item['userDescription']}

### 大模型评判参考

{item['aiGuidelines']['description']}

#### 关键评判点
"""
            for point in item['aiGuidelines']['keyPoints']:
                md_content += f"- {point}\n"

            md_content += "\n#### 常见错误\n"
            for mistake in item['aiGuidelines']['commonMistakes']:
                md_content += f"- {mistake}\n"

            md_content += "\n#### 评分逻辑\n"
            for score_level, description in item['aiGuidelines']['scoringLogic'].items():
                md_content += f"- **{score_level}**: {description}\n"

            md_content += f"""
### 示例

#### 优秀示例
**回答**: {item['examples']['excellent']['answer']}

**说明**: {item['examples']['excellent']['explanation']}

#### 不足示例
"""
            for j, poor_example in enumerate(item['examples']['poor'], 1):
                md_content += f"""
**示例 {j}**
**回答**: {poor_example['answer']}

**问题**: {poor_example['explanation']}
"""

            md_content += "\n---\n\n"

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)


def main():
    """CLI入口"""
    if len(sys.argv) < 2:
        print("使用方法: python rubric_generator.py <markdown_file_path>")
        sys.exit(1)

    md_path = sys.argv[1]

    # 读取markdown文件
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在: {md_path}")
        sys.exit(1)

    # 处理
    try:
        generator = RubricGenerator()
        config, output_dir = generator.process(md_content, md_path)

        print("\n✨ 成功完成!")
        print(f"\n📋 生成的评价标准:")
        print(f"   总分: {config['totalScore']} 分")
        print(f"   评分项数: {len(config['scoringItems'])}")
        for item in config['scoringItems']:
            print(f"   - {item['name']}: {item['maxScore']} 分")
        print(f"\n📂 输出目录: {output_dir}")

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
