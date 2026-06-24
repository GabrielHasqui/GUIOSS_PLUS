from io import BytesIO
from html import escape

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


GUIOS_NAVY = colors.HexColor("#12216a")
GUIOS_ORANGE = colors.HexColor("#f59e0b")
GUIOS_TEXT = colors.HexColor("#0f172a")
GUIOS_MUTED = colors.HexColor("#475569")
GUIOS_BORDER = colors.HexColor("#d7dee7")
GUIOS_SURFACE = colors.HexColor("#f8fafc")
GUIOS_GOOD = colors.HexColor("#dcfce7")
GUIOS_BAD = colors.HexColor("#fce7f3")


def _safe_text(value):
    """Escape untrusted text before ReportLab parses its XML-like markup."""
    return escape(str(value or ""), quote=True)


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="GuiosTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=22,
            textColor=GUIOS_NAVY,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuiosSubtitle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=GUIOS_MUTED,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuiosSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=GUIOS_NAVY,
            spaceBefore=6,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuiosBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=GUIOS_TEXT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuiosMuted",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=GUIOS_MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuiosCenter",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=18,
            alignment=TA_CENTER,
            textColor=GUIOS_ORANGE,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuiosCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=GUIOS_TEXT,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuiosHeaderCell",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=colors.white,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuiosCompactCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10.4,
            textColor=GUIOS_TEXT,
            alignment=TA_LEFT,
        )
    )

    return styles


def _format_factor_items(items):
    if not items:
        return "Sin factores"

    lines = []
    for item in items:
        evaluation_factor = item["evaluation_factor"]
        mean_weight = (
            f"{evaluation_factor.mean_weight:.1f}"
            if evaluation_factor.mean_weight is not None
            else "-"
        )
        lines.append(
            f"• {_safe_text(evaluation_factor.factor.name)} (PM {mean_weight})"
        )

    return "<br/>".join(lines)


