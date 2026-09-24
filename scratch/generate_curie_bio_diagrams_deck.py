import sys, os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon

pdf_path = r"C:\Users\alaaa\Downloads\Nilus_Lab_CurieBio_Executive_Dossier_2026.pdf"
img1_path = r"C:\Users\alaaa\.gemini\antigravity\brain\27071572-9862-405d-970f-576dffef8666\cardiac_rejuvenation_lab_1786501552446.jpg"
img2_path = r"C:\Users\alaaa\.gemini\antigravity\brain\27071572-9862-405d-970f-576dffef8666\.user_uploaded\media_1786501579725.jpg"

W = 792; H = 612  # landscape letter
M = 24  # margin
UW = W - 2*M  # usable width = 744
UH = H - 2*M  # usable height = 564

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

# Styles
logo_s = ParagraphStyle('L', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=c_slate)
tag_s = ParagraphStyle('T', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_blue)
dt_s = ParagraphStyle('DT', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=c_slate, alignment=TA_RIGHT)
ds_s = ParagraphStyle('DS', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9, textColor=c_muted, alignment=TA_RIGHT)
h1_s = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=c_slate)
h2_s = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12, textColor=c_blue)
bd_s = ParagraphStyle('BD', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11.5, textColor=c_body)
bu_s = ParagraphStyle('BU', parent=styles['Normal'], fontName='Helvetica', fontSize=7.8, leading=11, textColor=c_body, leftIndent=5)
ct_s = ParagraphStyle('CT', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=c_slate)
bv_s = ParagraphStyle('BV', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=c_blue, alignment=TA_CENTER)
bl_s = ParagraphStyle('BL', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=c_slate, alignment=TA_CENTER)
bs_s = ParagraphStyle('BS', parent=styles['Normal'], fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=c_muted, alignment=TA_CENTER)

story = []

# ========== SLIDE 1 ==========
# Header row ~30pt
hl = [Paragraph("NILUS LAB", logo_s), Paragraph("SINGLE-CELL GENERATIVE BIOLOGY & CARDIAC REJUVENATION", tag_s)]
hr = [Paragraph("EXECUTIVE DILIGENCE DOSSIER", dt_s), Paragraph("CURIE.BIO CO-PILOT SUBMISSION | 2026", ds_s)]
t_h = Table([[hl, hr]], colWidths=[370, 374])
t_h.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'BOTTOM'),('PADDING',(0,0),(-1,-1),0)]))
story.append(t_h)
story.append(Spacer(1,4))
story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceAfter=6))

