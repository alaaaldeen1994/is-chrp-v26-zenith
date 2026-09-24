import sys, os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon

pdf_path = r"C:\Users\alaaa\Downloads\Nilus_Lab_Investment_Dossier_2026.pdf"
img1_path = r"C:\Users\alaaa\.gemini\antigravity\brain\27071572-9862-405d-970f-576dffef8666\cardiac_rejuvenation_lab_1786501552446.jpg"
img2_path = r"C:\Users\alaaa\.gemini\antigravity\brain\27071572-9862-405d-970f-576dffef8666\.user_uploaded\media_1786501579725.jpg"

W = 792; H = 612
M = 24
UW = W - 2*M
UH = H - 2*M

doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter), rightMargin=M, leftMargin=M, topMargin=M, bottomMargin=M)
styles = getSampleStyleSheet()

# Palette
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

# Styles (Larger Fonts for Maximum Readability)
logo_s = ParagraphStyle('L', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=c_slate)
tag_s = ParagraphStyle('T', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=c_blue)
dt_s = ParagraphStyle('DT', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=c_slate, alignment=TA_RIGHT)
ds_s = ParagraphStyle('DS', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=10.5, textColor=c_muted, alignment=TA_RIGHT)
h1_s = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14.5, leading=17.5, textColor=c_slate)
h2_s = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=13.5, textColor=c_blue)
bd_s = ParagraphStyle('BD', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12.2, textColor=c_body)
bu_s = ParagraphStyle('BU', parent=styles['Normal'], fontName='Helvetica', fontSize=8.8, leading=12, textColor=c_body, leftIndent=5)
ct_s = ParagraphStyle('CT', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=c_slate)
bv_s = ParagraphStyle('BV', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=17, leading=20, textColor=c_blue, alignment=TA_CENTER)
bl_s = ParagraphStyle('BL', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=10.5, textColor=c_slate, alignment=TA_CENTER)
bs_s = ParagraphStyle('BS', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=c_muted, alignment=TA_CENTER)
bv_g = ParagraphStyle('BVG', parent=bv_s, textColor=c_green)
bv_p = ParagraphStyle('BVP', parent=bv_s, textColor=c_purple)

story = []

# ====================================================================
# SLIDE 1: COVER + EXECUTIVE SUMMARY
# ====================================================================
hl = [Paragraph("NILUS LAB", logo_s), Paragraph("SINGLE-CELL GENERATIVE BIOLOGY & CARDIAC REJUVENATION", tag_s)]
hr = [Paragraph("INVESTMENT DOSSIER", dt_s), Paragraph("PRE-SEED CAPITAL RAISE | 2026", ds_s)]
t_h = Table([[hl, hr]], colWidths=[370, 374])
t_h.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'BOTTOM'),('PADDING',(0,0),(-1,-1),0)]))
story.append(t_h)
story.append(Spacer(1,4))
story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceAfter=6))

