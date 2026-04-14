"""
PDF 报告渲染器

将 ``EvaluationReport`` 渲染为多维度 PDF 报告, 使用 reportlab 原生图表以避免对
matplotlib 的依赖。中文字体优先使用系统已安装的 WQY ZenHei (Linux), 其次查找
macOS / Windows 常见的中文字体。
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart

# 允许脚本直接被项目根目录导入, 也允许从 skill_training_evaluation 包内导入。
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from types_def import (  # noqa: E402  (sys.path tweak must come first)
    DimensionScore,
    EvaluationReport,
    HighlightItem,
    IssueItem,
    SubDimensionScore,
)


# -----------------------------------------------------------------------------
# Font registration
# -----------------------------------------------------------------------------

_FONT_NAME = "SC"

_CANDIDATE_FONTS = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Windows (rare on servers but harmless to try)
    "C:\\Windows\\Fonts\\msyh.ttc",
    "C:\\Windows\\Fonts\\simhei.ttf",
]


def _register_cjk_font() -> str:
    """Register a CJK-capable TTF/TTC font; return the font name used."""
    if _FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return _FONT_NAME
    for path in _CANDIDATE_FONTS:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(_FONT_NAME, path))
            return _FONT_NAME
    raise RuntimeError(
        "No CJK font available for PDF rendering. Install one of: "
        + ", ".join(_CANDIDATE_FONTS)
    )


# -----------------------------------------------------------------------------
# Styles
# -----------------------------------------------------------------------------

LEVEL_COLORS = {
    "优秀": colors.HexColor("#16a34a"),
    "良好": colors.HexColor("#2563eb"),
    "合格": colors.HexColor("#f59e0b"),
    "不合格": colors.HexColor("#dc2626"),
    "一票否决": colors.HexColor("#7f1d1d"),
}

SEVERITY_COLORS = {
    "high": colors.HexColor("#dc2626"),
    "medium": colors.HexColor("#f59e0b"),
    "low": colors.HexColor("#64748b"),
}

SEVERITY_LABELS = {"high": "高", "medium": "中", "low": "低"}


def _build_styles():
    base = getSampleStyleSheet()
    font = _FONT_NAME
    styles = {
        "Title": ParagraphStyle(
            "CNTitle",
            parent=base["Title"],
            fontName=font,
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=10,
            textColor=colors.HexColor("#0f172a"),
        ),
        "Subtitle": ParagraphStyle(
            "CNSubtitle",
            parent=base["Normal"],
            fontName=font,
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=16,
        ),
        "H1": ParagraphStyle(
            "CNH1",
            parent=base["Heading1"],
            fontName=font,
            fontSize=16,
            leading=22,
            spaceBefore=8,
            spaceAfter=8,
            textColor=colors.HexColor("#0f172a"),
        ),
        "H2": ParagraphStyle(
            "CNH2",
            parent=base["Heading2"],
            fontName=font,
            fontSize=13,
            leading=18,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.HexColor("#1e293b"),
        ),
        "Body": ParagraphStyle(
            "CNBody",
            parent=base["Normal"],
            fontName=font,
            fontSize=10,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=4,
            textColor=colors.HexColor("#111827"),
        ),
        "Small": ParagraphStyle(
            "CNSmall",
            parent=base["Normal"],
            fontName=font,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        ),
        "Quote": ParagraphStyle(
            "CNQuote",
            parent=base["Normal"],
            fontName=font,
            fontSize=9,
            leading=13,
            leftIndent=10,
            textColor=colors.HexColor("#334155"),
            backColor=colors.HexColor("#f1f5f9"),
            borderPadding=4,
        ),
        "Bullet": ParagraphStyle(
            "CNBullet",
            parent=base["Normal"],
            fontName=font,
            fontSize=10,
            leading=15,
            leftIndent=14,
            bulletIndent=2,
            textColor=colors.HexColor("#111827"),
        ),
    }
    return styles


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _escape(text: str) -> str:
    """Escape XML special chars for reportlab Paragraph rendering."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _level_badge(level: str) -> Table:
    color = LEVEL_COLORS.get(level, colors.HexColor("#64748b"))
    badge = Table(
        [[Paragraph(f'<font color="white"><b>{_escape(level)}</b></font>', ParagraphStyle(
            "badge",
            fontName=_FONT_NAME,
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.white,
        ))]],
        colWidths=[3 * cm],
        rowHeights=[0.9 * cm],
    )
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.25, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return badge


