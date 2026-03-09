#!/usr/bin/env python3
"""
分场景剧本生成工具

将多案例的训练剧本配置拆分为独立的单案例配置文件。

使用方法:
    python split_scenario_script.py <markdown_file_path>

示例:
    python split_scenario_script.py \
        /path/to/训练剧本配置.md
"""

import sys
import re
import os
from pathlib import Path
from typing import List, Dict, Tuple


# 案例定义：从原始剧本中提取的案例列表
SCENARIOS = [
    {
        "name": "云南哈尼梯田文化景观",
        "short_name": "哈尼梯田",
        "key_feature": "强调'森林-村庄-梯田-河流'四素同构的水循环系统",
        "example_prompt": "比如，哈尼梯田的'四素同构'水循环系统是如何体现人与自然协作的？"
    },
    {
        "name": "云南景迈山古茶林文化景观",
        "short_name": "景迈山古茶林",
        "key_feature": "强调人与古茶树的千年共生关系",
        "example_prompt": "比如，景迈山古茶林中，人与古茶树的共生关系是如何维系千年而不衰的？"
    },
    {
        "name": "法国勃艮第气候葡萄园景观",
        "short_name": "勃艮第葡萄园",
        "key_feature": "强调气候与土壤的'风土'概念",
        "example_prompt": "比如，勃艮第葡萄园的'风土'概念如何体现人对自然条件的精准适应与利用？"
    },
    {
        "name": "江西景德镇瓷业文化景观",
        "short_name": "景德镇瓷业",
        "key_feature": "强调瓷业生产与自然资源（高岭土、窑火）的紧密结合",
        "example_prompt": "比如，景德镇瓷业生产中，高岭土开采、水运系统与窑火技术如何构成完整的文化景观？"
    }
]


def read_markdown_file(file_path: str) -> str:
    """读取markdown文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_stages(content: str) -> List[Dict]:
    """
    解析剧本配置，提取各个阶段
    返回阶段列表，每个阶段包含名称、开场白、提示词等
    """
    stages = []

    # 使用正则表达式匹配阶段
    stage_pattern = r'### 阶段\d+:[^\n]+\n'
    stage_matches = list(re.finditer(stage_pattern, content))

    for i, match in enumerate(stage_matches):
        stage_start = match.start()
        stage_end = stage_matches[i + 1].start() if i + 1 < len(stage_matches) else len(content)
        stage_content = content[stage_start:stage_end]

        # 提取阶段名称
        stage_name_match = re.search(r'### (阶段\d+:[^\n]+)', stage_content)
        stage_name = stage_name_match.group(1) if stage_name_match else f"阶段{i+1}"

        # 提取阶段标题（去掉"阶段X:"前缀）
        stage_title = re.sub(r'阶段\d+:\s*', '', stage_name)

        # 提取各字段
        fields = {}

        # 虚拟训练官名字
        name_match = re.search(r'\*\*虚拟训练官名字\*\*:\s*([^\n]+)', stage_content)
        fields['trainer_name'] = name_match.group(1).strip() if name_match else "张老师"

        # 模型
        model_match = re.search(r'\*\*模型\*\*:\s*([^\n]+)', stage_content)
        fields['model'] = model_match.group(1).strip() if model_match else "(选填，默认为空)"

        # 声音
        voice_match = re.search(r'\*\*声音\*\*:\s*([^\n]+)', stage_content)
        fields['voice'] = voice_match.group(1).strip() if voice_match else "(选填，默认为空)"

        # 形象
        avatar_match = re.search(r'\*\*形象\*\*:\s*([^\n]+)', stage_content)
        fields['avatar'] = avatar_match.group(1).strip() if avatar_match else "(选填，默认为空)"

        # 阶段描述
        desc_match = re.search(r'\*\*阶段描述\*\*:\s*([^\n]+)', stage_content)
        fields['description'] = desc_match.group(1).strip() if desc_match else ""

        # 背景图
        bg_match = re.search(r'\*\*背景图\*\*:\s*([^\n]+)', stage_content)
        fields['background'] = bg_match.group(1).strip() if bg_match else "(选填，默认为空)"

        # 互动轮次
        rounds_match = re.search(r'\*\*互动轮次\*\*:\s*(\d+)轮', stage_content)
        fields['rounds'] = rounds_match.group(1) if rounds_match else "3"

        # flowCondition
        flow_match = re.search(r'\*\*flowCondition\*\*:\s*"([^"]+)"', stage_content)
        fields['flow_condition'] = flow_match.group(1) if flow_match else None

        # transitionPrompt
        trans_match = re.search(r'\*\*transitionPrompt\*\*:\s*```\n([\s\S]*?)```', stage_content)
        fields['transition_prompt'] = trans_match.group(1).strip() if trans_match else ""

        # 开场白
        opening_match = re.search(r'\*\*开场白\*\*:\s*```\n([\s\S]*?)```', stage_content)
        fields['opening'] = opening_match.group(1).strip() if opening_match else ""

        # 提示词
        prompt_match = re.search(r'\*\*提示词\*\*:\s*```markdown\n([\s\S]*?)```', stage_content)
        fields['prompt'] = prompt_match.group(1).strip() if prompt_match else ""

        stages.append({
            'name': stage_name,
            'title': stage_title,
            **fields
        })

    return stages


def generate_stage1_for_scenario(scenario: Dict, base_stage: Dict) -> str:
    """为特定案例生成阶段1内容（移除选择环节，直接针对特定案例开场）"""

    # 新的开场白
    new_opening = f"""同学，你好！欢迎来到风景园林遗产保护与管理实训。我是张老师。