# Badges
b1 = [Paragraph("EPIGENETIC AGE RESET", bl_s), Paragraph("-13.0 Years", bv_s), Paragraph("EnsembleAge Multi-Clock (GeroSci 2026)", bs_s)]
b2 = [Paragraph("SARCOMERE SAFETY GATE", bl_s), Paragraph(">94% Retention", bv_g), Paragraph("TNNT2 & Cx43 Identity (Arrhythmia Safe)", bs_s)]
b3 = [Paragraph("ACSL4 CYTOPROTECTION", bl_s), Paragraph(">90% Safe Score", bv_p), Paragraph("Ferro-Aging Protection (Cell Metab 2026)", bs_s)]
t_b = Table([[b1, b2, b3]], colWidths=[248, 248, 248])
t_b.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_bg),('BOX',(0,0),(-1,-1),0.5,c_border),('INNERGRID',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(t_b)
story.append(Spacer(1,6))

cov = [
    Paragraph("<b>EXECUTIVE SUMMARY & LONGEVITY THESIS</b>", ct_s), Spacer(1,4),
    Paragraph("Nilus Lab is an AI-native longevity biotechnology company (HomeLab Accelerator Cohort 5) building <b>Zenith v31.0 GOLD</b> -- a generative single-cell foundation model operating across 2.42M human cardiac single cells. Our lead asset, <b>NL-101</b>, delivers non-oncogenic factor cocktails (<i>SIRT1+SIRT6+GATA4+ZBTB16</i>) via mRNA-LNP to safely reverse biological age in human cardiomyocytes.", bd_s), Spacer(1,6),
    Paragraph("<b>Primary Ask:</b> $500,000 Pre-Seed Round to complete automated in-vitro OT-2 assays and CRO in-vivo mouse MI proof-of-concept.", ParagraphStyle('M1', parent=bd_s, fontName='Helvetica-Bold', textColor=c_blue)),
    Paragraph("<b>Core Indication:</b> Post-Myocardial Infarction Ischemic Heart Failure (NYHA Class II-IV).", ParagraphStyle('M2', parent=bd_s, textColor=c_slate)), Spacer(1,8),
    Paragraph("<b>WHY INVEST IN NILUS LAB</b>", ct_s), Spacer(1,3),
    Paragraph("1. Cardiac aging is the #1 cause of global mortality (18.6M deaths/year, WHO 2024).", bu_s),
    Paragraph("2. First platform to solve the arrhythmia safety bottleneck in cardiac reprogramming.", bu_s),
    Paragraph("3. Healthspan-first approach: reverse biological age at the organ level, not systemic.", bu_s),
    Paragraph("4. Healthspan-first thesis: extend cardiac lifespan for 64M heart failure patients globally.", bu_s),
    Paragraph("5. Asset-light CRO model: 100% capital to validation, zero lab overhead.", bu_s),
    Paragraph("6. ACSL4 ferro-aging cytoprotection (Liu et al., Cell Metabolism 2026).", bu_s),
]
lab_img = Image(img1_path, width=370, height=260)
t_main = Table([[cov, lab_img]], colWidths=[370, 374])
t_main.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),c_card),('BOX',(0,0),(0,0),0.5,c_border),('PADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_main)
story.append(PageBreak())

# ====================================================================
# SLIDE 2: MARKET OPPORTUNITY & COMPETITIVE LANDSCAPE
# ====================================================================
story.append(Paragraph("SLIDE 1: MARKET OPPORTUNITY & COMPETITIVE LANDSCAPE", h1_s))
story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceAfter=6))

