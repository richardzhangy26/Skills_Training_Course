"""定点更新冠心病中西医结合诊疗能力训练。

默认只生成备份和更新预览；只有 CLI 显式传入 ``--apply`` 才允许写平台。
"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

import requests


TASK_ID = "gbxP2ro08oh4L66KpaVQ"
COURSE_ID = "0MdW9Q4j76iBRJOqeDBb"
LIBRARY_FOLDER_ID = "7zn9KnZTNh"
ORIGINAL_KNOWLEDGE_BASE_ID = "VWHlRhoca5"
DEFAULT_BACKUP_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills_training_course"
    / "湖南中医药大学-冠心病的中西医结合诊疗"
    / "platform_backups"
)

CASE1_INFO_STEP_ID = "5vamqgVPGVivQ5AV2a4y"
CASE1_PHYSICAL_STEP_ID = "87dB023ZQ3IzY3eK9DZ2"
CASE1_AUXILIARY_STEP_ID = "WwD673p2QpfWO4N3WxkJ"
CASE1_TREATMENT_STEP_ID = "B6DNLrQnZQsrGkoRgdJL"
CASE1_PAIRED_EXAM_STEP_ID = "m0D0KNG7QGhVwj439ajn"
CASE1_SUMMARY_STEP_ID = "VPDz2YNGXNhmljg0yDjZ"

CASE2_INTERVIEW_STEP_ID = "M6DLzroRvoc4gkKYQdVr"
CASE2_INFO_STEP_ID = "8eDVMQorOocRpmy0AakN"
CASE2_AUXILIARY_STEP_ID = "MRaAgyp2QpuwZJ9BOxpZ"
CASE2_DIAGNOSIS_STEP_ID = "mPxYJQoAYouXB91rBd0Y"
CASE2_TREATMENT_STEP_ID = "QgDjBp8jP8IWZwe7pD51"
CASE2_PAIRED_EXAM_STEP_ID = "bmaKAro1NoiermZbRxgY"
CASE2_SUMMARY_STEP_ID = "Z8DbqV1QX1iQnoK6la0X"
CASE2_INTERVIEW_FLOW_ID = "8eDVMQorOocZp0PlbakN"
CASE2_PATIENT_CLOSING = "医生，我暂时没有别的要补充了，您接着安排吧。"
CASE2_INFO_PROLOGUE = (
    "下面进入信息补充。同学，刚才你对张先生的问诊先告一段落。"
    "接下来我以接诊医生的身份补全尚未问到的信息，"
    "然后请你对他的病情做中西医初步研判。"
)

CASE3_INFO_STEP_ID = "rGDnyjWzOWuKX098yanQ"
CASE3_PHYSICAL_STEP_ID = "3JdrylmP7mu34KBngxeK"
CASE3_AUXILIARY_STEP_ID = "g2dlgpPMWPuwQlvWPxkb"
CASE3_TREATMENT_STEP_ID = "4Ya9P7p2QpsMALeJ5dPZ"
CASE3_PAIRED_EXAM_STEP_ID = "4AxegnNP0NujEm8y9aQV"
CASE3_SUMMARY_STEP_ID = "5vamqgVPGVivQ5A22a4y"
CASE3_REPORT_FILE_ID = "aCHMF8xbUn"
CASE3_REPORT_FILE_NAME = "病例三_辅助检查报告.png"
CASE3_REPORT_FILE_URL = (
    "https://prod-polymas-oss.polymas.com/"
    "polymas-basic-resource/202607/6a6b0d19e4b0c636f68862c8.png"
)
CASE3_REPORT_RESOURCE_TYPE_NID = "F9dmIDgAR6"

CASE1_AUXILIARY_PROLOGUE = (
    "体格检查分析合理。接下来先不看结果，请你说说："
    "患者需要做哪些辅助检查？"
)
CASE2_AUXILIARY_PROLOGUE = CASE1_AUXILIARY_PROLOGUE
CASE3_PHYSICAL_PROLOGUE = (
    "问诊和信息补充先到这里，情况紧急，咱们抓紧时间看体征。"
    "现在给李先生做了体格检查，结果是这样的——"
    "体温36.4℃，脉搏98次/分，呼吸22次/分，血压105/65mmHg；"
    "神志清楚，急性痛苦病容，面色苍白，大汗淋漓，四肢偏凉；"
    "双肺呼吸音清，未闻及干湿性啰音；"
    "心率98次/分，律齐，第一心音减弱，"
    "各瓣膜听诊区未闻及病理性杂音；"
    "腹软，无压痛、无反跳痛；双下肢无水肿；"
    "舌淡紫，舌边有瘀点，苔薄白，脉细涩无力。"
    "\n\n先说说——面色苍白、大汗肢冷、脉细涩无力，"
    "从中医角度看，这组体征提示的核心病机是什么？"
)

CASE3_NITROGLYCERIN_ANSWER = (
    "心绞痛仅为冠脉狭窄、供血不足，血管未完全闭塞，"
    "硝酸甘油可扩张冠脉改善供血；急性心梗为冠脉完全血栓闭塞，"
    "硝酸甘油无法疏通闭塞血栓，故无效。"
)

TARGET_STEP_SPECS = (
    (CASE1_INFO_STEP_ID, "信息补充与初步研判（带教医生补全 + 邀请研判）"),
    (CASE1_PHYSICAL_STEP_ID, "体格检查与解读"),
    (CASE1_AUXILIARY_STEP_ID, "辅助检查与解读"),
    (CASE1_TREATMENT_STEP_ID, "治则与中西医治疗方案"),
    (CASE1_PAIRED_EXAM_STEP_ID, "诊断与治疗配套考核"),
    (CASE1_SUMMARY_STEP_ID, "全流程总结评价"),
    (CASE2_INTERVIEW_STEP_ID, "专项问诊"),
    (CASE2_INFO_STEP_ID, "信息补充与辅助检查规划"),
    (CASE2_AUXILIARY_STEP_ID, "辅助检查与解读"),
    (CASE2_DIAGNOSIS_STEP_ID, "中西医诊断与鉴别"),
    (CASE2_TREATMENT_STEP_ID, "治则与中西医治疗方案"),
    (CASE2_PAIRED_EXAM_STEP_ID, "诊断与治疗配套考核"),
    (CASE2_SUMMARY_STEP_ID, "全流程总结评价"),
    (CASE3_INFO_STEP_ID, "信息补充与初步研判"),
    (CASE3_PHYSICAL_STEP_ID, "体格检查与解读"),
    (CASE3_AUXILIARY_STEP_ID, "辅助检查与解读"),
    (CASE3_TREATMENT_STEP_ID, "治则与中西医治疗方案"),
    (CASE3_PAIRED_EXAM_STEP_ID, "诊断与治疗配套考核"),
    (CASE3_SUMMARY_STEP_ID, "全流程总结评价"),
)
TARGET_STEP_IDS = tuple(step_id for step_id, _ in TARGET_STEP_SPECS)


class PreflightError(RuntimeError):
    """Raised when the live platform state no longer matches expectations."""


def _replace_required(
    text: str,
    old: str,
    new: str,
    *,
    label: str,
    minimum: int = 1,
) -> str:
    count = text.count(old)
    if count < minimum:
        raise PreflightError(f"{label} 未找到预期文本：{old}")
    return text.replace(old, new)


def _remove_example_lines(prompt: str) -> str:
    """Remove answer-repeating example lines from high-risk teaching nodes."""
    return "\n".join(
        line
        for line in prompt.splitlines()
        if "**话术示例**" not in line
    )


def _append_override(prompt: str, title: str, body: str) -> str:
    marker = f"# 教师7月24日修改覆盖规则·{title}（最高优先级）"
    if marker in prompt:
        raise PreflightError(f"重复追加覆盖规则：{title}")
    return f"{prompt.rstrip()}\n\n{marker}\n{body.strip()}\n"


TARGET_MARKER_TITLES = {
    CASE1_AUXILIARY_STEP_ID: "病例一辅助检查先问后给",
    CASE1_TREATMENT_STEP_ID: f"{CASE1_TREATMENT_STEP_ID}治疗独立必答",
    CASE1_SUMMARY_STEP_ID: f"{CASE1_SUMMARY_STEP_ID}先标准答案后评分",
    CASE2_INFO_STEP_ID: "病例二信息补充职责",
    CASE2_AUXILIARY_STEP_ID: "病例二辅助检查先问后给",
    CASE2_DIAGNOSIS_STEP_ID: "病例二中医诊断硬门槛",
    CASE2_TREATMENT_STEP_ID: f"{CASE2_TREATMENT_STEP_ID}治疗独立必答",
    CASE2_SUMMARY_STEP_ID: f"{CASE2_SUMMARY_STEP_ID}先标准答案后评分",
    CASE3_AUXILIARY_STEP_ID: "病例三检查结果呈现",
    CASE3_TREATMENT_STEP_ID: f"{CASE3_TREATMENT_STEP_ID}治疗独立必答",
    CASE3_PAIRED_EXAM_STEP_ID: "病例三硝酸甘油题",
    CASE3_SUMMARY_STEP_ID: f"{CASE3_SUMMARY_STEP_ID}先标准答案后评分",
}


def _target_marker(step_id: str) -> str:
    title = TARGET_MARKER_TITLES[step_id]
    return f"# 教师7月24日修改覆盖规则·{title}（最高优先级）"


def _step_is_already_target(step_id: str, detail: dict) -> bool:
    """Recognize only a complete target; reject marker-based half updates."""
    prompt = detail.get("llmPrompt") or ""
    prologue = detail.get("prologue") or ""
    step_name = detail.get("stepName") or ""
    marker = _target_marker(step_id) if step_id in TARGET_MARKER_TITLES else ""

    required_prompt: tuple[str, ...] = ()
    forbidden_prompt: tuple[str, ...] = ()
    required_prologue: tuple[str, ...] = ()
    forbidden_prologue: tuple[str, ...] = ()
    expected_prologue: str | None = None
    expected_name: str | None = None

    if step_id == CASE1_AUXILIARY_STEP_ID:
        required_prompt = (
            marker,
            "CK-MB 18 U/L",
            "肌钙蛋白I 0.02 ng/mL",
            "不能仅凭单次正常结果绝对排除急性心肌梗死",
        )
        forbidden_prompt = ("辅助检查结果已呈现", "数值正常可排除急性心肌梗死")
        expected_prologue = CASE1_AUXILIARY_PROLOGUE
    elif step_id == CASE2_AUXILIARY_STEP_ID:
        required_prompt = (
            marker,
            "CK-MB 16 U/L",
            "肌钙蛋白I 0.02 ng/mL",
            "不能仅凭单次正常结果绝对排除急性心肌梗死",
        )
        forbidden_prompt = ("辅助检查结果已呈现", "数值正常可排除急性心肌梗死")
        expected_prologue = CASE2_AUXILIARY_PROLOGUE
    elif step_id == CASE2_INFO_STEP_ID:
        required_prompt = (
            marker,
            "西医与中医初步考虑什么诊断？",
            "进入体格检查",
        )
        forbidden_prompt = (
            "信息补充与辅助检查规划",
            "检查设想",
            "安排哪些辅助检查",
        )
        expected_prologue = CASE2_INFO_PROLOGUE
        expected_name = "信息补充与初步研判"
    elif step_id == CASE2_DIAGNOSIS_STEP_ID:
        required_prompt = (
            marker,
            "中医病名、证型、辨证依据是三个独立必答项",
            "只依据学生最新一轮回答",
            "单次血压不能直接确诊原发性高血压",
        )
        forbidden_prompt = (
            "学生此前在本诊断节点",
            "原发性高血压2级",
        )
    elif step_id in TREATMENT_STANDARDS:
        required_prompt = (
            marker,
            "中医治则、主方、具体药物组成",
            "西医治疗原则、具体药物",
            "仅依据学生在本节点亲自说出的内容",
        )
        expected_name = "中西医结合治疗方案"
    elif step_id in SUMMARY_STANDARDS:
        required_prompt = (
            marker,
            "【标准答案】",
            "【评分与点评】",
            "人文沟通与急救素养：__/10",
            "问诊采集：__/35",
            "辅助检查与体征解读：__/15",
            "中西医诊断与鉴别：__/20",
            "中西医结合治疗方案：__/20",
            "含【标准答案】与【评分与点评】即视为已完成总结",
        )
        forbidden_prompt = ("总结报告≤400字",)
    elif step_id == CASE3_AUXILIARY_STEP_ID:
        required_prompt = (
            marker,
            "12.6 ng/mL",
            "85 U/L",
            "7.2 mmol/L",
            "3.1 mmol/L",
            "4.8 mmol/L",
            "0.9 mmol/L",
        )
        required_prologue = (
            "肌钙蛋白I 12.6 ng/mL",
            "CK-MB 85 U/L",
            "总胆固醇 7.2 mmol/L",
            "甘油三酯 3.1 mmol/L",
            "低密度脂蛋白 4.8 mmol/L",
            "高密度脂蛋白 0.9 mmol/L",
        )
        forbidden_prologue = (
            "肌钙蛋白I 12.6，",
            "CK-MB 85，",
            "总胆固醇7.2、",
        )
    elif step_id == CASE3_PAIRED_EXAM_STEP_ID:
        required_prompt = (
            marker,
            "为何急性心梗患者硝酸甘油含服无效？",
            CASE3_NITROGLYCERIN_ANSWER,
        )
        forbidden_prompt = ("请结合血管病理与中医病机作答",)
        required_prologue = (
            "接下来",
            "为何急性心梗患者硝酸甘油含服无效？",
        )
        forbidden_prologue = (
            "趁热打铁",
            "请结合血管病理与中医病机作答",
        )

    if marker:
        marker_present = marker in prompt
        complete = (
            all(text in prompt for text in required_prompt)
            and all(text not in prompt for text in forbidden_prompt)
            and all(text in prologue for text in required_prologue)
            and all(text not in prologue for text in forbidden_prologue)
            and (expected_prologue is None or prologue == expected_prologue)
            and (expected_name is None or step_name == expected_name)
        )
        if marker_present and not complete:
            raise PreflightError(f"{step_id} 检测到半更新状态，拒绝继续")
        if complete:
            return True

    if step_id == CASE1_INFO_STEP_ID:
        complete = (
            "西医与中医初步考虑什么诊断？" in prompt
            and "西医大致考虑什么方向" not in prompt
            and "**话术示例**" not in prompt
        )
        if "西医与中医初步考虑什么诊断？" in prompt and not complete:
            raise PreflightError(f"{step_id} 检测到半更新状态，拒绝继续")
        return complete
    if step_id == CASE1_PHYSICAL_STEP_ID:
        return "干湿性啰音" in prompt and "干湿啰音" not in prompt
    if step_id in {CASE1_PAIRED_EXAM_STEP_ID, CASE2_PAIRED_EXAM_STEP_ID}:
        return (
            "接下来" in prologue
            and "趁热打铁" not in prologue
            and "趁热打铁" not in prompt
        )
    if step_id == CASE2_INTERVIEW_STEP_ID:
        return (
            CASE2_PATIENT_CLOSING in prompt
            and "进入信息补充" not in prompt
        )
    if step_id == CASE3_INFO_STEP_ID:
        prologue_done = (
            "咱们抓紧时间" in prologue
            and "咱们抓紧。" not in prologue
        )
        prompt_done = (
            "咱们抓紧时间" in prompt
            and "咱们抓紧。" not in prompt
            and "**话术示例**" not in prompt
        )
        if prologue_done != prompt_done:
            raise PreflightError(f"{step_id} 检测到半更新状态，拒绝继续")
        return prologue_done and prompt_done
    if step_id == CASE3_PHYSICAL_STEP_ID:
        complete = (
            prologue == CASE3_PHYSICAL_PROLOGUE
            and "抓紧时间看体征" in prompt
        )
        partial = (
            "抓紧时间看体征" in prologue
            or "抓紧时间看体征" in prompt
        )
        if partial and not complete:
            raise PreflightError(f"{step_id} 检测到半更新状态，拒绝继续")
        return complete
    return False


CASE1_AUXILIARY_RESULTS = (
    "心电图：窦性心律，V3至V5导联ST段水平型下移0.05~0.1 mV，"
    "T波低平；CK-MB 18 U/L；肌钙蛋白I 0.02 ng/mL；"
    "总胆固醇 7.5 mmol/L；甘油三酯 3.3 mmol/L；"
    "低密度脂蛋白 5.2 mmol/L；高密度脂蛋白 0.6 mmol/L；"
    "冠脉CTA示左前降支近段粥样硬化、管腔狭窄45%，"
    "回旋支和右冠未见器质性狭窄。"
)
CASE2_AUXILIARY_RESULTS = (
    "心电图：窦性心律，V2至V6导联ST段轻度压低、T波倒置，"
    "发作时ST段压低较静息时明显加重；CK-MB 16 U/L；"
    "肌钙蛋白I 0.02 ng/mL；总胆固醇 6.5 mmol/L；"
    "甘油三酯 2.8 mmol/L；低密度脂蛋白 4.6 mmol/L；"
    "高密度脂蛋白 0.8 mmol/L；冠脉CTA示左前降支中段"
    "狭窄60%、斑块形态欠规则且稳定性差，"
    "回旋支和右冠轻度斑块、狭窄50%。"
)


def _build_auxiliary_prompt(
    *,
    step_id: str,
    patient: str,
    results: str,
    first_interpretation: str,
    second_interpretation: str,
) -> str:
    """Build a conflict-free ask-first, reveal-second auxiliary stage."""
    title = TARGET_MARKER_TITLES[step_id]
    return _append_override(
        f"""# Role
