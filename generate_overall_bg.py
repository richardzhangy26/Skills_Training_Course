#!/usr/bin/env python3
import os
import json
import requests
from volcenginesdkarkruntime import Ark
from dotenv import load_dotenv

load_dotenv('/Users/zhangyichi/工作/能力训练/.trae/.env')
api_key = os.environ.get("ARK_API_KEY")
if not api_key:
    print("错误: 未设置 ARK_API_KEY 环境变量")
    exit(1)

client = Ark(api_key=api_key)

prompt = "现代景观设计后期制作工作室全景，自然光透过百叶窗洒入室内，深灰色专业制图台上整齐摆放着CAD工程图纸套装、比例尺、彩色马克笔和专业图解手册，主工作区配置双屏显示器，一屏显示规范制图软件界面，另一屏展示3D渲染效果图和PPT汇报页面，墙面悬挂着景观节点施工图规范展板和渲染作品案例，书架上陈列着景观材料样本册和植物图鉴，角落摆放着1:100口袋公园模型和渲染材质板，整体环境体现工程严谨性与视觉美感的融合，中国当代设计事务所风格，写实风格，专业室内摄影质感，电影级光影，16:9宽屏构图"

print("生成整体背景图中...")
response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt=prompt,
    size="2K"
)
image_url = response.data[0].url
print("图片已生成，下载中...")
img_response = requests.get(image_url)
output_path = "/Users/zhangyichi/工作/能力训练/skills_training_course/天津财经大学-景观设计程序方法与AI协同实践/任务3/backgrounds/overall_background.png"
with open(output_path, "wb") as f:
    f.write(img_response.content)
print(f"已保存: {output_path}")
print("完成!")