# Market Size Badges
m1 = [Paragraph("HEART FAILURE MARKET", bl_s), Paragraph("$47.2B", bv_s), Paragraph("Global HF Therapeutics by 2030 (CAGR 7.8%)", bs_s)]
m2 = [Paragraph("LONGEVITY BIOTECH MARKET", bl_s), Paragraph("$64.0B", bv_g), Paragraph("Anti-Aging Therapeutics by 2032 (CAGR 12.3%)", bs_s)]
m3 = [Paragraph("mRNA-LNP THERAPEUTICS", bl_s), Paragraph("$28.5B", bv_p), Paragraph("Non-Vaccine mRNA Applications by 2031", bs_s)]
t_m = Table([[m1, m2, m3]], colWidths=[248, 248, 248])
t_m.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_bg),('BOX',(0,0),(-1,-1),0.5,c_border),('INNERGRID',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(t_m)
story.append(Spacer(1,8))

# Market problem + Competitive Landscape
ml = [
    Paragraph("<b>THE UNMET MEDICAL NEED</b>", ct_s), Spacer(1,4),
    Paragraph("Heart failure affects <b>64 million people globally</b> (Lancet 2024). After myocardial infarction, adult cardiomyocytes lose proliferative capacity and accumulate epigenetic damage. Current treatments (ACE inhibitors, beta-blockers, SGLT2i) manage symptoms but do not reverse underlying biological aging.", bd_s), Spacer(1,6),
    Paragraph("<b>THE PROBLEM WITH CURRENT REPROGRAMMING:</b>", ct_s), Spacer(1,3),
    Paragraph("- Yamanaka OSKM factors (OCT4, SOX2, KLF4, MYC) cause <b>teratoma formation</b> and <b>lethal cardiac arrhythmias</b> due to sarcomeric disassembly of TNNT2 and Connexin-43 gap junctions.", bu_s), Spacer(1,3),
    Paragraph("- No existing reprogramming company has solved the cardiac safety problem.", bu_s), Spacer(1,3),
    Paragraph("- Altos Labs ($3B), Retro Bio ($180M), NewLimit ($40M) all focus on <b>systemic</b> reprogramming without organ-specific safety guarantees.", bu_s), Spacer(1,6),
    Paragraph("<b>NILUS LAB SOLUTION:</b>", ct_s), Spacer(1,3),
    Paragraph("Replace oncogenic Yamanaka factors with non-oncogenic cardiac-specific factors (SIRT1+SIRT6+GATA4+ZBTB16) delivered via targeted mRNA-LNPs with built-in safety gates.", bu_s),
]
mr = [
    Paragraph("<b>COMPETITIVE LANDSCAPE MATRIX</b>", ct_s), Spacer(1,4),
]
ph = ParagraphStyle('PH', parent=bd_s, fontName='Helvetica-Bold')
comp = [
    [Paragraph("<b>Company</b>",ph), Paragraph("<b>Raised</b>",ph), Paragraph("<b>Approach</b>",ph), Paragraph("<b>Cardiac Safety</b>",ph)],
    [Paragraph("<b>Altos Labs</b>",bd_s), Paragraph("$3.0B",bd_s), Paragraph("Systemic OSKM Reprogramming",bd_s), Paragraph("None",ParagraphStyle('R',parent=bd_s,textColor=colors.HexColor("#DC2626")))],
    [Paragraph("<b>Retro Bio</b>",bd_s), Paragraph("$180M",bd_s), Paragraph("Autophagy + Partial Reprog",bd_s), Paragraph("None",ParagraphStyle('R2',parent=bd_s,textColor=colors.HexColor("#DC2626")))],
    [Paragraph("<b>NewLimit</b>",bd_s), Paragraph("$40M",bd_s), Paragraph("Epigenetic (Liver/Immune)",bd_s), Paragraph("None",ParagraphStyle('R3',parent=bd_s,textColor=colors.HexColor("#DC2626")))],
    [Paragraph("<b>Turn Bio</b>",bd_s), Paragraph("$60M",bd_s), Paragraph("ERA Transient Reprogramming",bd_s), Paragraph("Minimal",ParagraphStyle('R4',parent=bd_s,textColor=colors.HexColor("#F59E0B")))],
    [Paragraph("<b>Shift Bio</b>",bd_s), Paragraph("$21M",bd_s), Paragraph("Partial Reprogramming + Aging",bd_s), Paragraph("None",ParagraphStyle('R5',parent=bd_s,textColor=colors.HexColor("#DC2626")))],
    [Paragraph("<b>Nilus Lab</b>",ParagraphStyle('NL',parent=bd_s,fontName='Helvetica-Bold',textColor=c_blue)), Paragraph("$500K Ask",ParagraphStyle('NL2',parent=bd_s,textColor=c_blue)), Paragraph("Non-Oncogenic Cardiac-Only",ParagraphStyle('NL3',parent=bd_s,textColor=c_blue)), Paragraph(">94% TNNT2/Cx43",ParagraphStyle('NL4',parent=bd_s,fontName='Helvetica-Bold',textColor=c_green))],
]
t_c = Table(comp, colWidths=[80,60,165,69])
t_c.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),c_card),('BACKGROUND',(0,6),(-1,6),colors.HexColor("#EFF6FF")),('GRID',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),4),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
mr.append(t_c)
mr.append(Spacer(1,8))
mr.append(Paragraph("<b>KEY INSIGHT:</b> Nilus Lab is the <b>ONLY</b> company in this landscape with quantified cardiac identity safety (TNNT2 >94%, Connexin-43 >94%, SERCA2a calcium stability).", ParagraphStyle('KI',parent=bu_s,textColor=c_blue,fontName='Helvetica-Bold')))

t_ml = Table([[ml, mr]], colWidths=[370, 374])
t_ml.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_card),('BOX',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_ml)
story.append(PageBreak())

# ====================================================================
# SLIDE 3: MOLECULAR MECHANISM & ZENITH PLATFORM
# ====================================================================
story.append(Paragraph("SLIDE 2: NL-101 MOLECULAR MECHANISM & ZENITH AI PLATFORM", h1_s))
story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceAfter=6))

