"""Sanxingdui consecutive-interp student-prompt rules and 4-stage script shape."""
from pathlib import Path

import auto_script_train as ast
from skill_training_build.create_task_from_markdown import parse_markdown

COURSE_DIR = Path(
    "/Users/zhangyichi/工作/能力训练/skills_training_course/中国民用航天学院-口译"
)
SCRIPT = COURSE_DIR / "训练剧本配置_三星堆博物馆口译实训.md"

PARAGRAPHS = [
    "各位游客大家好，欢迎来到三星堆博物馆，我是讲解员林晓。",
    "在正式参观之前，我想先介绍一下巴蜀文化。",
    "巴蜀文化指的是以四川盆地为中心的区域文化，距今已有数千年。",
    "它是中华文明的重要组成部分，与中原文化长期交流、互相影响。",
    "中华文明的特点是多元一体，各地文化既各具特色，又统一于整体。",
    "三星堆遗址位于四川省德阳市广汉市，距离成都约三十八公里。",
    "遗址总面积约十二平方公里，核心区域约三点六平方公里。",
    "遗址的文化堆积距今约四千五百年至两千八百年，延续了两千多年。",
    "一九八六年，考古工作者在这里发现了一号、二号两座祭祀坑。",
    "二零一九年以后，又陆续发现了六座，目前共发现八座祭祀坑。",
    "这八座坑的年代为商代晚期，距今约三千二百年至三千年。",
    "三星堆是迄今我国西南地区发现的规模最大、延续时间最长的古文化遗址。",
    "下面我为大家介绍几件代表性文物，首先是青铜面具。",
    "青铜面具最突出的特征是夸张的造型和向外凸出的双眼。",
    "它的双眼呈柱状向前伸出，学界称之为\"纵目\"。",
    "接下来是青铜大立人像，它通高两米六二，是同时期体量最大的青铜人物雕像。",
    "大立人身穿三层衣，衣上装饰着精美的龙纹，双手环握于胸前。",
    "再请看这件金面具，它出土于五号祭祀坑，是目前发现最完整的金面具。",
    "此外还有青铜神树，高三米九六，是中国现存最高大的单件青铜文物。",
    "新出土的文物中还有大量象牙、玉器和丝绸遗痕。",
    "为了保护这些珍贵文物，我们运用了三维扫描、数字复原等现代技术。",
    "文物修复馆向公众开放，大家可以近距离观看修复过程。",
    "下面介绍一下交通方式，如果您是自驾前来，从成都出发大约需要一个小时。",
    "也可以乘坐高铁到广汉北站，再换乘公交车或出租车到达博物馆。",
    "成都市区还开通了旅游专线大巴，可以直达博物馆门口。",
    "馆区内设有停车场，节假日车位紧张，建议大家尽量选择公共交通。",
    "三星堆遗址以其独特面貌，展现了中华文明的多样性与创造力。",
    "它已列入《中国世界文化遗产预备名单》，正在与金沙遗址联合申遗。",
    "建议参观时间不少于三个小时，重点观看综合馆和青铜馆。",
    "希望大家不只看到文物之美，更能理解它背后的文明内涵。我的讲解到此结束，谢谢！",
]


def test_interp_turn_uses_full_english_render_rules():
    q = "各位游客大家好，欢迎来到三星堆博物馆，我是讲解员林晓。请翻译。"
    assert ast.is_consecutive_interp_turn(q)
    rules = "\n".join(ast.build_chinese_student_output_rules(q, ""))
    assert "完整英文译文" in rules
    assert "500" in rules or str(ast.INTERP_STUDENT_MAX_CHARS) in rules
    assert "急救顺序" not in rules


LIVE_DEBRIEF_OPENING = (
    "我是陈文博，接下来由我对你的交传表现做复盘。请稍等，我先对照五项标准给你打分。"
)


def test_debrief_opening_does_not_tell_student_to_say_done():
    """Live runCard opening contains 交传表现; must NOT push 完成 before the score table."""
    assert ast.is_debrief_opening(LIVE_DEBRIEF_OPENING)
    assert not ast.is_debrief_turn(LIVE_DEBRIEF_OPENING)
    assert not ast.has_score_table(LIVE_DEBRIEF_OPENING)
    rules = "\n".join(ast.build_chinese_student_output_rules(LIVE_DEBRIEF_OPENING, ""))
    assert "我准备好了" in rules
    assert "不要说「完成」" in rules or "禁止" in rules and "完成" in rules
    assert "我没有其他问题了，完成" not in rules


def test_after_score_table_student_may_finish():
    table = (
        "【实训评分表】\n"
        "| 评分项 | 得分 | 满分 |\n"
        "| 英文交流能力 | 14 | 15 |\n"
        "| 口译信息完整度 | 28 | 30 |\n"
        "【亮点】\n1. 祭祀坑译为 sacrificial pit"
    )
    assert ast.has_score_table(table)
    assert ast.is_debrief_turn(table)
    assert not ast.is_debrief_opening(table)
    rules = "\n".join(ast.build_chinese_student_output_rules(table, ""))
    assert "完成" in rules
    assert "实训评分表" in rules or "评分表" in rules


def test_nursing_hint_only_when_context_is_nursing():
    general = "\n".join(ast.build_chinese_student_output_rules("你准备好了吗？", "三星堆博物馆口译"))
    assert "急救顺序" not in general
    nursing = "\n".join(
        ast.build_chinese_student_output_rules("下一步做什么？", "急性广泛前壁心肌梗死急救护理")
    )
    assert "急救顺序" in nursing


def test_four_stage_script_is_consecutive_interp_not_english_commentary():
    assert SCRIPT.exists(), SCRIPT
    steps = parse_markdown(SCRIPT)
    assert len(steps) == 4, [s.get("stepName") for s in steps]
    names = [s.get("stepName") for s in steps]
    assert any(k in names[2] for k in ("交传", "传译", "讲解"))
    s3 = steps[2]["llmPrompt"]
    assert "请翻译" in s3
    assert "不得" in s3 and "评价" in s3
    for para in PARAGRAPHS:
        assert para in s3, para
    s2 = steps[1]["llmPrompt"] + "\n" + steps[1]["prologue"]
    assert "diversity in unity" not in s2.lower()
    assert "unity in diversity" not in s2.lower()
    s1p = steps[0]["llmPrompt"] + "\n" + steps[0]["prologue"]
    assert "diversity in unity" not in s1p.lower()
    s4 = steps[3]["llmPrompt"]
    assert "实训评分表" in s4
    assert "口译信息完整度" in s4
    assert "评分表未输出" in s4 or "评分表尚未" in s4 or "夹带" in s4
    flows = [s.get("flowCondition") for s in steps]
    assert flows[0] == "进入讲解员沟通阶段"
    assert flows[1] == "进入交传实战阶段"
    assert flows[2] == "进入复盘阶段"
    assert flows[3] == "训练完成"