def _build_info_table(report_context, styles):
    evaluation = report_context["evaluation"]
    recommendation = report_context["recommendation"]
    issued_at = report_context["issued_at"].strftime("%d/%m/%Y %H:%M")

    rows = [
        [
            Paragraph("<b>Software evaluado</b>", styles["GuiosMuted"]),
            Paragraph(_safe_text(evaluation.software_name), styles["GuiosBody"]),
            Paragraph("<b>Contexto</b>", styles["GuiosMuted"]),
            Paragraph(_safe_text(evaluation.context), styles["GuiosBody"]),
        ],
        [
            Paragraph("<b>Metodologia</b>", styles["GuiosMuted"]),
            Paragraph("GUIOS+", styles["GuiosBody"]),
            Paragraph("<b>Estado</b>", styles["GuiosMuted"]),
            Paragraph(_safe_text(report_context["evaluation_status_display"]), styles["GuiosBody"]),
        ],
        [
            Paragraph("<b>Factores relevantes</b>", styles["GuiosMuted"]),
            Paragraph(str(report_context["relevant_factor_count"]), styles["GuiosBody"]),
            Paragraph("<b>Factores evaluados</b>", styles["GuiosMuted"]),
            Paragraph(str(report_context["evaluated_factor_count"]), styles["GuiosBody"]),
        ],
        [
            Paragraph("<b>Consultas bibliograficas</b>", styles["GuiosMuted"]),
            Paragraph(str(report_context["query_count"]), styles["GuiosBody"]),
            Paragraph("<b>Documentos bibliograficos</b>", styles["GuiosMuted"]),
            Paragraph(str(report_context["document_count"]), styles["GuiosBody"]),
        ],
        [
            Paragraph("<b>Fecha de emision</b>", styles["GuiosMuted"]),
            Paragraph(issued_at, styles["GuiosBody"]),
            Paragraph("<b>Resultado</b>", styles["GuiosMuted"]),
            Paragraph(
                _safe_text(
                    f"Recomendacion {recommendation.code}"
                    if recommendation
                    else "Pendiente"
                ),
                styles["GuiosBody"],
            ),
        ],
    ]

    table = Table(rows, colWidths=[42 * mm, 48 * mm, 38 * mm, 50 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, GUIOS_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GUIOS_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _build_recommendation_table(report_context, styles):
    recommendation = report_context["recommendation"]
    recommendation_code = _safe_text(recommendation.code if recommendation else "-")
    recommendation_text = (
        recommendation.text
        if recommendation
        else "La evaluacion aun no dispone de una recomendacion final."
    )

    rows = [
        [
            Paragraph(recommendation_code, styles["GuiosCenter"]),
            Paragraph(
                (
                    f"<b>{_safe_text(report_context['recommendation_title'])}</b>"
                    f"<br/>{_safe_text(recommendation_text)}"
                ),
                styles["GuiosBody"],
            ),
        ]
    ]

    table = Table(rows, colWidths=[22 * mm, 156 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, GUIOS_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def _build_foda_distribution_table(report_context, styles):
    groups = report_context["foda_groups"]
    rows = [
        [
            Paragraph("<b>Fortalezas</b>", styles["GuiosBody"]),
            Paragraph("<b>Oportunidades</b>", styles["GuiosBody"]),
        ],
        [
            Paragraph(
                f"<b>{report_context['fortalezas']}</b><br/>{_format_factor_items(groups['Fortaleza'])}",
                styles["GuiosCompactCell"],
            ),
            Paragraph(
                f"<b>{report_context['oportunidades']}</b><br/>{_format_factor_items(groups['Oportunidad'])}",
                styles["GuiosCompactCell"],
            ),
        ],
        [
            Paragraph("<b>Debilidades</b>", styles["GuiosBody"]),
            Paragraph("<b>Amenazas</b>", styles["GuiosBody"]),
        ],
        [
            Paragraph(
                f"<b>{report_context['debilidades']}</b><br/>{_format_factor_items(groups['Debilidad'])}",
                styles["GuiosCompactCell"],
            ),
            Paragraph(
                f"<b>{report_context['amenazas']}</b><br/>{_format_factor_items(groups['Amenaza'])}",
                styles["GuiosCompactCell"],
            ),
        ],
    ]

    table = Table(rows, colWidths=[89 * mm, 89 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, GUIOS_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GUIOS_BORDER),
                ("BACKGROUND", (0, 0), (-1, 0), GUIOS_SURFACE),
                ("BACKGROUND", (0, 2), (-1, 2), GUIOS_SURFACE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _build_factor_detail_table(report_context, styles):
    rows = [
        [
            Paragraph("#", styles["GuiosHeaderCell"]),
            Paragraph("Factor", styles["GuiosHeaderCell"]),
            Paragraph("Imp. sugerida", styles["GuiosHeaderCell"]),
            Paragraph("Imp. relativa", styles["GuiosHeaderCell"]),
            Paragraph("Pond. media", styles["GuiosHeaderCell"]),
            Paragraph("Alcance", styles["GuiosHeaderCell"]),
            Paragraph("FODA", styles["GuiosHeaderCell"]),
        ]
    ]

    for index, summary in enumerate(report_context["relevant_summaries"], start=1):
        evaluation_factor = summary["evaluation_factor"]
        rows.append(
            [
                Paragraph(str(index), styles["GuiosCompactCell"]),
                Paragraph(_safe_text(evaluation_factor.factor.name), styles["GuiosCompactCell"]),
                Paragraph(
                    _safe_text(evaluation_factor.get_suggested_importance_display()),
                    styles["GuiosCompactCell"],
                ),
                Paragraph(
                    _safe_text(
                        evaluation_factor.get_relative_importance_display()
                        if evaluation_factor.relative_importance
                        else "-"
                    ),
                    styles["GuiosCompactCell"],
                ),
                Paragraph(
                    f"{evaluation_factor.mean_weight:.1f}"
                    if evaluation_factor.mean_weight is not None
                    else "-",
                    styles["GuiosCompactCell"],
                ),
                Paragraph(_safe_text(evaluation_factor.selected_scope or "-"), styles["GuiosCompactCell"]),
                Paragraph(_safe_text(evaluation_factor.foda or "-"), styles["GuiosCompactCell"]),
            ]
        )

    table = Table(
        rows,
        repeatRows=1,
        colWidths=[8 * mm, 64 * mm, 22 * mm, 22 * mm, 20 * mm, 19 * mm, 25 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GUIOS_NAVY),
                ("BOX", (0, 0), (-1, -1), 0.6, GUIOS_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GUIOS_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GUIOS_SURFACE]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _draw_header_footer(canvas, doc, report_context):
    page_number = canvas.getPageNumber()
    report_code = report_context["report_code"]
    issued_at = report_context["issued_at"].strftime("%d/%m/%Y %H:%M")

    canvas.saveState()
    canvas.setStrokeColor(GUIOS_BORDER)
    canvas.setFillColor(GUIOS_NAVY)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(doc.leftMargin, A4[1] - 16 * mm, "GUIOS+")
    canvas.setFillColor(GUIOS_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(
        A4[0] - doc.rightMargin,
        A4[1] - 16 * mm,
        f"{report_code} · {issued_at}",
    )
    canvas.line(doc.leftMargin, A4[1] - 18 * mm, A4[0] - doc.rightMargin, A4[1] - 18 * mm)

    canvas.line(doc.leftMargin, 12 * mm, A4[0] - doc.rightMargin, 12 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(doc.leftMargin, 8 * mm, "GUIOS+ · Documento confidencial")
    canvas.drawRightString(
        A4[0] - doc.rightMargin,
        8 * mm,
        f"Pagina {page_number}",
    )
    canvas.restoreState()


def build_evaluation_report_response(report_context):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=24 * mm,
        bottomMargin=18 * mm,
    )
    styles = _build_styles()

    story = [
        Paragraph("INFORME DE EVALUACION FLOSS", styles["GuiosTitle"]),
        Paragraph(
            (
                f"{_safe_text(report_context['evaluation'].software_name)} · "
                f"{_safe_text(report_context['evaluation'].context)}"
            ),
            styles["GuiosSubtitle"],
        ),
        Paragraph("DATOS DEL INFORME", styles["GuiosSection"]),
        _build_info_table(report_context, styles),
        Spacer(1, 10),
        Paragraph("VEREDICTO Y RECOMENDACION", styles["GuiosSection"]),
        _build_recommendation_table(report_context, styles),
        Spacer(1, 10),
        Paragraph("DISTRIBUCION FODA", styles["GuiosSection"]),
        _build_foda_distribution_table(report_context, styles),
        PageBreak(),
        Paragraph("DETALLE POR FACTOR", styles["GuiosSection"]),
        _build_factor_detail_table(report_context, styles),
    ]

    document.build(
        story,
        onFirstPage=lambda canvas, doc: _draw_header_footer(canvas, doc, report_context),
        onLaterPages=lambda canvas, doc: _draw_header_footer(canvas, doc, report_context),
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Informe_GUIOS_{report_context["report_code"]}.pdf"'
    )
    return response
