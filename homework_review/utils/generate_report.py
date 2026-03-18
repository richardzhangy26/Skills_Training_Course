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
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "report.pdf")

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
        canvas.circle(self.diameter / 2, self.diameter / 2, self.diameter / 2, stroke=0, fill=1)
        canvas.setFillColor(self.text_color)
        canvas.setFont(FONT_NAME, 9)
        canvas.drawCentredString(
            self.diameter / 2,
            self.diameter / 2 - 3,
            self.text,
        )
        canvas.restoreState()


class ScoreRing(Flowable):
    def __init__(self, score, size=50):
        super().__init__()
        self.score = score
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
        extent = -360 * (self.score / 100.0)
        canvas.arc(4, 4, self.size - 4, self.size - 4, startAng=90, extent=extent)
        canvas.restoreState()


class RadarChart(Flowable):
    def __init__(self, labels, scores, full_marks, size=240):
        super().__init__()
        self.labels = labels
        self.scores = scores
        self.full_marks = full_marks
        self.size = size

    def wrap(self, avail_width, avail_height):
        return self.size, self.size

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        size = self.size
        cx = size / 2
        cy = size / 2
        radius = (size / 2) - 18
        num_vars = len(self.labels)
        angles = [(2 * math.pi * i / num_vars) - (math.pi / 2) for i in range(num_vars)]

        def draw_polygon(points, stroke_color, fill_color=None, stroke_width=1):
            path = canvas.beginPath()
            path.moveTo(points[0][0], points[0][1])
            for x, y in points[1:]:
                path.lineTo(x, y)
            path.close()
            if fill_color:
                canvas.setFillColor(fill_color)
            canvas.setStrokeColor(stroke_color)
            canvas.setLineWidth(stroke_width)
            canvas.drawPath(path, stroke=1, fill=1 if fill_color else 0)

        # Grid levels
        levels = 5
        for level in range(levels, 0, -1):
            level_r = radius * (level / levels)
            points = [
                (cx + level_r * math.cos(angle), cy + level_r * math.sin(angle))
                for angle in angles
            ]
            stroke = COLOR_BORDER if level < levels else colors.HexColor("#d8dde6")
            draw_polygon(points, stroke)

        # Axis lines + labels
        canvas.setFont(FONT_NAME, 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        for idx, angle in enumerate(angles):
            x_outer = cx + radius * math.cos(angle)
            y_outer = cy + radius * math.sin(angle)
            canvas.setStrokeColor(COLOR_BORDER)
            canvas.setLineWidth(1)
            canvas.line(cx, cy, x_outer, y_outer)

            label_r = radius + 14
            lx = cx + label_r * math.cos(angle)
            ly = cy + label_r * math.sin(angle)
            label_text = self.labels[idx]
            if len(label_text) > 6:
                label_text = label_text[:6] + ".."

            if lx < cx - 5:
                canvas.drawRightString(lx, ly - 3, label_text)
            elif lx > cx + 5:
                canvas.drawString(lx, ly - 3, label_text)
            else:
                canvas.drawCentredString(lx, ly - 3, label_text)

        # Data polygon
        data_points = []
        for score, full, angle in zip(self.scores, self.full_marks, angles):
            ratio = min(score / full, 1)
            r = radius * ratio
            data_points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

        draw_polygon(
            data_points,
            stroke_color=COLOR_PRIMARY,
            fill_color=colors.Color(0.16, 0.38, 1.0, alpha=0.25),
            stroke_width=1.5,
        )

        canvas.setFillColor(COLOR_PRIMARY)
        for x, y in data_points:
            canvas.circle(x, y, 2.2, stroke=0, fill=1)

        canvas.restoreState()


class DimensionCard(Flowable):
    def __init__(self, label, score, full, width=120, height=70):
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
        canvas.setFillColor(COLOR_SOFT)
        canvas.roundRect(0, 0, self.width, self.height, 8, stroke=0, fill=1)

        label_lines = [self.label]
        if len(self.label) > 8:
            label_lines = [self.label[:8], self.label[8:16]]

        canvas.setFont(FONT_NAME, 8.5)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        y = self.height - 16
        for line in label_lines[:2]:
            canvas.drawCentredString(self.width / 2, y, line)
            y -= 11

        score_text = str(self.score)
        full_text = f"/ {self.full}"
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


class GradedScoreCard(Flowable):
    """分档评分卡片 - 用于显示档位范围和标签"""

    def __init__(self, graded_name, label, range_min, range_max,
                 description, is_current, width=100, height=60):
        super().__init__()
        self.graded_name = graded_name
        self.label = label
        self.range_min = range_min
        self.range_max = range_max
        self.description = description
        self.is_current = is_current
        self.width = width
        self.height = height

    def wrap(self, avail_width, avail_height):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()

        # 根据是否当前档位选择颜色
        if self.is_current:
            bg_color = colors.HexColor("#E3F2FD")  # 浅蓝色背景
            border_color = COLOR_PRIMARY
            text_color = COLOR_PRIMARY
        else:
            bg_color = COLOR_SOFT
            border_color = COLOR_BORDER
            text_color = colors.HexColor("#6b7280")

        # 绘制圆角矩形背景
        canvas.setFillColor(bg_color)
        canvas.setStrokeColor(border_color)
        canvas.setLineWidth(2 if self.is_current else 1)
        canvas.roundRect(0, 0, self.width, self.height, 6, stroke=1, fill=1)

        # 绘制档位名称 (如 "分档1")
        canvas.setFont(FONT_NAME, 9)
        canvas.setFillColor(text_color)
        canvas.drawCentredString(self.width / 2, self.height - 14, self.graded_name)

        # 绘制分数范围
        range_text = f"{self.range_min}-{self.range_max}分"
        canvas.setFont(FONT_NAME, 10)
        canvas.setFillColor(colors.HexColor("#111827"))
        canvas.drawCentredString(self.width / 2, self.height - 30, range_text)

        # 绘制标签 (如 "差", "良好" 等)
        canvas.setFont(FONT_NAME, 11)
        canvas.setFillColor(COLOR_PRIMARY if self.is_current else colors.HexColor("#6b7280"))
        label_text = self.label
        if self.is_current:
            label_text = f"{self.label} ★"
        canvas.drawCentredString(self.width / 2, self.height - 46, label_text)

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
    icon = CircleBadge("评", diameter=22, fill=colors.HexColor("#E3F2FD"), text_color=COLOR_PRIMARY)
    title = Paragraph("测评报告 Evaluation Report", styles["title"])
    left_width = available_width * 0.68
    right_width = available_width - left_width
    left = Table([[icon, title]], colWidths=[24, max(left_width - 24, 120)])
    left.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))

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


