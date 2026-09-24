import sys
import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

pdf_path = r"C:\Users\alaaa\Downloads\Nilus_Lab_CurieBio_Executive_Dossier_2026.pdf"

# Landscape 16:9 Presentation Format (792 x 612 pt)
doc = SimpleDocTemplate(
    pdf_path,
    pagesize=landscape(letter),
    rightMargin=36,
    leftMargin=36,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()

# TechBio Executive Presentation Palette (Dark Slate, Deep Navy, Cool Slate & Crisp Cyan)
c_bg_dark = colors.HexColor("#0B0F19")      # Dark Space Slate
c_card_dark = colors.HexColor("#111827")    # Deep Slate Card
c_header_dark = colors.HexColor("#1E293B")  # Slate Container Header
c_border = colors.HexColor("#334155")       # Cool Grey Border
c_cyan = colors.HexColor("#0284C7")         # Institutional Accent Cyan
c_white = colors.HexColor("#F8FAFC")        # Pure Light Text
c_body = colors.HexColor("#CBD5E1")         # Slate Body Text
c_muted = colors.HexColor("#94A3B8")        # Muted Slate

# Typography Styles
title_cover_style = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=28, leading=34, textColor=c_white)
subtitle_cover_style = ParagraphStyle('CoverSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=c_cyan)
body_cover_style = ParagraphStyle('CoverBody', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=c_body)

slide_h1_style = ParagraphStyle('SlideH1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=c_white)
slide_h2_style = ParagraphStyle('SlideH2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=c_cyan)
body_style = ParagraphStyle('SlideBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=c_body)
bullet_style = ParagraphStyle('SlideBullet', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=c_body, leftIndent=8)

card_title_style = ParagraphStyle('CardT', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=c_white)
badge_val_style = ParagraphStyle('BadgeV', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=c_cyan, alignment=TA_CENTER)
badge_lbl_style = ParagraphStyle('BadgeL', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=c_white, alignment=TA_CENTER)
badge_sub_style = ParagraphStyle('BadgeS', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=c_muted, alignment=TA_CENTER)

story = []

# ==========================================
# SLIDE 1: DARK EXECUTIVE COVER SLIDE
# ==========================================
cov_left = [
    Paragraph("NILUS LAB", title_cover_style),
    Spacer(1, 4),
    Paragraph("GENERATIVE BIOLOGY & CARDIAC CELLULAR REJUVENATION", subtitle_cover_style),
    Spacer(1, 10),
    Paragraph("In-Silico Single-Cell Transcriptomic AI Platform for Cardiac Biological Age Reversal", body_cover_style),
    Spacer(1, 14),
    Paragraph("<b>Target Ask:</b> $500,000 Pre-Seed Round | <b>Program:</b> HomeLab Accelerator Cohort 5", ParagraphStyle('CoverMeta', parent=body_cover_style, fontName='Helvetica-Bold', fontSize=9, textColor=c_white))
]

cov_right = [
    Paragraph("<b>CURIE.BIO CO-PILOT DILIGENCE DOSSIER</b>", ParagraphStyle('CR1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=c_white, alignment=TA_RIGHT)),
    Spacer(1, 4),
    Paragraph("Prepared for Curie.Bio Senior Scientific Team", ParagraphStyle('CR2', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=c_muted, alignment=TA_RIGHT)),
    Spacer(1, 12),
    Paragraph("<b>Lead Asset:</b> NL-101 (mRNA-LNP)<br/><b>Entity:</b> Nilus Lab Ltd. (UK / UAE)<br/><b>Domain:</b> niluslab.com", ParagraphStyle('CR3', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=c_body, alignment=TA_RIGHT))
]

t_cover = Table([[cov_left, cov_right]], colWidths=[460, 260])
t_cover.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), c_card_dark),
    ('BOX', (0,0), (-1,-1), 1, c_border),
    ('PADDING', (0,0), (-1,-1), 20),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(t_cover)
story.append(Spacer(1, 14))

# KPI Badges Bar (3 Key Metrics)
b1 = [Paragraph("EPIGENETIC AGE RESET", badge_lbl_style), Paragraph("-13.0 Years", badge_val_style), Paragraph("EnsembleAge Multi-Clock (GeroSci 2026)", badge_sub_style)]
b2 = [Paragraph("SARCOMERE SAFETY GATE", badge_lbl_style), Paragraph(">94% Retention", badge_val_style), Paragraph("TNNT2 & Cx43 Identity (Arrhythmia Safe)", badge_sub_style)]
b3 = [Paragraph("ACSL4 CYTOPROTECTION", badge_lbl_style), Paragraph(">90% Safe Score", badge_val_style), Paragraph("Ferro-Aging Protection (Cell Metab 2026)", badge_sub_style)]

t_badges = Table([[b1, b2, b3]], colWidths=[235, 235, 235])
t_badges.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), c_header_dark),
    ('BOX', (0,0), (-1,-1), 1, c_border),
    ('INNERGRID', (0,0), (-1,-1), 1, c_border),
    ('PADDING', (0,0), (-1,-1), 10),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(t_badges)

story.append(PageBreak())

# ==========================================
# SLIDE 2: QUESTIONS 1 & 2 — LEAD PROGRAM & PLATFORM ARCHITECTURE
# ==========================================
story.append(Paragraph("SLIDE 1: LEAD PROGRAM (NL-101) & GENERATIVE AI PLATFORM", slide_h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=c_cyan, spaceAfter=10))

col1 = [
    Paragraph("1. LEAD PROGRAM & MOLECULAR MECHANISM", slide_h2_style),
    Paragraph("<b>Asset Identifier:</b> NL-101 (Transient mRNA-LNP Rejuvenation Cocktail)", card_title_style),
    Spacer(1, 4),
    Paragraph("<b>Unmet Need & Disease Rationale:</b> Adult human ventricular cardiomyocytes exhibit near-zero natural post-natal regeneration (&lt;0.5%/yr). Post-myocardial infarction (MI), wall stress and epigenetic drift cause progressive, fatal heart failure (HFpEF/HFrEF).", body_style),
    Spacer(1, 4),
    Paragraph("<b>Target Cocktail:</b> Non-oncogenic pioneer transcription factors & sirtuin deacetylases: <b>SIRT1 + SIRT6 + GATA4 + ZBTB16</b>.", body_style),
    Spacer(1, 4),
    Paragraph("<b>Biophysical Mode of Action:</b> Delivers a 2.0h Decaying Resonance Pulse (DRP) that deacetylates H3K9ac/H3K56ac, restores mitochondrial bioenergetics, and demethylates hypermethylated cardiac promoter loci.", body_style),
    Spacer(1, 4),
    Paragraph("<b>Advanced Supporting Data:</b> Single-cell validation across 2.42M cardiac cells demonstrates a <b>-13.0 year biological age reversal</b> (EnsembleAge Multi-Clock, Haghani 2026 / Horvath 2013) while maintaining &gt;94% Troponin T (<i>TNNT2</i>) and Connexin-43 (<i>GJA1</i>) gap junction expression, eliminating arrhythmia risk and enforcing zero pluripotency induction (<i>OCT4</i> &le; 0.35, <i>MYC</i> &le; 0.30).", body_style)
]

col2 = [
    Paragraph("2. GENERATIVE AI PLATFORM (ZENITH v31.0 GOLD)", slide_h2_style),
    Paragraph("<b>Platform Architecture:</b> Deep generative variational autoencoder (scVI) foundation model operating across a 5,009D transcriptomic embedding space over 2.42 million human cardiac single cells (Litviňuková et al., <i>Nature</i> 2020).", body_style),
    Spacer(1, 6),
    Paragraph("• <b>ACSL4 Ferro-Aging Protection Engine:</b> Audits ACSL4/GPX4 catalytic ratios (Liu et al., <i>Cell Metabolism</i> 2026) to prevent iron-catalyzed lipid peroxidation during factor expression (&gt;90% cytoprotection).", bullet_style),
    Spacer(1, 4),
    Paragraph("• <b>NEUROS-X 512 LIF Spiking Arrhythmia Check:</b> Simulates action potential propagation across a 512-neuron cardiac substrate to verify stable conduction velocity before wet-lab testing.", bullet_style),
    Spacer(1, 4),
    Paragraph("• <b>Automated Wet-Lab Exporters:</b> Built-in exporters for 1-click 3D structural protein folding manifests (Boltz-1 / AlphaFold 3) and liquid-handling robotics CSV scripts (Opentrons OT-2) for automated execution.", bullet_style)
]

t_slide2 = Table([[col1, col2]], colWidths=[350, 350])
t_slide2.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), c_card_dark),
    ('BOX', (0,0), (-1,-1), 1, c_border),
    ('PADDING', (0,0), (-1,-1), 12),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
]))
story.append(t_slide2)

