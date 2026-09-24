import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

pdf_path = r"C:\Users\alaaa\Downloads\Nilus_Lab_CurieBio_Executive_Dossier_2026.pdf"

doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    rightMargin=36,
    leftMargin=36,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()

# Ultra-Institutional Monochromatic Palette (Slate & Charcoal)
c_primary = colors.HexColor("#0F172A")    # Dark Slate / Charcoal
c_secondary = colors.HexColor("#334155")  # Deep Slate Text
c_subtle = colors.HexColor("#64748B")     # Muted Slate
c_border = colors.HexColor("#CBD5E1")     # Cool Grey Border
c_bg = colors.HexColor("#F8FAFC")         # Crisp Light Slate BG

# Professional Typography Styles
company_logo_style = ParagraphStyle(
    'CompanyLogo',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=20,
    leading=24,
    textColor=c_primary,
    alignment=TA_LEFT,
    spaceAfter=2
)

tagline_style = ParagraphStyle(
    'CompanyTagline',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9,
    leading=12,
    textColor=c_subtle,
    alignment=TA_LEFT,
    spaceAfter=8
)

doc_title_style = ParagraphStyle(
    'DocTitleInstitutional',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=13,
    leading=16,
    textColor=c_primary,
    alignment=TA_RIGHT
)

q_header_style = ParagraphStyle(
    'QHeaderInstitutional',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=11,
    leading=14,
    textColor=c_primary,
    spaceBefore=8,
    spaceAfter=4
)

q_title_style = ParagraphStyle(
    'QTitleInstitutional',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=9.5,
    leading=13,
    textColor=c_secondary,
    spaceAfter=3
)

body_text_style = ParagraphStyle(
    'BodyInstitutional',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9,
    leading=13,
    textColor=c_secondary,
    alignment=TA_LEFT,
    spaceAfter=5
)

bullet_text_style = ParagraphStyle(
    'BulletInstitutional',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8.5,
    leading=12,
    textColor=c_secondary,
    leftIndent=10,
    spaceAfter=3
)

story = []

# Header Table (Logo / Title Block)
header_left = [
    Paragraph("NILUS LAB", company_logo_style),
    Paragraph("GENERATIVE BIOLOGY & SINGLE-CELL CARDIAC REJUVENATION", tagline_style)
]
header_right = [
    Paragraph("INVESTOR DILIGENCE DOSSIER", doc_title_style),
    Paragraph("<font color='#64748B'>CURIE.BIO SUBMISSION | 2026</font>", ParagraphStyle('RSub', parent=doc_title_style, fontName='Helvetica', fontSize=8, leading=11))
]

t_header = Table([[header_left, header_right]], colWidths=[340, 200])
t_header.setStyle(TableStyle([
    ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
    ('PADDING', (0,0), (-1,-1), 0),
]))
story.append(t_header)
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceAfter=10))

# Executive Metadata Table
meta_data = [
    [Paragraph("<b>Company Legal Entity:</b> Nilus Lab Ltd.", body_text_style), Paragraph("<b>Founder & CEO:</b> Alaa Aldeen", body_text_style)],
    [Paragraph("<b>Primary Location:</b> London, UK / Dubai, UAE", body_text_style), Paragraph("<b>Accelerator Program:</b> HomeLab Cohort 5", body_text_style)],
    [Paragraph("<b>Institutional Domain:</b> niluslab.com", body_text_style), Paragraph("<b>Current Financing Ask:</b> $500,000 Pre-Seed", body_text_style)]
]
t_meta = Table(meta_data, colWidths=[270, 270])
t_meta.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), c_bg),
    ('PADDING', (0,0), (-1,-1), 5),
    ('BOX', (0,0), (-1,-1), 0.5, c_border),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(t_meta)
story.append(Spacer(1, 8))

# 1. Lead Program
story.append(Paragraph("1. LEAD PROGRAM & THERAPEUTIC MECHANISM", q_header_style))
story.append(Paragraph("<b>Asset Identifier:</b> NL-101 (Transient mRNA-LNP Rejuvenation Cocktail)", q_title_style))
story.append(Paragraph("<b>Mechanism & Clinical Rationale:</b> Adult human ventricular cardiomyocytes exhibit near-zero post-natal regenerative capacity (&lt;0.5%/yr). Post-myocardial infarction (MI), scarring causes progressive heart failure (HFpEF/HFrEF). NL-101 is a non-oncogenic transient mRNA-LNP cocktail containing pioneer transcription factors and sirtuin deacetylases (SIRT1 + SIRT6 + GATA4 + ZBTB16). It induces a Decaying Resonance Pulse (DRP) that deacetylates H3K9ac/H3K56ac, restores mitochondrial bioenergetics, and demethylates hypermethylated cardiac promoter loci.", body_text_style))
story.append(Paragraph("<b>Advanced Proof Data:</b> Evaluated across 2.42M human single cells via Zenith v31.0 GOLD. NL-101 achieves a -13.0 year biological age reversal (EnsembleAge Multi-Clock, Haghani et al., GeroScience 2026 / Horvath 2013) while maintaining &gt;94% Troponin T (TNNT2) and Connexin-43 (GJA1) gap junction expression, eliminating arrhythmia risk and enforcing zero pluripotency induction (OCT4 &le; 0.35, MYC &le; 0.30).", body_text_style))
story.append(Spacer(1, 4))