你现在扮演“心血管内科带教医生——李医生”。

- 当前患者：{patient}
- 当前任务：先检查学生的辅助检查规划，再呈现结果，最后循序完成结果解读。
- 原则：不抢答、不泄露标准答案、每次只问一个问题。

# Opening Line
“体格检查分析合理。接下来先不看结果，请你说说：患者需要做哪些辅助检查？”

# 唯一状态机
1. 若尚未呈现检查结果：
   - 只评价学生最新一轮提出的检查类别。
   - 方案基本覆盖心电图、心肌坏死标志物、血脂和冠脉影像时，用“分析合理”承接；有遗漏时只指出遗漏的检查类别。
   - 无论方案是否完整，完成这一次规划互动后，必须一次性呈现下方全部检查结果，再提出第一个解读问题。
2. 若结果已呈现、第一项解读未完成：
   - 只依据学生最新一轮回答判断；只追问心肌坏死标志物与临床过程的意义。
3. 若第一项已完成、第二项未完成：
   - 只依据学生最新一轮回答判断；只追问冠脉影像与发病机制。
4. 两项解读均完成时，仅输出 `进入中西医诊断`。

# 检查结果（仅在完成一次规划互动后向学生展示）
{results}

# 内部判定标准（不得在过程反馈中整段复述）
- 第一项：{first_interpretation}
- 第二项：{second_interpretation}

