#!/usr/bin/env python3
"""从路由节点开始测试所有15个分支 - 修正版"""

import sys
import os
import time
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

    # 设置日志目录
    log_dir = Path(f"test_logs_v2/{branch_key}")
    log_dir.mkdir(parents=True, exist_ok=True)
    tester.log_context_path = log_dir
    tester._prepare_log_files(TASK_ID)

    # Step 1: 直接从路由节点开始
    print(f"\n🔧 从路由节点开始: {ROUTING_STEP_ID}")
    tester.task_id = TASK_ID
    tester.dialogue_round = 0
    tester.conversation_history = []

    run_result = tester.run_card(TASK_ID, ROUTING_STEP_ID)
    data = (run_result or {}).get("data") or {}
    tester.question_text = data.get("text") or ""
    tester.current_step_id = ROUTING_STEP_ID
    print(f"路由节点开场白: {tester.question_text[:200]}...")

    # Step 2: 发送路由回答（第一轮）
    print(f"\n📝 第1轮 - 注入路由回答: {routing_answer}")
    tester.dialogue_round = 1
    tester.conversation_history.append({"ai": tester.question_text, "student": routing_answer})

    chat_result = tester.chat(routing_answer)
    data = (chat_result or {}).get("data") or {}
    ai_text = data.get("text") or ""

    # chat 方法内部处理了 needSkipStep，会自动调用 run_card 并更新 current_step_id 和 question_text
    tester.question_text = tester.question_text or ai_text

    # 检查路由是否成功：current_step_id 不再是路由节点说明已跳转
    routing_success = tester.current_step_id != ROUTING_STEP_ID
    if routing_success:
        print(f"✅ 路由成功! 跳转到: {tester.current_step_id}")
    else:
        print(f"⚠️ 路由可能未触发，继续对话...")

    # Step 3: 后续轮次使用好学生自动回答
    round_num = 2
    max_rounds = 80

    while round_num <= max_rounds:
        if tester.current_step_id is None:
            print("\n✅ 工作流完成！没有更多步骤了。")
            break

        print(f"\n{'='*60}")
        print(f"🤖 第 {round_num} 轮对话")
        print(f"{'='*60}")

        # 生成回答
        print(f"\n🔄 正在生成回答...")
        generated_answer = tester.generate_answer_with_replay(tester.question_text)

        if not generated_answer:
            print("❌ 无法生成回答，跳过此轮")
            break

        print(f"🤖 生成的回答: {generated_answer}")

        tester.conversation_history.append({
            "ai": tester.question_text,
            "student": generated_answer
        })

        # 发送回答
        try:
            result = tester.chat(generated_answer)
        except Exception as e:
            print(f"\n⚠️ 发送回答失败: {str(e)}")
            break

        data = (result or {}).get("data") or {}
        if data.get("text") is None and data.get("nextStepId") is None:
            print("\n✅ 工作流完成！")
            break

        tester.question_text = data.get("text") or ""
        round_num += 1
        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"[{branch_index}/15] {branch_key} 测试完成")
    print(f"总轮次: {round_num}")
    print(f"路由成功: {'是' if routing_success else '否'}")
    print(f"{'='*60}")

    try:
        tester._finalize_workflow()
    except Exception:
        pass

    return {
        "branch": branch_key,
        "routing_success": routing_success,
        "total_rounds": round_num,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", type=int, default=None, help="只测试指定编号的分支(1-15)")
    parser.add_argument("--start", type=int, default=1, help="从第几个分支开始")
    parser.add_argument("--end", type=int, default=15, help="测试到第几个分支")
    args = parser.parse_args()

    print(f"任务ID: {TASK_ID}")
    print(f"路由节点: {ROUTING_STEP_ID}")
    print(f"学生档位: good")
    print(f"总分支数: {len(BRANCHES)}")

    results = []

    if args.branch:
        idx = args.branch - 1
        if 0 <= idx < len(BRANCHES):
            branch_key, routing_answer = BRANCHES[idx]
            result = test_branch(branch_key, routing_answer, args.branch)
            results.append(result)
    else:
        start = max(1, args.start)
        end = min(15, args.end)
        for i in range(start, end + 1):
            idx = i - 1
            branch_key, routing_answer = BRANCHES[idx]
            try:
                result = test_branch(branch_key, routing_answer, i)
                results.append(result)
            except Exception as e:
                print(f"❌ {branch_key} 测试异常: {e}")
                import traceback
                traceback.print_exc()
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
    success_count = 0
    for r in results:
        status = "✅" if r["routing_success"] else "❌"
        rounds = r.get("total_rounds", 0)
        error = r.get("error", "")
        print(f"{status} {r['branch']} | 轮次={rounds} {f'| 错误={error}' if error else ''}")
        if r["routing_success"]:
            success_count += 1
    print(f"\n路由成功: {success_count}/{len(results)}")


if __name__ == "__main__":
    main()
