#!/usr/bin/env python3
"""
环境变量快速切换工具
支持多地区配置快速切换
"""

import os
import sys
import shutil
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent


def list_available_envs():
    """列出所有可用的环境配置"""
    env_files = sorted(ROOT_DIR.glob(".env.*"))
    # 排除 .env.example
    env_files = [f for f in env_files if f.name != ".env.example"]

    regions = []
    for f in env_files:
        region = f.name.replace(".env.", "")
        regions.append((region, f))

    return regions


def get_current_env():
    """获取当前使用的环境"""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return None

    # 读取第一行注释来判断当前环境
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line.startswith("# CURRENT:"):
                return first_line.replace("# CURRENT:", "").strip()
    except:
        pass

    return "未知"


def switch_env(region: str):
    """切换到指定地区的环境配置"""
    source_file = ROOT_DIR / f".env.{region}"
    target_file = ROOT_DIR / ".env"

    if not source_file.exists():
        print(f"❌ 配置文件不存在: {source_file}")
        return False

    # 备份当前 .env
    if target_file.exists():
        backup_file = ROOT_DIR / ".env.backup"
        shutil.copy2(target_file, backup_file)
        print(f"📦 已备份当前配置到 .env.backup")

    # 复制新配置
    shutil.copy2(source_file, target_file)

    # 在文件开头添加标记
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(f"# CURRENT: {region}\n")
        f.write(content)

    print(f"✅ 已切换到 [{region}] 环境")
    return True


def create_template(region: str):
    """创建新的地区配置模板"""
    template_file = ROOT_DIR / ".env.example"
    new_file = ROOT_DIR / f".env.{region}"

    if new_file.exists():
        print(f"❌ 配置文件已存在: {new_file}")
        return False

    if not template_file.exists():
        print(f"❌ 模板文件不存在: {template_file}")
        return False

    shutil.copy2(template_file, new_file)
    print(f"✅ 已创建配置模板: .env.{region}")
    print(f"📝 请编辑该文件填入 {region} 地区的配置")
    return True


def main():
    """主函数"""
    # 获取可用环境列表
    available_envs = list_available_envs()
    current_env = get_current_env()

    print("\n" + "=" * 60)
    print("🌍 环境配置切换工具")
    print("=" * 60)

    if current_env:
        print(f"\n当前环境: {current_env}")

    print("\n可用环境:")
    if not available_envs:
        print("  (暂无配置，请先创建)")
    else:
        for i, (region, _) in enumerate(available_envs, 1):
            marker = " ← 当前" if region == current_env else ""
            print(f"  {i}. {region}{marker}")

    print("\n操作选项:")
    print("  [数字] - 切换到对应环境")
    print("  [n/new] - 创建新地区配置")
    print("  [q/quit] - 退出")

    try:
        choice = input("\n请选择: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n👋 退出")
        return

    # 退出
    if choice in ["q", "quit"]:
        print("👋 退出")
        return

    # 创建新配置
    if choice in ["n", "new"]:
        region = input("请输入地区名称 (如: beijing, shanghai): ").strip()
        if region:
            create_template(region)
        return

    # 切换环境
    try:
        index = int(choice) - 1
        if 0 <= index < len(available_envs):
            region, _ = available_envs[index]
            switch_env(region)
        else:
            print("❌ 无效的选择")
    except ValueError:
        print("❌ 无效的输入")


if __name__ == "__main__":
    main()
