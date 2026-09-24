import sys, os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon, Group

pdf_path = r"C:\Users\alaaa\Downloads\Nilus_Lab_Longevium_Partnership_Proposal.pdf"
img1_path = r"C:\Users\alaaa\.gemini\antigravity\brain\27071572-9862-405d-970f-576dffef8666\cardiac_rejuvenation_lab_1786501552446.jpg"

W = 792; H = 612
M = 24
UW = W - 2*M
UH = H - 2*M

doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter), rightMargin=M, leftMargin=M, topMargin=M, bottomMargin=M)
styles = getSampleStyleSheet()

# Colors
c_slate = colors.HexColor("#0F172A")
c_blue = colors.HexColor("#1D4ED8")
c_white = colors.HexColor("#FFFFFF")
c_body = colors.HexColor("#334155")
c_muted = colors.HexColor("#64748B")
c_border = colors.HexColor("#CBD5E1")
c_bg = colors.HexColor("#F8FAFC")
c_card = colors.HexColor("#F1F5F9")
c_green = colors.HexColor("#15803D")
c_purple = colors.HexColor("#7C3AED")

# Styles
logo_s = ParagraphStyle('L', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=c_slate)
tag_s = ParagraphStyle('T', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=c_blue)
dt_s = ParagraphStyle('DT', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=c_slate, alignment=TA_RIGHT)
ds_s = ParagraphStyle('DS', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=c_purple, alignment=TA_RIGHT)

h1_s = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, leading=17, textColor=c_slate)
h2_s = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=c_blue)
bd_s = ParagraphStyle('BD', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12.5, textColor=c_body)
bu_s = ParagraphStyle('BU', parent=styles['Normal'], fontName='Helvetica', fontSize=8.8, leading=12, textColor=c_body, leftIndent=5)
ct_s = ParagraphStyle('CT', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=c_slate)

bv_s = ParagraphStyle('BV', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, leading=21, textColor=c_blue, alignment=TA_CENTER)
bl_s = ParagraphStyle('BL', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=10.5, textColor=c_slate, alignment=TA_CENTER)
bs_s = ParagraphStyle('BS', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=c_muted, alignment=TA_CENTER)

story = []

# Header Row
hl = [Paragraph("NILUS LAB  ×  LONGEVIUM", logo_s), Paragraph("AI × MEDICINE × BIOTECHNOLOGY × REGENERATIVE SCIENCE", tag_s)]
hr = [Paragraph("DUBAI SCIENCE PARK R&D HUB", dt_s), Paragraph("PARTNERSHIP PROPOSAL | Q4 2026", ds_s)]
t_h = Table([[hl, hr]], colWidths=[420, 324])
t_h.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'BOTTOM'),('PADDING',(0,0),(-1,-1),0)]))
story.append(t_h)
story.append(Spacer(1,4))
story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceAfter=6))

# Badges Banner
b1 = [Paragraph("BIOLOGICAL AGE RESET", bl_s), Paragraph("-13.0 Years", bv_s), Paragraph("Epigenetic Multi-Clock Reset", bs_s)]
b2 = [Paragraph("SINGLE-CELL AI ENGINE", bl_s), Paragraph("2.42M Cells", ParagraphStyle('BV2',parent=bv_s,textColor=c_green)), Paragraph("Zenith v31.0 GOLD (scVI 5,009D)", bs_s)]
b3 = [Paragraph("SAFETY RETENTION", bl_s), Paragraph(">94% Retention", ParagraphStyle('BV3',parent=bv_s,textColor=c_purple)), Paragraph("TNNT2 & Cx43 Identity Gate", bs_s)]
t_b = Table([[b1, b2, b3]], colWidths=[248, 248, 248])
t_b.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_bg),('BOX',(0,0),(-1,-1),0.5,c_border),('INNERGRID',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(t_b)
story.append(Spacer(1,8))

# Content Layout: Left Clean Text Cards + Right Lab Photo & Strategic Alignment
c1 = [
    Paragraph("<b>PARTNERSHIP OVERVIEW</b>", ct_s), Spacer(1,4),
    Paragraph("Nilus Lab proposes a founding R&D partnership with <b>Longevium</b> for the <b>Longevity AI Research Lab at Dubai Science Park</b>.", bd_s), Spacer(1,6),
    Paragraph("<b>KEY COLLABORATION PILLARS:</b>", ct_s), Spacer(1,4),
    Paragraph("• <b>Biological Age AI & Digital Twins:</b> Integrate Zenith's single-cell AI (2.42M cells) into Longevium patient digital twins.", bu_s), Spacer(1,3),
    Paragraph("• <b>Regenerative Medicine:</b> Deploy NL-101 mRNA-LNPs for targeted cardiac age reversal (-13.0y reset).", bu_s), Spacer(1,3),
    Paragraph("• <b>Physician AI Support:</b> Equip Longevium's 10,000+ trained doctors with real-time arrhythmia safety audits.", bu_s), Spacer(1,3),
    Paragraph("• <b>Robotic Diagnostics:</b> 1-click Opentrons OT-2 liquid-handling robotics script export for clinical diagnostics.", bu_s), Spacer(1,8),
    Paragraph("<b>FOUNDER & TEAM TRACK RECORD:</b>", ct_s), Spacer(1,4),
    Paragraph("• <b>Alaa Aldeen (Founder & CEO):</b> Multi-venture AI builder (Promatly & Saharyn), HomeLab Accelerator Cohort 5.", bu_s),
    Paragraph("• <b>Asset-Light Model:</b> 100% capital directed to clinical data generation via automated OT-2 robotics & CROs.", bu_s),
]

img_box = [
    Image(img1_path, width=358, height=170), Spacer(1,6),
    Paragraph("<b>DUBAI SCIENCE PARK Q4 2026 ROADMAP:</b>", ct_s), Spacer(1,3),
    Paragraph("1. Co-locate Zenith AI computational nodes at Longevium DSP Lab.", bu_s),
    Paragraph("2. Non-invasive cardiac biomarker profiling across Longevium's 30,000+ annual patients.", bu_s),
    Paragraph("3. Joint IP filings & DoH Abu Dhabi / MoHAP pre-IND regulatory strategy.", bu_s), Spacer(1,8),
    Paragraph("<b>CONTACT:</b> Alaa Aldeen (Founder & CEO) | <b>alaa@niluslab.com</b> | niluslab.com", ParagraphStyle('CTCT',parent=ct_s,textColor=c_blue,alignment=TA_CENTER)),
]

t_main = Table([[c1, img_box]], colWidths=[370, 374])
t_main.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_card),('BOX',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_main)

doc.build(story)
print("Done - Minimal visual proposal generated successfully")