story.append(PageBreak())

# ==========================================
# SLIDE 3: QUESTIONS 3, 4 & PIPELINE MATRIX
# ==========================================
story.append(Paragraph("SLIDE 2: PRECLINICAL / CLINICAL PROOF OF CONCEPT & PIPELINE", slide_h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=c_cyan, spaceAfter=10))

col3_1 = [
    Paragraph("3. PRECLINICAL PROOF OF CONCEPT (DE-RISKING)", slide_h2_style),
    Paragraph("<b>Definitive Animal Model:</b> Mouse LAD Coronary Artery Ligation Model of Myocardial Infarction.", body_style),
    Paragraph("<b>Targeted Delivery:</b> Active-targeted mRNA-LNPs surface-conjugated with anti-VCAM-1 / anti-NCAM1 peptide ligands to cross non-fenestrated myocardial capillaries and bypass liver ApoE trapping (&gt;80% myocardial uptake).", body_style),
    Paragraph("• <b>Ejection Fraction Recovery:</b> Statistically significant LVEF recovery (+15%) measured by cardiac MRI at 28 days.", bullet_style),
    Paragraph("• <b>Fibrosis & Telemetry Safety:</b> &gt;50% reduction in scar area by Masson's trichrome staining, with 24/7 telemetric ECG confirming zero ventricular arrhythmia episodes.", bullet_style)
]

