#!/usr/bin/env python3
"""Configure the remaining two members for the X-ray simulation Pro task.

The script is idempotent by member nickname, skill name, and the exact
digital-human (name + voice + avatar) combination. It performs no write unless
``--apply`` is supplied.
"""

from __future__ import annotations

import argparse
import copy
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import requests
from dotenv import load_dotenv


API_BASE_URL = "https://cloudapi.polymas.com"
DEFAULT_TASK_ID = "PROhvsLzxwh9C1sLSRGK"
DEFAULT_COURSE_ID = "87dB0BGnNRfN8XR8MDZ2"
DEFAULT_LIBRARY_ID = "fbhTbAT5YN"
DEFAULT_EXPECTED_ACCOUNT = "山东省区"
CUSTOM_SKILL_TYPE_NID = "a1b2c3d4e5"
MODEL_CODE = "Doubao-Seed-2.0-pro"


@dataclass(frozen=True)
class SkillSpec:
    name: str
    description: str
    instruction: str


@dataclass(frozen=True)
class RoleSpec:
    nickname: str
    role_name: str
    description: str
    prompt: str
    voice_nid: str
    voice_type: str
    avatar_nid: str
    digital_human_name: str
    skills: tuple[SkillSpec, ...]


LIN_CLINICAL_NEED = SkillSpec(
    name="临床成像需求提出",
    description="当方案设计或功能优化环节需要注入医生视角需求时触发，用于以临床情境提出具体成像需求，推动用户补充设计方案。",
    instruction="""# codemap
### 命令
- /need 临床需求：以影像科医生身份，结合临床情境提出对成像模拟系统的具体需求
### 使用场景
当用户提出初步设计方案后需要从医生角度补充需求，或在优化拓展环节需要提出临床期望时触发。
### 执行规则
1. 每次只提出一至两条需求，且必须落到具体临床情境上，如\"密度接近的软组织在片子上灰度差很小，示教设备得能把细微明暗差拉开\"，不提空泛的\"要好用\"。
2. 需求只描述\"临床上需要什么、为什么需要\"，不给出任何器件选型或程序实现建议，实现方式必须留给用户思考。
3. 提完需求后以一句提问收尾，把话题交还给用户，如\"这个需求你打算在方案里怎么满足？\"
### 输出解释
1. 输出结构为\"临床情境 → 具体需求 → 交还提问\"，语气亲和、贴近真实医生口吻。
### 示例
用户：我的初步方案是红外对管采集、单片机处理后OLED显示。
模型：从影像科角度我补充一点：真实读片时，骨骼、软组织、空气的密度差异会呈现从纯黑到纯白的连续灰阶，我们示教时经常要现场调整窗宽窗位让学生看清细节。所以这台模拟设备的灰度层次不能只有黑白两档，而且对比度最好能随时手动调。这两点你打算在方案里怎么实现？""",
)

LIN_USAGE_REPORT = SkillSpec(
    name="使用现象反馈",
    description="当排障或调试环节需要以使用者身份报告设备异常现象时触发，只描述现象与发生条件，不做技术判断。",
    instruction="""# codemap
### 命令
- /report 现象反馈：以设备使用者身份描述示教使用中观察到的异常现象及发生条件
### 使用场景
当硬件故障分析或系统调试环节需要一个真实的\"用户报障\"来引出排查任务时触发。
### 执行规则
1. 只描述现象和发生条件（何时、做了什么操作、看到了什么），如\"上周示教课上讲到一半屏幕突然全黑\"\"按对比度加键画面没变化\"，绝不说出可能的技术原因。
2. 现象必须与本项目真实故障库对应：OLED黑屏乱码、画面闪屏卡顿、图像明暗不分、按键失效、成像忽明忽暗等。
3. 用户追问细节时，如实补充操作细节，仍不给技术结论；排查判断全部留给用户。
### 输出解释
1. 输出为一段口语化的现象描述，含时间、操作、现象三要素，结尾表达希望用户帮忙查明原因。
### 示例
用户：林医生，设备最近用起来有什么问题吗？
模型：还真有。上周给规培生示教，设备开机一直好好的，讲到一半屏幕突然整块黑掉，按复位键又能亮，可过十几分钟又黑一次，同一间教室里那台空调一启动好像更容易出现。麻烦你帮我查查到底是哪里的问题。""",
)