本次实训，我们将以【{scenario['short_name']}】为研究对象，深入探索这处世界文化遗产，完成从价值认知到保护策略拟定的全流程训练。

你对{scenario['short_name']}有什么初步的了解或印象吗？"""

    # 修改提示词
    prompt = base_stage['prompt']

    # 替换Context & Task部分
    old_context = "当前处于【场景导入与案例选择阶段】。学生需要从给定的四个典型乡村文化景观案例中选择一个，并简要说明选择理由。本阶段目标是帮助学生快速激活背景知识，建立初步的研究对象认知。"
    new_context = f"当前处于【场景导入阶段】。本次实训以【{scenario['short_name']}】为固定研究对象，学生需要确认进入该案例的学习，并简要谈谈对该案例的初步印象或了解。本阶段目标是帮助学生快速激活背景知识，建立初步的研究对象认知。"
    prompt = prompt.replace(old_context, new_context)

    # 替换Opening Line
    old_opening_line = f'"同学，你好！欢迎来到风景园林遗产保护与管理实训。我是张老师，今天我们将一起深入一个真实的乡村文化景观案例，完成从价值认知到保护策略拟定的全流程训练。本次实训，请从以下典型案例中选择一处：①云南哈尼梯田 ②云南景迈山古茶林 ③法国勃艮第葡萄园 ④江西景德镇瓷业文化景观。请告诉我你的选择，并简单说说理由。"'
    new_opening_line = f'"同学，你好！欢迎来到风景园林遗产保护与管理实训。我是张老师。本次实训，我们将以【{scenario['short_name']}】为研究对象，深入探索这处世界文化遗产，完成从价值认知到保护策略拟定的全流程训练。你对{scenario['short_name']}有什么初步的了解或印象吗？"'
    prompt = prompt.replace(old_opening_line, new_opening_line)

    # 修改通过条件 - 直接替换完整的条件行
    old_condition = "学生明确说出了要选择的案例名称，并给出了任何形式的选择理由（哪怕简短）"
    new_condition = f"学生确认进入{scenario['short_name']}案例学习，并给出了对该案例的初步印象或了解（哪怕简短）"
    prompt = prompt.replace(old_condition, new_condition)

    # 修改引导话术
    old_guide = '给予简要引导，帮助学生快速做出选择，不需要过度纠缠于理由质量。\n   - 话术示例："没关系，你可以先选一个你相对熟悉或感兴趣的。比如说，你听说过哈尼梯田或景迈山吗？对哪个印象更深一些？"'
    new_guide = f'给予简要引导，帮助学生进入案例学习状态，不需要过度纠缠于前期了解深度。\n   - 话术示例："没关系，我们可以从基础开始。你听说过{scenario['short_name']}吗？或者你对世界遗产这类文化景观有什么好奇的地方？"'
    prompt = prompt.replace(old_guide, new_guide)

    # 生成阶段内容
    flow_condition_line = f'\n**flowCondition**: "{base_stage["flow_condition"]}"' if base_stage.get('flow_condition') else ''
    transition_section = f'''\n**transitionPrompt**:
```
{base_stage['transition_prompt']}
```''' if base_stage.get('transition_prompt') else ''

    return f"""### 阶段1: 场景导入与{scenario['short_name']}案例