d1 = Drawing(744, 120)
d1.add(Rect(10,15,195,90,rx=6,ry=6,fillColor=colors.HexColor("#FEF2F2"),strokeColor=colors.HexColor("#FCA5A5"),strokeWidth=1))
d1.add(String(107,82,"AGED CARDIOMYOCYTE",textAnchor="middle",fontName="Helvetica-Bold",fontSize=9,fillColor=colors.HexColor("#991B1B")))
d1.add(String(107,66,"Chronological Age: 65.0y",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8.5,fillColor=c_slate))
d1.add(String(107,50,"High Hypermethylation | Low SIRT1/6",textAnchor="middle",fontName="Helvetica",fontSize=7.5,fillColor=c_body))
d1.add(String(107,34,"Impaired SERCA2a Ca2+ Handling",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_muted))
d1.add(Line(205,60,255,60,strokeColor=c_blue,strokeWidth=2))
d1.add(Polygon([250,55,260,60,250,65],fillColor=c_blue,strokeColor=c_blue))
d1.add(Rect(260,10,215,100,rx=6,ry=6,fillColor=colors.HexColor("#EFF6FF"),strokeColor=c_blue,strokeWidth=1.5))
d1.add(String(367,92,"NL-101 DRP PULSE (2.0h ON)",textAnchor="middle",fontName="Helvetica-Bold",fontSize=9.5,fillColor=c_blue))
d1.add(String(367,76,"SIRT1 + SIRT6 + GATA4 + ZBTB16",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8.5,fillColor=c_slate))
d1.add(String(367,60,"H3K9ac Deacetylation & Demethylation",textAnchor="middle",fontName="Helvetica",fontSize=7.5,fillColor=c_body))
d1.add(String(367,44,"ACSL4 Ferro-Aging Protection (>90%)",textAnchor="middle",fontName="Helvetica",fontSize=7.5,fillColor=c_body))
d1.add(String(367,28,"OCT4 <= 0.35 | MYC <= 0.30 (Zero Tumor)",textAnchor="middle",fontName="Helvetica-Bold",fontSize=7,fillColor=c_green))
d1.add(Line(475,60,525,60,strokeColor=c_blue,strokeWidth=2))
d1.add(Polygon([520,55,530,60,520,65],fillColor=c_blue,strokeColor=c_blue))
d1.add(Rect(530,15,205,90,rx=6,ry=6,fillColor=colors.HexColor("#F0FDF4"),strokeColor=colors.HexColor("#86EFAC"),strokeWidth=1))
d1.add(String(632,82,"REJUVENATED CARDIOMYOCYTE",textAnchor="middle",fontName="Helvetica-Bold",fontSize=9,fillColor=c_green))
d1.add(String(632,66,"Biological Age: 52.0y (-13.0y Reset)",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8.5,fillColor=c_slate))
d1.add(String(632,50,"TNNT2 >94% | Cx43 >94% (Arrhythmia Safe)",textAnchor="middle",fontName="Helvetica",fontSize=7.5,fillColor=c_body))
d1.add(String(632,34,"Restored SERCA2a Diastolic Ca2+",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_muted))
story.append(d1)
story.append(Spacer(1,6))