# 医学安全边界
- 心肌坏死标志物未升高，只能说明当前未见明确心肌坏死证据。
- 不能仅凭单次正常结果绝对排除急性心肌梗死；必须结合发病时间、症状变化、动态心电图及复测肌钙蛋白综合判断。
- 对本病例可结合完整临床过程判断相应诊断方向，但过程反馈不得直接报出最终诊断。
""",
        title,
        """
1. 本阶段开场只询问“患者需要做哪些辅助检查？”，学生回答前不得展示任何检查结果。
2. 过程反馈只指出遗漏的检查类别或解读维度，不得复述完整标准答案。
3. 只依据学生最新一轮回答判断当前问题是否完成，不得把医生自己的反馈算作学生答案。
""",
    )


def _extract_patient_information(prompt: str, *, label: str) -> str:
    start = "# 患者完整问诊信息"
    end = "# Opening Line"
    if start not in prompt or end not in prompt:
        raise PreflightError(f"{label} 未找到患者问诊信息区段")
    return prompt[prompt.index(start):prompt.index(end)].strip()


def _build_case2_info_prompt(original_prompt: str) -> str:
    patient_information = _extract_patient_information(
        original_prompt,
        label=CASE2_INFO_STEP_ID,
    )
    return _append_override(
        f"""# Role
你现在扮演“心血管内科带教医生——李医生”。

- 当前任务：回读专项问诊对话，只补充学生没有问到的患者信息，然后邀请学生做中西医初步研判。
- 顺序边界：本节点结束后进入体格检查；不得提前规划或展示后续检查。

{patient_information}

# Opening Line
“{CASE2_INFO_PROLOGUE}”

# 唯一状态机
1. 若尚未输出【信息补充】：
   - 逐项比对上方20个问诊点，只补充学生未问到的内容；已问到的不得重复。
   - 第一句必须以“下面进入信息补充”开头。
   - 最后必须逐字提问：“西医与中医初步考虑什么诊断？”
2. 若【信息补充】已经输出：
   - 只对学生最新一轮初步研判做一句方向性承接，不给标准诊断答案。
   - 随后仅输出 `进入体格检查`。

# 约束
- 不得泄露体格检查结果、后续检查结果、最终诊断、证型或治疗答案。
- 不得把医生补充的信息算成学生主动问诊所得。
- 输出为自然的带教医生口吻，不得出现“状态”“分支”等内部词。
""",
        TARGET_MARKER_TITLES[CASE2_INFO_STEP_ID],
        """
本节点职责只有“补充问诊遗漏→提出中西医初步诊断问题→进入体格检查”。
任何与该顺序冲突的旧逻辑均作废。
""",
    )


def _build_case2_diagnosis_prompt() -> str:
    return _append_override(
        """# Role
你现在扮演“心血管内科带教医生——李医生”。

# Opening Line
“检查结果都摆出来了，机制你也分析清楚了。现在到了下结论的时候——结合张先生的问诊、体征和这些检查，请你先给出西医诊断：诊断是什么、依据是什么？”

# 唯一状态机
1. 西医诊断：
   - 内部标准为冠状动脉粥样硬化性心脏病·不稳定型心绞痛。
   - 学生最新一轮需说出规范诊断，并给出至少两类依据：近期进行性加重且静息/夜间发作、硝酸甘油效果下降、动态ST-T改变、斑块不稳定、当前未见明确心肌坏死证据。
   - 本次血压165/95mmHg仅表示血压达2级高血压水平；单次血压不能直接确诊原发性高血压，应复测或动态监测。
2. 中医诊断：
   - 中医病名、证型、辨证依据是三个独立必答项。
   - 内部标准：病名“胸痹心痛”、证型“痰湿内阻证”、辨证依据至少一条。
   - 只依据学生最新一轮回答判断三项是否同时齐全；缺哪项只追问哪项，三项未齐不得推进。
3. 鉴别：
   - 西医可与稳定型心绞痛、急性心肌梗死鉴别；中医可与心血瘀阻证、寒凝心脉证鉴别。
   - 学生最新一轮给出至少一个合理鉴别及要点后，仅输出 `进入中西医治疗`。

# 反馈约束
- 每次只处理当前一个问题。
- 只指出缺失维度，不得在追问中直接说出该维度答案。
- 不得把医生反馈、提示词知识库或前序节点内容算成学生答案。
""",
        TARGET_MARKER_TITLES[CASE2_DIAGNOSIS_STEP_ID],
        """
中医病名、证型、辨证依据必须在学生最新一轮回答中同时出现；
不得累计此前回答，也不得把单次升高的血压写成已确诊高血压病。
""",
    )


TREATMENT_STANDARDS = {
    CASE1_TREATMENT_STEP_ID: (
        "王先生",
        "活血化瘀、通络止痛；血府逐瘀汤加减；"
        "桃仁、红花、当归、川芎、赤芍、丹参、延胡索、柴胡、枳壳等。",
        "抗血小板、调脂稳斑、改善心肌缺血及危险因素控制；"
        "阿司匹林、阿托伐他汀、单硝酸异山梨酯、氨氯地平、硝酸甘油等。",
    ),
    CASE2_TREATMENT_STEP_ID: (
        "张先生",
        "通阳泄浊、豁痰开痹；瓜蒌薤白半夏汤合二陈汤加减；"
        "瓜蒌、薤白、法半夏、陈皮、茯苓、白术、枳实、厚朴、丹参、郁金、炙甘草等。",
        "抗血小板、抗凝、强化调脂稳斑、改善缺血和解除冠脉痉挛；"
        "阿司匹林、低分子肝素（评估出血风险及肾功能后使用）、"
        "阿托伐他汀、单硝酸异山梨酯、地尔硫卓、硝酸甘油等。",
    ),
    CASE3_TREATMENT_STEP_ID: (
        "李先生",
        "益气活血、通脉止痛；补阳还五汤加减；"
        "生黄芪、党参、当归、赤芍、川芎、桃仁、红花、地龙、郁金、炙甘草等。",
        "尽快再灌注并联合抗血小板、抗凝、强化调脂及并发症防治；"
        "急诊PCI、阿司匹林、替格瑞洛、低分子肝素、阿托伐他汀等。",
    ),
}


def _treatment_override(step_id: str) -> str:
    patient, chinese_standard, western_standard = TREATMENT_STANDARDS[step_id]
    return f"""
1. 本阶段必须检查学生是否亲自回答以下五类内容：
   - 中医治则；
   - 中医主方；
   - 中医具体药物组成；
   - 西医治疗原则；
   - 西医具体药物。
2. 中医治则、主方、具体药物组成是三个独立必答项；西医治疗原则、具体药物是两个独立必答项。任一项缺失都不得跳转。
3. 仅依据学生在本节点亲自说出的内容累计完成度，不得把提示词知识库、前序医生陈述或医生自己的反馈计入学生答案。
4. 每次只追问一个缺失项，只能提示回答维度，严禁在追问或反馈中说出该项标准答案。
5. 内部核对标准（仅用于判定，禁止在过程反馈中直接输出）：
   - {patient}中医：{chinese_standard}
   - {patient}西医：{western_standard}
6. 学生五类内容全部完成后，方可进入健康宣教或下一阶段。
7. 上述规则优先于前文“说出方向即通过”“覆盖两项即通过”等宽松条件及所有旧话术示例。
"""


SUMMARY_STANDARDS = {
    CASE1_SUMMARY_STEP_ID: """
- 西医诊断：冠状动脉粥样硬化性心脏病·稳定型心绞痛；合并原发性高血压2级（很高危）及高脂血症。
- 中医诊断：胸痹心痛，心血瘀阻证；依据为固定刺痛、舌紫暗有瘀斑、脉弦涩等。
- 西医治疗：抗血小板、调脂稳斑、改善心肌缺血、控制血压和危险因素；可选阿司匹林、阿托伐他汀、单硝酸异山梨酯、氨氯地平及硝酸甘油。
- 中医治疗：活血化瘀、通络止痛，血府逐瘀汤加减，药物包括桃仁、红花、当归、川芎、赤芍、丹参、延胡索、柴胡、枳壳等。
""",
    CASE2_SUMMARY_STEP_ID: """