def _render_cover(report: EvaluationReport, model_name: str, dialogue_file: Optional[str], styles) -> list:
    story: list = []
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("智能体配置评估报告", styles["Title"]))
    story.append(Paragraph("Agent Configuration Evaluation Report", styles["Subtitle"]))
    story.append(Spacer(1, 8 * mm))

    level = report.final_level.value if hasattr(report.final_level, "value") else str(report.final_level)
    total = f"{report.total_score:.1f} / 100"

    meta_rows = [
        ["任务 ID", _escape(report.task_id or "—")],
        ["对话文件", _escape(dialogue_file or "—")],
        ["评测模型", _escape(model_name or "—")],
        ["评测时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["评测维度数", f"{len(report.dimensions)} 维度 / {sum(len(d.sub_scores) for d in report.dimensions)} 子项"],
        ["是否通过", "✓ 通过" if report.pass_criteria_met else "✗ 未通过"],
    ]
    meta_table = Table(
        [[Paragraph(_escape(k), styles["Body"]), Paragraph(_escape(v), styles["Body"])] for k, v in meta_rows],
        colWidths=[4 * cm, 12 * cm],
    )
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _FONT_NAME),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 1.5 * cm))

    # Big score block
    score_tbl = Table(
        [[
            Paragraph(f'<font size="32"><b>{_escape(total)}</b></font>', ParagraphStyle(
                "score", fontName=_FONT_NAME, fontSize=32, alignment=TA_CENTER, leading=36,
            )),
            _level_badge(level),
        ]],
        colWidths=[10 * cm, 4 * cm],
    )
    score_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 1 * cm))

    if report.veto_reasons:
        story.append(Paragraph("⚠️ 一票否决", styles["H2"]))
        for reason in report.veto_reasons:
            story.append(Paragraph("• " + _escape(reason), styles["Bullet"]))

    return story


def _render_dimension_overview(report: EvaluationReport, styles) -> list:
    story: list = []
    story.append(Paragraph("各维度得分总览", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))

    # Bar chart
    dims = report.dimensions
    data = [[d.score for d in dims]]
    category_names = [d.dimension for d in dims]

    drawing = Drawing(16 * cm, max(6 * cm, 1.2 * cm * len(dims) + 2 * cm))
    chart = HorizontalBarChart()
    chart.x = 3.5 * cm
    chart.y = 0.8 * cm
    chart.width = 11 * cm
    chart.height = drawing.height - 1.6 * cm
    chart.data = data
    chart.categoryAxis.categoryNames = category_names
    chart.categoryAxis.labels.fontName = _FONT_NAME
    chart.categoryAxis.labels.fontSize = 9
    chart.valueAxis.valueMin = 0
    max_full = max((d.full_score for d in dims), default=20)
    chart.valueAxis.valueMax = max_full
    chart.valueAxis.valueStep = max(1, int(max_full / 5) or 1)
    chart.valueAxis.labels.fontName = _FONT_NAME
    chart.valueAxis.labels.fontSize = 9
    chart.bars[0].fillColor = colors.HexColor("#2563eb")
    chart.bars[0].strokeColor = colors.HexColor("#1d4ed8")
    chart.barSpacing = 2
    chart.groupSpacing = 6
    # Value labels on bars
    chart.barLabels.fontName = _FONT_NAME
    chart.barLabels.fontSize = 9
    chart.barLabelFormat = "%.1f"
    chart.barLabels.nudge = 8
    drawing.add(chart)
    story.append(drawing)
    story.append(Spacer(1, 4 * mm))

    # Table
    header = ["维度", "得分", "满分", "百分比", "评级"]
    rows = [header]
    for d in dims:
        pct = (d.score / d.full_score * 100) if d.full_score else 0
        rows.append([
            d.dimension,
            f"{d.score:.1f}",
            str(d.full_score),
            f"{pct:.0f}%",
            d.level,
        ])
    tbl = Table(
        rows,
        colWidths=[4 * cm, 2 * cm, 2 * cm, 2.5 * cm, 2.5 * cm],
        hAlign="LEFT",
    )
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)

    return story


def _md_bold_to_paragraph(text: str, style) -> Paragraph:
    """Very small markdown-bold handler: **text** -> <b>text</b>."""
    escaped = _escape(text or "")
    # Rebuild bold: we escaped first, so ** became ** still (no HTML-special), safe to translate.
    import re as _re
    escaped = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    # Preserve newlines visually
    escaped = escaped.replace("\n", "<br/>")
    return Paragraph(escaped, style)