c1 = [
    Paragraph("MOLECULAR MECHANISM & REPROGRAMMING", h2_s),
    Paragraph("NL-101 targets the epigenetic driver of cardiac aging. Non-oncogenic pioneer factors (<i>GATA4</i>, <i>ZBTB16</i>) alongside deacetylases (<i>SIRT1</i>, <i>SIRT6</i>) under Decaying Resonance Pulse (DRP) kinetics reverse DNA hypermethylation across 353 Horvath CpG loci without sarcomeric disassembly or pluripotency.", bd_s), Spacer(1,4),
    Paragraph("- <b>ACSL4 Ferro-Aging Protection:</b> Audits ACSL4/GPX4 ratios (Liu et al., Cell Metab 2026) to prevent lipid peroxidation (&gt;90% cytoprotection).", bu_s),
    Paragraph("- <b>NEUROS-X Arrhythmia Audit:</b> 512-neuron spiking cardiac substrate with zero arrhythmia events.", bu_s), Spacer(1,6),
    Paragraph("<b>SAFETY BOUNDARIES ENFORCED BY ZENITH:</b>", ct_s), Spacer(1,3),
    Paragraph("- <b>OCT4 (POU5F1):</b> Capped at 0.35 (pluripotency lockout).", bu_s),
    Paragraph("- <b>c-MYC:</b> Capped at 0.30 (oncogenesis prevention gate).", bu_s),
    Paragraph("- <b>TNNT2:</b> Maintained above 94% (sarcomere integrity).", bu_s),
    Paragraph("- <b>GJA1 (Connexin-43):</b> Maintained above 94% (arrhythmia safety).", bu_s),
    Paragraph("- <b>ATP2A2 (SERCA2a):</b> Stabilized diastolic calcium handling.", bu_s),
]
c2 = [
    Paragraph("ZENITH GENERATIVE AI PLATFORM (scVI 5,009D)", h2_s),
    Paragraph("Zenith v31.0 GOLD: 5,009D transcriptomic manifold across 2.42M human cardiac single cells (Litvinukova et al., <i>Nature</i> 2020).", bd_s), Spacer(1,4),
    Paragraph("<b>Factor Regulatory Weights:</b>", ct_s),
    Paragraph("- <b>SIRT6 (+0.60):</b> Deacetylates H3K9ac/H3K56ac; stops transcriptional noise.", bu_s),
    Paragraph("- <b>SIRT1 (+0.55):</b> Restores mitochondrial bioenergetics & NAD+ balance.", bu_s),
    Paragraph("- <b>GATA4 (+0.46):</b> Promotes TNNT2, MYH7, and Cx43 promoters.", bu_s),
    Paragraph("- <b>ZBTB16 (+0.38):</b> Locks somatic cell identity & stress resilience.", bu_s), Spacer(1,6),
    Paragraph("<b>AUTOMATED WET-LAB INTEGRATIONS:</b>", ct_s), Spacer(1,3),
    Paragraph("- <b>Opentrons OT-2:</b> 1-click liquid-handling robotics CSV export.", bu_s),
    Paragraph("- <b>Boltz-1 / AlphaFold 3:</b> 3D structural protein folding manifests.", bu_s),
    Paragraph("- <b>LNP Delivery Optimizer:</b> 94.4% encapsulation efficiency.", bu_s),
    Paragraph("- <b>Multi-Clock EnsembleAge:</b> Horvath 353 + Krolevets 8 + Hannum 71.", bu_s),
]
t_mc = Table([[c1, c2]], colWidths=[370, 374])
t_mc.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_card),('BOX',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_mc)
story.append(PageBreak())

# ====================================================================
# SLIDE 4: mRNA-LNP DELIVERY + PIPELINE + DNA IMAGE
# ====================================================================
story.append(Paragraph("SLIDE 3: TARGETED mRNA-LNP DELIVERY & THERAPEUTIC PIPELINE", h1_s))
story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceAfter=6))

d2 = Drawing(744, 110)
d2.add(Rect(10,15,200,80,rx=6,ry=6,fillColor=c_card,strokeColor=c_border,strokeWidth=1))
d2.add(String(110,72,"SYSTEMIC IV INJECTION",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8.5,fillColor=c_slate))
d2.add(String(110,56,"NL-101 Peptide-Conjugated LNPs",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8,fillColor=c_blue))
d2.add(String(110,40,"Anti-VCAM-1 / Anti-NCAM1 Ligands",textAnchor="middle",fontName="Helvetica",fontSize=7.5,fillColor=c_body))
d2.add(String(110,24,"N/P Ratio: 6.0 | PEG-2000 Da",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_muted))
d2.add(Line(210,55,260,75,strokeColor=colors.HexColor("#EF4444"),strokeWidth=1.5))
d2.add(Line(210,55,260,35,strokeColor=c_blue,strokeWidth=1.5))
d2.add(Rect(265,60,215,40,rx=4,ry=4,fillColor=colors.HexColor("#FEF2F2"),strokeColor=colors.HexColor("#FCA5A5"),strokeWidth=1))
d2.add(String(372,84,"PASSIVE LNP: 84% LIVER TRAPPING",textAnchor="middle",fontName="Helvetica-Bold",fontSize=7.5,fillColor=colors.HexColor("#991B1B")))
d2.add(String(372,68,"ApoE Corona Opsonization & Clearance",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_body))
d2.add(Rect(265,10,215,40,rx=4,ry=4,fillColor=colors.HexColor("#EFF6FF"),strokeColor=c_blue,strokeWidth=1))
d2.add(String(372,34,"ACTIVE NL-101: MYOCARDIAL BYPASS",textAnchor="middle",fontName="Helvetica-Bold",fontSize=7.5,fillColor=c_blue))
d2.add(String(372,18,"Crosses Non-Fenestrated Capillaries",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_body))
d2.add(Line(480,30,520,30,strokeColor=c_blue,strokeWidth=2))
d2.add(Polygon([515,25,525,30,515,35],fillColor=c_blue,strokeColor=c_blue))
d2.add(Rect(525,15,210,80,rx=6,ry=6,fillColor=colors.HexColor("#F0FDF4"),strokeColor=colors.HexColor("#86EFAC"),strokeWidth=1))
d2.add(String(630,72,">80% CARDIAC TROPISM",textAnchor="middle",fontName="Helvetica-Bold",fontSize=9,fillColor=c_green))
d2.add(String(630,56,"Cardiomyocyte Specific Uptake",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8,fillColor=c_slate))
d2.add(String(630,40,"Zero Hepatocyte Toxicity",textAnchor="middle",fontName="Helvetica",fontSize=7.5,fillColor=c_body))
d2.add(String(630,24,"Endosomal Escape: 12.9%",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_muted))
story.append(d2)
story.append(Spacer(1,6))