- 西医诊断：冠状动脉粥样硬化性心脏病·不稳定型心绞痛；合并混合型高脂血症及肥胖症。本次血压165/95mmHg达2级高血压水平，但单次血压不能直接确诊原发性高血压，需复测或动态监测。
- 中医诊断：胸痹心痛，痰湿内阻证；依据为形体肥胖、胸闷沉重、痰多身困、纳差便溏、舌胖有齿痕苔白厚腻、脉滑等。
- 西医治疗：抗血小板、抗凝、强化调脂稳斑、改善缺血和解除冠脉痉挛；可选阿司匹林、低分子肝素（评估出血风险及肾功能后使用）、阿托伐他汀、单硝酸异山梨酯、地尔硫卓及硝酸甘油。
- 中医治疗：通阳泄浊、豁痰开痹，瓜蒌薤白半夏汤合二陈汤加减，药物包括瓜蒌、薤白、法半夏、陈皮、茯苓、白术、枳实、厚朴、丹参、郁金、炙甘草等。
""",
    CASE3_SUMMARY_STEP_ID: """
- 西医诊断：冠状动脉粥样硬化性心脏病·急性ST段抬高型心肌梗死；合并高脂血症、原发性高血压病2级（很高危）。
- 中医诊断：真心痛，气虚血瘀证；依据为持续剧烈胸痛、大汗肢冷、舌淡紫有瘀点、脉细涩无力等。
- 西医治疗：尽快开通梗死相关血管实施再灌注，联合双联抗血小板、抗凝、强化调脂及并发症防治；可采用急诊PCI、阿司匹林、替格瑞洛、低分子肝素及阿托伐他汀等。
- 中医治疗：益气活血、通脉止痛，补阳还五汤加减，药物包括生黄芪、党参、当归、赤芍、川芎、桃仁、红花、地龙、郁金、炙甘草等。
""",
}


def _build_summary_prompt(step_id: str) -> str:
    standard = SUMMARY_STANDARDS[step_id].strip()
    return _append_override(
        f"""# Role
你现在扮演“心血管内科带教导师——李医生”。

# 总结状态判定
- 上下文未同时出现【标准答案】与【评分与点评】：尚未总结，立即输出完整总结。
- 上下文同时含【标准答案】与【评分与点评】即视为已完成总结，不得重复输出。
- 总结后学生表示完成时，仅输出 `完成训练`；如提问，可答疑最多5轮。

# 首次总结的强制顺序
必须先完整给出标准答案，再给数字评分与基于真实对话的点评：

【标准答案】
{standard}

【评分与点评】
总分：__/100
1. 人文沟通与急救素养：__/10
2. 问诊采集：__/35
3. 辅助检查与体征解读：__/15
4. 中西医诊断与鉴别：__/20
5. 中西医结合治疗方案：__/20
扣分原因：逐项说明学生实际遗漏或错误；无扣分则写“无”。
过程点评：只评价学生在真实对话中亲自完成的内容。

# 硬性要求
- 五项得分相加必须等于总分，总分必须是0至100之间的整数。
- “优秀／良好／需改进”只能作为数字分数后的附加说明，绝不能替代总分和分项得分。
- 标准答案必须完整出现在过程点评之前。
- 智能体补充或提示过、但学生没有亲自回答的内容不得计分。
- 必须完整输出上述内容，不得因旧字数限制截断标准答案、分项分数或扣分原因。
""",
        TARGET_MARKER_TITLES[step_id],
        """
本提示词是本节点唯一总结规则；旧的【全流程复盘】状态识别、
先总后分等级模板和短字数限制均不再使用。
""",
    )


def build_target_step(existing_step: dict) -> dict:
    """Return the exact teacher-approved content target for one live step."""
    target = copy.deepcopy(existing_step)
    step_id = target.get("stepId")
    if step_id not in TARGET_STEP_IDS:
        raise PreflightError(f"非本次目标节点：{step_id}")
    detail = target.setdefault("stepDetailDTO", {})
    if _step_is_already_target(step_id, detail):
        return target
    prompt = detail.get("llmPrompt") or ""
    prologue = detail.get("prologue") or ""

    if step_id == CASE1_INFO_STEP_ID:
        detail["llmPrompt"] = _remove_example_lines(
            _replace_required(
                prompt,
                "西医大致考虑什么方向、中医又怀疑哪类证型？",
                "西医与中医初步考虑什么诊断？",
                label=step_id,
            )
        )
    elif step_id == CASE1_PHYSICAL_STEP_ID:
        detail["llmPrompt"] = _replace_required(
            prompt,
            "干湿啰音",
            "干湿性啰音",
            label=step_id,
        )
    elif step_id == CASE1_AUXILIARY_STEP_ID:
        detail["prologue"] = CASE1_AUXILIARY_PROLOGUE
        detail["llmPrompt"] = _build_auxiliary_prompt(
            step_id=step_id,
            patient="王先生",
            results=CASE1_AUXILIARY_RESULTS,
            first_interpretation=(
                "标志物当前未升高，结合劳力诱发、持续短且休息缓解，"
                "提示当前无明确心肌坏死证据；仍需结合发病时间与动态复测。"
            ),
            second_interpretation=(
                "左前降支狭窄使供血储备下降，劳累或情绪激动增加耗氧，"
                "形成一过性供需失衡；可结合瘀血阻滞心脉解释。"
            ),
        )
    elif step_id in TREATMENT_STANDARDS:
        detail["stepName"] = "中西医结合治疗方案"
        detail["llmPrompt"] = _append_override(
            _remove_example_lines(prompt),
            f"{step_id}治疗独立必答",
            _treatment_override(step_id),
        )
    elif step_id == CASE1_PAIRED_EXAM_STEP_ID:
        detail["prologue"] = _replace_required(
            prologue, "趁热打铁", "接下来", label=step_id
        )
        detail["llmPrompt"] = _remove_example_lines(
            _replace_required(
                prompt, "趁热打铁", "接下来", label=step_id
            )
        )
    elif step_id == CASE2_INTERVIEW_STEP_ID:
        detail["llmPrompt"] = _replace_required(
            prompt,
            "进入信息补充",
            CASE2_PATIENT_CLOSING,
            label=step_id,
        )
    elif step_id == CASE2_INFO_STEP_ID:
        detail["stepName"] = "信息补充与初步研判"
        detail["prologue"] = CASE2_INFO_PROLOGUE
        detail["llmPrompt"] = _build_case2_info_prompt(prompt)
    elif step_id == CASE2_AUXILIARY_STEP_ID:
        detail["prologue"] = CASE2_AUXILIARY_PROLOGUE
        detail["llmPrompt"] = _build_auxiliary_prompt(
            step_id=step_id,
            patient="张先生",
            results=CASE2_AUXILIARY_RESULTS,
            first_interpretation=(
                "标志物当前未升高，结合静息及夜间发作、近期进行性加重"
                "和药效下降，提示当前无明确心肌坏死证据；"
                "仍需动态心电图与复测肌钙蛋白。"
            ),
            second_interpretation=(
                "狭窄60%且斑块不稳定，可能出现斑块微破裂、"
                "血小板聚集或冠脉痉挛，使静息状态也发生缺血；"
                "可结合痰湿阻滞胸阳解释。"
            ),
        )
    elif step_id == CASE2_DIAGNOSIS_STEP_ID:
        detail["llmPrompt"] = _build_case2_diagnosis_prompt()
    elif step_id == CASE2_PAIRED_EXAM_STEP_ID:
        detail["prologue"] = _replace_required(
            prologue, "趁热打铁", "接下来", label=step_id
        )
        detail["llmPrompt"] = _remove_example_lines(
            _replace_required(
                prompt, "趁热打铁", "接下来", label=step_id
            )
        )
    elif step_id == CASE3_INFO_STEP_ID:
        detail["prologue"] = _replace_required(
            prologue, "咱们抓紧", "咱们抓紧时间", label=step_id
        )
        detail["llmPrompt"] = _remove_example_lines(
            _replace_required(
                prompt, "咱们抓紧", "咱们抓紧时间", label=step_id
            )
        )
    elif step_id == CASE3_PHYSICAL_STEP_ID:
        if "咱们抓紧看体征" not in prologue:
            raise PreflightError(f"{step_id} 未找到原始体格检查开场")
        detail["prologue"] = CASE3_PHYSICAL_PROLOGUE
        detail["llmPrompt"] = _replace_required(
            prompt, "咱们抓紧看体征", "咱们抓紧时间看体征", label=step_id
        )
    elif step_id == CASE3_AUXILIARY_STEP_ID:
        for old, new in (
            ("肌钙蛋白I 12.6，", "肌钙蛋白I 12.6 ng/mL，"),
            ("CK-MB 85，", "CK-MB 85 U/L，"),
            ("总胆固醇7.2、", "总胆固醇 7.2 mmol/L、"),
            ("甘油三酯3.1、", "甘油三酯 3.1 mmol/L、"),
            ("低密度脂蛋白4.8、", "低密度脂蛋白 4.8 mmol/L、"),
            ("高密度脂蛋白0.9；", "高密度脂蛋白 0.9 mmol/L；"),
        ):
            prologue = _replace_required(
                prologue, old, new, label=step_id
            )
        for old, new in (
            ("12.6ng/mL", "12.6 ng/mL"),
            ("85U/L", "85 U/L"),
            ("7.2mmol/L", "7.2 mmol/L"),
            ("3.1mmol/L", "3.1 mmol/L"),
            ("4.8mmol/L", "4.8 mmol/L"),
            ("0.9mmol/L", "0.9 mmol/L"),
        ):
            prompt = _replace_required(prompt, old, new, label=step_id)
        detail["prologue"] = prologue
        detail["llmPrompt"] = _append_override(
            _remove_example_lines(prompt),
            "病例三检查结果呈现",
            """
