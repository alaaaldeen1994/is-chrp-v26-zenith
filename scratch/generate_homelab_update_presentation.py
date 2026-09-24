import sys, os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon

pdf_path = r"C:\Users\alaaa\Downloads\Nilus_Lab_HomeLab_Phase2_Presentation.pdf"
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
hl = [Paragraph("NILUS LAB", logo_s), Paragraph("HOMELAB ACCELERATOR COHORT 5 | PHASE II EXECUTIVE UPDATE", tag_s)]
hr = [Paragraph("OPENAI PARTNER × DUBAI R&D", dt_s), Paragraph("AUGUST 2026 | FOUNDER: ALAA ALDEEN", ds_s)]
t_h = Table([[hl, hr]], colWidths=[420, 324])
t_h.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'BOTTOM'),('PADDING',(0,0),(-1,-1),0)]))
story.append(t_h)
story.append(Spacer(1,4))
story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceAfter=6))

# Banners
b1 = [Paragraph("OPENAI AI PARTNER", bl_s), Paragraph("Featured Case Study", bv_s), Paragraph("Single-Cell AI Bio Engine", bs_s)]
b2 = [Paragraph("AGE REVERSAL METRIC", bl_s), Paragraph("-13.0 Years", ParagraphStyle('BV2',parent=bv_s,textColor=c_green)), Paragraph("EnsembleAge Multi-Clock", bs_s)]
b3 = [Paragraph("DUBAI SCIENCE PARK", bl_s), Paragraph("Q4 2026 Lab Test", ParagraphStyle('BV3',parent=bv_s,textColor=c_purple)), Paragraph("Longevium R&D Collaboration", bs_s)]
t_b = Table([[b1, b2, b3]], colWidths=[248, 248, 248])
t_b.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_bg),('BOX',(0,0),(-1,-1),0.5,c_border),('INNERGRID',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(t_b)
story.append(Spacer(1,8))

# Content Columns
c1 = [
    Paragraph("<b>1. OPENAI AI PARTNER CASE STUDY</b>", ct_s), Spacer(1,4),
    Paragraph("• <b>AI Single-Cell Pioneer:</b> Recognized as an official OpenAI AI Partner leveraging advanced models across 2.42M cardiac cells (scVI 5,009D space).", bu_s), Spacer(1,3),
    Paragraph("• <b>Generative Factor Discovery:</b> Discovered non-oncogenic factor cocktails (SIRT1+SIRT6+GATA4+ZBTB16) to reverse cell age safely.", bu_s), Spacer(1,3),
    Paragraph("• <b>Conduction Safety Gate:</b> Enforces >94% Troponin T & Connexin-43 gap junction retention with 0% arrhythmia risk.", bu_s), Spacer(1,3),
    Paragraph("• <b>Automated Robotics Output:</b> Translates AI outputs into 1-click executable Opentrons OT-2 liquid-handling scripts.", bu_s), Spacer(1,8),
    Paragraph("<b>2. TECHNICAL & IP ASSETS</b>", ct_s), Spacer(1,4),
    Paragraph("• Proprietary Zenith v31.0 GOLD latent manifold architecture.", bu_s),
    Paragraph("• Provisional patent filings covering NL-101 and DRP kinetics.", bu_s),
]

c2 = [
    Image(img1_path, width=358, height=155), Spacer(1,6),
    Paragraph("<b>3. CUSTOMER DISCOVERY & DUBAI LAUNCH</b>", ct_s), Spacer(1,3),
    Paragraph("• <b>Longevium Meeting (Today):</b> Partnering to run in-vitro cardiac validation tests at Longevium's Dubai Science Park Lab (Q4 2026).", bu_s), Spacer(1,3),
    Paragraph("• <b>Curie.Bio & Global VCs:</b> Submitted executive diligence dossier for Pre-Seed co-pilot funding.", bu_s), Spacer(1,3),
    Paragraph("• <b>$500K Pre-Seed Ask:</b> Funding OT-2 automated assays ($60K) and CRO mouse MI in-vivo proof-of-concept ($150K).", bu_s), Spacer(1,6),
    Paragraph("<b>CONTACT:</b> Alaa Aldeen | <b>info@niluslab.com</b> | niluslab.com", ParagraphStyle('CTCT',parent=ct_s,textColor=c_blue,alignment=TA_CENTER)),
]

t_main = Table([[c1, c2]], colWidths=[370, 374])
t_main.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_card),('BOX',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_main)

doc.build(story)
print("Done - HomeLab Phase II short presentation PDF generated successfully")