story.append(Paragraph("THERAPEUTIC PIPELINE MATRIX", h2_s))
pd = [
    [Paragraph("<b>Program</b>",ph), Paragraph("<b>Target Modality</b>",ph), Paragraph("<b>Primary Indication</b>",ph), Paragraph("<b>Stage</b>",ph)],
    [Paragraph("<b>NL-101</b>",bd_s), Paragraph("SIRT1+6+GATA4+ZBTB16 mRNA-LNP",bd_s), Paragraph("Post-MI Heart Failure",bd_s), Paragraph("In-Vitro Validated / In-Vivo Ready",bd_s)],
    [Paragraph("<b>NL-102</b>",bd_s), Paragraph("VE-Cadherin/CD31 Endothelial",bd_s), Paragraph("Microvascular Angina",bd_s), Paragraph("In-Silico Target Discovery",bd_s)],
    [Paragraph("<b>NL-103</b>",bd_s), Paragraph("Synaptic Preservation Factors",bd_s), Paragraph("Cardiac Denervation",bd_s), Paragraph("In-Silico Target Discovery",bd_s)]
]
t_p = Table(pd, colWidths=[60,250,200,234])
t_p.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),c_card),('GRID',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),5),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(t_p)
story.append(Spacer(1,8))

nilus_img = Image(img2_path, width=744, height=270)
story.append(nilus_img)
story.append(PageBreak())

# ====================================================================
# SLIDE 5: TEAM, ADVISORS & SCIENTIFIC PUBLICATIONS
# ====================================================================
story.append(Paragraph("SLIDE 4: FOUNDING TEAM, ADVISORS & SCIENTIFIC FOUNDATION", h1_s))
story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceAfter=6))