1. 学生可见文本中的每个检查数值必须同时带单位，不得省略。
2. 本节点配套的复合检查报告图与文本数据含义一致；若图片未加载，以本提示词和开场白中的带单位文本为准。
3. 过程反馈只评价学生解读，不得替学生直接给出最终诊断。
""",
        )
    elif step_id == CASE3_PAIRED_EXAM_STEP_ID:
        question_old = (
            "为什么急性心梗患者硝酸甘油含服无效，"
            "请结合血管病理与中医病机作答？"
        )
        question_new = "为何急性心梗患者硝酸甘油含服无效？"
        prologue = _replace_required(
            prologue, "趁热打铁", "接下来", label=step_id
        )
        prologue = _replace_required(
            prologue, question_old, question_new, label=step_id
        )
        prompt = _replace_required(
            prompt, "趁热打铁", "接下来", label=step_id
        )
        prompt = _replace_required(
            prompt, question_old, question_new, label=step_id
        )
        lines = []
        replaced_answer = False
        for line in prompt.splitlines():
            if (
                "**参考答案**：西医层面，心绞痛仅为冠脉狭窄"
                in line
            ):
                indent = line[: len(line) - len(line.lstrip())]
                line = f"{indent}- **参考答案**：{CASE3_NITROGLYCERIN_ANSWER}"
                replaced_answer = True
            lines.append(line)
        if not replaced_answer:
            raise PreflightError(f"{step_id} 未找到硝酸甘油参考答案")
        detail["prologue"] = prologue
        detail["llmPrompt"] = _append_override(
            _remove_example_lines("\n".join(lines)),
            "病例三硝酸甘油题",
            f"""
第一题题干必须逐字使用：“{question_new}”
第一题参考答案仅按以下内容判定，不附加中医病机要求：
{CASE3_NITROGLYCERIN_ANSWER}
学生未答完整时只追问“冠脉狭窄与完全闭塞有什么差别”，不得直接复述参考答案。
""",
        )
    elif step_id in SUMMARY_STANDARDS:
        detail["llmPrompt"] = _build_summary_prompt(step_id)
    else:
        raise PreflightError(f"目标节点尚无内容补丁：{step_id}")
    return target


def _case3_report_is_attached(step: dict) -> bool:
    resources = (
        (step.get("stepDetailDTO") or {}).get("scriptStepResourceList") or []
    )
    return any(
        item.get("fileId") == CASE3_REPORT_FILE_ID
        for item in resources
    )


def _resource_submit_item(
    item: dict,
    *,
    step_id: str,
    default_sort: int,
) -> dict:
    required_fields = ("fileId", "fileName", "fileUrl")
    missing = [field for field in required_fields if not item.get(field)]
    if missing:
        raise PreflightError(
            "节点资源缺少提交所需字段：" + "、".join(missing)
        )
    target = {
        "type": item.get("type") or "resource",
        "fileId": item["fileId"],
        "fileName": item["fileName"],
        "thumbnail": item.get("thumbnail") or item["fileUrl"],
        "fileUrl": item["fileUrl"],
        "isRequired": bool(item.get("isRequired", False)),
        "description": item.get("description") or "",
        "trainTaskId": TASK_ID,
        "scriptStepId": step_id,
        "sort": item.get("sort") or default_sort,
    }
    return target


def _is_empty_resource_category_shell(item: dict) -> bool:
    if item.get("scriptStepResourceId") or item.get("fileId"):
        return False
    return not any(
        item.get(field)
        for field in (
            "fileUrl",
            "ossUrl",
            "fileName",
            "description",
        )
    )


def build_ability_step_submit_payload(
    existing_step: dict,
    *,
    extra_resources: tuple[dict, ...] = (),
) -> dict:
    """Convert a query response into the front-end ability-node submit shape."""
    step_id = existing_step.get("stepId")
    if not step_id:
        raise PreflightError("能力节点缺少 stepId")
    position = existing_step.get("positionDTO")
    if not isinstance(position, dict):
        raise PreflightError(f"能力节点 {step_id} 缺少 positionDTO")

    detail = copy.deepcopy(existing_step.get("stepDetailDTO") or {})
    flat_resources = detail.get("scriptStepResourceList") or []
    if not isinstance(flat_resources, list):
        raise PreflightError(f"能力节点 {step_id} 资源结构已变化")

    resources = copy.deepcopy(flat_resources)
    for extra in extra_resources:
        if not any(
            item.get("fileId") == extra.get("fileId") for item in resources
        ):
            item = copy.deepcopy(extra)
            item.setdefault("sort", len(resources) + 1)
            resources.append(item)

    resources.sort(key=lambda item: int(item.get("sort") or 0))
    grouped: list[dict] = []
    for index, item in enumerate(resources, start=1):
        resource_type_nid = str(
            item.get("resourceTypeNid") or item.get("nid") or ""
        )
        category = item.get("category") or "资源"
        last_group = grouped[-1] if grouped else None
        same_as_last = bool(
            last_group
            and (
                (
                    resource_type_nid
                    and last_group["nid"] == resource_type_nid
                )
                or (
                    not resource_type_nid
                    and not last_group["nid"]
                    and last_group["category"] == category
                )
            )
        )
        if _is_empty_resource_category_shell(item):
            if not same_as_last:
                grouped.append(
                    {
                        "nid": resource_type_nid,
                        "category": category,
                        "list": [],
                    }
                )
            continue

        submit_item = _resource_submit_item(
            item,
            step_id=step_id,
            default_sort=index,
        )
        if same_as_last:
            last_group["list"].append(submit_item)
        else:
            grouped.append(
                {
                    "nid": resource_type_nid,
                    "category": category,
                    "list": [submit_item],
                }
            )

    ext_property = copy.deepcopy(detail.get("stepExtProperty") or {})
    ext_property.pop("trainSubType", None)
    ext_property["resources"] = [
        {
            "category": group["category"],
            "list": group["list"],
        }
        for group in grouped
    ]
    detail["trainSubType"] = "ability"
    detail["stepExtProperty"] = ext_property
    detail.pop("scriptStepResourceList", None)
    detail.pop("resources", None)

    return {
        "stepId": step_id,
        "stepDetailDTO": detail,
        "positionDTO": copy.deepcopy(position),
    }


def build_case3_report_resource_step(existing_step: dict) -> dict:
    """Attach the uploaded case-3 report using the ability submit shape."""
    if existing_step.get("stepId") != CASE3_AUXILIARY_STEP_ID:
        raise PreflightError("病例三检查报告只能关联到指定辅助检查节点")
    return build_ability_step_submit_payload(
        existing_step,
        extra_resources=(
            {
                "type": "resource",
                "fileId": CASE3_REPORT_FILE_ID,
                "fileName": CASE3_REPORT_FILE_NAME,
                "thumbnail": CASE3_REPORT_FILE_URL,
                "fileUrl": CASE3_REPORT_FILE_URL,
                "isRequired": False,
                "description": "",
                "category": "未分类",
                "resourceTypeNid": CASE3_REPORT_RESOURCE_TYPE_NID,
            },
        ),
    )


def build_target_flow(existing_flow: dict) -> dict:
    """Change only the case-2 patient closing trigger, not flow topology."""
    if existing_flow.get("flowId") != CASE2_INTERVIEW_FLOW_ID:
        raise PreflightError(f"非本次目标流程边：{existing_flow.get('flowId')}")
    if (
        existing_flow.get("scriptStepStartId") != CASE2_INTERVIEW_STEP_ID
        or existing_flow.get("scriptStepEndId") != CASE2_INFO_STEP_ID
    ):
        raise PreflightError("病例二问诊流程边起点或终点不匹配")
    try:
        conditions = existing_flow["flowConfiguration"]["conditions"][0][
            "conditions"
        ]
    except (KeyError, IndexError, TypeError) as exc:
        raise PreflightError("病例二问诊流程触发条件结构已变化") from exc
    if len(conditions) != 1:
        raise PreflightError("病例二问诊流程触发条件结构已变化")
    top_condition = existing_flow.get("flowCondition")
    nested_condition = conditions[0].get("text")
    if (
        top_condition == CASE2_PATIENT_CLOSING
        and nested_condition == CASE2_PATIENT_CLOSING
    ):
        return copy.deepcopy(existing_flow)
    if (
        top_condition == CASE2_PATIENT_CLOSING
        or nested_condition == CASE2_PATIENT_CLOSING
    ):
        raise PreflightError("病例二问诊流程检测到半更新状态，拒绝继续")
    if top_condition != "进入信息补充" or nested_condition != "进入信息补充":
        raise PreflightError("病例二问诊流程触发条件结构已变化")
    target = copy.deepcopy(existing_flow)
    target["flowCondition"] = CASE2_PATIENT_CLOSING
    target["flowConfiguration"]["conditions"][0]["conditions"][0][
        "text"
    ] = CASE2_PATIENT_CLOSING
    return target


TARGET_TASK_NAME = "冠心病的中西医结合诊疗模拟训练"


def build_target_configuration(current: dict) -> dict:
    """Preserve all configuration fields except the teacher-approved name."""
    if current.get("trainTaskId") != TASK_ID:
        raise PreflightError("基础配置任务ID不匹配")
    target = copy.deepcopy(current)
    target["trainTaskName"] = TARGET_TASK_NAME
    ext_config = target.setdefault("extConfig", {})
    ext_config["trainTaskName"] = TARGET_TASK_NAME
    return target


SCORE_SPECS = (
    {
        "itemId": "B9D5jqpvQpczrXLLmxKj",
        "itemName": "一、人文沟通与急救素养",
        "score": 10,
        "description": (
            "考查学生能否礼貌、清晰地与患者沟通；"
            "面对急性心梗病例时能否兼顾安抚、紧迫性和患者安全。"
        ),
        "requireDetail": """