col3_2 = [
    Paragraph("4. CLINICAL PROOF OF CONCEPT", slide_h2_style),
    Paragraph("<b>Target Clinical Population:</b> Post-Myocardial Infarction Ischemic Heart Failure (NYHA Class II-IV).", body_style),
    Paragraph("<b>Therapeutic Impact:</b> Reversal of cardiomyocyte biological age, stabilization of diastolic SERCA2a calcium handling, reduction of plasma NT-proBNP stress biomarkers by &gt;30%, and functional NYHA class improvement (Class III &rarr; Class I/II).", body_style)
]

t_slide3_top = Table([[col3_1, col3_2]], colWidths=[350, 350])
t_slide3_top.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), c_card_dark),
    ('BOX', (0,0), (-1,-1), 1, c_border),
    ('PADDING', (0,0), (-1,-1), 10),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
]))
story.append(t_slide3_top)
story.append(Spacer(1, 8))

# Pipeline Matrix Table
story.append(Paragraph("THERAPEUTIC ASSET PIPELINE MATRIX", slide_h2_style))
pipe_data = [
    [Paragraph("<b>Program</b>", card_title_style), Paragraph("<b>Target Modality</b>", card_title_style), Paragraph("<b>Primary Indication</b>", card_title_style), Paragraph("<b>Development Stage</b>", card_title_style)],
    [Paragraph("<b>NL-101</b>", body_style), Paragraph("SIRT1+SIRT6+GATA4+ZBTB16 mRNA-LNP", body_style), Paragraph("Post-MI Heart Failure", body_style), Paragraph("In-Vitro Validated / In-Vivo Ready", body_style)],
    [Paragraph("<b>NL-102</b>", body_style), Paragraph("VE-Cadherin/CD31 Endothelial Rejuvenator", body_style), Paragraph("Ischemic Microvascular Angina", body_style), Paragraph("In-Silico Target Discovery", body_style)],
    [Paragraph("<b>NL-103</b>", body_style), Paragraph("Autonomic Synaptic Preservation Factors", body_style), Paragraph("Age-Related Cardiac Denervation", body_style), Paragraph("In-Silico Target Discovery", body_style)]
]
t_pipe = Table(pipe_data, colWidths=[75, 260, 180, 185])
t_pipe.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), c_header_dark),
    ('BACKGROUND', (0,1), (-1,-1), c_card_dark),
    ('GRID', (0,0), (-1,-1), 0.5, c_border),
    ('PADDING', (0,0), (-1,-1), 4.5),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(t_pipe)