tl = [
    Paragraph("<b>FOUNDING TEAM</b>", ct_s), Spacer(1,6),
    Paragraph("<b>Alaa Aldeen</b> - Founder & CEO", ParagraphStyle('TN',parent=bd_s,fontName='Helvetica-Bold',textColor=c_blue)), Spacer(1,3),
    Paragraph("AI-native biotech founder with deep expertise in computational biology, single-cell transcriptomics, and generative AI drug discovery. Builder of the Zenith platform from first principles across 2.42M human cardiac single cells.", bd_s), Spacer(1,6),
    Paragraph("<b>Key Technical Competencies:</b>", ct_s), Spacer(1,3),
    Paragraph("- Variational Autoencoders (scVI/scANVI) for single-cell biology", bu_s),
    Paragraph("- mRNA-LNP delivery system design & optimization", bu_s),
    Paragraph("- Epigenetic clock engineering (Horvath, Hannum, Krolevets)", bu_s),
    Paragraph("- Automated liquid-handling robotics (Opentrons OT-2)", bu_s),
    Paragraph("- Structural biology integration (Boltz-1, AlphaFold 3)", bu_s),
    Paragraph("- NEUROS-X spiking neural network safety auditing", bu_s), Spacer(1,8),
    Paragraph("<b>ACCELERATOR & PROGRAM</b>", ct_s), Spacer(1,3),
    Paragraph("- <b>HomeLab Deep Science Accelerator</b> (Cohort 5)", bu_s),
    Paragraph("- Mentored by SDVC biotech investor network", bu_s),
    Paragraph("- Guest speakers: George Voren + Industry LPs", bu_s),
]
tr = [
    Paragraph("<b>SCIENTIFIC PUBLICATION & PAPER FOUNDATION</b>", ct_s), Spacer(1,4),
    Paragraph("• <b>Zenith Paper:</b> <font color='#1D4ED8'><b>niluslab.com/zenith_scientific_paper.html</b></font>", ParagraphStyle('SP',parent=bd_s,textColor=c_blue)), Spacer(1,3),
    Paragraph("<b>Core Training Data:</b>", ct_s), Spacer(1,2),
    Paragraph("- Litvinukova et al., <i>Nature</i> 2020 -- Human Heart Cell Atlas (2.42M cells, 14 cardiac subtypes)", bu_s), Spacer(1,3),
    Paragraph("<b>Epigenetic Age Reversal:</b>", ct_s), Spacer(1,3),
    Paragraph("- Horvath S., <i>Genome Biology</i> 2013 -- 353-CpG DNA Methylation Clock", bu_s),
    Paragraph("- Hannum G. et al., <i>Mol Cell</i> 2013 -- 71-CpG Blood-Based Age Clock", bu_s),
    Paragraph("- Krolevets M. et al., <i>GeroScience</i> 2026 -- 8-Locus Cardiac-Specific Clock", bu_s), Spacer(1,3),
    Paragraph("<b>Safety & Cytoprotection:</b>", ct_s), Spacer(1,3),
    Paragraph("- Liu et al., <i>Cell Metabolism</i> 2026 -- ACSL4 Ferro-Aging Cytoprotection", bu_s),
    Paragraph("- Parkhitko et al., <i>Aging Cell</i> 2023 -- Sirtuin Cardiac Deacetylation", bu_s), Spacer(1,3),
    Paragraph("<b>mRNA-LNP Delivery:</b>", ct_s), Spacer(1,3),
    Paragraph("- Cheng et al., <i>Nat Nanotech</i> 2023 -- Organ-Selective LNP Targeting", bu_s),
    Paragraph("- Paunovska et al., <i>Nat Rev Genetics</i> 2022 -- LNP Drug Delivery Systems", bu_s), Spacer(1,3),
    Paragraph("<b>Structural Biology:</b>", ct_s), Spacer(1,3),
    Paragraph("- Wohlwend et al., <i>Nature Methods</i> 2025 -- Boltz-1 Biomolecular Prediction", bu_s),
    Paragraph("- Abramson et al., <i>Nature</i> 2024 -- AlphaFold 3 Protein Structure", bu_s),
]
t_t = Table([[tl, tr]], colWidths=[370, 374])
t_t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_card),('BOX',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_t)
story.append(PageBreak())

# ====================================================================
# SLIDE 6: ROADMAP, ASK & CONTACT
# ====================================================================
story.append(Paragraph("SLIDE 5: DE-RISKING ROADMAP & $500,000 THE ASK", h1_s))
story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceAfter=6))

d3 = Drawing(744, 100)
d3.add(Line(30,50,710,50,strokeColor=c_border,strokeWidth=3.5))
d3.add(Circle(100,50,11,fillColor=c_blue,strokeColor=c_white,strokeWidth=2))
d3.add(String(100,76,"MILESTONE 1 (Q3-Q4 2026)",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8,fillColor=c_blue))
d3.add(String(100,28,"OT-2 In-Vitro Validation",textAnchor="middle",fontName="Helvetica-Bold",fontSize=7.5,fillColor=c_slate))
d3.add(String(100,14,"$60,000 Budget",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_muted))
d3.add(Circle(300,50,11,fillColor=c_blue,strokeColor=c_white,strokeWidth=2))
d3.add(String(300,76,"MILESTONE 2 (Q1 2027)",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8,fillColor=c_blue))
d3.add(String(300,28,"CRO Mouse MI LVEF POC",textAnchor="middle",fontName="Helvetica-Bold",fontSize=7.5,fillColor=c_slate))
d3.add(String(300,14,"$150,000 Budget",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_muted))
d3.add(Circle(500,50,11,fillColor=c_blue,strokeColor=c_white,strokeWidth=2))
d3.add(String(500,76,"MILESTONE 3 (Q2 2027)",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8,fillColor=c_blue))
d3.add(String(500,28,"Provisional Patent Filings",textAnchor="middle",fontName="Helvetica-Bold",fontSize=7.5,fillColor=c_slate))
d3.add(String(500,14,"$50,000 Budget",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_muted))
d3.add(Circle(680,50,11,fillColor=c_green,strokeColor=c_white,strokeWidth=2))
d3.add(String(680,76,"MILESTONE 4 (Q3 2027)",textAnchor="middle",fontName="Helvetica-Bold",fontSize=8,fillColor=c_green))
d3.add(String(680,28,"Biopharma Co-Dev Deal",textAnchor="middle",fontName="Helvetica-Bold",fontSize=7.5,fillColor=c_slate))
d3.add(String(680,14,"FDA Pre-IND Clearance",textAnchor="middle",fontName="Helvetica",fontSize=7,fillColor=c_muted))
story.append(d3)
story.append(Spacer(1,8))

