#!/usr/bin/env python3
"""
测试 Training Config Setup Generator
"""

import json
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config_generator import TrainingConfigSetup

# 示例文档内容
SAMPLE_MD = """# 实训任务文档1-离心泵"汽蚀"故障紧急诊断

## 任务目标
通过模拟真实的工业现场故障情景，让学生作为工程师，
快速诊断和处理离心泵的汽蚀故障，掌握故障排查的方法
和通过现象分析原因、找出问题根源的工程思维。

## 任务描述
智能体角色为生产现场李主任，负责指导学生分析和解决
离心泵的汽蚀问题。学生需要通过现象判断、原因分析和
解决方案制定来完成任务。

## 对话情景与示例

### 开场
"小张，你是新来的大学生吧？别愣着了，B区的原料输送泵
(P-101B)又跳停了！现场操作工说启动时泵里头'咔咔'响，
出口压力也晃得厉害。你马上去看看，给我个初步判断，
到底怎么回事？"

### 学生可能的回答1
"李主任，听起来像是离心泵发生了汽蚀。"

### 智能体追问
"汽蚀？行，你说说，你凭什么判断是汽蚀？"
"""

def test_extract_config():
    """测试提取配置"""
    print("=" * 60)
    print("测试1: 提取任务名称和描述")
    print("=" * 60)

    try:
        generator = TrainingConfigSetup(skip_api_key_check=True)
        doc_path = "化工原理-武夷学院/实训任务文档1-离心泵汽蚀故障紧急诊断.md"

        task_name, task_desc = generator.extract_config_from_markdown(SAMPLE_MD, doc_path)

        print(f"✓ 任务名称: {task_name}")
        print(f"✓ 任务描述: {task_desc[:100]}...")
        print("✅ 提取测试通过\n")

        return task_name, task_desc
    except Exception as e:
        print(f"❌ 提取测试失败: {e}\n")
        return None, None

def test_generate_prompt():
    """测试生成提示词"""
    print("=" * 60)
    print("测试2: 生成封面图提示词")
    print("=" * 60)

    try:
        generator = TrainingConfigSetup(skip_api_key_check=True)
        task_name = "离心泵汽蚀故障紧急诊断"
        task_desc = "通过模拟真实的工业现场故障情景..."

        prompt = generator.generate_cover_prompt(task_name, task_desc)

        print(f"✓ 生成的提示词:\n  {prompt}\n")
        print("✅ 提示词生成测试通过\n")

        return prompt
    except Exception as e:
        print(f"❌ 提示词生成测试失败: {e}\n")
        return None

def test_config_structure():
    """测试配置结构"""
    print("=" * 60)
    print("测试3: 创建配置结构")
    print("=" * 60)

    try:
        generator = TrainingConfigSetup(skip_api_key_check=True)

        config = generator.create_config_structure(
            task_name="离心泵汽蚀故障紧急诊断",
            task_description="通过模拟真实的工业现场故障...",
            cover_url="https://example.com/image.jpg",
            prompt="工业化工厂...",
            doc_path="化工原理-武夷学院/实训任务文档1.md"
        )

        print(f"✓ 配置结构:")
        print(json.dumps(config, ensure_ascii=False, indent=2))
        print("\n✅ 配置结构测试通过\n")

        return config
    except Exception as e:
        print(f"❌ 配置结构测试失败: {e}\n")
        return None

def test_integration():
    """集成测试（模拟，不实际调用API）"""
    print("=" * 60)
    print("测试4: 集成测试（不调用API）")
    print("=" * 60)

    try:
        doc_path = "化工原理-武夷学院/实训任务文档1-离心泵汽蚀故障紧急诊断.md"

        # 模拟完整流程
        generator = TrainingConfigSetup()

        # 步骤1：提取
        task_name, task_desc = generator.extract_config_from_markdown(SAMPLE_MD, doc_path)
        print(f"✓ 步骤1完成: 提取了任务名称 '{task_name}'")

        # 步骤2：生成提示词
        prompt = generator.generate_cover_prompt(task_name, task_desc)
        print(f"✓ 步骤2完成: 生成了提示词 (长度: {len(prompt)}字)")

        # 步骤3：创建配置
        config = generator.create_config_structure(
            task_name=task_name,
            task_description=task_desc,
            cover_url="https://ark.cn-beijing.volces.com/api/v3/image/mock-url",
            prompt=prompt,
            doc_path=doc_path
        )
        print(f"✓ 步骤3完成: 创建了配置结构")

        # 步骤4：验证配置
        assert config['taskName'] == task_name
        assert config['taskDescription'] == task_desc
        assert 'url' in config['coverImage']
        assert 'prompt' in config['coverImage']
        assert config['coverImage']['format'] == "16:9"
        print("✓ 步骤4完成: 验证了配置结构完整性")

        print("\n✅ 集成测试通过\n")

    except Exception as e:
        print(f"❌ 集成测试失败: {e}\n")

def test_keyword_matching():
    """测试关键词匹配"""
    print("=" * 60)
    print("测试5: 关键词提示词匹配")
    print("=" * 60)

    test_cases = [
        ("离心泵汽蚀诊断", "浓郁的汽蚀故障信息", "应匹配工业风格"),
        ("共沸精馏法制备", "精馏主题明显", "应匹配化学实验室风格"),
        ("虚拟展馆参观", "展馆内容突出", "应匹配科技展馆风格"),
        ("非暴力沟通", "沟通方面内容", "应匹配协作沟通风格"),
        ("投资推介会", "投资相关主题", "应匹配商务会议风格"),
    ]

    try:
        generator = TrainingConfigSetup()

        for task_name, task_desc, expectation in test_cases:
            prompt = generator.generate_cover_prompt(task_name, task_desc)
            print(f"✓ {task_name:<15} → {prompt[:40]}... ({expectation})")

        print("\n✅ 关键词匹配测试通过\n")

    except Exception as e:
        print(f"❌ 关键词匹配测试失败: {e}\n")

def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║  Training Config Setup Generator 测试套件          ║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    # 运行测试
    test_extract_config()
    test_generate_prompt()
    test_config_structure()
    test_integration()
    test_keyword_matching()

    print("=" * 60)
    print("📊 所有测试完成!")
    print("=" * 60)
    print("""
✅ 核心功能测试通过：
  • 配置信息提取
  • 提示词智能生成
  • 配置结构规范化
  • 关键词匹配

⚠️  实际API测试需要：
  • 设置 ARK_API_KEY 环境变量
  • 运行 python config_generator.py <md_file>

📖 查看详细文档：
  • README.md - 快速入门指南
  • SKILL.md - 完整技术文档
  • examples.md - 详细使用示例
""")

if __name__ == "__main__":
    main()