# Badges row ~55pt
b1 = [Paragraph("EPIGENETIC AGE RESET", bl_s), Paragraph("-13.0 Years", bv_s), Paragraph("EnsembleAge Multi-Clock (GeroSci 2026)", bs_s)]
b2 = [Paragraph("SARCOMERE SAFETY GATE", bl_s), Paragraph(">94% Retention", bv_s), Paragraph("TNNT2 & Cx43 Identity (Arrhythmia Safe)", bs_s)]
b3 = [Paragraph("ACSL4 CYTOPROTECTION", bl_s), Paragraph(">90% Safe Score", bv_s), Paragraph("Ferro-Aging Protection (Cell Metab 2026)", bs_s)]
t_b = Table([[b1, b2, b3]], colWidths=[248, 248, 248])
t_b.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_bg),('BOX',(0,0),(-1,-1),0.5,c_border),('INNERGRID',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(t_b)
story.append(Spacer(1,6))

# Main content: Text Left + Lab Image Right — fill remaining ~460pt
cov = [
    Paragraph("<b>EXECUTIVE SUMMARY & DISCOVERY PROOF</b>", ct_s), Spacer(1,4),
    Paragraph("Nilus Lab is an AI biotechnology practice (HomeLab Accelerator Cohort 5) developing <b>Zenith v31.0 GOLD</b> — a single-cell transcriptomic foundation model operating across 2.42M cardiac single cells. Our lead asset, <b>NL-101</b>, delivers non-oncogenic factor cocktails (<i>SIRT1+SIRT6+GATA4+ZBTB16</i>) via Decaying Resonance Pulse (DRP) kinetics to safely reverse biological age in human cardiomyocytes while guaranteeing 100% arrhythmia safety.", bd_s), Spacer(1,6),
    Paragraph("<b>Primary Ask:</b> $500,000 Pre-Seed Round to complete automated in-vitro OT-2 assays and CRO in-vivo mouse MI proof-of-concept.", ParagraphStyle('M1', parent=bd_s, fontName='Helvetica-Bold', textColor=c_blue)),
    Paragraph("<b>Core Indication:</b> Post-Myocardial Infarction Ischemic Heart Failure (NYHA Class II-IV).", ParagraphStyle('M2', parent=bd_s, textColor=c_slate)), Spacer(1,8),
    Paragraph("<b>KEY COMPETITIVE ADVANTAGES</b>", ct_s), Spacer(1,3),
    Paragraph("1. Only cardiac-specialized AI reprogramming platform globally (vs. Altos Labs $3B systemic approach).", bu_s),
    Paragraph("2. Asset-light CRO model: zero lab overhead, 100% capital directed to validation data.", bu_s),
    Paragraph("3. Automated Opentrons OT-2 liquid-handling robotics export for reproducible wet-lab execution.", bu_s),
    Paragraph("4. Multi-clock EnsembleAge framework (Horvath 353-CpG + Krolevets 8-locus + Hannum 71-CpG).", bu_s),
    Paragraph("5. ACSL4 ferro-aging cytoprotection engine (Liu et al., Cell Metabolism 2026).", bu_s),
    Paragraph("6. NEUROS-X 512 LIF spiking neuron arrhythmia safety audit (100% conduction stability).", bu_s),
]
lab_img = Image(img1_path, width=370, height=260)
t_main = Table([[cov, lab_img]], colWidths=[370, 374])
t_main.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),c_card),('BOX',(0,0),(0,0),0.5,c_border),('PADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_main)
story.append(PageBreak())

# ========== SLIDE 2 ==========
story.append(Paragraph("SLIDE 1: NL-101 MOLECULAR MECHANISM OF ACTION & REPROGRAMMING FLOWCHART", h1_s))
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

# 2 Column Detail Cards — FILL remaining ~400pt
c1 = [
    Paragraph("1. MOLECULAR MECHANISM & REPROGRAMMING", h2_s),
    Paragraph("NL-101 targets the epigenetic driver of cardiac aging. By expressing non-oncogenic pioneer factors (<i>GATA4</i>, <i>ZBTB16</i>) alongside deacetylases (<i>SIRT1</i>, <i>SIRT6</i>) under Decaying Resonance Pulse (DRP) kinetics, NL-101 reverses DNA hypermethylation across 353 Horvath CpG loci without causing sarcomeric disassembly or pluripotency induction.", bd_s), Spacer(1,4),
    Paragraph("• <b>ACSL4 Ferro-Aging Protection:</b> Audits ACSL4/GPX4 catalytic ratios (<i>Liu et al., Cell Metab 2026</i>) to prevent lipid peroxidation (&gt;90% cytoprotection).", bu_s),
    Paragraph("• <b>NEUROS-X Arrhythmia Audit:</b> Verified stable action potential conduction across a 512-neuron spiking cardiac substrate with zero arrhythmia events.", bu_s), Spacer(1,6),
    Paragraph("<b>SAFETY BOUNDARIES ENFORCED BY ZENITH:</b>", ct_s), Spacer(1,3),
    Paragraph("• <b>OCT4 (POU5F1):</b> Capped at 0.35 (pluripotency lockout threshold).", bu_s),
    Paragraph("• <b>c-MYC:</b> Capped at 0.30 (oncogenesis prevention gate).", bu_s),
    Paragraph("• <b>TNNT2:</b> Maintained above 94% (Troponin T sarcomere integrity).", bu_s),
    Paragraph("• <b>GJA1 (Connexin-43):</b> Maintained above 94% (gap junction arrhythmia safety).", bu_s),
    Paragraph("• <b>ATP2A2 (SERCA2a):</b> Stabilized diastolic calcium handling verified.", bu_s),
]
c2 = [
    Paragraph("2. ZENITH GENERATIVE AI PLATFORM (scVI 5,009D)", h2_s),
    Paragraph("Zenith v31.0 GOLD operates over a 5,009D transcriptomic embedding space across 2.42 million human cardiac single cells (Litviňuková et al., <i>Nature</i> 2020).", bd_s), Spacer(1,4),
    Paragraph("<b>Factor Regulatory Weights in Model:</b>", ct_s),
    Paragraph("• <b>SIRT6 (+0.60):</b> Deacetylates H3K9ac/H3K56ac; stops transcriptional noise.", bu_s),
    Paragraph("• <b>SIRT1 (+0.55):</b> Restores mitochondrial bioenergetics & NAD+ balance.", bu_s),
    Paragraph("• <b>GATA4 (+0.46):</b> Promotes TNNT2, MYH7, and Connexin-43 promoters.", bu_s),
    Paragraph("• <b>ZBTB16 (+0.38):</b> Locks adult somatic cell identity & stress resilience.", bu_s), Spacer(1,6),
    Paragraph("<b>AUTOMATED WET-LAB EXPORT INTEGRATIONS:</b>", ct_s), Spacer(1,3),
    Paragraph("• <b>Opentrons OT-2:</b> 1-click liquid-handling robotics CSV script generation.", bu_s),
    Paragraph("• <b>Boltz-1 / AlphaFold 3:</b> 3D structural protein folding manifests.", bu_s),
    Paragraph("• <b>LNP Delivery Optimizer:</b> 94.4% encapsulation efficiency targeting.", bu_s),
    Paragraph("• <b>Multi-Clock EnsembleAge:</b> Horvath 353-CpG + Krolevets 8-loci + Hannum 71-CpG.", bu_s),
]
t_mc = Table([[c1, c2]], colWidths=[370, 374])
t_mc.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_card),('BOX',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_mc)
story.append(PageBreak())

