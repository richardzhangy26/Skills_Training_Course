"""
题卷类型 (exam_paper) PDF 报告生成器

基于 generate_report.py 适配题卷类型数据结构：
- 使用 questionScores 而非 dimensionScores
- overallComment 而非 comprehensiveComment
- 无顶层 fullMark，从 questionScores[].totalScore 累加
- 评分结果以网格卡片展示（5列），首卡为总得分 + ScoreRing
- 无雷达图
"""

import argparse
import datetime
import json
import math
import os
from xml.sax.saxutils import escape

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Flowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.styles import ParagraphStyle
except ImportError as exc:  # pragma: no cover - runtime dependency
    raise SystemExit(
        "Missing dependency: reportlab. Install with `pip install reportlab`."
    ) from exc

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.join(SCRIPT_DIR, "result.json")
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "report_exam.pdf")

PAGE_MARGIN = 16 * mm
CONTAINER_PADDING = 12 * mm

COLOR_BG = colors.HexColor("#f5f7fa")
COLOR_CARD = colors.HexColor("#ffffff")
COLOR_MUTED = colors.HexColor("#9aa0a6")
COLOR_TEXT = colors.HexColor("#2c3e50")
COLOR_PRIMARY = colors.HexColor("#2962FF")
COLOR_BORDER = colors.HexColor("#e9edf3")
COLOR_SOFT = colors.HexColor("#f7f9fc")


# -------- Font Utilities --------


def register_cjk_font():
    candidates = [
        ("PingFangSC", "/System/Library/Fonts/PingFang.ttc", [0, 1, 2, 3]),
        ("STHeiti", "/System/Library/Fonts/STHeiti Medium.ttc", [0]),
        ("HiraginoSansGB", "/System/Library/Fonts/Hiragino Sans GB.ttc", [0]),
        ("SongtiSC", "/System/Library/Fonts/Songti.ttc", [0]),
        ("MicrosoftYaHei", "C:/Windows/Fonts/msyh.ttc", [0]),
        ("NotoSansCJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", [0]),
    ]
    for font_name, path, indices in candidates:
        if not os.path.exists(path):
            continue
        for idx in indices:
            try:
                pdfmetrics.registerFont(TTFont(font_name, path, subfontIndex=idx))
                return font_name
            except Exception:
                continue
    return "Helvetica"


FONT_NAME = register_cjk_font()


# -------- Text Helpers --------


def markdown_bold_to_html(text: str) -> str:
    parts = text.split("**")
    if len(parts) == 1:
        return escape(text)
    html_parts = []
    for idx, part in enumerate(parts):
        safe = escape(part)
        if idx % 2 == 1:
            html_parts.append(f"<b>{safe}</b>")
        else:
            html_parts.append(safe)
    return "".join(html_parts)


def truncate_text(text: str, max_chars: int) -> str:
    clean = " ".join(text.replace("\n", " ").split())
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rstrip() + "..."


def format_score(score) -> str:
    """格式化分数：整数不带小数点，小数保留"""
    if isinstance(score, float) and score == int(score):
        return str(int(score))
    return str(score)


# -------- Custom Flowables --------


class CircleBadge(Flowable):
    def __init__(self, text, diameter=18, fill=COLOR_PRIMARY, text_color=colors.white):
        super().__init__()
        self.text = text
        self.diameter = diameter
        self.fill = fill
        self.text_color = text_color

    def wrap(self, avail_width, avail_height):
        return self.diameter, self.diameter

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(self.fill)
        canvas.circle(
            self.diameter / 2, self.diameter / 2, self.diameter / 2, stroke=0, fill=1
        )
        canvas.setFillColor(self.text_color)
        canvas.setFont(FONT_NAME, 9)
        canvas.drawCentredString(
            self.diameter / 2,
            self.diameter / 2 - 3,
            self.text,
        )
        canvas.restoreState()


class ScoreRing(Flowable):
    """圆环进度条，用于展示总得分占比"""

    def __init__(self, score, full_mark=100, size=50):
        super().__init__()
        self.score = score
        self.full_mark = full_mark
        self.size = size

    def wrap(self, avail_width, avail_height):
        return self.size, self.size

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        center = self.size / 2
        radius = center - 4
        canvas.setLineWidth(4)
        canvas.setStrokeColor(COLOR_BORDER)
        canvas.circle(center, center, radius, stroke=1, fill=0)
        canvas.setStrokeColor(COLOR_PRIMARY)
        canvas.setLineCap(1)
        ratio = min(self.score / self.full_mark, 1.0) if self.full_mark > 0 else 0
        extent = -360 * ratio
        canvas.arc(4, 4, self.size - 4, self.size - 4, startAng=90, extent=extent)
        canvas.restoreState()


