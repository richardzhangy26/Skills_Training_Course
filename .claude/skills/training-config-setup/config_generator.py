#!/usr/bin/env python3
"""
Training Config Setup Generator
生成训练基础配置和Doubao封面图
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv

class TrainingConfigSetup:
    """训练基础配置生成器"""

    def __init__(self, skip_api_key_check=False):
        """初始化，读取ARK_API_KEY

        Args:
            skip_api_key_check: 如果为True，跳过API密钥检查（用于测试）
        """
        api_key = os.environ.get("ARK_API_KEY")
        if not api_key and not skip_api_key_check:
            raise ValueError(
                "请设置 ARK_API_KEY 环境变量。"
                "您可以通过以下方式设置:\n"
                "export ARK_API_KEY='your-api-key'"
            )

        if api_key:
            self.client = OpenAI(
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key=api_key,
            )
        else:
            self.client = None

        self.model = "doubao-seedream-4-0-250828"

    def extract_config_from_markdown(self, md_content: str, doc_path: str) -> Tuple[str, str]:
        """
        从markdown文档中提取任务名称和描述

        Args:
            md_content: markdown文件内容
            doc_path: 文档路径

        Returns:
            (任务名称, 任务描述)
        """
        lines = md_content.split('\n')

        # 提取任务名称（从路径或文档标题）
        task_name = Path(doc_path).stem
        task_name = task_name.replace("实训任务文档", "").replace("实训任务-", "").strip()
        if task_name.startswith("-"):
            task_name = task_name[1:].strip()

        # 提取任务描述
        task_description = ""
        in_task_section = False
        desc_lines = []

        for i, line in enumerate(lines):
            # 查找"任务目标"或"任务描述"部分
            if "任务目标" in line or "课程描述" in line:
                in_task_section = True
                continue

            if in_task_section:
                # 如果遇到新的标题或分隔符，停止
                if line.startswith("#") and "任务目标" not in line:
                    break

                # 收集描述文本
                line = line.strip()
                if line and not line.startswith("-") and not line.startswith("*"):
                    desc_lines.append(line)
                    if len(desc_lines) >= 3:  # 收集足够的描述
                        break

        task_description = " ".join(desc_lines)[:200]  # 限制长度200字

        return task_name, task_description

    def generate_cover_prompt(self, task_name: str, task_description: str) -> str:
        """
        根据任务信息生成Doubao封面图的提示词

        Args:
            task_name: 任务名称
            task_description: 任务描述

        Returns:
            提示词
        """
        # 关键词匹配，为不同类型的课程生成特定的提示词
        prompt_templates = {
            "离心泵": "工业化工厂，离心泵运行场景，技术人员在仔细检查泵的状态，高清现代化工业设备，蓝色和灰色调，工业气氛浓厚，精密检测仪器，16:9宽屏，电影级质感，光影细节丰富",
            "汽蚀": "工业现场，泵的故障诊断场景，工程师手持诊断工具，高科技仪器，动态光线，深蓝色和银灰色调，紧张专业的工作氛围，16:9宽屏，科技感十足",
            "精馏": "化学实验室，精馏装置运行中，液体流动通过冷凝管，蒸馏烧瓶加热，科学仪器精密排列，蓝白调，科技感强，专业教学环境，玻璃仪器闪烁反光，16:9宽屏，细节丰富",
            "展馆": "现代科技展馆内部，宽敞明亮的展厅，各种创意展示品，参观者在互动体验，科技感强烈，现代建筑风格，柔和的照明，开放式空间，16:9宽屏，沉浸感十足",
            "非暴力沟通": "温暖的协作工作室，两个人在进行深入沟通交流，放松的氛围，柔和的自然光线，绿植点缀，现代简约风格，友好和谐，16:9宽屏，人性化气氛",
            "投资": "现代办公会议室，投资推介会场景，专业的演讲者，观众认真听讲，高档的会议设备，蓝色商务调，专业严谨的氛围，大屏幕显示，16:9宽屏，企业级质感",
        }

        # 匹配关键词并选择模板
        combined_text = (task_name + " " + task_description).lower()
        for keyword, template in prompt_templates.items():
            if keyword.lower() in combined_text:
                return template

        # 默认提示词（通用教学场景）
        default_prompt = (
            f"现代教学培训场景，专业人士在讲解'{task_name}'，"
            "互动教学环境，科技感和教育感结合，光线充足，"
            "氛围积极向上，现代化设施，16:9宽屏，高清质感，"
            "细节丰富，专业呈现"
        )
        return default_prompt

    def generate_cover_image(self, prompt: str) -> str:
        """
        调用Doubao API生成封面图

        Args:
            prompt: 图片生成提示词

        Returns:
            图片URL
        """
        try:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size="2K",  # 2560x1440，16:9比例
                response_format="url",
                extra_body={
                    "watermark": True,
                },
            )
            return response.data[0].url
        except Exception as e:
            raise RuntimeError(f"Doubao API调用失败: {str(e)}")

    def create_config_structure(
        self,
        task_name: str,
        task_description: str,
        cover_url: str,
        prompt: str,
        doc_path: str
    ) -> Dict:
        """
        创建基础配置结构

        Args:
            task_name: 任务名称
            task_description: 任务描述
            cover_url: 封面图URL
            prompt: 生成提示词
            doc_path: 源文档路径

        Returns:
            配置字典
        """
        return {
            "taskName": task_name,
            "taskDescription": task_description,
            "coverImage": {
                "url": cover_url,
                "prompt": prompt,
                "format": "16:9",
                "size": "2K",
                "model": self.model
            },
            "metadata": {
                "createdAt": datetime.now().isoformat() + "Z",
                "source": doc_path
            }
        }

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
        # 提取配置信息
        print("📖 提取任务信息...")
        task_name, task_description = self.extract_config_from_markdown(md_content, doc_path)
        print(f"   ✓ 任务名称: {task_name}")
        print(f"   ✓ 任务描述: {task_description[:50]}...")

        # 生成提示词
        print("\n🎨 生成封面图提示词...")
        cover_prompt = self.generate_cover_prompt(task_name, task_description)
        print(f"   ✓ 提示词: {cover_prompt[:60]}...")

        # 生成封面图
        print("\n🖼️  调用Doubao生成封面图...")
        cover_url = self.generate_cover_image(cover_prompt)
        print(f"   ✓ 成功生成! URL: {cover_url[:80]}...")

        # 创建输出目录
        if output_dir is None:
            # 自动创建以任务名称命名的目录
            doc_dir = Path(doc_path).parent
            output_dir = doc_dir / task_name
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 输出目录: {output_dir}")

        # 创建配置结构
        config = self.create_config_structure(
            task_name,
            task_description,
            cover_url,
            cover_prompt,
            doc_path
        )

        # 保存JSON配置
        config_path = output_dir / "基础配置.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"   ✓ 配置已保存: {config_path}")

        # 保存提示词
        prompt_path = output_dir / "封面图提示词.txt"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(f"任务: {task_name}\n")
            f.write(f"生成时间: {config['metadata']['createdAt']}\n")
            f.write(f"模型: {self.model}\n")
            f.write(f"图片格式: 16:9 (2560x1440)\n")
            f.write(f"================\n\n")
            f.write(cover_prompt)
        print(f"   ✓ 提示词已保存: {prompt_path}")

        return config, str(output_dir)


def main():
    """CLI入口"""
    if len(sys.argv) < 2:
        print("使用方法: python config_generator.py <markdown_file_path>")
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
        generator = TrainingConfigSetup()
        config, output_dir = generator.process(md_content, md_path)

        print("\n✨ 成功完成!")
        print(f"\n📋 生成的配置:")
        print(f"   任务名称: {config['taskName']}")
        print(f"   任务描述: {config['taskDescription']}")
        print(f"   封面图URL: {config['coverImage']['url']}")
        print(f"\n📂 输出目录: {output_dir}")

    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