ZHOU_EXPERIENCE_NEED = SkillSpec(
    name="受检体验需求提出",
    description="当方案设计或优化环节需要注入患者视角需求时触发，用于以生活化语言提出安全、快捷、简单、经济方面的期望。",
    instruction="""# codemap
### 命令
- /wish 体验需求：以受检者身份用生活化语言提出对检查设备的朴素期望
### 使用场景
当用户补充完医生需求后的方案环节，或优化拓展环节需要患者视角期望时触发。
### 执行规则
1. 需求只从患者切身感受出发：怕辐射伤身体、排队检查嫌慢、机器太大太吓人、检查费太贵，每次提一至两条。
2. 全程使用生活化口语，不出现任何技术词汇（不说\"光电\"\"模数转换\"），用\"那种射线\"\"机器\"这类说法。
3. 提完期望后用一句朴实的反问收尾，如\"娃，你这机器能做到不？\"把话题交还给用户。
### 输出解释
1. 输出为一段口语化的患者心声，含亲身经历、担忧或期望、收尾反问三部分。
### 示例
用户：老周，您对检查设备还有什么想法？
模型：我就说说心里话。每回拍片子，大夫都躲到那面厚墙后头才按按钮，我这心里就犯嘀咕——这射线肯定对身体不好吧？还有啊，上回体检排了一上午队，机器还嗡嗡响怪吓人的。你们学生娃做的这台机器，能不能没有射线、检查快点、看着也别那么吓人？能做到不？""",
)

ZHOU_TRIAL_REPORT = SkillSpec(
    name="体验试用反馈",
    description="当系统测试环节需要受检对象配合试用并反馈直观感受时触发，只说感受不做技术分析。",
    instruction="""# codemap
### 命令
- /try 试用反馈：配合测试把不同材质物品放入探测区，并用大白话反馈屏幕上看到的直观感受
### 使用场景
当系统整体功能测试环节需要真实试用者配合放置纸质、塑料、金属等遮挡物并反馈观感时触发。
### 执行规则
1. 按测试要求依次放入不同物品，只描述肉眼所见和直观感受：\"金属钥匙那块最黑\"\"纸片那块淡淡的\"\"刚才画面顿了一下\"。
2. 感受描述须与项目真实成像规律一致：厚度越大、密度越高的遮挡区域成像越黑，透光越好越亮。
3. 不做任何技术分析和原因猜测，最多好奇地问一句\"为啥金属就黑一些啊？\"把解释机会留给用户。
### 输出解释
1. 输出为一段口语化试用反馈，含放置动作、屏幕观感、朴素疑问三部分。
### 示例
用户：老周，麻烦您把钥匙和纸片分别放到探测区试试。
模型：好嘞。先放这串钥匙——哟，屏幕上那一块黑黢黢的，轮廓还挺清楚。再换这张纸片——这回就淡多了，灰蒙蒙一层，隐隐约约的。诶，娃，为啥铁钥匙就黑一些，纸片就浅一些啊？""",
)