def build_top_section(styles, refined, labels, scores, full_marks, available_width):
    chart_title = Paragraph("维度得分分布", styles["label"])
    radar = RadarChart(labels, scores, full_marks, size=220)
    left = [chart_title, Spacer(1, 6), radar]

    score_text = f"<font size='32' color='#2962FF'>{refined['total_score']}</font><font size='12' color='#c0c4cc'>/100</font>"
    score_para = Paragraph(score_text, styles["score"])
    ring = ScoreRing(refined["total_score"], size=52)
    score_row = Table([[score_para, ring]], colWidths=[120, 60])
    score_row.setStyle(TableStyle([( "VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0)]))

    summary_title = Paragraph("维度评语", styles["section"])
    summary_text = truncate_text(refined["comment"], 120).replace("**", "")
    summary_para = Paragraph(escape(summary_text), styles["summary"])

    right = [
        Paragraph("总得分 Total Score", styles["label"]),
        Spacer(1, 6),
        score_row,
        Spacer(1, 8),
        summary_title,
        Spacer(1, 4),
        summary_para,
    ]

    left_width = 240
    right_width = max(available_width - left_width, 180)
    if left_width + right_width > available_width:
        right_width = available_width - left_width
    table = Table([[left, right]], colWidths=[left_width, right_width])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def build_graded_top_section(styles, refined, available_width):
    """分档评分类型的顶部区域 - 不显示雷达图"""
    score_text = f"<font size='32' color='#2962FF'>{refined['total_score']}</font><font size='12' color='#c0c4cc'>/{refined['full_mark']}</font>"
    score_para = Paragraph(score_text, styles["score"])
    ring = ScoreRing(refined["total_score"], size=52)
    score_row = Table([[score_para, ring]], colWidths=[120, 60])
    score_row.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0)]))

    summary_title = Paragraph("综合评语", styles["section"])
    summary_text = truncate_text(refined["comment"], 180).replace("**", "")
    summary_para = Paragraph(escape(summary_text), styles["summary"])

    content = [
        Paragraph("总得分 Total Score", styles["label"]),
        Spacer(1, 6),
        score_row,
        Spacer(1, 12),
        summary_title,
        Spacer(1, 4),
        summary_para,
    ]

    table = Table([[content]], colWidths=[available_width])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def build_dimension_cards(refined, available_width):
    cards = [
        DimensionCard(d["name"], d["score"], d["full"], width=110, height=70)
        for d in refined["dimensions"]
    ]
    num_cols = 4
    gap = 12
    card_width = (available_width - gap * (num_cols - 1)) / num_cols
    card_height = 70

    widths = []
    for idx in range(num_cols):
        widths.append(card_width)
        if idx < num_cols - 1:
            widths.append(gap)

    rows = []
    for start in range(0, len(cards), num_cols):
        row_cards = cards[start : start + num_cols]
        row = []
        for idx in range(num_cols):
            if idx < len(row_cards):
                row_cards[idx].width = card_width
                row.append(row_cards[idx])
            else:
                row.append(Spacer(card_width, card_height))
            if idx < num_cols - 1:
                row.append(Spacer(gap, card_height))
        rows.append(row)

    table = Table(rows, colWidths=widths)
    table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return table