**虚拟训练官名字**: {base_stage['trainer_name']}

**模型**: {base_stage['model']}

**声音**: {base_stage['voice']}

**形象**: {base_stage['avatar']}

**阶段描述**: 张老师介绍本次实训背景，以【{scenario['short_name']}】为研究对象，初步激活学生对"人与自然共同作品"这一文化景观核心特征的认知。

**背景图**: {base_stage['background']}

**互动轮次**: {base_stage['rounds']}轮{flow_condition_line}{transition_section}

**开场白**:
```
{new_opening}
```

**提示词**:
```markdown
{prompt}
```
"""


def generate_stage2_for_scenario(scenario: Dict, base_stage: Dict) -> str:
    """为特定案例生成阶段2内容（替换占位符并添加案例特定引导）"""

    # 替换开场白中的占位符
    new_opening = base_stage['opening'].replace('[学生选定的案例]', f"【{scenario['short_name']}】")

    # 修改提示词
    prompt = base_stage['prompt']

    # 替换Opening Line中的占位符
    old_opening_line = '"好，你选择了这处文化景观，我们先从最核心的问题入手'
    new_opening_line = f'"好，我们今天研究【{scenario['short_name']}】，先从最核心的问题入手'
    prompt = prompt.replace(old_opening_line, new_opening_line)

    # 在Workflow中添加案例特定的引导示例
    old_example = "梯田（或茶园/葡萄园）"
    new_example = scenario['short_name']
    prompt = prompt.replace(old_example, new_example)

    # 添加案例特定的示例到话术示例中
    old_phrase = "话术示例：\"你对人与自然的互动关系分析得不错"
    new_phrase = f"话术示例：\"你对{scenario['short_name']}人与自然的互动关系分析得不错"
    prompt = prompt.replace(old_phrase, new_phrase)

    # 更新阶段描述
    new_description = base_stage['description'].replace('学生选定的案例', scenario['short_name'])

    # 生成阶段内容
    flow_condition_line = f'\n**flowCondition**: "{base_stage["flow_condition"]}"' if base_stage.get('flow_condition') else ''
    transition_section = f'''\n**transitionPrompt**:
```
{base_stage['transition_prompt']}
```''' if base_stage.get('transition_prompt') else ''

    return f"""### 阶段2: 核心认知——文化景观本质特征

**虚拟训练官名字**: {base_stage['trainer_name']}

**模型**: {base_stage['model']}

**声音**: {base_stage['voice']}

**形象**: {base_stage['avatar']}

**阶段描述**: {new_description}

**背景图**: {base_stage['background']}

**互动轮次**: {base_stage['rounds']}轮{flow_condition_line}{transition_section}

**开场白**:
```
{new_opening}
```

**提示词**:
```markdown
{prompt}
```
"""


def generate_generic_stage_for_scenario(stage_num: int, scenario: Dict, base_stage: Dict) -> str:
    """为特定案例生成通用阶段内容（阶段3-6，替换占位符）"""

    # 替换开场白中的占位符
    new_opening = base_stage['opening'].replace('[学生选定的案例]', scenario['short_name'])

    # 修改提示词
    prompt = base_stage['prompt']

    # 更新阶段描述（如果包含占位符）
    new_description = base_stage['description'].replace('学生选定的案例', scenario['short_name'])

    # 阶段3-6特定替换
    if stage_num == 3:
        # 阶段3：价值凝练
        old_phrase = "这处案例最核心的3项价值主张"
        new_phrase = f"【{scenario['short_name']}】最核心的3项价值主张"
        prompt = prompt.replace(old_phrase, new_phrase)
    elif stage_num == 4:
        # 阶段4：要素识别
        pass  # 主要逻辑在提示词中已经通用
    elif stage_num == 5:
        # 阶段5：保护策略
        pass  # 主要逻辑在提示词中已经通用

    # 生成阶段内容
    flow_condition_line = f'\n**flowCondition**: "{base_stage["flow_condition"]}"' if base_stage.get('flow_condition') else ''
    transition_section = f'''\n**transitionPrompt**:
```
{base_stage['transition_prompt']}
```''' if base_stage.get('transition_prompt') else ''

    return f"""### {base_stage['name']}

**虚拟训练官名字**: {base_stage['trainer_name']}

**模型**: {base_stage['model']}

**声音**: {base_stage['voice']}

**形象**: {base_stage['avatar']}