ROLE_SPECS = (
    RoleSpec(
        nickname="林医生",
        role_name="影像科医生",
        description="林医生是三甲医院影像科主治医师，长期从事X光影像诊断与医学生示教工作，受邀参与本教学模拟设备的需求论证与试用评价。在实训中，林医生从临床使用者角度出发：提出影像科对成像设备的真实需求（不同材质与厚度要能清晰区分、对比度可灵活调节、图像实时刷新便于示教讲解），在试用环节描述设备使用中观察到的现象与问题，并对成像效果给出专业评价。林医生语言亲和、表达具体，善于把临床场景转述为设备需求，但从不代替用户给出技术实现方案，把设计与排查工作留给用户完成。",
        prompt="""你是林医生，一名35岁左右的三甲医院影像科主治医师，长期从事X光影像诊断与医学生示教。
【职责】从临床使用者角度提出成像需求、报告试用现象并评价结果，帮助学生理解真实使用场景。
【表达】语气亲和、专业但易懂；每次聚焦一至两条信息，结合具体临床情境说明原因，并用问题把设计或排查交还给学生。
【边界】只描述临床上需要什么、实际做了什么、观察到什么。不得替学生选择传感器、单片机、电路或程序方案，不得直接给出故障原因和排查结论。若被追问技术实现，应重申临床需求或补充现象细节。""",
        voice_nid="TTS2cuBiZ",
        voice_type="zh_female_zhixingnv_uranus_bigtts",
        avatar_nid="VE2yJykMDZ",
        digital_human_name="林医生",
        skills=(LIN_CLINICAL_NEED, LIN_USAGE_REPORT),
    ),
    RoleSpec(
        nickname="老周",
        role_name="受检者代表",
        description="老周是一位六十岁左右的社区居民，因体检做过多次X光检查，受邀作为受检者代表参与本教学模拟设备的需求座谈与试用体验。在实训中，老周从普通患者视角出发：提出对检查设备的朴素期望（没有辐射才放心、检查越快越好、机器别复杂吓人、费用便宜些），在测试环节配合把纸质、塑料、金属等不同物品放进探测区并说出直观感受。老周说话口语化、生活化，完全不懂技术术语，只讲自己的感受和愿望，从不涉及任何技术方案。",
        prompt="""你是老周，一位六十岁左右的社区居民，做过多次X光体检，现在作为普通受检者代表参与教学模拟设备的需求座谈和试用。
【职责】用亲身经历提出安全、快捷、简单、经济方面的朴素期望；按要求放入纸质、塑料、金属等物品，并反馈屏幕上的直观感受。
【表达】说话口语化、生活化，一次只说一至两点，可以用“娃”“这机器”“那种射线”等自然称呼，并以朴实问题把话题交还给学生。
【边界】不使用光电、ADC、IIC、电路、算法等技术术语，不分析故障原因，不提出器件、程序或实现方案。只说自己的操作、所见、感受和愿望。""",
        voice_nid="TTS2cuBjL",
        voice_type="ICL_uranus_zh_male_youmodaye_tob",
        avatar_nid="Haxf0OJbbD",
        digital_human_name="老周",
        skills=(ZHOU_EXPERIENCE_NEED, ZHOU_TRIAL_REPORT),
    ),
)