def build_graded_score_cards(refined, available_width):
    """构成分档评分卡片布局"""
    graded_scores = refined.get("graded_scores", [])
    if not graded_scores:
        return Spacer(1, 1)

    cards = [
        GradedScoreCard(
            graded_name=g["name"],
            label=g["label"],
            range_min=g["range_min"],
            range_max=g["range_max"],
            description=g.get("description", ""),
            is_current=g.get("is_current", False),
            width=90,
            height=60
        )
        for g in graded_scores
    ]

    num_cols = 5  # 每行最多5个档位
    gap = 10
    card_width = (available_width - gap * (num_cols - 1)) / num_cols
    card_height = 60

    widths = []
    for idx in range(num_cols):
        widths.append(card_width)
        if idx < num_cols - 1:
            widths.append(gap)

    rows = []
    for start in range(0, len(cards), num_cols):
        row_cards = cards[start : start + num_cols]
        row = []
        for idx in range(num_cols):
            if idx < len(row_cards):
                row_cards[idx].width = card_width
                row.append(row_cards[idx])
            else:
                row.append(Spacer(card_width, card_height))
            if idx < num_cols - 1:
                row.append(Spacer(gap, card_height))
        rows.append(row)

    table = Table(rows, colWidths=widths)
    table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return table


def build_section_header(styles, title, color, badge_text):
    badge = CircleBadge(badge_text, diameter=18, fill=color, text_color=colors.white)
    title_para = Paragraph(title, styles["section"])
    header = Table([[badge, title_para]], colWidths=[22, 200])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
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


def build_story(refined, labels, scores, full_marks, doc):
    styles = build_styles()
    story = []

    story.append(build_header(styles, refined, doc.width))
    story.append(Spacer(1, 16))

    # 根据评分类型选择不同的布局
    if refined["scoring_type"] == "dimension":
        # 维度评分类型: 显示雷达图 + 维度卡片
        story.append(build_top_section(styles, refined, labels, scores, full_marks, doc.width))
        story.append(Spacer(1, 18))
        story.append(build_dimension_cards(refined, doc.width))
    else:
        # 分档评分类型: 显示总得分 + 档位卡片
        story.append(build_graded_top_section(styles, refined, doc.width))
        story.append(Spacer(1, 18))
        story.append(build_section_header(styles, "分档评分标准", colors.HexColor("#2962FF"), "档"))
        story.append(Spacer(1, 8))
        story.append(build_graded_score_cards(refined, doc.width))

    story.append(Spacer(1, 20))

    story.append(build_section_header(styles, "综合评语", colors.HexColor("#FF5252"), "评"))
    story.append(Spacer(1, 8))
    comment_blocks = [blk.strip() for blk in refined["comment"].split("\n\n") if blk.strip()]
    for idx, block in enumerate(comment_blocks):
        safe = markdown_bold_to_html(block).replace("\n", "<br/>")
        story.append(Paragraph(safe, styles["body"]))
        if idx != len(comment_blocks) - 1:
            story.append(Spacer(1, 8))
    story.append(Spacer(1, 18))

    story.append(build_section_header(styles, "改进建议", colors.HexColor("#66BB6A"), "改"))
    story.append(Spacer(1, 8))
    for sug in refined["suggestions"]:
        story.append(build_suggestion_block(sug, styles, doc.width))
        story.append(Spacer(1, 8))
    story.append(Spacer(1, 10))

    story.append(build_section_header(styles, "引文详情", colors.HexColor("#FFA726"), "引"))
    story.append(Spacer(1, 8))
    story.append(Paragraph("暂无引文信息", styles["summary"]))

    return story