class TotalScoreCard(Flowable):
    """总得分卡片：包含分数文本 + 圆环"""

    def __init__(self, score, full_mark, width=120, height=80):
        super().__init__()
        self.score = score
        self.full_mark = full_mark
        self.width = width
        self.height = height

    def wrap(self, avail_width, avail_height):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()

        # 背景
        canvas.setFillColor(colors.HexColor("#EEF2FF"))
        canvas.roundRect(0, 0, self.width, self.height, 8, stroke=0, fill=1)

        # 标签
        canvas.setFont(FONT_NAME, 9)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawCentredString(self.width / 2, self.height - 14, "总得分")

        # 圆环
        ring_size = 36
        ring_x = (self.width - ring_size) / 2
        ring_y = 8

        # 绘制圆环背景
        center_x = ring_x + ring_size / 2
        center_y = ring_y + ring_size / 2
        ring_radius = ring_size / 2 - 3
        canvas.setLineWidth(3.5)
        canvas.setStrokeColor(COLOR_BORDER)
        canvas.circle(center_x, center_y, ring_radius, stroke=1, fill=0)

        # 绘制圆环进度
        canvas.setStrokeColor(COLOR_PRIMARY)
        canvas.setLineCap(1)
        ratio = min(self.score / self.full_mark, 1.0) if self.full_mark > 0 else 0
        extent = -360 * ratio
        canvas.arc(
            ring_x + 3,
            ring_y + 3,
            ring_x + ring_size - 3,
            ring_y + ring_size - 3,
            startAng=90,
            extent=extent,
        )

        # 圆环内分数
        score_text = format_score(self.score)
        canvas.setFont(FONT_NAME, 11)
        canvas.setFillColor(COLOR_PRIMARY)
        canvas.drawCentredString(center_x, center_y - 4, score_text)

        canvas.restoreState()


class QuestionScoreCard(Flowable):
    """单题得分卡片"""

    def __init__(self, label, score, full, width=120, height=80):
        super().__init__()
        self.label = label
        self.score = score
        self.full = full
        self.width = width
        self.height = height

    def wrap(self, avail_width, avail_height):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()

        # 背景
        canvas.setFillColor(COLOR_SOFT)
        canvas.roundRect(0, 0, self.width, self.height, 8, stroke=0, fill=1)

        # 标签（支持两行）
        label_lines = [self.label]
        if len(self.label) > 8:
            label_lines = [self.label[:8], self.label[8:16]]

        canvas.setFont(FONT_NAME, 8.5)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        y = self.height - 14
        for line in label_lines[:2]:
            canvas.drawCentredString(self.width / 2, y, line)
            y -= 11

        # 分数
        score_text = format_score(self.score)
        full_text = f"/ {format_score(self.full)}"
        score_size = 18
        full_size = 9
        score_width = pdfmetrics.stringWidth(score_text, FONT_NAME, score_size)
        full_width = pdfmetrics.stringWidth(full_text, FONT_NAME, full_size)
        total_width = score_width + 4 + full_width
        start_x = (self.width - total_width) / 2
        base_y = 12

        canvas.setFont(FONT_NAME, score_size)
        canvas.setFillColor(colors.HexColor("#111827"))
        canvas.drawString(start_x, base_y, score_text)
        canvas.setFont(FONT_NAME, full_size)
        canvas.setFillColor(colors.HexColor("#9aa0a6"))
        canvas.drawString(start_x + score_width + 4, base_y + 4, full_text)

        canvas.restoreState()


# -------- Layout Builders --------


def build_styles():
    return {
        "title": ParagraphStyle(
            "title",
            fontName=FONT_NAME,
            fontSize=14,
            leading=18,
            textColor=COLOR_TEXT,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName=FONT_NAME,
            fontSize=9,
            leading=12,
            textColor=COLOR_MUTED,
            alignment=TA_RIGHT,
        ),
        "section": ParagraphStyle(
            "section",
            fontName=FONT_NAME,
            fontSize=13,
            leading=16,
            textColor=COLOR_TEXT,
        ),
        "label": ParagraphStyle(
            "label",
            fontName=FONT_NAME,
            fontSize=10,
            leading=12,
            textColor=COLOR_MUTED,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=17,
            textColor=colors.HexColor("#374151"),
        ),
        "summary": ParagraphStyle(
            "summary",
            fontName=FONT_NAME,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#6b7280"),
        ),
        "score": ParagraphStyle(
            "score",
            fontName=FONT_NAME,
            fontSize=32,
            leading=32,
            textColor=COLOR_PRIMARY,
        ),
    }


def build_header(styles, refined, available_width):
    icon = CircleBadge(
        "评", diameter=22, fill=colors.HexColor("#E3F2FD"), text_color=COLOR_PRIMARY
    )
    title = Paragraph("测评报告 Evaluation Report", styles["title"])
    left_width = available_width * 0.68
    right_width = available_width - left_width
    left = Table([[icon, title]], colWidths=[24, max(left_width - 24, 120)])
    left.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    meta_text = f"提交时间: {refined['timestamp']}"
    meta = Paragraph(meta_text, styles["meta"])

    header = Table([[left, meta]], colWidths=[left_width, right_width])
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BORDER),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return header