**阶段描述**: {new_description}

**背景图**: {base_stage['background']}

**互动轮次**: {base_stage['rounds']}轮{flow_condition_line}{transition_section}

**开场白**:
```
{new_opening}
```

**提示词**:
```markdown
{prompt}
```
"""


def generate_scenario_markdown(scenario: Dict, stages: List[Dict], base_content: str) -> str:
    """为特定案例生成完整的markdown配置"""

    # 提取基础配置部分（从文件开头到第一个阶段）
    base_config_match = re.search(r'^(# .+?)### 阶段1:', base_content, re.DOTALL)
    base_config = base_config_match.group(1) if base_config_match else ""

    # 更新任务名称和描述
    base_config = base_config.replace(
        "乡村文化景观遗产保护管理实训",
        f"{scenario['short_name']}遗产保护管理实训"
    )
    base_config = base_config.replace(
        "引导学生围绕典型乡村文化景观案例",
        f"引导学生围绕【{scenario['short_name']}】案例"
    )

    # 生成各阶段内容
    stage_contents = []

    for i, stage in enumerate(stages):
        stage_num = i + 1

        if stage_num == 1:
            stage_content = generate_stage1_for_scenario(scenario, stage)
        elif stage_num == 2:
            stage_content = generate_stage2_for_scenario(scenario, stage)
        else:
            stage_content = generate_generic_stage_for_scenario(stage_num, scenario, stage)

        stage_contents.append(stage_content)

    # 提取阶段跳转关系和配置说明
    jump_section_match = re.search(r'## 🔄 阶段跳转关系.+', base_content, re.DOTALL)
    jump_section = jump_section_match.group(0) if jump_section_match else ""

    # 修改阶段跳转关系中的阶段1描述
    jump_section = jump_section.replace(
        "学生明确选定案例并给出理由 → 跳转关键词",
        f"学生确认进入{scenario['short_name']}案例学习并给出初步印象 → 跳转关键词"
    )

    # 修改使用建议中的案例特定说明
    jump_section = jump_section.replace(
        '哈尼梯田强调"四素同构"水循环系统；景迈山强调人与古茶树共生；勃艮第侧重气候与土壤的"风土"概念',
        scenario['key_feature']
    )

    # 组合完整内容
    full_content = base_config + "\n" + "\n---\n\n".join(stage_contents) + "\n\n---\n\n" + jump_section

    return full_content


def get_safe_filename(name: str) -> str:
    """将案例名称转换为安全的文件名"""
    # 移除省份前缀
    name = re.sub(r'^云南|^法国|^江西', '', name)
    # 移除"文化景观"等后缀
    name = re.sub(r'文化景观$|景观$', '', name)
    return name.strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python split_scenario_script.py <markdown_file_path>")
        print("\nExample:")
        print("    python split_scenario_script.py /path/to/训练剧本配置.md")
        sys.exit(1)

    input_file = sys.argv[1]

    # 检查输入文件
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    print(f"正在读取原始剧本配置: {input_file}")

    # 读取文件内容
    content = read_markdown_file(input_file)

    # 解析各阶段
    stages = parse_stages(content)

    if len(stages) < 6:
        print(f"Warning: Expected 6 stages, found {len(stages)}")

    print(f"成功解析 {len(stages)} 个阶段")

    # 确定输出目录
    input_path = Path(input_file)
    output_dir = input_path.parent / "split_scenarios"
    output_dir.mkdir(exist_ok=True)

    print(f"\n输出目录: {output_dir}")
    print("=" * 60)

    # 为每个案例生成独立的配置文件
    generated_files = []

    for scenario in SCENARIOS:
        print(f"\n正在生成: {scenario['name']}")

        # 生成markdown内容
        markdown_content = generate_scenario_markdown(scenario, stages, content)

        # 确定输出文件名
        safe_name = get_safe_filename(scenario['short_name'])
        output_file = output_dir / f"训练剧本配置_{safe_name}.md"

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        generated_files.append(output_file)
        print(f"  ✓ 已生成: {output_file.name}")

    print("\n" + "=" * 60)
    print(f"\n生成完成！共生成 {len(generated_files)} 个配置文件:")
    for f in generated_files:
        print(f"  - {f}")

    print("\n使用方式:")
    print(f"  cd skill_training_build")
    print(f"  python create_task_from_markdown.py '{generated_files[0]}' [TASK_ID]")


if __name__ == "__main__":
    main()