def load_data(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 支持两种JSON包装结构: data.artifacts 或 response.data.artifacts
    data = raw.get("data") or raw.get("response", {}).get("data", {})
    artifacts = data.get("artifacts", [])
    if not artifacts:
        raise ValueError("No artifacts found in data")

    core_data = artifacts[0]["parts"][0]["data"]
    meta_info = data.get("status", {})

    # 统一提取基础数据
    refined = {
        "total_score": core_data.get("totalScore", 0),
        "full_mark": core_data.get("fullMark", 100),
        "status_state": meta_info.get("state", "completed"),
        "timestamp": datetime.datetime.fromisoformat(meta_info.get("timestamp", datetime.datetime.now().isoformat())).strftime("%Y-%m-%d %H:%M"),
        "comment": core_data.get("comprehensiveComment", ""),
        "suggestions": core_data.get("improvementSuggestions", []),
        "dimensions": [],
        "graded_scores": [],
        "scoring_type": "dimension",  # 'dimension' | 'graded'
        "current_score": core_data.get("totalScore", 0),
    }

    labels, scores, full_marks = [], [], []

    # 处理维度评分 (essay_writing, thesis_writing 类型)
    if "dimensionScores" in core_data:
        refined["scoring_type"] = "dimension"
        for dim in core_data["dimensionScores"]:
            refined["dimensions"].append(
                {
                    "name": dim["evaluationDimension"],
                    "score": dim["dimensionScore"],
                    "full": dim["dimensionFullMark"],
                }
            )
            labels.append(dim["evaluationDimension"])
            scores.append(dim["dimensionScore"])
            full_marks.append(dim["dimensionFullMark"])

    # 处理分档评分 (心得体会类型)
    elif "gradedScores" in core_data:
        refined["scoring_type"] = "graded"
        current_score = refined["total_score"]
        for g in core_data["gradedScores"]:
            graded_item = {
                "name": g.get("gradedName", ""),
                "range_min": g.get("gradedRangeMin", 0),
                "range_max": g.get("gradedRangeMax", 0),
                "label": g.get("gradedLabel", ""),
                "description": g.get("gradedDescription", ""),
                "is_current": False,
            }
            # 判断当前档位: 分数在档位范围内
            if graded_item["range_min"] <= current_score <= graded_item["range_max"]:
                graded_item["is_current"] = True
            refined["graded_scores"].append(graded_item)

    return refined, labels, scores, full_marks


def generate_pdf(input_path, output_path):
    refined, labels, scores, full_marks = load_data(input_path)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=PAGE_MARGIN + CONTAINER_PADDING,
        rightMargin=PAGE_MARGIN + CONTAINER_PADDING,
        topMargin=PAGE_MARGIN + CONTAINER_PADDING,
        bottomMargin=PAGE_MARGIN + CONTAINER_PADDING,
    )

    story = build_story(refined, labels, scores, full_marks, doc)
    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate PDF evaluation report.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input JSON file path")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PDF file path")
    return parser.parse_args()


def main():
    args = parse_args()
    generate_pdf(args.input, args.output)
    print(f"PDF Report generated at: {args.output}")


if __name__ == "__main__":
    main()
