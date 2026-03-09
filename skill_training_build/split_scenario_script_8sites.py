#!/usr/bin/env python3
"""
分场景剧本生成工具 - 8遗址版本

将多遗址的训练剧本配置拆分为独立的单遗址配置文件。

使用方法:
    python split_scenario_script_8sites.py <markdown_file_path>

示例:
    python split_scenario_script_8sites.py \
        /path/to/训练剧本配置.md
"""

import sys
import re
import os
from pathlib import Path
from typing import List, Dict


# 8个遗址定义
SITES = [
    {
        "name": "世界自然遗产——三江并流",
        "short_name": "三江并流",
        "key_feature": "壮丽的怒江、澜沧江、金沙江三江并行奔流的自然奇观，展现地球演化历史",
        "heritage_type": "世界自然遗产",
        "iconic_spot": "高黎贡山雪峰观景台",
        "jump_keyword": "NEXT_TO_SANJIANG"
    },
    {
        "name": "世界自然与文化双遗产——泰山",
        "short_name": "泰山",
        "key_feature": "五岳之首，承载深厚的封禅文化与自然地质奇观",
        "heritage_type": "世界自然与文化双遗产",
        "iconic_spot": "南天门与玉皇顶",
        "jump_keyword": "NEXT_TO_TAISHAN"
    },
    {
        "name": "世界文化遗产·江南古典园林——拙政园",
        "short_name": "拙政园",
        "key_feature": "江南古典园林的巅峰之作，水景造园艺术的典范",
        "heritage_type": "世界文化遗产",
        "iconic_spot": "小飞虹廊桥与远香堂",
        "jump_keyword": "NEXT_TO_ZHUOZHENG"
    },
    {
        "name": "世界文化遗产·北方皇家园林——颐和园",
        "short_name": "颐和园",
        "key_feature": "皇家园林恢弘气势的代表，山水园林与建筑艺术的完美融合",
        "heritage_type": "世界文化遗产",
        "iconic_spot": "佛香阁与昆明湖",
        "jump_keyword": "NEXT_TO_YIHEYUAN"
    },
    {
        "name": "文化景观——杭州西湖",
        "short_name": "杭州西湖",
        "key_feature": "'三面云山一面城'的城湖空间格局，人文与自然的和谐统一",
        "heritage_type": "文化景观",
        "iconic_spot": "断桥与三潭印月",
        "jump_keyword": "NEXT_TO_XIHU"
    },
    {
        "name": "遗产线路——丝绸之路",
        "short_name": "丝绸之路",
        "key_feature": "横跨亚欧大陆的古代商贸与文化线路遗产",
        "heritage_type": "遗产线路",
        "iconic_spot": "长安城门遗址",
        "jump_keyword": "NEXT_TO_SILKROAD"
    },
    {
        "name": "遗产运河——大运河",
        "short_name": "大运河",
        "key_feature": "世界上最长的人工运河，连接南北的水运大动脉",
        "heritage_type": "遗产运河",
        "iconic_spot": "拱宸桥与漕运码头",
        "jump_keyword": "NEXT_TO_CANAL"
    },
    {
        "name": "古村落园林——宏村",
        "short_name": "宏村",
        "key_feature": "'画里乡村'，牛形村落布局与徽派建筑的完美结合",
        "heritage_type": "古村落园林",
        "iconic_spot": "月沼与南湖书院",
        "jump_keyword": "NEXT_TO_HONGCUN"
    }
]


