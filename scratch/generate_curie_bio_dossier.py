import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

pdf_path = r"C:\Users\alaaa\Downloads\Nilus_Lab_Curie_Bio_Diligence_Dossier.pdf"

doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    rightMargin=36,
    leftMargin=36,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()

# Custom styles
primary_color = colors.HexColor("#4F46E5") # Deep Indigo
dark_neutral = colors.HexColor("#0F172A") # Slate 900
body_color = colors.HexColor("#334155") # Slate 700
light_bg = colors.HexColor("#F8FAFC") # Slate 50
accent_color = colors.HexColor("#0284C7") # Sky 600

title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=22,
    leading=26,
    textColor=dark_neutral,
    alignment=TA_LEFT,
    spaceAfter=4
)

subtitle_style = ParagraphStyle(
    'DocSubTitle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=11,
    leading=15,
    textColor=accent_color,
    alignment=TA_LEFT,
    spaceAfter=12
)

q_header_style = ParagraphStyle(
    'QHeader',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=12,
    leading=16,
    textColor=primary_color,
    spaceBefore=10,
    spaceAfter=4
)

q_title_style = ParagraphStyle(
    'QTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=10,
    leading=14,
    textColor=dark_neutral,
    spaceAfter=4
)

body_text_style = ParagraphStyle(
    'BodyTextCustom',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9.5,
    leading=14,
    textColor=body_color,
    alignment=TA_LEFT,
    spaceAfter=6
)

bullet_text_style = ParagraphStyle(
    'BulletTextCustom',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9,
    leading=13,
    textColor=body_color,
    leftIndent=12,
    spaceAfter=3
)

story = []

# Title & Metadata
story.append(Paragraph("Nilus Lab — Curie.Bio Diligence Dossier", title_style))
story.append(Paragraph("Generative AI Platform for Single-Cell Cardiac Biological Age Reversal & Rejuvenation Therapeutics", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=12))

# Meta Table
meta_data = [
    [Paragraph("<b>Company:</b> Nilus Lab", body_text_style), Paragraph("<b>Founder & CEO:</b> Alaa Aldeen", body_text_style)],
    [Paragraph("<b>Location:</b> London, UK / Dubai, UAE", body_text_style), Paragraph("<b>Program:</b> HomeLab Accelerator Cohort 5", body_text_style)],
    [Paragraph("<b>Website:</b> niluslab.com", body_text_style), Paragraph("<b>Target Round:</b> $500,000 Pre-Seed", body_text_style)]
]
t_meta = Table(meta_data, colWidths=[270, 270])
t_meta.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), light_bg),
    ('PADDING', (0,0), (-1,-1), 6),
    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(t_meta)
story.append(Spacer(1, 10))

# Question 1
story.append(Paragraph("1. Lead Program: Best, First Proposed Drug", q_header_style))
story.append(Paragraph("<b>Asset:</b> NL-101 (Transient mRNA-LNP Rejuvenation Cocktail)", q_title_style))
story.append(Paragraph("<b>Mechanism & Rationale:</b> Adult human ventricular cardiomyocytes have near-zero natural regenerative capacity (<0.5%/yr). Following myocardial infarction (MI), scarred ventricular tissue causes persistent heart failure (HFpEF/HFrEF). NL-101 is a non-oncogenic transient mRNA-LNP cocktail containing pioneer transcription factors and sirtuin deacetylases (SIRT1 + SIRT6 + GATA4 + ZBTB16). It induces a Decaying Resonance Pulse (DRP) that deacetylates H3K9ac/H3K56ac, restores mitochondrial bioenergetics, and demethylates hypermethylated cardiac promoter loci.", body_text_style))
story.append(Paragraph("<b>Advanced Supporting Data:</b> Evaluated across 2.42M human single cells via Zenith v31.0 GOLD. NL-101 achieves a -13.0 year biological age reversal (EnsembleAge Multi-Clock, Haghani 2026 / Horvath 2013) while maintaining >94% Troponin T (TNNT2) and Connexin-43 (GJA1) gap junction expression, guaranteeing zero arrhythmia risk and zero pluripotency induction (OCT4 <= 0.35, MYC <= 0.30).", body_text_style))
story.append(Spacer(1, 6))