story.append(PageBreak())

# ==========================================
# SLIDE 4: QUESTIONS 5, 6 & 7 — WHY NOW, DIFFERENTIATION & THE ASK
# ==========================================
story.append(Paragraph("SLIDE 3: WHY NOW, COMPETITIVE MOAT & THE $500K ASK", slide_h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=c_cyan, spaceAfter=10))

col4_1 = [
    Paragraph("5. WHY NOW & COMPETITIVE DIFFERENTIATION", slide_h2_style),
    Paragraph("• <b>Market Convergence:</b> 2026 multi-clock EnsembleAge frameworks (Haghani et al. 2026) and ACSL4 ferro-aging discovery (Liu et al. 2026) solve the key measurement and cytotoxicity bottlenecks in cardiac reprogramming.", bullet_style),
    Spacer(1, 4),
    Paragraph("• <b>Unbeatable Competitive Moat:</b> While Altos Labs ($3B) and Retro Biosciences ($180M) focus on un-targeted systemic partial reprogramming, Nilus Lab is hyper-specialized on the heart — solving the Connexin-43 gap junction arrhythmia bottleneck first.", bullet_style),
    Spacer(1, 4),
    Paragraph("• <b>Asset-Light CRO Model:</b> We operate a capital-efficient model, partnering with top cardiology CROs for in-vivo execution while exporting automated Opentrons OT-2 robotic scripts.", bullet_style)
]

col4_2 = [
    Paragraph("6. TEAM POSITIONING & 7. THE $500K PRE-SEED ASK", slide_h2_style),
    Paragraph("<b>Executing Team:</b> Led by Alaa Aldeen (HomeLab Accelerator Cohort 5), integrating high-dimensional scVI generative manifolds with cloud-automated liquid handling.", body_style),
    Spacer(1, 4),
    Paragraph("<b>Use of Proceeds ($500,000 Pre-Seed Round):</b>", card_title_style),
    Paragraph("1. Complete Opentrons OT-2 automated in-vitro cardiomyocyte age reversal assays ($60k Killer Experiment).", bullet_style),
    Paragraph("2. Execute mouse LAD ligation MI model in-vivo LVEF ejection fraction recovery POC via CRO ($150k).", bullet_style),
    Paragraph("3. Secure provisional patent portfolio over non-oncogenic factor ratios and targeted LNP formulations ($50k).", bullet_style),
    Paragraph("4. Prepare FDA Pre-IND briefing dossier and execute first biopharma co-development partnership ($40k).", bullet_style)
]

t_slide4 = Table([[col4_1, col4_2]], colWidths=[350, 350])
t_slide4.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), c_card_dark),
    ('BOX', (0,0), (-1,-1), 1, c_border),
    ('PADDING', (0,0), (-1,-1), 12),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
]))
story.append(t_slide4)

doc.build(story)
print(f"✅ Generated Ultra-High-End 16:9 Landscape Pitch Deck PDF at: {pdf_path}")