按当前进入的病例逐条评分，并在评分结果中写明扣分原因：
- 病例一：开场礼貌，回应焦虑，提问通俗且有条理。
- 病例二：尊重患者、避免评判生活习惯，能解释提问目的并关注焦虑。
- 病例三：迅速安抚濒死恐惧，语言沉稳简洁，体现急救优先与风险意识。
评分：人文关怀4分；沟通清晰与问诊秩序3分；急危重症安全意识3分。
只依据学生真实表达评分；智能体代为安抚的内容不得计分。
""",
    },
    {
        "itemId": "boD7Wgp2QpUE30VV4DqV",
        "itemName": "二、问诊采集",
        "score": 35,
        "description": (
            "考查学生能否围绕胸痛完成系统问诊，覆盖主诉、现病史、"
            "既往史、个人史和家族史，并识别当前病例的关键危险线索。"
        ),
        "requireDetail": """
按当前进入的病例逐条评分，并在评分结果中写明扣分原因：
- 病例一：劳累或情绪诱发、持续3至5分钟、休息缓解、近3天加重，以及高血压、高脂、烟酒和家族史等。
- 病例二：近期进行性加重、静息及夜间发作、约10分钟、硝酸甘油效果下降，以及肥胖、痰多身困、纳差便溏等。
- 病例三：突发持续剧痛约2小时、休息和两次硝酸甘油均无效、大汗肢冷、濒死感等危重线索。
评分：胸痛核心特征12分；伴随症状与中医四诊线索8分；既往史及用药史6分；个人史与危险因素5分；家族史及问诊逻辑4分。
由智能体补充后才出现、学生未主动询问的内容不得计分。
""",
    },
    {
        "itemId": "WZDMnQoX0ou7Nn669x60",
        "itemName": "三、辅助检查与体征解读",
        "score": 15,
        "description": (
            "考查学生能否按病例既定流程解读体征、心电图、"
            "心肌坏死标志物、血脂和冠脉影像，并遵守急性心梗排除边界。"
        ),
        "requireDetail": """
按当前进入的病例逐条评分，并在评分结果中写明扣分原因：
- 病例一：先提出心电图、心肌坏死标志物、血脂及冠脉影像等合理检查；正确解读V3至V5导联ST段下移、CK-MB 18 U/L、肌钙蛋白I 0.02 ng/mL、血脂7.5/3.3/5.2/0.6 mmol/L及左前降支狭窄45%。
- 病例二：先提出合理检查；正确解读V2至V6导联ST段压低、CK-MB 16 U/L、肌钙蛋白I 0.02 ng/mL、血脂6.5/2.8/4.6/0.8 mmol/L及左前降支狭窄60%、斑块不稳定。
- 病例三：正确解读完整体征、ST段弓背向上抬高、肌钙蛋白I 12.6 ng/mL、CK-MB 85 U/L、血脂7.2/3.1/4.8/0.9 mmol/L及左前降支完全闭塞。病例三不设置检查规划环节，不得因未规划检查扣分。
评分：体征与心电图4分；心肌坏死标志物4分；血脂2分；冠脉影像与机制5分。
病例一、二单次标志物未升高只能表述为当前无明确心肌坏死证据；若绝对化称“已排除心梗”，应扣除相应解读分。
""",
    },
    {
        "itemId": "3Zdq0OAzYAIrqgRRnxOE",
        "itemName": "四、中西医诊断与鉴别",
        "score": 20,
        "description": (
            "考查学生能否给出规范西医诊断及依据，"
            "并分别回答中医病名、证型、辨证依据与必要鉴别。"
        ),
        "requireDetail": """
按当前进入的病例逐条评分，并在评分结果中写明扣分原因：
- 病例一：西医为冠心病稳定型心绞痛；中医为胸痹心痛、心血瘀阻证，并有固定刺痛、舌紫暗瘀斑、脉弦涩等依据。
- 病例二：西医为冠心病不稳定型心绞痛；中医为胸痹心痛、痰湿内阻证，并有肥胖、胸闷沉重、痰多身困、舌胖苔白厚腻、脉滑等依据。本次血压仅达2级高血压水平，单次读数不得直接确诊原发性高血压。
- 病例三：西医为急性ST段抬高型心肌梗死，并合并高脂血症、原发性高血压病2级（很高危）；中医为真心痛、气虚血瘀证，并有持续剧痛、大汗肢冷、舌淡紫瘀点、脉细涩无力等依据。
评分：西医诊断及依据8分；中医病名3分；证型3分；辨证依据3分；中西医鉴别3分。各项独立计分。
""",
    },
    {
        "itemId": "9VDE93rbBrUmWEppbDjG",
        "itemName": "五、中西医结合治疗方案",
        "score": 20,
        "description": (
            "考查学生能否分别给出西医治疗原则与具体药物，"
            "以及中医治则、主方和具体药物组成。"
        ),
        "requireDetail": """
