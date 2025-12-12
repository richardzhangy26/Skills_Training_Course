#!/usr/bin/env python3
"""
测试 DeepSeek 模型接入功能
"""

import os
from openai import OpenAI

def test_deepseek_connection():
    """测试 DeepSeek API 连接"""
    print("🔍 测试 DeepSeek API 连接...")

    # 检查环境变量
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY 未设置")
        return False

    print(f"✅ DEEPSEEK_API_KEY: {api_key[:10]}...")

    try:
        # 初始化客户端
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # 测试简单调用
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个测试助手"},
                {"role": "user", "content": "你好，请回复'测试成功'"}
            ],
            max_tokens=50
        )

        answer = response.choices[0].message.content
        print(f"✅ DeepSeek 响应: {answer}")
        print("🎉 DeepSeek API 连接测试成功！")
        return True

    except Exception as e:
        print(f"❌ DeepSeek API 连接失败: {str(e)}")
        return False

def test_workflow_tester():
    """测试 WorkflowTester 的 DeepSeek 初始化"""
    print("\n🔍 测试 WorkflowTester DeepSeek 初始化...")

    # 设置环境变量
    os.environ["MODEL_TYPE"] = "deepseek_sdk"
    os.environ["DEEPSEEK_API_KEY"] = "test_key"  # 使用测试密钥

    try:
        from auto_script_train_5characters import WorkflowTester

        tester = WorkflowTester()

        if tester.model_type == "deepseek_sdk":
            print(f"✅ 模型类型正确: {tester.model_type}")
            print(f"✅ DeepSeek 模型: {tester.deepseek_model}")

            if tester.deepseek_client:
                print("✅ DeepSeek 客户端初始化成功")
            else:
                print("❌ DeepSeek 客户端初始化失败")

            return True
        else:
            print(f"❌ 模型类型错误: {tester.model_type}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🧪 DeepSeek 模型接入测试")
    print("="*60)

    # 测试1: 直接API连接
    print("\n1️⃣  测试直接API连接...")
    test1_success = test_deepseek_connection()

    # 测试2: WorkflowTester集成
    print("\n2️⃣  测试WorkflowTester集成...")
    test2_success = test_workflow_tester()

    print("\n" + "="*60)
    print("📊 测试结果汇总:")
    print(f"  测试1 (直接API): {'✅ 成功' if test1_success else '❌ 失败'}")
    print(f"  测试2 (集成测试): {'✅ 成功' if test2_success else '❌ 失败'}")

    if test1_success and test2_success:
        print("\n🎉 所有测试通过！DeepSeek 模型已成功接入。")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")
    print("="*60)