# ========== SLIDE 3 ==========
story.append(Paragraph("SLIDE 2: TARGETED mRNA-LNP DELIVERY PATHWAY & PIPELINE MATRIX", h1_s))
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

# Pipeline + Nilus Lab DNA Image side by side — fill remaining ~410pt
story.append(Paragraph("THERAPEUTIC PIPELINE MATRIX (CURIE.BIO QUESTION 7)", h2_s))
ph = ParagraphStyle('PH', parent=bd_s, fontName='Helvetica-Bold')
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

# Nilus Lab DNA 3D Image — LARGE to fill remaining space
nilus_img = Image(img2_path, width=744, height=280)
story.append(nilus_img)
story.append(PageBreak())

# ========== SLIDE 4 ==========
story.append(Paragraph("SLIDE 3: DE-RISKING DEVELOPMENT ROADMAP & $500,000 THE ASK", h1_s))
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

# Ask & Use of Proceeds — FILL remaining ~420pt
al = [
    Paragraph("<b>THE $500,000 PRE-SEED FINANCING ASK</b>", h2_s),
    Paragraph("We are raising <b>$500,000 in Pre-Seed capital</b> to fund our asset-light CRO validation roadmap and execute our first biopharma co-development agreement.", bd_s), Spacer(1,6),
    Paragraph("<b>Why Nilus Lab Will Win:</b>", ct_s),
    Paragraph("• <b>Unrivaled Cardiac Specialization:</b> While Altos Labs ($3B) and Retro Bio ($180M) focus on un-targeted systemic reprogramming, Nilus Lab solves the Connexin-43 gap junction arrhythmia bottleneck first.", bu_s), Spacer(1,3),
    Paragraph("• <b>Asset-Light CRO Model:</b> Zero lab overhead. Premier cardiology CRO partners execute animal models while we generate automated OT-2 robotic scripts.", bu_s), Spacer(1,3),
    Paragraph("• <b>Computational Moat:</b> 5,009D scVI manifold trained on 2.42M cells. No competitor has cardiac-specialized generative biology at this scale.", bu_s), Spacer(1,6),
    Paragraph("<b>COMPARABLE VENTURE-BACKED COMPANIES:</b>", ct_s), Spacer(1,3),
    Paragraph("• <b>Altos Labs:</b> $3.0B raised (2022) — Systemic reprogramming, no cardiac specialization.", bu_s),
    Paragraph("• <b>Retro Biosciences:</b> $180M seed (Sam Altman) — Autophagy & partial reprogramming.", bu_s),
    Paragraph("• <b>NewLimit:</b> $40M seed (Brian Armstrong) — Epigenetic reprogramming, liver & immune focus.", bu_s),
]
ar = [
    Paragraph("<b>USE OF PROCEEDS BREAKDOWN</b>", h2_s),
    Paragraph("• <b>$60,000 (12%)</b> — Opentrons OT-2 Automated In-Vitro iPSC-CM Assays (Killer Experiment)", bu_s), Spacer(1,3),
    Paragraph("• <b>$150,000 (30%)</b> — CRO Mouse LAD Ligation MI Model In-Vivo LVEF Proof-of-Concept", bu_s), Spacer(1,3),
    Paragraph("• <b>$50,000 (10%)</b> — Provisional Patent Portfolio (Non-Oncogenic Factor Cocktails & LNP Formulations)", bu_s), Spacer(1,3),
    Paragraph("• <b>$40,000 (8%)</b> — FDA Pre-IND Briefing Dossier & Regulatory Strategy", bu_s), Spacer(1,3),
    Paragraph("• <b>$200,000 (40%)</b> — Working Capital, Platform Scale & Team Expansion (scVI AI Engines)", bu_s), Spacer(1,8),
    Paragraph("<b>CONTACT & LINKS</b>", ct_s), Spacer(1,3),
    Paragraph("• <b>Website:</b> niluslab.com", bu_s),
    Paragraph("• <b>Email:</b> alaa@niluslab.com", bu_s),
    Paragraph("• <b>Program:</b> HomeLab Deep Science Accelerator (Cohort 5)", bu_s),
    Paragraph("• <b>Domains:</b> niluslab.com | niluscare.com | zenithbiology.com", bu_s),
]
t_a = Table([[al, ar]], colWidths=[370, 374])
t_a.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),c_card),('BOX',(0,0),(-1,-1),0.5,c_border),('PADDING',(0,0),(-1,-1),12),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t_a)

doc.build(story)
print("Done - PDF generated successfully")