al = [
    Paragraph("<b>THE $500,000 PRE-SEED FINANCING ASK</b>", h2_s),
    Paragraph("We are raising <b>$500,000 in Pre-Seed capital</b> to fund our asset-light CRO validation roadmap and execute our first biopharma co-development agreement.", bd_s), Spacer(1,6),
    Paragraph("<b>Why Nilus Lab Will Win:</b>", ct_s),
    Paragraph("- <b>Unrivaled Cardiac Specialization:</b> While Altos Labs ($3B) and Retro Bio ($180M) focus on un-targeted systemic reprogramming, Nilus Lab solves the Cx43 arrhythmia bottleneck first.", bu_s), Spacer(1,3),
    Paragraph("- <b>Asset-Light CRO Model:</b> Zero lab overhead. Premier CRO partners execute animal models while we generate automated OT-2 robotic scripts.", bu_s), Spacer(1,3),
    Paragraph("- <b>Computational Moat:</b> 5,009D scVI manifold trained on 2.42M cells. No competitor has cardiac-specialized generative biology at this scale.", bu_s), Spacer(1,3),
    Paragraph("- <b>Healthspan Impact:</b> If successful, NL-101 could extend cardiac healthspan by 13+ years for 64M heart failure patients globally.", bu_s), Spacer(1,6),
    Paragraph("<b>INVESTOR RETURN THESIS:</b>", ct_s), Spacer(1,3),
    Paragraph("- Series A target: $15-25M at 18-24 months post-investment", bu_s),
    Paragraph("- Biopharma co-development licensing deal potential: $50-200M", bu_s),
    Paragraph("- Comparable exit multiples: 10-50x (longevity biotech sector)", bu_s),
]
ar = [
    Paragraph("<b>USE OF PROCEEDS BREAKDOWN</b>", h2_s),
    Paragraph("- <b>$60,000 (12%)</b> -- OT-2 Automated In-Vitro iPSC-CM Assays", bu_s), Spacer(1,3),
    Paragraph("- <b>$150,000 (30%)</b> -- CRO Mouse LAD Ligation MI LVEF POC", bu_s), Spacer(1,3),
    Paragraph("- <b>$50,000 (10%)</b> -- Provisional Patent Portfolio", bu_s), Spacer(1,3),
    Paragraph("- <b>$40,000 (8%)</b> -- FDA Pre-IND Briefing Dossier", bu_s), Spacer(1,3),
    Paragraph("- <b>$200,000 (40%)</b> -- Working Capital & Platform Scale", bu_s), Spacer(1,8),
    Paragraph("<b>CONTACT & LINKS</b>", ct_s), Spacer(1,3),
    Paragraph("- <b>Founder:</b> Alaa Aldeen (Founder & CEO)", bu_s),
    Paragraph("- <b>Website:</b> niluslab.com", bu_s),
    Paragraph("- <b>Scientific Paper:</b> niluslab.com/zenith_scientific_paper.html", ParagraphStyle('SP2',parent=bu_s,textColor=c_blue,fontName='Helvetica-Bold')),
    Paragraph("- <b>Email:</b> info@niluslab.com", bu_s),
    Paragraph("- <b>Program:</b> HomeLab Deep Science Accelerator (Cohort 5)", bu_s),
    Paragraph("- <b>Domains:</b> niluslab.com | niluscare.com | zenithbiology.com", bu_s), Spacer(1,4),
    Paragraph("<b>NILUS LAB | CARDIAC LONGEVITY PLATFORM</b>", ParagraphStyle('EX',parent=ct_s,textColor=c_blue,alignment=TA_CENTER)),
    Paragraph("niluslab.com | Pre-Seed 2026", ParagraphStyle('EX2',parent=bs_s,alignment=TA_CENTER)),
]
t_a = Table([[al, ar]], colWidths=[370, 374])
t_a.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_card),('BOX',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),12),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_a)

doc.build(story)
print("Done - PDF generated successfully")
