import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    PROJECT_ROOT
    / ".claude"
    / "skills"
    / "training-pro-script-generator"
    / "scripts"
    / "validate_pro_config.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_pro_config", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def valid_config() -> str:
    return """# 测试任务 - 能力训练 Pro 配置

## 全局配置
- **能力名称**: 测试任务
- **描述**: 用于验证 Pro 配置格式

## 全局成员配置

### 成员1: 林医生
- **角色名称**: 影像科医生
- **角色描述**: 三甲医院影像科主治医师，负责提出临床需求并反馈设备试用现象。
- **角色提示词**: 你是林医生。只从临床使用者角度提出需求、报告现象和评价结果；表达专业亲和，每次聚焦一至两点；不得替用户选择器件、电路、程序或直接给出排障结论，必须把设计和判断交还给用户完成。
- **模型**: Doubao-Seed-2.0-pro
- **数字人名称**: 林医生
- **数字人类型**: NORMAL
- **声音名称**: 知性女声 2.0
- **声音资源ID**: TTS2cuBiZ
- **声音参数**: zh_female_zhixingnv_uranus_bigtts
- **声音选择条件**: 中文、成年女性、知性、专业、亲和
- **形象资源ID**: VE2yJykMDZ
- **形象描述**: 中国成年女性，浅蓝职业装，专业亲和，适合医护或教师角色
- **数字人组合ID**: 运行时解析
- **技能**:
  - 临床需求提出 | 类型: custom_skill | 描述: 需要注入医生视角需求时触发
    <skill_instruction>
    # codemap
    ### 命令
    - /need 临床需求：提出具体临床需求
    ### 使用场景
    用户完成初步方案后触发。
    ### 执行规则
    1. 只描述需求，不给技术实现。
    ### 输出解释
    1. 输出临床情境、具体需求和交还问题。
    ### 示例
    用户：我的方案完成了。
    模型：临床示教需要连续灰阶，你准备如何满足？
    </skill_instruction>

## 训练剧本

### 阶段1: 需求分析
**卡片描述**: 识别临床成像需求
**用户扮演角色名称**: 单片机开发学生
**AI 对用户称呼**: 同学
**用户扮演角色描述**: 用户负责完成需求分析并提出实现思路。
**剧本模型**: Doubao-Seed-2.0-pro
**对话结束策略**: 达成目标后结束
**是否可跳过**: 否
**后继阶段**: END
**背景图描述**: 医院影像科设备需求讨论室

**阶段剧本提示词**:
<script_prompt>
依据剧本设定统筹实训进程，按既定逻辑调度各角色，有序分配对应任务与履职动作。

【阶段触发条件】
训练开始后进入本阶段。

【背景设定】
用户正在完成成像模拟设备需求分析。

【完整执行流程】
步骤1 - 提出需求：
- 参与人员：@林医生
- 具体动作：@林医生 提出临床需求并等待用户回答。

【阶段结束判定】
用户能够说明需求后结束当前卡片，等待平台运行时切换或结束训练。

【行为边界规范】
- 允许：讨论临床成像需求。
- 禁止：直接替用户完成技术方案。
</script_prompt>
"""


def test_valid_import_ready_config_passes() -> None:
    validator = load_validator()

    assert validator.validate_text(valid_config()) == []


def test_unknown_fixed_resource_and_fixed_custom_id_fail() -> None:
    validator = load_validator()
    text = valid_config().replace("TTS2cuBiZ", "UNKNOWN_VOICE").replace(
        "**数字人组合ID**: 运行时解析",
        "**数字人组合ID**: fixed-custom-id",
    )

    errors = validator.validate_text(text)

    assert any("未知声音资源ID" in error for error in errors)
    assert any("数字人组合ID必须写“运行时解析”" in error for error in errors)


def test_unknown_member_reference_fails() -> None:
    validator = load_validator()
    text = valid_config().replace("@林医生 提出临床需求", "@王老师 提出临床需求")

    errors = validator.validate_text(text)

    assert any("引用了未定义成员 @王老师" in error for error in errors)


def test_user_reference_is_allowed_without_global_member() -> None:
    validator = load_validator()
    text = valid_config().replace(
        "提出临床需求并等待用户回答",
        "提出临床需求并等待@用户 回答",
    )

    assert validator.validate_text(text) == []


def test_legacy_jump_directive_fails() -> None:
    validator = load_validator()
    text = valid_config().replace(
        "等待平台运行时切换或结束训练。",
        "输出 NEXT_TO_STAGE_2 并跳转下一阶段。",
    )

    errors = validator.validate_text(text)

    assert any("旧版跳转指令" in error for error in errors)


def test_member_example_outside_script_prompt_is_ignored() -> None:
    validator = load_validator()
    text = valid_config().replace(
        "# 测试任务 - 能力训练 Pro 配置",
        "# 测试任务 - 能力训练 Pro 配置\n\n> 成员引用格式示例：`@成员名`",
    )

    assert validator.validate_text(text) == []