def read_markdown_file(file_path: str) -> str:
    """读取markdown文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_stages(content: str) -> List[Dict]:
    """解析剧本配置，提取各个阶段"""
    stages = []
    stage_pattern = r'### 阶段\d+:[^\n]+\n'
    stage_matches = list(re.finditer(stage_pattern, content))

    for i, match in enumerate(stage_matches):
        stage_start = match.start()
        stage_end = stage_matches[i + 1].start() if i + 1 < len(stage_matches) else len(content)
        stage_content = content[stage_start:stage_end]

        stage_name_match = re.search(r'### (阶段\d+:[^\n]+)', stage_content)
        stage_name = stage_name_match.group(1) if stage_name_match else f"阶段{i+1}"
        stage_title = re.sub(r'阶段\d+:\s*', '', stage_name)

        fields = {}
        name_match = re.search(r'\*\*虚拟训练官名字\*\*:\s*([^\n]+)', stage_content)
        fields['trainer_name'] = name_match.group(1).strip() if name_match else "苏导"

        model_match = re.search(r'\*\*模型\*\*:\s*([^\n]+)', stage_content)
        fields['model'] = model_match.group(1).strip() if model_match else "(选填，默认为空)"

        voice_match = re.search(r'\*\*声音\*\*:\s*([^\n]+)', stage_content)
        fields['voice'] = voice_match.group(1).strip() if voice_match else "(选填，默认为空)"

        avatar_match = re.search(r'\*\*形象\*\*:\s*([^\n]+)', stage_content)
        fields['avatar'] = avatar_match.group(1).strip() if avatar_match else "(选填，默认为空)"

        desc_match = re.search(r'\*\*阶段描述\*\*:\s*([^\n]+)', stage_content)
        fields['description'] = desc_match.group(1).strip() if desc_match else ""

        bg_match = re.search(r'\*\*背景图\*\*:\s*([^\n]+)', stage_content)
        fields['background'] = bg_match.group(1).strip() if bg_match else "(选填，默认为空)"

        rounds_match = re.search(r'\*\*互动轮次\*\*:\s*(\d+)轮', stage_content)
        fields['rounds'] = rounds_match.group(1) if rounds_match else "3"

        flow_match = re.search(r'\*\*flowCondition\*\*:\s*"([^"]+)"', stage_content)
        fields['flow_condition'] = flow_match.group(1) if flow_match else None

        trans_match = re.search(r'\*\*transitionPrompt\*\*:\s*```\n([\s\S]*?)```', stage_content)
        fields['transition_prompt'] = trans_match.group(1).strip() if trans_match else ""

        opening_match = re.search(r'\*\*开场白\*\*:\s*```\n([\s\S]*?)```', stage_content)
        fields['opening'] = opening_match.group(1).strip() if opening_match else ""

        prompt_match = re.search(r'\*\*提示词\*\*:\s*```markdown\n([\s\S]*?)```', stage_content)
        fields['prompt'] = prompt_match.group(1).strip() if prompt_match else ""

        stages.append({
            'name': stage_name,
            'title': stage_title,
            **fields
        })

    return stages


def generate_stage1_for_site(site: Dict, base_stage: Dict, output_dir: Path) -> str:
    """为特定遗址生成阶段1内容"""

    bg_path = output_dir / "backgrounds" / f"训练剧本配置_{site['short_name']}_stage_1_探访准备与{site['short_name']}选择.png"

    new_opening = f"""欢迎来到本次世界遗产实地探访模拟！我是你的探访向导苏导，从事遗产研学向导工作12年，今天将全程陪你深入探访。

今天我们将专注于探访【{site['short_name']}】——{site['heritage_type']}。

{site['short_name']}的核心特色是：{site['key_feature']}。

在我们出发前，你最想重点探访哪个方向？比如它的核心景观特色、保护现状，还是游客管理方式？"""

    prompt = f"""# Role
你现在扮演"苏导"。
- **人设**：风景园林遗产实地探访向导兼遗产保护解说专家，从事遗产研学向导工作12年，深耕世界遗产保护研究。
- **性格特点**：热情专业、条理清晰，善于聚焦遗址核心看点与保护细节，引导主动观察思考。
- **当前状态**：正带领学生前往【{site['short_name']}】进行实地探访。

# Context & Task
当前处于【探访准备阶段】。本次实训以【{site['short_name']}】（{site['heritage_type']}）为固定探访对象，学生需要确认进入该遗址的探访，并说明希望重点关注的方向（造园手法/自然景观、保护措施、管理模式等）。

遗址核心特色：{site['key_feature']}

# Opening Line (你已经在上一轮输出过这句话，请基于此进行回复)
"欢迎来到本次世界遗产实地探访模拟！我是你的探访向导苏导，今天将全程陪你深入探访。今天我们将专注于探访【{site['short_name']}】——{site['heritage_type']}。在我们出发前，你最想重点探访哪个方向？"

# Workflow & Interaction Rules

1. **判定学生确认探访并说明关注方向**:
   - 条件：学生确认进入{site['short_name']}探访，并给出了关注方向（哪怕简短）。(等类似意思)
   - 操作：**不要输出任何对话内容**。**仅输出**跳转关键词: `{site['jump_keyword']}`

2. **判定学生未说明关注方向**:
   - 条件：学生确认探访但未提及具体关注方向。(等类似意思)
   - 回复策略：确认遗址选择，进一步引导学生说明关注方向。
   - 话术示例："好的，{site['short_name']}是个很棒的选择！在我们出发前，你最想重点探访哪个方向？比如它的核心景观特色、保护现状，还是游客管理方式？" (不要完全按照话术实例输出)

3. **判定无关话题**:
   - 条件：学生提出与探访任务完全无关的话题。(等类似意思)
   - 回复策略：礼貌回应并引导回到探访任务。

