from pathlib import Path

from skill_training_build import create_task_from_markdown as ctm
from skill_training_build import import_njtech_branching_task as importer


MARKDOWN_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills_training_course"
    / "南京理工-有机化学"
    / "场景一-基础无机操作类能力训练"
    / "训练剧本配置.md"
)


def test_branch_flow_specs_split_all_easter_egg_routes() -> None:
    steps = ctm.parse_markdown(MARKDOWN_PATH)

    specs = importer.build_branch_flow_specs(MARKDOWN_PATH, steps)
    triples = {
        (spec["sourceName"], spec["targetName"], spec["flowCondition"])
        for spec in specs
    }

    assert len(steps) == 16
    assert len(specs) == 26
    assert all("/" not in spec["flowCondition"] for spec in specs)
    assert ("START", "减压过滤规范", "") in triples
    assert ("总结复盘", "END", "TASK_COMPLETE") in triples
    assert ("减压过滤规范", "倒吸事故彩蛋", "NEXT_TO_EGG_BACKFLOW") in triples
    assert ("蒸发与灼烧理论", "蒸发皿炸裂彩蛋", "NEXT_TO_EGG_DRY_CRACK") in triples
    assert ("蒸发与灼烧理论", "高温固体飞溅彩蛋", "NEXT_TO_EGG_HOT_SPLASH") in triples
    assert ("蒸发与灼烧理论", "pH控制", "NEXT_TO_PH_CONTROL") in triples
    assert ("pH控制", "碱液腐蚀彩蛋", "NEXT_TO_EGG_PH_CORROSION") in triples
    assert ("分批加料", "溶液溢出彩蛋", "NEXT_TO_EGG_FEED_OVERFLOW") in triples
    assert ("高温固体飞溅彩蛋", "趁热过滤", "NEXT_TO_HOT_FILTER") in triples
    assert ("蒸发皿炸裂彩蛋", "完整流程梳理", "NEXT_TO_FULL_PROCESS") in triples
