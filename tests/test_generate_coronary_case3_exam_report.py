from pathlib import Path

from PIL import Image

from skill_training_build import generate_coronary_case3_exam_report as report


def test_report_data_contains_all_teacher_visible_units() -> None:
    text = "\n".join(report.EXAM_REPORT_DATA)

    assert "V2～V5导联ST段弓背向上抬高" in text
    assert "肌钙蛋白 I：12.6 ng/mL" in text
    assert "CK-MB：85 U/L" in text
    assert "总胆固醇：7.2 mmol/L" in text
    assert "甘油三酯：3.1 mmol/L" in text
    assert "低密度脂蛋白：4.8 mmol/L" in text
    assert "高密度脂蛋白：0.9 mmol/L" in text
    assert "左前降支近段完全闭塞" in text


def test_generate_report_creates_1920_by_1080_png(tmp_path: Path) -> None:
    output = tmp_path / "report.png"

    result = report.generate_report(output)

    assert result == output
    with Image.open(output) as image:
        assert image.format == "PNG"
        assert image.size == (1920, 1080)
