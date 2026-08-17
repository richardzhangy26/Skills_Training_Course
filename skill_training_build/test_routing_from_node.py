#!/usr/bin/env python3
"""从路由节点开始测试所有15个分支"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from auto_script_train import WorkflowTester

TASK_ID = "XBDgqJorLJU52N2MjdNO"
ROUTING_STEP_ID = "pbDQprZ2OrsYlGK5EaWL"

BRANCHES = [
    ("PSYCHOANALYSIS_FREUD", "我想学习经典精神分析（弗洛伊德）"),
    ("PSYCHOANALYSIS_EGO", "我想学习自我心理学（安娜·弗洛伊德）"),
    ("PSYCHOANALYSIS_OBJECT_RELATIONS", "我想学习客体关系学派（克莱因）"),
    ("PSYCHOANALYSIS_SULLIVAN", "我想学习人际精神分析（沙利文）"),
    ("PSYCHOANALYSIS_SOCIOCULTURAL", "我想学习社会文化学派（霍妮）"),
    ("PSYCHOANALYSIS_SELF", "我想学习自体心理学（科胡特）"),
    ("PSYCHOANALYSIS_INTERSUBJECTIVE", "我想学习主体间性精神分析（史托罗楼）"),
    ("PSYCHOANALYSIS_RELATIONAL", "我想学习关系精神分析（米切尔）"),
    ("PSYCHOANALYSIS_ATTACHMENT", "我想学习依恋精神分析（鲍尔比）"),
    ("PSYCHOANALYSIS_TRAUMA", "我想学习创伤精神分析"),
    ("PSYCHOANALYSIS_LACAN", "我想学习拉康学派（拉康）"),
    ("PSYCHOANALYSIS_EXISTENTIAL", "我想学习存在主义精神分析（弗兰克尔）"),
    ("PSYCHOANALYSIS_CULTURAL", "我想学习文化精神分析（弗洛姆）"),
    ("PSYCHOANALYSIS_NEURO", "我想学习神经精神分析（索尔姆斯）"),
    ("PSYCHOANALYSIS_CHILD", "我想学习儿童精神分析"),
]

def test_branch(branch_key, routing_answer, branch_index):
    """测试单个分支"""
    print(f"\n{'='*60}")
    print(f"[{branch_index}/15] 测试分支: {branch_key}")
    print(f"路由回答: {routing_answer}")
    print(f"{'='*60}")

    tester = WorkflowTester()
    tester.student_profile_key = "good"
    tester.task_id = TASK_ID
    tester.log_dir = Path(f"test_logs_v2/{branch_key}")

    # 直接从路由节点开始，不调用 start_workflow
    tester.task_id = TASK_ID
    tester.dialogue_round = 0
    tester.conversation_history = []
    tester._prepare_log_files(TASK_ID)

    # 手动调用 run_card 指定路由节点
    print(f"🔧 手动指定路由节点: {ROUTING_STEP_ID}")
    result = tester.run_card(TASK_ID, ROUTING_STEP_ID)

    # 第一轮：注入路由回答
    print(f"📝 第1轮 - 注入路由回答: {routing_answer}")
    tester.dialogue_round = 1

    chat_result = tester.chat(routing_answer)

    text = chat_result.get("text") or ""
    next_step_id = chat_result.get("nextStepId")
    need_skip = chat_result.get("needSkipStep", False)

    print(f"   AI回复: {text[:200] if text else '(空)'}...")
    print(f"   nextStepId: {next_step_id}")
    print(f"   needSkipStep: {need_skip}")

    # 如果有跳转，说明路由成功
    if next_step_id and next_step_id != ROUTING_STEP_ID:
        print(f"✅ 路由成功! 跳转到: {next_step_id}")
        routing_success = True
    elif need_skip:
        print(f"✅ 路由成功(needSkipStep)! 进入下一步")
        routing_success = True
    else:
        print(f"⚠️ 路由可能未触发，继续对话...")
        routing_success = False

    # 后续轮次：使用好学生自动回答
    max_rounds = 80
    while tester.dialogue_round < max_rounds:
        tester.dialogue_round += 1
        print(f"\n📝 第{tester.dialogue_round}轮")

        # 生成回答
        try:
            answer = tester.generate_answer_with_doubao(
                text if text else "请继续"
            )
        except Exception as e:
            print(f"❌ 生成回答失败: {e}")
            break

        if not answer:
            print("⚠️ 生成的回答为空，跳过")
            break

        print(f"   学生回答: {answer[:100]}...")

        chat_result = tester.chat(answer)
        text = chat_result.get("text") or ""
        next_step_id = chat_result.get("nextStepId")
        need_skip = chat_result.get("needSkipStep", False)

        print(f"   AI回复: {text[:200] if text else '(空)'}...")

        if not text and not next_step_id:
            print("✅ 工作流完成！")
            break

        if need_skip and next_step_id:
            print(f"🔄 自动跳转到下一步: {next_step_id}")

    print(f"\n{'='*60}")
    print(f"[{branch_index}/15] {branch_key} 测试完成")
    print(f"总轮次: {tester.dialogue_round}")
    print(f"路由成功: {'是' if routing_success else '否'}")
    print(f"{'='*60}")

    return {
        "branch": branch_key,
        "routing_success": routing_success,
        "total_rounds": tester.dialogue_round,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", type=int, default=None, help="只测试指定编号的分支(1-15)")
    args = parser.parse_args()

    print(f"任务ID: {TASK_ID}")
    print(f"路由节点: {ROUTING_STEP_ID}")
    print(f"学生档位: good")
    print(f"总分支数: {len(BRANCHES)}")

    results = []

    if args.branch:
        # 只测试指定分支
        idx = args.branch - 1
        if 0 <= idx < len(BRANCHES):
            branch_key, routing_answer = BRANCHES[idx]
            result = test_branch(branch_key, routing_answer, args.branch)
            results.append(result)
    else:
        # 测试所有分支
        for i, (branch_key, routing_answer) in enumerate(BRANCHES, 1):
            try:
                result = test_branch(branch_key, routing_answer, i)
                results.append(result)
            except Exception as e:
                print(f"❌ {branch_key} 测试异常: {e}")
                results.append({
                    "branch": branch_key,
                    "routing_success": False,
                    "total_rounds": 0,
                    "error": str(e),
                })

    # 汇总
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    for r in results:
        status = "✅" if r["routing_success"] else "❌"
        print(f"{status} {r['branch']} | 轮次={r['total_rounds']}")

if __name__ == "__main__":
    main()