def _render_issue_card(issue: IssueItem, styles) -> KeepTogether:
    sev = (issue.severity or "medium").lower()
    sev_color = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["medium"])
    sev_label = SEVERITY_LABELS.get(sev, sev)

    header = [
        Paragraph(f"❗ <b>{_escape(issue.description)}</b>", styles["Body"]),
        Paragraph(
            f'<font color="white"><b>严重度: {_escape(sev_label)}</b></font>',
            ParagraphStyle("sevp", fontName=_FONT_NAME, fontSize=9, alignment=TA_CENTER, textColor=colors.white),
        ),
    ]
    hdr_tbl = Table([header], colWidths=[12 * cm, 2.5 * cm])
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, 0), sev_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    body_items: list = [hdr_tbl]
    if issue.location:
        body_items.append(Paragraph("📍 " + _escape(issue.location), styles["Small"]))
    if issue.quote:
        body_items.append(Paragraph("💬 " + _escape(issue.quote), styles["Quote"]))
    if issue.impact:
        body_items.append(Paragraph("影响: " + _escape(issue.impact), styles["Small"]))

    wrapper = Table([[item] for item in body_items], colWidths=[15 * cm])
    wrapper.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fecaca")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return KeepTogether([wrapper, Spacer(1, 2 * mm)])


def _render_highlight_card(h: HighlightItem, styles) -> KeepTogether:
    items: list = [Paragraph("⭐ <b>" + _escape(h.description) + "</b>", styles["Body"])]
    if h.location:
        items.append(Paragraph("📍 " + _escape(h.location), styles["Small"]))
    if h.quote:
        items.append(Paragraph("💬 " + _escape(h.quote), styles["Quote"]))
    if h.impact:
        items.append(Paragraph("影响: " + _escape(h.impact), styles["Small"]))
    wrapper = Table([[i] for i in items], colWidths=[15 * cm])
    wrapper.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return KeepTogether([wrapper, Spacer(1, 2 * mm)])


def _render_dimension_detail(dim: DimensionScore, styles) -> list:
    story: list = []
    header_line = f"{dim.dimension}  <font size='11' color='#475569'>{dim.score:.1f} / {dim.full_score} 分 · 权重 {dim.weight:.0%} · 评级 {dim.level}</font>"
    if dim.is_veto:
        header_line += "  <font color='#dc2626'><b>[一票否决触发]</b></font>"
    story.append(Paragraph(header_line, styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=4))

    # Sub-dim summary table
    rows = [["子维度", "得分", "满分", "评级", "分数段"]]
    for sub in dim.sub_scores:
        rows.append([
            sub.sub_dimension,
            f"{sub.score}",
            f"{sub.full_score}",
            sub.rating or "—",
            sub.score_range or "—",
        ])
    tbl = Table(rows, colWidths=[4 * cm, 1.8 * cm, 1.8 * cm, 2.2 * cm, 5.5 * cm])
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (3, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 4 * mm))

    # Per-sub detail
    for sub in dim.sub_scores:
        story.append(Paragraph(f"◆ {sub.sub_dimension} · {sub.score}/{sub.full_score} · {sub.rating}", styles["H2"]))
        if sub.judgment_basis:
            story.append(_md_bold_to_paragraph(sub.judgment_basis, styles["Body"]))
        for issue in (sub.issues or []):
            story.append(_render_issue_card(issue, styles))
        for hl in (sub.highlights or []):
            story.append(_render_highlight_card(hl, styles))
        story.append(Spacer(1, 2 * mm))

    return story


def _render_summary_page(report: EvaluationReport, styles) -> list:
    story: list = []
    story.append(Paragraph("评测总结", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
    if report.analysis:
        story.append(_md_bold_to_paragraph(report.analysis, styles["Body"]))
    story.append(Spacer(1, 4 * mm))

    if report.issues:
        story.append(Paragraph("关键问题", styles["H2"]))
        for item in report.issues:
            story.append(Paragraph("• " + _escape(item), styles["Bullet"]))
        story.append(Spacer(1, 3 * mm))

    if report.suggestions:
        story.append(Paragraph("改进建议", styles["H2"]))
        for item in report.suggestions:
            story.append(Paragraph("• " + _escape(item), styles["Bullet"]))
        story.append(Spacer(1, 3 * mm))

    if report.veto_reasons:
        story.append(Paragraph("一票否决原因", styles["H2"]))
        for item in report.veto_reasons:
            story.append(Paragraph("• " + _escape(item), styles["Bullet"]))

    return story


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def generate_pdf(
    report: EvaluationReport,
    output_path: str,
    model_name: str = "",
    dialogue_file: Optional[str] = None,
) -> None:
    """Render an EvaluationReport to a multi-page PDF at ``output_path``."""
    _register_cjk_font()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="智能体配置评估报告",
        author="Skills Training Course evaluation",
    )

    story: list = []

    # Cover
    story.extend(_render_cover(report, model_name, dialogue_file, styles))
    story.append(PageBreak())

    # Overview
    story.extend(_render_dimension_overview(report, styles))
    story.append(PageBreak())

    # Per-dim detail pages
    for i, dim in enumerate(report.dimensions):
        story.extend(_render_dimension_detail(dim, styles))
        if i != len(report.dimensions) - 1:
            story.append(PageBreak())

    story.append(PageBreak())
    story.extend(_render_summary_page(report, styles))

    doc.build(story)
