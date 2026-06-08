# backend/app/services/pdf_service.py

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable,
    KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
import os

# -----------------------------------------------
# COLOR PALETTE
# -----------------------------------------------
BLUE       = colors.HexColor("#1d4ed8")
LIGHT_BLUE = colors.HexColor("#eff6ff")
RED        = colors.HexColor("#dc2626")
LIGHT_RED  = colors.HexColor("#fef2f2")
GREEN      = colors.HexColor("#16a34a")
LIGHT_GREEN= colors.HexColor("#f0fdf4")
ORANGE     = colors.HexColor("#ea580c")
GRAY       = colors.HexColor("#6b7280")
LIGHT_GRAY = colors.HexColor("#f9fafb")
DARK       = colors.HexColor("#111827")
WHITE      = colors.white


def get_styles():
    """Custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Title2",
        fontSize=24,
        fontName="Helvetica-Bold",
        textColor=DARK,
        spaceAfter=6,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="Subtitle",
        fontSize=12,
        fontName="Helvetica",
        textColor=GRAY,
        spaceAfter=20,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=14,
        fontName="Helvetica-Bold",
        textColor=BLUE,
        spaceBefore=16,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="Body2",
        fontSize=10,
        fontName="Helvetica",
        textColor=DARK,
        spaceAfter=6,
        leading=16,
    ))
    styles.add(ParagraphStyle(
        name="Small",
        fontSize=8,
        fontName="Helvetica",
        textColor=GRAY,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="BigNumber",
        fontSize=28,
        fontName="Helvetica-Bold",
        textColor=BLUE,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="InsightText",
        fontSize=10,
        fontName="Helvetica",
        textColor=DARK,
        spaceAfter=6,
        leftIndent=10,
        leading=16,
    ))

    return styles


def make_stat_table(stats: list) -> Table:
    """
    Creates a row of stat cards.
    stats = [{"label": "Total", "value": "7043", "color": RED}, ...]
    """
    data = [[
        Paragraph(
            f'<font size="20" color="{s["color"].hexval()}">'
            f'<b>{s["value"]}</b></font>',
            ParagraphStyle("c", alignment=TA_CENTER)
        )
        for s in stats
    ], [
        Paragraph(
            f'<font size="9" color="#6b7280">{s["label"]}</font>',
            ParagraphStyle("c", alignment=TA_CENTER)
        )
        for s in stats
    ]]

    col_width = 6.5 * inch / len(stats)
    t = Table(data, colWidths=[col_width] * len(stats), rowHeights=[36, 20])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("ROWBACKGROUND", (0, 0), (-1, 0), WHITE),
        ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("INNERGRID",   (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    return t


def make_data_table(headers: list, rows: list) -> Table:
    """Creates a styled data table."""
    data = [headers] + rows
    col_width = 6.5 * inch / len(headers)

    t = Table(data, colWidths=[col_width] * len(headers))
    t.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",   (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 8),

        # Data rows
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("ALIGN",        (0, 1), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 6),

        # Alternating rows
        ("ROWBACKGROUND", (0, 1), (-1, -1), WHITE),

        # Grid
        ("BOX",       (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN",    (0, 0), (-1, -1), "MIDDLE"),
    ]))

    # Alternate row colors
    for i in range(1, len(rows) + 1):
        if i % 2 == 0:
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY)
            ]))

    return t


def generate_analytics_report(summary: dict, analytics_data: dict) -> bytes:
    """
    Generate a full analytics PDF report.
    Returns PDF as bytes.
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles  = get_styles()
    story   = []
    now     = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # -----------------------------------------------
    # HEADER
    # -----------------------------------------------
    story.append(Paragraph("ChurnAI Analytics Report", styles["Title2"]))
    story.append(Paragraph(f"Generated on {now}", styles["Subtitle"]))
    story.append(HRFlowable(
        width="100%", thickness=2,
        color=BLUE, spaceAfter=16
    ))

    # -----------------------------------------------
    # EXECUTIVE SUMMARY
    # -----------------------------------------------
    story.append(Paragraph("Executive Summary", styles["SectionTitle"]))

    stats = [
        {
            "label": "Total Customers",
            "value": str(summary.get("total_customers", 0)),
            "color": BLUE
        },
        {
            "label": "Churned",
            "value": str(summary.get("churned_customers", 0)),
            "color": RED
        },
        {
            "label": "Churn Rate",
            "value": f"{summary.get('churn_rate', 0)}%",
            "color": ORANGE
        },
        {
            "label": "Retained",
            "value": str(summary.get("retained_customers", 0)),
            "color": GREEN
        },
    ]
    story.append(make_stat_table(stats))
    story.append(Spacer(1, 12))

    # Financial stats
    fin_stats = [
        {
            "label": "Avg Monthly Charges",
            "value": f"${summary.get('avg_monthly_charges', 0)}",
            "color": BLUE
        },
        {
            "label": "Churner Avg Monthly",
            "value": f"${summary.get('churner_avg_monthly', 0)}",
            "color": RED
        },
        {
            "label": "Retained Avg Monthly",
            "value": f"${summary.get('retained_avg_monthly', 0)}",
            "color": GREEN
        },
        {
            "label": "Revenue at Risk",
            "value": f"${summary.get('revenue_at_risk', 0):,.0f}",
            "color": ORANGE
        },
    ]
    story.append(make_stat_table(fin_stats))
    story.append(Spacer(1, 16))

    # -----------------------------------------------
    # CHURN BY CONTRACT
    # -----------------------------------------------
    contract_data = analytics_data.get("contract", [])
    if contract_data:
        story.append(Paragraph(
            "Churn Analysis by Contract Type", styles["SectionTitle"]
        ))

        headers = ["Contract Type", "Total Customers", "Churned", "Retained", "Churn Rate"]
        rows    = [
            [
                str(item.get("name", "")),
                str(item.get("total", 0)),
                str(item.get("churned", 0)),
                str(item.get("retained", 0)),
                f"{item.get('churnRate', 0)}%",
            ]
            for item in contract_data
        ]
        story.append(make_data_table(headers, rows))

        # Insight
        if contract_data:
            highest = contract_data[0]
            story.append(Spacer(1, 8))
            story.append(Paragraph(
                f"💡 Key Insight: {highest['name']} customers have the highest "
                f"churn rate at {highest['churnRate']}%. "
                f"Encouraging longer-term contracts is the most impactful "
                f"retention strategy.",
                styles["InsightText"]
            ))

    story.append(Spacer(1, 12))

    # -----------------------------------------------
    # CHURN BY TENURE
    # -----------------------------------------------
    tenure_data = analytics_data.get("tenure", [])
    if tenure_data:
        story.append(Paragraph(
            "Churn Analysis by Customer Tenure", styles["SectionTitle"]
        ))

        headers = ["Tenure Group", "Customers", "Churned", "Churn Rate"]
        rows    = [
            [
                str(item.get("tenure", "")),
                str(item.get("customers", 0)),
                str(item.get("churned", 0)),
                f"{item.get('churnRate', 0)}%",
            ]
            for item in tenure_data
        ]
        story.append(make_data_table(headers, rows))

        if tenure_data:
            highest = tenure_data[0]
            story.append(Spacer(1, 8))
            story.append(Paragraph(
                f"💡 Key Insight: Customers in their {highest['tenure']} "
                f"have the highest churn rate at {highest['churnRate']}%. "
                f"Focus retention efforts on new customers immediately "
                f"after signup.",
                styles["InsightText"]
            ))

    story.append(Spacer(1, 12))

    # -----------------------------------------------
    # CHURN BY INTERNET SERVICE
    # -----------------------------------------------
    internet_data = analytics_data.get("internet", [])
    if internet_data:
        story.append(Paragraph(
            "Churn Analysis by Internet Service", styles["SectionTitle"]
        ))

        headers = ["Internet Service", "Customers", "Churn Rate"]
        rows    = [
            [
                str(item.get("name", "")),
                str(item.get("customers", 0)),
                f"{item.get('churnRate', 0)}%",
            ]
            for item in internet_data
        ]
        story.append(make_data_table(headers, rows))

    story.append(Spacer(1, 12))

    # -----------------------------------------------
    # CHURN BY PAYMENT METHOD
    # -----------------------------------------------
    payment_data = analytics_data.get("payment", [])
    if payment_data:
        story.append(Paragraph(
            "Churn Analysis by Payment Method", styles["SectionTitle"]
        ))

        headers = ["Payment Method", "Customers", "Churn Rate"]
        rows    = [
            [
                str(item.get("name", "")),
                str(item.get("customers", 0)),
                f"{item.get('churnRate', 0)}%",
            ]
            for item in payment_data
        ]
        story.append(make_data_table(headers, rows))

    story.append(Spacer(1, 12))

    # -----------------------------------------------
    # KEY RECOMMENDATIONS
    # -----------------------------------------------
    story.append(Paragraph(
        "Strategic Recommendations", styles["SectionTitle"]
    ))

    recommendations = [
        ["1", "Contract Conversion",
         "Convert month-to-month customers to annual contracts "
         "with targeted discounts. This single action can reduce "
         "churn by up to 40%."],
        ["2", "New Customer Onboarding",
         "Implement a structured 90-day onboarding program for "
         "new customers. First 12 months are the highest risk period."],
        ["3", "Service Bundling",
         "Customers with Online Security and Tech Support churn "
         "significantly less. Offer free trials to at-risk customers."],
        ["4", "Payment Method Incentives",
         "Incentivize customers to switch from electronic checks "
         "to automatic payments. Reduces churn by up to 30%."],
        ["5", "Revenue Protection",
         f"Monthly revenue at risk: ${summary.get('revenue_at_risk', 0):,.0f}. "
         "Proactive retention campaigns targeting high-risk customers "
         "can save 60% of this revenue."],
    ]

    rec_table = Table(
        recommendations,
        colWidths=[0.4*inch, 1.5*inch, 4.6*inch]
    )
    rec_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), BLUE),
        ("TEXTCOLOR",     (0, 0), (0, -1), WHITE),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica-Bold"),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUND", (0, 1), (-1, -1), WHITE),
    ]))

    for i in range(0, len(recommendations), 2):
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (1, i), (-1, i), LIGHT_GRAY)
        ]))

    story.append(rec_table)

    # -----------------------------------------------
    # FOOTER
    # -----------------------------------------------
    story.append(Spacer(1, 20))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#e5e7eb"),
        spaceAfter=8
    ))
    story.append(Paragraph(
        f"Generated by ChurnAI Platform · {now} · Confidential",
        ParagraphStyle(
            "footer",
            fontSize=8,
            textColor=GRAY,
            alignment=TA_CENTER
        )
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def generate_customer_report(prediction: dict) -> bytes:
    """
    Generate a single customer prediction PDF report.
    Returns PDF as bytes.
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = get_styles()
    story  = []
    now    = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Risk color
    risk      = prediction.get("risk_category", "Low")
    risk_color = (
        RED    if risk == "Critical" else
        ORANGE if risk == "High"     else
        colors.HexColor("#f59e0b") if risk == "Medium" else
        GREEN
    )

    # -----------------------------------------------
    # HEADER
    # -----------------------------------------------
    story.append(Paragraph(
        "Customer Churn Risk Report", styles["Title2"]
    ))
    story.append(Paragraph(
        f"Customer ID: {prediction.get('customer_id', 'N/A')} · {now}",
        styles["Subtitle"]
    ))
    story.append(HRFlowable(
        width="100%", thickness=2,
        color=BLUE, spaceAfter=16
    ))

    # -----------------------------------------------
    # RISK SCORE CARD
    # -----------------------------------------------
    story.append(Paragraph("Churn Risk Assessment", styles["SectionTitle"]))

    prob    = prediction.get("churn_probability", 0)
    prob_pct = f"{prob * 100:.1f}%"

    risk_data = [[
        Paragraph(
            f'<font size="32" color="{risk_color.hexval()}">'
            f'<b>{prob_pct}</b></font>',
            ParagraphStyle("c", alignment=TA_CENTER)
        ),
        Paragraph(
            f'<font size="18" color="{risk_color.hexval()}">'
            f'<b>{risk} Risk</b></font><br/>'
            f'<font size="10" color="#6b7280">'
            f'Churn Probability Score</font>',
            ParagraphStyle("c", alignment=TA_CENTER)
        ),
        Paragraph(
            f'<font size="10" color="#111827">'
            f'{prediction.get("explanation", "")}</font>',
            ParagraphStyle(
                "c", alignment=TA_LEFT,
                leading=16, leftIndent=8
            )
        ),
    ]]

    risk_table = Table(
        risk_data,
        colWidths=[1.8*inch, 1.8*inch, 2.9*inch],
        rowHeights=[80]
    )
    risk_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (1, 0), LIGHT_GRAY),
        ("BACKGROUND",    (2, 0), (2, 0), WHITE),
        ("BOX",           (0, 0), (-1, -1), 1, risk_color),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5,
         colors.HexColor("#e5e7eb")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (1, 0), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 16))

    # -----------------------------------------------
    # TOP RISK FACTORS
    # -----------------------------------------------
    top_factors = prediction.get("top_risk_factors", [])
    if top_factors:
        story.append(Paragraph(
            "Top Risk Factors (SHAP Analysis)", styles["SectionTitle"]
        ))

        headers = ["Rank", "Feature", "Impact Direction", "Impact Score"]
        rows    = []
        for i, factor in enumerate(top_factors, 1):
            impact    = factor.get("impact", 0)
            direction = "↑ Increases Risk" if impact > 0 else "↓ Reduces Risk"
            rows.append([
                str(i),
                str(factor.get("feature", "")).replace("_", " ").title(),
                direction,
                f"{abs(impact):.4f}",
            ])

        t = make_data_table(headers, rows)

        # Color impact direction
        for i, factor in enumerate(top_factors, 1):
            impact = factor.get("impact", 0)
            color  = colors.HexColor("#fef2f2") if impact > 0 \
                     else colors.HexColor("#f0fdf4")
            t.setStyle(TableStyle([
                ("BACKGROUND", (2, i), (2, i), color)
            ]))

        story.append(t)
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "💡 SHAP (SHapley Additive exPlanations) values show "
            "the contribution of each feature to this prediction. "
            "Positive values increase churn risk, negative values "
            "reduce it.",
            styles["InsightText"]
        ))

    story.append(Spacer(1, 16))

    # -----------------------------------------------
    # RETENTION STRATEGIES
    # -----------------------------------------------
    strategies = prediction.get("retention_strategies", [])
    if strategies:
        story.append(Paragraph(
            "Recommended Retention Strategies",
            styles["SectionTitle"]
        ))

        rows = [
            [f"{i}.", str(strategy)]
            for i, strategy in enumerate(strategies, 1)
        ]

        t = Table(rows, colWidths=[0.4*inch, 6.1*inch])
        t.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("TEXTCOLOR",     (0, 0), (0, -1), BLUE),
            ("ALIGN",         (0, 0), (0, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("BOX",           (0, 0), (-1, -1), 0.5,
             colors.HexColor("#e5e7eb")),
            ("INNERGRID",     (0, 0), (-1, -1), 0.5,
             colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUND", (0, 1), (-1, -1), WHITE),
        ]))

        for i in range(0, len(strategies), 2):
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, i), (-1, i), LIGHT_GREEN)
            ]))

        story.append(t)

    story.append(Spacer(1, 16))

    # -----------------------------------------------
    # ACTION SUMMARY
    # -----------------------------------------------
    story.append(Paragraph("Action Summary", styles["SectionTitle"]))

    urgency = (
        "IMMEDIATE ACTION REQUIRED"   if risk == "Critical" else
        "Action required this week"   if risk == "High"     else
        "Monitor and engage"          if risk == "Medium"   else
        "Low priority — monitor"
    )

    action_data = [
        ["Customer ID",      prediction.get("customer_id", "N/A")],
        ["Risk Category",    f"{risk} Risk"],
        ["Churn Probability",f"{prob * 100:.1f}%"],
        ["Urgency Level",    urgency],
        ["Model Version",    prediction.get("model_version", "v1.0")],
        ["Report Generated", now],
    ]

    t = Table(action_data, colWidths=[2.5*inch, 4.0*inch])
    t.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("BACKGROUND",    (0, 0), (0, -1), LIGHT_BLUE),
        ("TEXTCOLOR",     (0, 0), (0, -1), BLUE),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5,
         colors.HexColor("#e5e7eb")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5,
         colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUND", (0, 3), (-1, 3),
         colors.HexColor("#fef2f2") if risk in ["Critical", "High"]
         else LIGHT_GRAY),
    ]))
    story.append(t)

    # -----------------------------------------------
    # FOOTER
    # -----------------------------------------------
    story.append(Spacer(1, 20))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#e5e7eb"),
        spaceAfter=8
    ))
    story.append(Paragraph(
        f"Generated by ChurnAI Platform · {now} · Confidential",
        ParagraphStyle(
            "footer",
            fontSize=8,
            textColor=GRAY,
            alignment=TA_CENTER
        )
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()