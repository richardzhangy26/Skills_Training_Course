"""生成病例三精确文字版辅助检查报告图。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1920
HEIGHT = 1080
COURSE_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills_training_course"
    / "湖南中医药大学-冠心病的中西医结合诊疗"
)
DEFAULT_OUTPUT = (
    COURSE_DIR
    / "辅助检查图片"
    / "病例三_辅助检查报告.png"
)

EXAM_REPORT_DATA = (
    "心电图：窦性心律，V2～V5导联ST段弓背向上抬高，伴T波倒置",
    "肌钙蛋白 I：12.6 ng/mL",
    "CK-MB：85 U/L",
    "总胆固醇：7.2 mmol/L",
    "甘油三酯：3.1 mmol/L",
    "低密度脂蛋白：4.8 mmol/L",
    "高密度脂蛋白：0.9 mmol/L",
    "冠脉造影：左前降支近段完全闭塞；回旋支和右冠斑块形成、轻度狭窄",
)

FONT_REGULAR = Path("/System/Library/Fonts/STHeiti Light.ttc")
FONT_MEDIUM = Path("/System/Library/Fonts/STHeiti Medium.ttc")


def _font(size: int, *, medium: bool = False) -> ImageFont.FreeTypeFont:
    font_path = FONT_MEDIUM if medium else FONT_REGULAR
    return ImageFont.truetype(str(font_path), size=size)


def _rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: str,
    outline: str = "#D9E4EE",
    radius: int = 24,
) -> None:
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=2,
    )


def _draw_section(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    number: str,
    title: str,
    lines: tuple[str, ...],
    critical_lines: tuple[int, ...] = (),
) -> None:
    x1, y1, x2, y2 = box
    _rounded_panel(draw, box, fill="#FFFFFF")
    draw.ellipse(
        (x1 + 30, y1 + 30, x1 + 88, y1 + 88),
        fill="#1D5E8C",
    )
    draw.text(
        (x1 + 59, y1 + 59),
        number,
        font=_font(26, medium=True),
        fill="#FFFFFF",
        anchor="mm",
    )
    draw.text(
        (x1 + 110, y1 + 34),
        title,
        font=_font(36, medium=True),
        fill="#17324D",
    )
    line_y = y1 + 112
    for index, line in enumerate(lines):
        fill = "#B42318" if index in critical_lines else "#334E68"
        draw.text(
            (x1 + 38, line_y),
            line,
            font=_font(29, medium=index in critical_lines),
            fill=fill,
        )
        line_y += 58


def generate_report(output_path: Path = DEFAULT_OUTPUT) -> Path:
    """Render a deterministic 16:9 report card with exact medical values."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), "#EEF4F8")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, WIDTH, 190), fill="#123B5D")
    draw.text(
        (90, 52),
        "冠心病中西医结合诊疗模拟训练",
        font=_font(52, medium=True),
        fill="#FFFFFF",
    )
    draw.text(
        (92, 125),
        "病例三｜辅助检查报告",
        font=_font(32),
        fill="#D9ECF7",
    )
    draw.rounded_rectangle(
        (1515, 54, 1832, 136),
        radius=40,
        fill="#E8F3FA",
    )
    draw.text(
        (1674, 95),
        "教学模拟资料",
        font=_font(30, medium=True),
        fill="#123B5D",
        anchor="mm",
    )

    margin_x = 78
    gap = 34
    panel_width = (WIDTH - 2 * margin_x - gap) // 2
    left_x = margin_x
    right_x = margin_x + panel_width + gap

    _draw_section(
        draw,
        (left_x, 235, left_x + panel_width, 490),
        number="1",
        title="心电图",
        lines=(
            "窦性心律",
            "V2～V5导联ST段弓背向上抬高，伴T波倒置",
        ),
        critical_lines=(1,),
    )
    _draw_section(
        draw,
        (right_x, 235, right_x + panel_width, 490),
        number="2",
        title="心肌坏死标志物",
        lines=(
            "肌钙蛋白 I：12.6 ng/mL",
            "CK-MB：85 U/L",
        ),
        critical_lines=(0, 1),
    )
    _draw_section(
        draw,
        (left_x, 525, left_x + panel_width, 870),
        number="3",
        title="血脂四项",
        lines=(
            "总胆固醇：7.2 mmol/L",
            "甘油三酯：3.1 mmol/L",
            "低密度脂蛋白：4.8 mmol/L",
            "高密度脂蛋白：0.9 mmol/L",
        ),
    )
    _draw_section(
        draw,
        (right_x, 525, right_x + panel_width, 870),
        number="4",
        title="冠状动脉造影",
        lines=(
            "左前降支近段完全闭塞",
            "回旋支和右冠斑块形成、轻度狭窄",
        ),
        critical_lines=(0,),
    )

    draw.line((90, 930, 1830, 930), fill="#C7D7E5", width=2)
    draw.text(
        (90, 968),
        "请结合问诊、体格检查与以上结果进行分析，先陈述依据，再作出诊断。",
        font=_font(30),
        fill="#486581",
    )
    draw.text(
        (1830, 1015),
        "数值与单位以本报告为准",
        font=_font(25),
        fill="#829AB1",
        anchor="ra",
    )

    image.save(output_path, format="PNG", optimize=True)
    return output_path


def main() -> None:
    output = generate_report()
    print(output)


if __name__ == "__main__":
    main()