按当前进入的病例逐条评分，并在评分结果中写明扣分原因：
- 病例一：西医抗血小板、调脂稳斑、改善缺血和危险因素控制，具体药物可含阿司匹林、阿托伐他汀、单硝酸异山梨酯、氨氯地平、硝酸甘油；中医活血化瘀、通络止痛，血府逐瘀汤加减，并列出桃仁、红花、当归、川芎、赤芍、丹参等组成。
- 病例二：西医抗血小板、抗凝、强化调脂、改善缺血和解除痉挛，具体药物可含阿司匹林、低分子肝素（评估出血风险及肾功能）、阿托伐他汀、单硝酸异山梨酯、地尔硫卓、硝酸甘油；中医通阳泄浊、豁痰开痹，瓜蒌薤白半夏汤合二陈汤加减，并列出瓜蒌、薤白、法半夏、陈皮、茯苓等组成。
- 病例三：西医尽快再灌注并联合双抗、抗凝、强化调脂和并发症防治，具体措施或药物可含急诊PCI、阿司匹林、替格瑞洛、低分子肝素、阿托伐他汀；中医益气活血、通脉止痛，补阳还五汤加减，并列出生黄芪、党参、当归、赤芍、川芎、桃仁、红花等组成。
评分：西医治疗原则4分、具体措施或药物4分；中医治则3分、主方3分、药物组成3分；健康宣教与用药安全3分。五类核心内容独立计分，学生未亲自说出的内容不得计分。
""",
    },
)


def build_target_score_items(current_items: list[dict]) -> list[dict]:
    """Build five branch-aware score payloads keyed by stable item IDs."""
    current_by_id = {item.get("itemId"): item for item in current_items}
    if set(current_by_id) != {spec["itemId"] for spec in SCORE_SPECS}:
        raise PreflightError("线上评价项ID集合与预期不一致")
    targets = []
    for spec in SCORE_SPECS:
        target = copy.deepcopy(current_by_id[spec["itemId"]])
        for field in (
            "itemName",
            "score",
            "description",
            "requireDetail",
        ):
            value = spec[field]
            target[field] = value.strip() if isinstance(value, str) else value
        targets.append(target)
    return targets

class AbilityTrainGateway(Protocol):
    def export_snapshot(self, task_id: str) -> dict: ...

    def edit_configuration(self, payload: dict) -> None: ...

    def edit_step(self, payload: dict) -> None: ...

    def edit_score_item(self, payload: dict) -> None: ...

    def edit_flow(self, payload: dict) -> None: ...


class PolymasAbilityTrainGateway:
    """Minimal gateway for the verified legacy ability-training endpoints."""

    def __init__(
        self,
        *,
        course_id: str,
        library_folder_id: str,
        headers: dict,
        requester=requests,
        api_base: str = (
            "https://cloudapi.polymas.com/teacher-course/abilityTrain"
        ),
    ) -> None:
        self.course_id = course_id
        self.library_folder_id = library_folder_id
        self._headers = headers
        self._requester = requester
        self._api_base = api_base.rstrip("/")

    def _post(self, endpoint: str, payload: dict):
        response = self._requester.post(
            f"{self._api_base}/{endpoint}",
            headers=self._headers,
            json=payload,
            timeout=20,
        )
        body = response.json()
        if not (
            body.get("code") in (200, "200")
            or body.get("success") is True
        ):
            raise RuntimeError(
                f"{endpoint} 失败：http={response.status_code}, "
                f"code={body.get('code')}, msg={body.get('msg')}"
            )
        return body.get("data")

    def export_snapshot(self, task_id: str) -> dict:
        if task_id != TASK_ID:
            raise PreflightError(f"拒绝读取非目标任务：{task_id}")
        return {
            "configuration": self._post(
                "queryConfiguration",
                {
                    "trainTaskId": task_id,
                    "trainSubType": "ability",
                },
            ),
            "steps": self._post(
                "queryScriptStepList",
                {
                    "trainTaskId": task_id,
                    "trainSubType": "ability",
                },
            )
            or [],
            "flows": self._post(
                "queryScriptStepFlowList",
                {"trainTaskId": task_id},
            )
            or [],
            "scoreItems": self._post(
                "queryScoreItemList",
                {"trainTaskId": task_id},
            )
            or [],
        }

    def edit_configuration(self, payload: dict) -> None:
        target = copy.deepcopy(payload)
        target["trainTaskId"] = TASK_ID
        target["courseId"] = self.course_id
        self._post("editConfiguration", target)

    def edit_step(self, payload: dict) -> None:
        target = copy.deepcopy(payload)
        target["trainTaskId"] = TASK_ID
        target["courseId"] = self.course_id
        target["libraryFolderId"] = self.library_folder_id
        self._post("editScriptStep", target)

    def edit_score_item(self, payload: dict) -> None:
        target = copy.deepcopy(payload)
        target["trainTaskId"] = TASK_ID
        self._post("editScoreItem", target)

    def edit_flow(self, payload: dict) -> None:
        target = copy.deepcopy(payload)
        target["trainTaskId"] = TASK_ID
        self._post("editScriptStepFlow", target)


def write_backup(snapshot: dict, backup_dir: Path) -> Path:
    """Write a credential-free platform snapshot before any mutation."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_dir = Path(backup_dir) / timestamp
    target_dir.mkdir(parents=True, exist_ok=False)
    target_path = target_dir / "snapshot.json"
    safe_snapshot = _remove_secret_keys(snapshot)
    target_path.write_text(
        json.dumps(safe_snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target_path


def _remove_secret_keys(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("_", "").replace("-", "")
            if any(
                secret in normalized
                for secret in (
                    "authorization",
                    "cookie",
                    "accesstoken",
                    "refreshtoken",
                    "password",
                    "jwt",
                )
            ):
                continue
            sanitized[key] = _remove_secret_keys(item)
        return sanitized
    if isinstance(value, list):
        return [_remove_secret_keys(item) for item in value]
    return value


def build_update_plan(snapshot: dict) -> dict:
    """Validate live steps and build a deterministic Step-ID keyed plan."""
    live_by_id = {
        item.get("stepId"): item
        for item in snapshot.get("steps", [])
        if item.get("stepId")
    }
    planned_steps = []
    for step_id, expected_name in TARGET_STEP_SPECS:
        current = live_by_id.get(step_id)
        if current is None:
            raise PreflightError(f"缺少目标节点 {step_id}")
        actual_name = (current.get("stepDetailDTO") or {}).get("stepName")
        allowed_names = {expected_name}
        if step_id in TREATMENT_STANDARDS:
            allowed_names.add("中西医结合治疗方案")
        if step_id == CASE2_INFO_STEP_ID:
            allowed_names.add("信息补充与初步研判")
        if actual_name not in allowed_names:
            raise PreflightError(
                f"节点 {step_id} 名称不匹配："
                f"预期「{'／'.join(sorted(allowed_names))}」，"
                f"实际「{actual_name}」"
            )
        planned_steps.append(
            {
                "stepId": step_id,
                "expectedName": expected_name,
                "current": current,
                "target": build_target_step(current),
            }
        )

    flows = snapshot.get("flows", [])
    current_flow = next(
        (
            item
            for item in flows
            if item.get("flowId") == CASE2_INTERVIEW_FLOW_ID
        ),
        None,
    )
    if current_flow is None:
        raise PreflightError(f"缺少目标流程边 {CASE2_INTERVIEW_FLOW_ID}")

    configuration = snapshot.get("configuration")
    if not isinstance(configuration, dict):
        raise PreflightError("缺少基础配置")
    score_items = snapshot.get("scoreItems")
    if not isinstance(score_items, list):
        raise PreflightError("缺少评价项")

    return {
        "configuration": {
            "current": configuration,
            "target": build_target_configuration(configuration),
        },
        "steps": planned_steps,
        "scoreItems": [
            {
                "current": {
                    item.get("itemId"): item for item in score_items
                }[target["itemId"]],
                "target": target,
            }
            for target in build_target_score_items(score_items)
        ],
        "flows": [
            {
                "current": current_flow,
                "target": build_target_flow(current_flow),
            }
        ],
    }


def execute_update_plan(
    gateway: AbilityTrainGateway,
    plan: dict,
    *,
    include_flows: bool = False,
) -> int:
    """Execute each batch in order and stop immediately on any exception."""
    updated_count = 0
    configuration = plan["configuration"]
    if configuration["current"] != configuration["target"]:
        gateway.edit_configuration(configuration["target"])
        updated_count += 1

    for item in plan["steps"]:
        if item["current"] == item["target"]:
            continue
        gateway.edit_step(
            build_ability_step_submit_payload(item["target"])
        )
        updated_count += 1

    for item in plan["scoreItems"]:
        if item["current"] == item["target"]:
            continue
        gateway.edit_score_item(item["target"])
        updated_count += 1

    if include_flows:
        for item in plan["flows"]:
            if item["current"] == item["target"]:
                continue
            gateway.edit_flow(item["target"])
            updated_count += 1
    return updated_count


def write_update_plan(plan: dict, target_dir: Path) -> Path:
    """Write a human-reviewable plan without duplicating unrelated metadata."""
    controlled_step_fields = (
        "stepName",
        "description",
        "interactiveRounds",
        "prologue",
        "llmPrompt",
    )
    serialized_steps = []
    for item in plan["steps"]:
        current_detail = item["current"].get("stepDetailDTO") or {}
        target_detail = item["target"].get("stepDetailDTO") or {}
        changed_fields = [
            field
            for field in controlled_step_fields
            if current_detail.get(field) != target_detail.get(field)
        ]
        serialized_steps.append(
            {
                "stepId": item["stepId"],
                "expectedCurrentName": item["expectedName"],
                "targetName": target_detail.get("stepName"),
                "changedFields": changed_fields,
                "target": {
                    field: target_detail.get(field)
                    for field in controlled_step_fields
                    if field in changed_fields
                },
            }
        )
    summary = {
        "taskId": TASK_ID,
        "configuration": {
            "trainTaskName": plan["configuration"]["target"].get(
                "trainTaskName"
            )
        },
        "steps": serialized_steps,
        "scoreItems": [
            item["target"] for item in plan["scoreItems"]
        ],
        "flows": [item["target"] for item in plan["flows"]],
    }
    path = Path(target_dir) / "update_plan.json"
    path.write_text(
        json.dumps(_remove_secret_keys(summary), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def run_coronary_update(
    gateway: AbilityTrainGateway,
    *,
    backup_dir: Path,
    apply: bool = False,
    include_flows: bool = False,
) -> dict:
    """Export a snapshot and, by default, stop after a dry-run backup."""
    snapshot = gateway.export_snapshot(TASK_ID)
    backup_path = write_backup(snapshot, backup_dir)
    plan = build_update_plan(snapshot)
    plan_path = write_update_plan(plan, backup_path.parent)
    if not apply:
        return {
            "dry_run": True,
            "updated_count": 0,
            "backup_path": str(backup_path),
            "plan_path": str(plan_path),
            "flow_updates_enabled": False,
            "plan": plan,
        }
    latest_snapshot = gateway.export_snapshot(TASK_ID)
    if _canonical_snapshot(latest_snapshot) != _canonical_snapshot(snapshot):
        raise PreflightError(
            "线上任务在导出备份后已发生变化，已在写入前中止"
        )
    updated_count = execute_update_plan(
        gateway,
        plan,
        include_flows=include_flows,
    )
    return {
        "dry_run": False,
        "updated_count": updated_count,
        "backup_path": str(backup_path),
        "plan_path": str(plan_path),
        "flow_updates_enabled": include_flows,
        "plan": plan,
    }


def run_case3_report_attachment(
    gateway: AbilityTrainGateway,
    *,
    backup_dir: Path,
) -> dict:
    """Attach the existing report file once, then verify the query response."""
    snapshot = gateway.export_snapshot(TASK_ID)
    backup_path = write_backup(snapshot, backup_dir)
    step = next(
        (
            item
            for item in snapshot.get("steps", [])
            if item.get("stepId") == CASE3_AUXILIARY_STEP_ID
        ),
        None,
    )
    if step is None:
        raise PreflightError(
            f"缺少病例三辅助检查节点 {CASE3_AUXILIARY_STEP_ID}"
        )
    if _case3_report_is_attached(step):
        return {
            "updated_count": 0,
            "already_attached": True,
            "backup_path": str(backup_path),
            "post_snapshot_path": None,
        }

    content_before = _step_content_fingerprint(step)
    resources_before = _step_resource_fingerprint(step)
    payload = build_case3_report_resource_step(step)
    latest_snapshot = gateway.export_snapshot(TASK_ID)
    if _canonical_snapshot(latest_snapshot) != _canonical_snapshot(snapshot):
        raise PreflightError(
            "线上任务在导出备份后已发生变化，已在资源写入前中止"
        )

    gateway.edit_step(payload)
    post_snapshot = gateway.export_snapshot(TASK_ID)
    post_step = next(
        (
            item
            for item in post_snapshot.get("steps", [])
            if item.get("stepId") == CASE3_AUXILIARY_STEP_ID
        ),
        None,
    )
    if post_step is None or not _case3_report_is_attached(post_step):
        raise RuntimeError("病例三辅助检查报告写入后回查未发现资源关联")
    if _step_content_fingerprint(post_step) != content_before:
        raise RuntimeError("病例三辅助检查报告关联后教学内容发生变化")
    expected_resources = sorted(
        set(
            resources_before
            + [
                (
                    CASE3_REPORT_FILE_ID,
                    CASE3_REPORT_FILE_NAME,
                    CASE3_REPORT_FILE_URL,
                )
            ]
        )
    )
    if _step_resource_fingerprint(post_step) != expected_resources:
        raise RuntimeError("病例三辅助检查报告关联后原有资源关联发生变化")

    post_snapshot_path = backup_path.parent / "post_attachment_snapshot.json"
    post_snapshot_path.write_text(
        json.dumps(
            _remove_secret_keys(post_snapshot),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "updated_count": 1,
        "already_attached": False,
        "backup_path": str(backup_path),
        "post_snapshot_path": str(post_snapshot_path),
    }


def _step_content_fingerprint(step: dict) -> dict:
    detail = step.get("stepDetailDTO") or {}
    return {
        field: detail.get(field)
        for field in (
            "stepName",
            "description",
            "interactiveRounds",
            "prologue",
            "llmPrompt",
        )
    }


def _step_resource_fingerprint(step: dict) -> list[tuple[str, str, str]]:
    resources = (
        (step.get("stepDetailDTO") or {}).get("scriptStepResourceList") or []
    )
    return sorted(
        (
            str(item.get("fileId") or ""),
            str(item.get("fileName") or ""),
            str(item.get("fileUrl") or ""),
        )
        for item in resources
        if (
            item.get("fileId")
            or item.get("fileName")
            or item.get("fileUrl")
        )
    )


def run_course_context_repair(
    gateway: AbilityTrainGateway,
    *,
    backup_dir: Path,
) -> dict:
    """Re-save affected nodes with this task's verified course context."""
    snapshot = gateway.export_snapshot(TASK_ID)
    backup_path = write_backup(snapshot, backup_dir)
    steps_by_id = {
        item.get("stepId"): item for item in snapshot.get("steps", [])
    }
    missing = [step_id for step_id in TARGET_STEP_IDS if step_id not in steps_by_id]
    if missing:
        raise PreflightError("缺少目标节点：" + "、".join(missing))

    affected = [
        steps_by_id[step_id]
        for step_id in TARGET_STEP_IDS
        if (
            steps_by_id[step_id].get("stepDetailDTO") or {}
        ).get("knowledgeBaseId")
        != ORIGINAL_KNOWLEDGE_BASE_ID
    ]
    if not affected:
        return {
            "updated_count": 0,
            "already_repaired": True,
            "backup_path": str(backup_path),
            "post_snapshot_path": None,
        }

    content_before = {
        step["stepId"]: _step_content_fingerprint(step) for step in affected
    }
    resources_before = {
        step["stepId"]: _step_resource_fingerprint(step) for step in affected
    }
    latest_snapshot = gateway.export_snapshot(TASK_ID)
    if _canonical_snapshot(latest_snapshot) != _canonical_snapshot(snapshot):
        raise PreflightError(
            "线上任务在导出备份后已发生变化，已在课程上下文修复前中止"
        )

    for step in affected:
        step_id = step["stepId"]
        gateway.edit_step(build_ability_step_submit_payload(step))
        post_snapshot = gateway.export_snapshot(TASK_ID)
        post_step = next(
            (
                item
                for item in post_snapshot.get("steps", [])
                if item.get("stepId") == step_id
            ),
            None,
        )
        if post_step is None:
            raise RuntimeError(f"课程上下文修复后缺少节点 {step_id}")
        post_detail = post_step.get("stepDetailDTO") or {}
        if post_detail.get("knowledgeBaseId") != ORIGINAL_KNOWLEDGE_BASE_ID:
            raise RuntimeError(f"节点 {step_id} 的知识库上下文未恢复")
        if _step_content_fingerprint(post_step) != content_before[step_id]:
            raise RuntimeError(f"节点 {step_id} 的教学内容在修复后发生变化")
        if _step_resource_fingerprint(post_step) != resources_before[step_id]:
            raise RuntimeError(f"节点 {step_id} 的资源关联在修复后发生变化")

    post_snapshot_path = (
        backup_path.parent / "post_course_context_snapshot.json"
    )
    post_snapshot_path.write_text(
        json.dumps(
            _remove_secret_keys(post_snapshot),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "updated_count": len(affected),
        "already_repaired": False,
        "backup_path": str(backup_path),
        "post_snapshot_path": str(post_snapshot_path),
    }


def _canonical_snapshot(snapshot: dict) -> dict:
    """Normalize API list order for a conservative pre-write comparison."""
    normalized = copy.deepcopy(snapshot)
    for key, id_key in (
        ("steps", "stepId"),
        ("flows", "flowId"),
        ("scoreItems", "itemId"),
    ):
        items = normalized.get(key)
        if isinstance(items, list):
            normalized[key] = sorted(
                items,
                key=lambda item: str(item.get(id_key, "")),
            )
    return normalized


def build_live_gateway() -> PolymasAbilityTrainGateway:
    try:
        from skill_training_build import create_task_from_markdown as ctm
    except ImportError:  # pragma: no cover - direct script execution fallback
        import create_task_from_markdown as ctm

    ctm.load_env_config()
    return PolymasAbilityTrainGateway(
        course_id=COURSE_ID,
        library_folder_id=LIBRARY_FOLDER_ID,
        headers=ctm.get_headers(),
        api_base=ctm.get_ability_train_api_base(),
    )


def main(
    argv: list[str] | None = None,
    *,
    gateway: AbilityTrainGateway | None = None,
) -> dict:
    parser = argparse.ArgumentParser(
        description="定点更新冠心病中西医结合诊疗能力训练"
    )
    write_mode = parser.add_mutually_exclusive_group()
    write_mode.add_argument(
        "--apply",
        action="store_true",
        help="显式写入平台；省略时仅备份并生成预演清单",
    )
    write_mode.add_argument(
        "--attach-case3-report",
        action="store_true",
        help="仅关联病例三辅助检查报告图片并回查，不重写其他节点",
    )
    write_mode.add_argument(
        "--repair-course-context",
        action="store_true",
        help="以当前任务的正确课程上下文重存错库节点并回查",
    )
    parser.add_argument(
        "--include-flows",
        action="store_true",
        help="同时写入经预演的一条流程触发条件；默认不写流程",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="备份和更新清单保存目录",
    )
    args = parser.parse_args(argv)
    active_gateway = gateway or build_live_gateway()
    if args.attach_case3_report:
        if args.include_flows:
            parser.error("--attach-case3-report 不能与 --include-flows 同用")
        report = run_case3_report_attachment(
            active_gateway,
            backup_dir=args.backup_dir,
        )
        status = (
            "已存在，无需重复关联"
            if report["already_attached"]
            else "已关联并回查通过"
        )
        print(f"任务：{TASK_ID}")
        print(f"病例三辅助检查报告：{status}")
        print(f"备份：{report['backup_path']}")
        if report["post_snapshot_path"]:
            print(f"写后快照：{report['post_snapshot_path']}")
        print(f"远程更新数：{report['updated_count']}")
        return report

    if args.repair_course_context:
        if args.include_flows:
            parser.error("--repair-course-context 不能与 --include-flows 同用")
        report = run_course_context_repair(
            active_gateway,
            backup_dir=args.backup_dir,
        )
        status = (
            "已一致，无需重复修复"
            if report["already_repaired"]
            else "已按正确课程上下文重存并回查通过"
        )
        print(f"任务：{TASK_ID}")
        print(f"知识库上下文：{status}")
        print(f"备份：{report['backup_path']}")
        if report["post_snapshot_path"]:
            print(f"写后快照：{report['post_snapshot_path']}")
        print(f"远程更新数：{report['updated_count']}")
        return report

    report = run_coronary_update(
        active_gateway,
        backup_dir=args.backup_dir,
        apply=args.apply,
        include_flows=args.include_flows,
    )
    mode = "已写入" if args.apply else "仅预演，未写入"
    print(f"任务：{TASK_ID}")
    print(f"模式：{mode}")
    print(f"备份：{report['backup_path']}")
    print(f"清单：{report['plan_path']}")
    print(
        "流程写入："
        + ("已显式启用" if report["flow_updates_enabled"] else "未启用")
    )
    print(f"远程更新数：{report['updated_count']}")
    return report


if __name__ == "__main__":
    main()