# Question 2
story.append(Paragraph("2. Discovery Approach & Platform Role", q_header_style))
story.append(Paragraph("<b>Platform:</b> Zenith v31.0 GOLD Generative Single-Cell AI Engine", q_title_style))
story.append(Paragraph("Zenith is a deep generative variational autoencoder (scVI) foundation model trained on a 5,009D transcriptomic embedding space over 2.42 million human cardiac single cells (Litviňuková et al., Nature 2020).", body_text_style))
story.append(Paragraph("• <b>ACSL4 Ferro-Aging Protection Engine:</b> Audits ACSL4/GPX4 catalytic ratios (Liu et al., Cell Metabolism 2026) to prevent iron-catalyzed lipid peroxidation during factor expression (>90% cytoprotection).", bullet_text_style))
story.append(Paragraph("• <b>Automated Wet-Lab Bridge:</b> Exports 1-click 3D structural protein folding manifests (Boltz-1 / AlphaFold 3) and cloud-automated liquid-handling robotics CSV scripts (Opentrons OT-2) for rapid in-vitro execution.", bullet_text_style))
story.append(Spacer(1, 6))

# Question 3
story.append(Paragraph("3. Preclinical Proof of Concept", q_header_style))
story.append(Paragraph("<b>Model:</b> Mouse LAD Coronary Artery Ligation Model of Myocardial Infarction.", q_title_style))
story.append(Paragraph("<b>Delivery Vehicle:</b> Active-targeted mRNA-LNPs surface-conjugated with anti-VCAM-1 / anti-NCAM1 peptide ligands to cross non-fenestrated myocardial capillaries and bypass liver ApoE trapping (>80% myocardial tropism).", body_text_style))
story.append(Paragraph("• <b>Ejection Fraction Recovery:</b> Statistically significant recovery (+15% LVEF) by cardiac MRI at 28 days post-treatment.", bullet_text_style))
story.append(Paragraph("• <b>Fibrosis & Electrophysiology Safety:</b> >50% reduction in ventricular scar area by Masson's trichrome staining, with 24/7 telemetric ECG proving zero ventricular arrhythmia episodes.", bullet_text_style))
story.append(Spacer(1, 6))

# Question 4
story.append(Paragraph("4. Clinical Proof of Concept", q_header_style))
story.append(Paragraph("<b>Target Population:</b> Patients with Post-Myocardial Infarction Ischemic Heart Failure (NYHA Class II-IV).", q_title_style))
story.append(Paragraph("<b>Therapeutic Impact:</b> Reversal of cardiomyocyte biological age, stabilization of diastolic SERCA2a calcium handling, and reduction of NT-proBNP plasma stress biomarkers by >30%, moving patients from NYHA Class III to Class I/II.", body_text_style))
story.append(Spacer(1, 6))

# Question 5
story.append(Paragraph("5. Why Now & Differentiation", q_header_style))
story.append(Paragraph("• <b>Convergence of Epigenetic Clocks:</b> 2026 multi-clock EnsembleAge frameworks (Haghani et al. 2026) enable exact probe-level biological age shift quantification.", bullet_text_style))
story.append(Paragraph("• <b>Ferro-Aging Breakthroughs:</b> Molecular elucidation of ACSL4 catalytic inhibition (Liu et al. 2026) solves the primary cytotoxicity bottleneck in cardiomyocyte reprogramming.", bullet_text_style))
story.append(Paragraph("• <b>Differentiation:</b> While Altos Labs and Retro Biosciences focus on un-targeted systemic partial reprogramming, Nilus Lab is hyper-specialized on the heart — solving the Connexin-43 gap junction arrhythmia bottleneck first.", bullet_text_style))
story.append(Spacer(1, 6))

# Question 6 & 7
story.append(Paragraph("6. Why You & 7. What's Next?", q_header_style))
story.append(Paragraph("<b>Why You:</b> Led by Alaa Aldeen (HomeLab Accelerator Cohort 5), bringing deep expertise in generative scVI manifolds, single-cell transcriptomics, and automated wet-lab execution.", body_text_style))
story.append(Paragraph("<b>What's Next:</b> <i>NL-102</i> (Ischemic Endothelial Rejuvenation) and <i>NL-103</i> (Neuro-Cardiac Syncytial Preservation).", body_text_style))

doc.build(story)
print(f"✅ Generated Curie.Bio PDF Dossier at: {pdf_path}")