def build_score_cards(refined, available_width):
    """构建评分结果卡片网格（总分卡 + 各题目卡片，5列布局）"""
    num_cols = 5
    gap = 10
    card_width = (available_width - gap * (num_cols - 1)) / num_cols
    card_height = 80

    # 总分卡
    total_card = TotalScoreCard(
        refined["total_score"],
        refined["full_mark"],
        width=card_width,
        height=card_height,
    )

    # 各题目卡片
    question_cards = [
        QuestionScoreCard(
            q["name"], q["score"], q["full"], width=card_width, height=card_height
        )
        for q in refined["questions"]
    ]

    all_cards = [total_card] + question_cards

    # 构建列宽（卡片 + 间距交替）
    widths = []
    for idx in range(num_cols):
        widths.append(card_width)
        if idx < num_cols - 1:
            widths.append(gap)

    rows = []
    for start in range(0, len(all_cards), num_cols):
        row_cards = all_cards[start : start + num_cols]
        row = []
        for idx in range(num_cols):
            if idx < len(row_cards):
                # 更新卡片宽度以匹配
                row_cards[idx].width = card_width
                row.append(row_cards[idx])
            else:
                row.append(Spacer(card_width, card_height))
            if idx < num_cols - 1:
                row.append(Spacer(gap, card_height))
        rows.append(row)

    table = Table(rows, colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def build_section_header(styles, title, color, badge_text):
    badge = CircleBadge(badge_text, diameter=18, fill=color, text_color=colors.white)
    title_para = Paragraph(title, styles["section"])
    header = Table([[badge, title_para]], colWidths=[22, 200])
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return header


def build_suggestion_block(text, styles, width):
    safe_text = markdown_bold_to_html(text)
    para = Paragraph(safe_text, styles["body"])
    table = Table([[para]], colWidths=[width])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_SOFT),
                ("LINEBEFORE", (0, 0), (0, 0), 3, COLOR_PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def draw_background(canvas, doc):
    canvas.saveState()
    width, height = doc.pagesize
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    x = PAGE_MARGIN
    y = PAGE_MARGIN
    w = width - 2 * PAGE_MARGIN
    h = height - 2 * PAGE_MARGIN
    canvas.setFillColor(COLOR_CARD)
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(1)
    canvas.roundRect(x, y, w, h, 12, stroke=1, fill=1)
    canvas.restoreState()


def build_story(refined, doc):
    styles = build_styles()
    story = []

    # Header
    story.append(build_header(styles, refined, doc.width))
    story.append(Spacer(1, 16))

    # 评分结果
    story.append(
        build_section_header(styles, "评分结果", colors.HexColor("#42A5F5"), "分")
    )
    story.append(Spacer(1, 10))
    story.append(build_score_cards(refined, doc.width))
    story.append(Spacer(1, 20))

    # 综合评语
    story.append(
        build_section_header(styles, "综合评语", colors.HexColor("#FF5252"), "评")
    )
    story.append(Spacer(1, 8))
    comment_blocks = [
        blk.strip() for blk in refined["comment"].split("\n\n") if blk.strip()
    ]
    for idx, block in enumerate(comment_blocks):
        safe = markdown_bold_to_html(block).replace("\n", "<br/>")
        story.append(Paragraph(safe, styles["body"]))
        if idx != len(comment_blocks) - 1:
            story.append(Spacer(1, 8))
    story.append(Spacer(1, 18))

    # 改进建议
    story.append(
        build_section_header(styles, "改进建议", colors.HexColor("#66BB6A"), "改")
    )
    story.append(Spacer(1, 8))
    for sug in refined["suggestions"]:
        story.append(build_suggestion_block(sug, styles, doc.width))
        story.append(Spacer(1, 8))

    return story


def load_data(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    core_data = data["data"]["artifacts"][0]["parts"][0]["data"]
    meta_info = data["data"]["status"]

    question_scores = core_data.get("questionScores", [])
    full_mark = sum(q.get("totalScore", 0) for q in question_scores)

    refined = {
        "total_score": core_data["totalScore"],
        "full_mark": full_mark if full_mark > 0 else 100,
        "status_state": meta_info["state"],
        "timestamp": datetime.datetime.fromisoformat(meta_info["timestamp"]).strftime(
            "%Y-%m-%d %H:%M"
        ),
        "comment": core_data.get("overallComment", ""),
        "suggestions": core_data.get("improvementSuggestions", []),
        "questions": [],
    }

    for q in question_scores:
        refined["questions"].append(
            {
                "name": q.get("name", f"题目{q.get('questionIndex', '?')}"),
                "score": q.get("score", 0),
                "full": q.get("totalScore", 0),
                "comment": q.get("comment", ""),
                "answer": q.get("answer", ""),
            }
        )

    return refined


def generate_pdf(input_path, output_path):
    refined = load_data(input_path)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=PAGE_MARGIN + CONTAINER_PADDING,
        rightMargin=PAGE_MARGIN + CONTAINER_PADDING,
        topMargin=PAGE_MARGIN + CONTAINER_PADDING,
        bottomMargin=PAGE_MARGIN + CONTAINER_PADDING,
    )

    story = build_story(refined, doc)
    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate PDF evaluation report for exam paper type."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input JSON file path")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PDF file path")
    return parser.parse_args()


def main():
    args = parse_args()
    generate_pdf(args.input, args.output)
    print(f"PDF Report generated at: {args.output}")


if __name__ == "__main__":
    main()