# Response Constraints
- 语气热情专业，条理清晰，带有向导的引导感
- **跳转指令纯净性**：满足跳转条件时，**不要输出任何对话内容**，**仅输出**跳转关键词
- 单次回复字数限制：80-150字（仅适用于对话回复，不适用于跳转指令）"""

    return f"""### 阶段1: 探访准备与{site['short_name']}选择

**虚拟训练官名字**: 苏导

**模型**: {base_stage['model']}

**声音**: {base_stage['voice']}

**形象**: {base_stage['avatar']}

**阶段描述**: 苏导介绍【{site['short_name']}】概况，引导学生明确探访重点关注方向，完成探访启动。

**背景图**: {bg_path}

**互动轮次**: {base_stage['rounds']}轮

**flowCondition**: "{site['jump_keyword']}"

**transitionPrompt**:
```
【输入参数】
- 上一轮对话 ${{previous_dialogue}}
- 当前阶段名称 ${{current_stage_name}}
- 下一阶段原始开场白 ${{next_stage_opening}}

【整体生成目标】
学生已完成探访准备并选择了关注方向，即将进入核心景观探访阶段。生成自然的过渡话语：
1. 简短确认学生的选择和关注方向
2. 引导进入探访场景，衔接下一阶段开场白
```

**开场白**:
```
{new_opening}
```

**提示词**:
```markdown
{prompt}
```
"""


def generate_stage2_for_site(site: Dict, base_stage: Dict, output_dir: Path) -> str:
    """为特定遗址生成阶段2内容"""

    bg_path = output_dir / "backgrounds" / f"训练剧本配置_{site['short_name']}_stage_2_{site['short_name']}核心景观探访.png"

    new_opening = f"""好，出发！现在我们正式进入【{site['short_name']}】的探访！

我们从入口处开始——眼前这处{site['iconic_spot']}是遗址的核心节点之一。你观察一下，这处景观在设计上有哪些让你印象深刻的特点？它体现了什么样的{site['key_feature'].split('，')[0]}？"""

    prompt = base_stage['prompt']
    # 更新Opening Line引用
    prompt = prompt.replace(
        '"好，出发！现在我们正式进入[遗址名称]的探访！',
        f'"好，出发！现在我们正式进入【{site['short_name']}】的探访！'
    )

    # 更新遗址名称占位符
    prompt = prompt.replace('[遗址名称]', site['short_name'])

    flow_condition = base_stage.get('flow_condition', 'NEXT_TO_PROTECTION')
    transition_prompt = base_stage.get('transition_prompt', '')

    return f"""### 阶段2: {site['short_name']}核心景观探访

**虚拟训练官名字**: 苏导

**模型**: {base_stage['model']}

**声音**: {base_stage['voice']}

**形象**: {base_stage['avatar']}

**阶段描述**: 苏导带领学生探访【{site['short_name']}】，引导学生观察{site['iconic_spot']}等核心景观特征，考核遗产类型识别、景观描述与价值载体要素鉴别能力。

**背景图**: {bg_path}

**互动轮次**: {base_stage['rounds']}轮

**flowCondition**: "{flow_condition}"

**transitionPrompt**:
```
{transition_prompt}
```

**开场白**:
```
{new_opening}
```

**提示词**:
```markdown
{prompt}
```
"""


def generate_generic_stage_for_site(stage_num: int, site: Dict, base_stage: Dict, output_dir: Path) -> str:
    """为特定遗址生成通用阶段内容（阶段3-4）"""

    new_opening = base_stage['opening'].replace('[遗址名称]', f"【{site['short_name']}】")
    prompt = base_stage['prompt'].replace('[遗址名称]', site['short_name'])

    stage_names = {
        3: "遗址保护与管理分析",
        4: "探访总结与切换"
    }
    stage_titles = {
        3: f"训练剧本配置_{site['short_name']}_stage_3_遗址保护与管理分析.png",
        4: f"训练剧本配置_{site['short_name']}_stage_4_探访总结与切换.png"
    }
    stage_name = stage_names.get(stage_num, base_stage['title'])
    bg_filename = stage_titles.get(stage_num, f"训练剧本配置_{site['short_name']}_stage_{stage_num}.png")
    bg_path = output_dir / "backgrounds" / bg_filename

    flow_condition = base_stage.get('flow_condition')
    transition_prompt = base_stage.get('transition_prompt', '')

    flow_section = f'\n**flowCondition**: "{flow_condition}"\n' if flow_condition else ''
    transition_section = f'\n**transitionPrompt**:\n```\n{transition_prompt}\n```\n' if transition_prompt else ''

    return f"""### 阶段{stage_num}: {stage_name}