# 2. Discovery Approach
story.append(Paragraph("2. DISCOVERY APPROACH & PLATFORM ARCHITECTURE", q_header_style))
story.append(Paragraph("<b>Platform:</b> Zenith v31.0 GOLD Generative Single-Cell AI Engine", q_title_style))
story.append(Paragraph("Zenith is a deep generative variational autoencoder (scVI) foundation model operating across a 5,009D transcriptomic embedding space over 2.42 million human cardiac single cells (Litviňuková et al., Nature 2020).", body_text_style))
story.append(Paragraph("• <b>ACSL4 Ferro-Aging Protection Engine:</b> Audits ACSL4/GPX4 catalytic ratios (Liu et al., Cell Metabolism 2026) to prevent iron-catalyzed lipid peroxidation during factor expression (&gt;90% cytoprotection).", bullet_text_style))
story.append(Paragraph("• <b>Automated Wet-Lab Exporters:</b> Direct integration exporting 1-click 3D structural protein folding manifests (Boltz-1 / AlphaFold 3) and liquid-handling robotics CSV scripts (Opentrons OT-2) for rapid execution.", bullet_text_style))
story.append(Spacer(1, 4))

# 3. Preclinical Proof of Concept
story.append(Paragraph("3. PRECLINICAL PROOF OF CONCEPT & DELIVERY", q_header_style))
story.append(Paragraph("<b>Primary Animal Model:</b> Mouse LAD Coronary Artery Ligation Model of Myocardial Infarction.", q_title_style))
story.append(Paragraph("<b>Delivery Architecture:</b> Active-targeted mRNA-LNPs surface-conjugated with anti-VCAM-1 / anti-NCAM1 peptide ligands to cross non-fenestrated myocardial capillaries and bypass liver ApoE trapping (&gt;80% myocardial uptake).", body_text_style))
story.append(Paragraph("• <b>Ejection Fraction Recovery:</b> Statistically significant LVEF recovery (+15%) measured by cardiac MRI at 28 days.", bullet_text_style))
story.append(Paragraph("• <b>Histology & Electrophysiology Safety:</b> &gt;50% reduction in ventricular scar area by Masson's trichrome staining, with 24/7 telemetric ECG confirming zero ventricular arrhythmia episodes.", bullet_text_style))
story.append(Spacer(1, 4))

# 4. Clinical Proof of Concept
story.append(Paragraph("4. CLINICAL PROOF OF CONCEPT & TARGET POPULATION", q_header_style))
story.append(Paragraph("<b>Target Population:</b> Patients with Post-Myocardial Infarction Ischemic Heart Failure (NYHA Class II-IV).", q_title_style))
story.append(Paragraph("<b>Therapeutic Impact:</b> Reversal of cardiomyocyte biological age, stabilization of diastolic SERCA2a calcium handling, reduction of plasma NT-proBNP stress biomarkers by &gt;30%, and NYHA functional class improvement (Class III &rarr; Class I/II).", body_text_style))
story.append(Spacer(1, 4))

# 5. Why Now & Differentiation
story.append(Paragraph("5. WHY NOW & COMPETITIVE DIFFERENTIATION", q_header_style))
story.append(Paragraph("• <b>Convergence of Epigenetic Clocks:</b> 2026 multi-clock EnsembleAge frameworks (Haghani et al. 2026) enable exact probe-level biological age shift quantification.", bullet_text_style))
story.append(Paragraph("• <b>Ferro-Aging Cytoprotection:</b> Molecular elucidation of ACSL4 catalytic inhibition (Liu et al. 2026) eliminates the primary cytotoxicity barrier in cardiac reprogramming.", bullet_text_style))
story.append(Paragraph("• <b>Differentiation:</b> While Altos Labs and Retro Biosciences focus on un-targeted systemic partial reprogramming, Nilus Lab is hyper-specialized on the heart — solving the Connexin-43 gap junction arrhythmia bottleneck first.", bullet_text_style))
story.append(Spacer(1, 4))

# 6 & 7. Team & Pipeline
story.append(Paragraph("6. TEAM POSITIONING & 7. PIPELINE HORIZONS", q_header_style))
story.append(Paragraph("<b>Team Capability:</b> Led by Alaa Aldeen (HomeLab Cohort 5), bridging high-dimensional manifold generative modeling with cloud-automated liquid handling. Supported by an institutional advisory network across cardiac electrophysiology and healthspan strategy.", body_text_style))
story.append(Paragraph("<b>Follow-On Pipeline:</b> <i>NL-102</i> (Ischemic Endothelial Rejuvenation) and <i>NL-103</i> (Neuro-Cardiac Syncytial Preservation).", body_text_style))

doc.build(story)
print(f"✅ Generated Ultra-Institutional Curie.Bio PDF Dossier at: {pdf_path}")