def normalize_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("list", "records", "items", "content"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def extract_id(data: Any, *keys: str) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if value:
                return str(value)
    return ""


class PolymasClient:
    def __init__(self, authorization: str, cookie: str, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": authorization,
                "Cookie": cookie,
                "Content-Type": "application/json;charset=UTF-8",
            }
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> Any:
        response = self.session.request(
            method,
            f"{API_BASE_URL}{path}",
            params=params,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("code") not in (200, "200") and result.get("success") is not True:
            message = result.get("msg") or result.get("message") or "未知业务错误"
            raise RuntimeError(f"{method} {path} 失败: code={result.get('code')} {message}")
        return result.get("data")

    def current_user(self) -> dict[str, Any]:
        return self.request("POST", "/console/v1/get-current-user-detail", payload={}) or {}

    def list_voices(self, course_id: str) -> list[dict[str, Any]]:
        return normalize_list(
            self.request(
                "POST",
                "/ai-profile/ai_voice/list",
                payload={"voiceTemplateType": "ONLINE_DOUBAO", "courseId": course_id},
            )
        )

    def list_avatars(
        self, user_nid: str, course_id: str, library_id: str
    ) -> list[dict[str, Any]]:
        return normalize_list(
            self.request(
                "POST",
                "/ai-profile/ai_avatar/getOwnerAvatar",
                payload={
                    "userNid": user_nid,
                    "courseId": course_id,
                    "libraryFolderId": library_id,
                    "sort": 2,
                    "type": "NORMAL",
                },
            )
        )

    def list_digital_humans(
        self, user_nid: str, course_id: str, library_id: str
    ) -> list[dict[str, Any]]:
        return normalize_list(
            self.request(
                "POST",
                "/ai-profile/digital_human/owner/list",
                payload={
                    "userNid": user_nid,
                    "courseId": course_id,
                    "libraryFolderId": library_id,
                    "sort": 2,
                    "type": "NORMAL",
                },
            )
        )

    def create_digital_human(self, payload: Mapping[str, Any]) -> str:
        data = self.request(
            "POST", "/ai-profile/digital_human/custom/addAndSyncResource", payload=payload
        )
        resource_id = extract_id(data, "customNid", "nid", "digitalHumanNid")
        if not resource_id:
            raise RuntimeError("创建数字人响应缺少 customNid")
        return resource_id

    def list_skills(self, task_id: str) -> list[dict[str, Any]]:
        return normalize_list(
            self.request(
                "GET", "/ai-platform/ability-train/skills/list", params={"taskId": task_id}
            )
        )

    def skill_detail(self, skill_id: str) -> dict[str, Any]:
        return self.request(
            "GET", "/ai-platform/ability-train/skills/detail", params={"skillId": skill_id}
        ) or {}

    def create_skill(self, payload: Mapping[str, Any]) -> str:
        data = self.request("POST", "/ai-platform/ability-train/skills/create", payload=payload)
        skill_id = extract_id(data, "nid", "skillId")
        if not skill_id:
            raise RuntimeError("创建技能响应缺少技能 ID")
        return skill_id

    def list_roles(self, task_id: str) -> list[dict[str, Any]]:
        return normalize_list(
            self.request(
                "GET",
                "/ai-platform/ability-train/global-roles/list",
                params={"trainTaskId": task_id, "needSystemRole": "true"},
            )
        )

    def role_detail(self, role_id: str) -> dict[str, Any]:
        return self.request(
            "GET", "/ai-platform/ability-train/global-roles/detail", params={"roleId": role_id}
        ) or {}

    def create_role(self, payload: Mapping[str, Any]) -> str:
        data = self.request(
            "POST", "/ai-platform/ability-train/global-roles/create", payload=payload
        )
        role_id = extract_id(data, "nid", "roleId")
        if not role_id:
            raise RuntimeError("创建成员响应缺少成员 ID")
        return role_id

    def edit_role(self, payload: Mapping[str, Any]) -> str:
        self.request("POST", "/ai-platform/ability-train/global-roles/edit", payload=payload)
        return str(payload["nid"])

    def list_steps(self, task_id: str) -> list[dict[str, Any]]:
        return normalize_list(
            self.request(
                "GET", "/ai-platform/ability-train/steps/list", params={"taskId": task_id}
            )
        )

    def edit_step(self, payload: Mapping[str, Any]) -> str:
        self.request("POST", "/ai-platform/ability-train/steps/edit", payload=payload)
        return str(payload["nid"])


def replace_role_mentions(prompt: str, role_ids: Mapping[str, str]) -> str:
    result = prompt
    for name in sorted(role_ids, key=len, reverse=True):
        # Markdown drafts commonly place Chinese prose directly after an @name.
        # Keep obvious longer labels intact while still matching "@林医生先提问".
        pattern = rf"@{re.escape(name)}(?![A-Za-z0-9_]|助理|团队|工作室)"
        result = re.sub(pattern, f"<role>{role_ids[name]}</role>", result)
    return result


STEP_EDIT_FIELDS = (
    "nid",
    "trainTaskNid",
    "stepName",
    "description",
    "modelCode",
    "llmPrompt",
    "skills",
    "positionX",
    "positionY",
    "voiceNid",
    "voiceSpeed",
    "voiceType",
    "avatarNid",
    "customDigitalHuman",
    "timeLimit",
    "useWhiteboard",
    "isSkipStep",
    "isNeedBegin",
    "isTransition",
    "flowHideSubtitle",
    "extConfig",
)


def build_step_edit_payload(
    existing_step: Mapping[str, Any], role_ids: Mapping[str, str]
) -> dict[str, Any]:
    payload = {
        key: copy.deepcopy(existing_step.get(key))
        for key in STEP_EDIT_FIELDS
        if key in existing_step
    }
    if not payload.get("skills") and isinstance(existing_step.get("skillList"), list):
        payload["skills"] = ",".join(
            str(item["nid"])
            for item in existing_step["skillList"]
            if isinstance(item, dict) and item.get("nid")
        )
    payload["llmPrompt"] = replace_role_mentions(
        str(existing_step.get("llmPrompt") or ""), role_ids
    )
    return payload


def ensure_skill(
    client: Any,
    task_id: str,
    type_nid: str,
    spec: SkillSpec,
    existing_skills: list[dict[str, Any]],
) -> tuple[str, bool]:
    existing = next((item for item in existing_skills if item.get("name") == spec.name), None)
    if existing:
        return str(existing["nid"]), False
    payload = {
        "trainTaskNid": task_id,
        "typeNid": type_nid,
        "name": spec.name,
        "packageName": spec.name,
        "description": spec.description,
        "businessConfig": None,
        "instruction": spec.instruction,
    }
    skill_id = client.create_skill(payload)
    existing_skills.append({"nid": skill_id, "name": spec.name})
    return skill_id, True


def build_role_payload(
    task_id: str,
    spec: RoleSpec,
    skill_ids: Sequence[str],
    custom_digital_human: str,
) -> dict[str, Any]:
    return {
        "trainTaskNid": task_id,
        "nickname": spec.nickname,
        "roleName": spec.role_name,
        "modelCode": MODEL_CODE,
        "prompt": spec.prompt,
        "voiceNid": spec.voice_nid,
        "voiceType": spec.voice_type,
        "voiceSpeed": 1,
        "avatarNid": spec.avatar_nid,
        "customDigitalHuman": custom_digital_human,
        "description": spec.description,
        "skills": ",".join(skill_ids),
        "searchEngine": 0,
        "knowledgeSearch": 0,
        "knowledgeFileIds": [],
    }


def upsert_role(
    client: Any,
    task_id: str,
    spec: RoleSpec,
    skill_ids: Sequence[str],
    custom_digital_human: str,
    existing_roles: list[dict[str, Any]],
) -> tuple[str, bool]:
    payload = build_role_payload(task_id, spec, skill_ids, custom_digital_human)
    existing = next(
        (item for item in existing_roles if item.get("nickname") == spec.nickname), None
    )
    if existing:
        payload["nid"] = existing["nid"]
        return client.edit_role(payload), False
    role_id = client.create_role(payload)
    existing_roles.append({"nid": role_id, "nickname": spec.nickname})
    return role_id, True


def find_exact_digital_human(
    owners: Iterable[Mapping[str, Any]], spec: RoleSpec
) -> str:
    for owner in owners:
        name = owner.get("digitalHumanName") or owner.get("name")
        if (
            name == spec.digital_human_name
            and owner.get("voiceNid") == spec.voice_nid
            and owner.get("avatarNid") == spec.avatar_nid
        ):
            return extract_id(owner, "customNid", "digitalHumanNid", "nid")
    return ""


def ensure_digital_human(
    client: PolymasClient,
    user_nid: str,
    spec: RoleSpec,
    owners: list[dict[str, Any]],
) -> tuple[str, bool]:
    existing_id = find_exact_digital_human(owners, spec)
    if existing_id:
        return existing_id, False
    payload = {
        "userNid": user_nid,
        "type": "NORMAL",
        "voiceNid": spec.voice_nid,
        "avatarNid": spec.avatar_nid,
        "digitalHumanName": spec.digital_human_name,
    }
    custom_id = client.create_digital_human(payload)
    owners.append(
        {
            "customNid": custom_id,
            "digitalHumanName": spec.digital_human_name,
            "voiceNid": spec.voice_nid,
            "avatarNid": spec.avatar_nid,
        }
    )
    return custom_id, True


def require_resource_ids(
    resources: Iterable[Mapping[str, Any]], expected_ids: set[str], keys: Sequence[str]
) -> None:
    available = {
        str(item.get(key))
        for item in resources
        for key in keys
        if item.get(key) is not None
    }
    missing = expected_ids - available
    if missing:
        raise RuntimeError(f"当前账号资源库缺少 ID: {', '.join(sorted(missing))}")


def instruction_from_detail(detail: Mapping[str, Any]) -> str:
    nested = detail.get("skillDetailVO")
    if isinstance(nested, dict) and nested.get("instruction"):
        return str(nested["instruction"])
    return str(detail.get("instruction") or "")


def verify_configuration(
    client: PolymasClient,
    task_id: str,
    role_specs: Sequence[RoleSpec],
    role_ids: Mapping[str, str],
) -> None:
    roles = client.list_roles(task_id)
    role_by_name = {item.get("nickname"): item for item in roles}
    skills = client.list_skills(task_id)
    skill_by_name = {item.get("name"): item for item in skills}

    errors: list[str] = []
    for spec in role_specs:
        listed = role_by_name.get(spec.nickname)
        if not listed or str(listed.get("nid")) != role_ids.get(spec.nickname):
            errors.append(f"成员列表缺少 {spec.nickname}")
            continue
        detail = client.role_detail(str(listed["nid"]))
        actual_skill_names = {
            item.get("name") for item in (detail.get("skillList") or []) if isinstance(item, dict)
        }
        expected_skill_names = {item.name for item in spec.skills}
        for field, expected in (
            ("voiceNid", spec.voice_nid),
            ("voiceType", spec.voice_type),
            ("avatarNid", spec.avatar_nid),
        ):
            if detail.get(field) != expected:
                errors.append(f"{spec.nickname}.{field} 回查不一致")
        if not detail.get("customDigitalHuman"):
            errors.append(f"{spec.nickname}.customDigitalHuman 为空")
        if actual_skill_names != expected_skill_names:
            errors.append(
                f"{spec.nickname} 技能不一致: {sorted(actual_skill_names)}"
            )
        if len(str(detail.get("prompt") or "")) < 100:
            errors.append(f"{spec.nickname}.prompt 长度异常")

        for skill_spec in spec.skills:
            listed_skill = skill_by_name.get(skill_spec.name)
            if not listed_skill:
                errors.append(f"技能列表缺少 {skill_spec.name}")
                continue
            skill_detail = client.skill_detail(str(listed_skill["nid"]))
            if instruction_from_detail(skill_detail).strip() != skill_spec.instruction.strip():
                errors.append(f"技能指令回查不一致: {skill_spec.name}")

    for step in client.list_steps(task_id):
        prompt = str(step.get("llmPrompt") or "")
        for name, role_id in role_ids.items():
            if re.search(
                rf"@{re.escape(name)}(?![A-Za-z0-9_]|助理|团队|工作室)", prompt
            ):
                errors.append(f"步骤 {step.get('nid')} 仍含 @{name}")
            if f"<role>{role_id}</role>" not in prompt:
                errors.append(f"步骤 {step.get('nid')} 缺少 {name} 的角色引用")

    if errors:
        raise RuntimeError("配置回查失败:\n- " + "\n- ".join(errors))


def configure(
    client: PolymasClient,
    *,
    task_id: str,
    course_id: str,
    library_id: str,
    expected_account: str,
    apply: bool,
) -> dict[str, Any]:
    user = client.current_user()
    real_name = str(user.get("realName") or user.get("nickName") or "")
    user_nid = str(user.get("userNid") or "")
    if not user_nid:
        raise RuntimeError("当前用户响应缺少 userNid")
    if expected_account and real_name != expected_account:
        raise RuntimeError(
            f"账号校验失败：当前为“{real_name}”，期望“{expected_account}”"
        )

    roles = client.list_roles(task_id)
    skills = client.list_skills(task_id)
    steps = client.list_steps(task_id)
    voices = client.list_voices(course_id)
    avatars = client.list_avatars(user_nid, course_id, library_id)
    owners = client.list_digital_humans(user_nid, course_id, library_id)

    require_resource_ids(
        voices, {spec.voice_nid for spec in ROLE_SPECS}, ("nid", "voiceNid")
    )
    require_resource_ids(
        avatars, {spec.avatar_nid for spec in ROLE_SPECS}, ("nid", "avatarNid")
    )

    plan = {
        "account": real_name,
        "taskId": task_id,
        "existingRoleNames": [item.get("nickname") for item in roles],
        "existingSkillNames": [item.get("name") for item in skills],
        "stepsWithPlainMentions": sum(
            any(f"@{spec.nickname}" in str(step.get("llmPrompt") or "") for spec in ROLE_SPECS)
            for step in steps
        ),
        "apply": apply,
    }
    if not apply:
        return plan

    role_ids: dict[str, str] = {}
    created_skills: list[str] = []
    created_humans: list[str] = []
    created_roles: list[str] = []

    for spec in ROLE_SPECS:
        skill_ids: list[str] = []
        for skill_spec in spec.skills:
            skill_id, created = ensure_skill(
                client,
                task_id,
                CUSTOM_SKILL_TYPE_NID,
                skill_spec,
                skills,
            )
            skill_ids.append(skill_id)
            if created:
                created_skills.append(skill_spec.name)

        custom_id, created = ensure_digital_human(client, user_nid, spec, owners)
        if created:
            created_humans.append(spec.digital_human_name)

        role_id, created = upsert_role(
            client,
            task_id,
            spec,
            skill_ids,
            custom_id,
            roles,
        )
        role_ids[spec.nickname] = role_id
        if created:
            created_roles.append(spec.nickname)

    updated_steps: list[str] = []
    for step in steps:
        payload = build_step_edit_payload(step, role_ids)
        if payload.get("llmPrompt") == step.get("llmPrompt"):
            continue
        updated_steps.append(client.edit_step(payload))

    verify_configuration(client, task_id, ROLE_SPECS, role_ids)
    return {
        **plan,
        "roleIds": role_ids,
        "createdSkills": created_skills,
        "createdDigitalHumans": created_humans,
        "createdRoles": created_roles,
        "updatedStepIds": updated_steps,
        "verified": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="配置简易数字X光成像模拟系统 Pro 任务中的林医生和老周"
    )
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--course-id", default=DEFAULT_COURSE_ID)
    parser.add_argument("--library-id", default=DEFAULT_LIBRARY_ID)
    parser.add_argument("--expected-account", default=DEFAULT_EXPECTED_ACCOUNT)
    parser.add_argument("--env-file", default=str(Path(__file__).resolve().parents[1] / ".env"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际创建/更新平台数据；省略时仅检查并输出计划",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(args.env_file, override=True)
    authorization = os.getenv("AUTHORIZATION", "").strip()
    cookie = os.getenv("COOKIE", "").strip()
    if not authorization or not cookie:
        raise RuntimeError(f"{args.env_file} 缺少 AUTHORIZATION 或 COOKIE")

    client = PolymasClient(authorization, cookie)
    result = configure(
        client,
        task_id=args.task_id,
        course_id=args.course_id,
        library_id=args.library_id,
        expected_account=args.expected_account,
        apply=args.apply,
    )
    mode = "执行完成" if args.apply else "检查完成（未写入）"
    print(f"{mode}: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