**虚拟训练官名字**: 苏导

**模型**: {base_stage['model']}

**声音**: {base_stage['voice']}

**形象**: {base_stage['avatar']}

**阶段描述**: {base_stage['description'].replace('[遗址名称]', site['short_name'])}

**背景图**: {bg_path}

**互动轮次**: {base_stage['rounds']}轮{flow_section}{transition_section}
**开场白**:
```
{new_opening}
```

**提示词**:
```markdown
{prompt}
```
"""


def generate_site_markdown(site: Dict, stages: List[Dict], base_content: str, output_dir: Path) -> str:
    """为特定遗址生成完整的markdown配置"""

    base_config_match = re.search(r'^(# .+?)### 阶段1:', base_content, re.DOTALL)
    base_config = base_config_match.group(1) if base_config_match else ""

    # 更新任务名称和描述
    base_config = base_config.replace(
        "风景园林遗产保护与管理——世界遗产实地探访模拟",
        f"【{site['short_name']}】实地探访模拟"
    )
    base_config = base_config.replace(
        "为学生提供8处指定世界遗产的模拟实地参观服务",
        f"为学生提供【{site['short_name']}】（{site['heritage_type']}）的模拟实地探访服务"
    )

    # 生成各阶段内容
    stage_contents = []

    for i, stage in enumerate(stages):
        stage_num = i + 1

        if stage_num == 1:
            stage_content = generate_stage1_for_site(site, stage, output_dir)
        elif stage_num == 2:
            stage_content = generate_stage2_for_site(site, stage, output_dir)
        else:
            stage_content = generate_generic_stage_for_site(stage_num, site, stage, output_dir)

        stage_contents.append(stage_content)

    # 提取阶段跳转关系和配置说明
    jump_section_match = re.search(r'## 🔄 阶段跳转关系.+', base_content, re.DOTALL)
    jump_section = jump_section_match.group(0) if jump_section_match else ""

    # 简化跳转关系为单遗址版本
    jump_section = f"""## 🔄 阶段跳转关系

- **阶段1（探访准备）→ 阶段2（核心景观探访）**：学生确认探访并说明关注方向，跳转关键词 `{site['jump_keyword']}`
- **阶段2（核心景观探访）→ 阶段3（保护管理分析）**：学生涵盖遗产类型识别、核心景观描述、价值载体鉴别3项内容，跳转关键词 `NEXT_TO_PROTECTION`
- **阶段3（保护管理分析）→ 阶段4（探访总结）**：学生涵盖保护原则分析、管理模式评价、保护与利用平衡思考3项内容，跳转关键词 `NEXT_TO_SUMMARY`
- **阶段4（探访总结）→ 结束**：学生结束探访，输出 `TASK_COMPLETE`

---

## 📖 配置说明

### 遗址特色

**{site['short_name']}** - {site['heritage_type']}

核心特色：{site['key_feature']}

标志性景观：{site['iconic_spot']}

### 使用建议

本配置为【{site['short_name']}】专属探访剧本，阶段2-4的提示词保留通用结构，可根据该遗址具体特征进行微调。
"""

    full_content = base_config + "\n" + "\n---\n\n".join(stage_contents) + "\n\n---\n\n" + jump_section

    return full_content


def get_safe_filename(name: str) -> str:
    """将遗址名称转换为安全的文件名"""
    # 移除前缀
    name = re.sub(r'^世界自然遗产——|^世界自然与文化双遗产——|^世界文化遗产·江南古典园林——|^世界文化遗产·北方皇家园林——|^文化景观——|^遗产线路——|^遗产运河——|^古村落园林——', '', name)
    return name.strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python split_scenario_script_8sites.py <markdown_file_path>")
        print("\nExample:")
        print("    python split_scenario_script_8sites.py /path/to/训练剧本配置.md")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    print(f"正在读取原始剧本配置: {input_file}")

    content = read_markdown_file(input_file)
    stages = parse_stages(content)

    if len(stages) < 4:
        print(f"Warning: Expected 4 stages, found {len(stages)}")

    print(f"成功解析 {len(stages)} 个阶段")

    input_path = Path(input_file)
    output_dir = input_path.parent / "split_scenarios"
    output_dir.mkdir(exist_ok=True)

    print(f"\n输出目录: {output_dir}")
    print("=" * 60)

    generated_files = []

    for site in SITES:
        print(f"\n正在生成: {site['name']}")

        markdown_content = generate_site_markdown(site, stages, content, output_dir)

        safe_name = get_safe_filename(site['name'])
        output_file = output_dir / f"训练剧本配置_{safe_name}.md"

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
