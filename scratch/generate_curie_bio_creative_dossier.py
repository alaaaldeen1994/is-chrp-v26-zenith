import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
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

# Creative TechBio Monochromatic Palette
c_primary = colors.HexColor("#0F172A")     # Charcoal Dark Slate
c_secondary = colors.HexColor("#1E293B")   # Navy Slate
c_body = colors.HexColor("#334155")        # Slate Text
c_subtle = colors.HexColor("#64748B")      # Muted Slate
c_border = colors.HexColor("#CBD5E1")      # Border Grey
c_bg_light = colors.HexColor("#F8FAFC")    # Cool Light BG
c_card_bg = colors.HexColor("#F1F5F9")     # Highlight Card BG

# Typography Styles
logo_style = ParagraphStyle('Logo', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=c_primary)
tagline_style = ParagraphStyle('Tagline', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=c_subtle)
doc_title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=c_primary, alignment=TA_RIGHT)
doc_sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=c_subtle, alignment=TA_RIGHT)

h1_style = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=c_primary, spaceBefore=8, spaceAfter=4)
h2_style = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=c_secondary, spaceAfter=2)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12.5, textColor=c_body, spaceAfter=4)
bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=c_body, leftIndent=8, spaceAfter=2)
badge_text_style = ParagraphStyle('Badge', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=c_primary, alignment=TA_CENTER)

story = []

# --- HEADER BLOCK ---
h_left = [
    Paragraph("NILUS LAB", logo_style),
    Paragraph("SINGLE-CELL GENERATIVE BIOLOGY & CARDIAC REJUVENATION", tagline_style)
]
h_right = [
    Paragraph("EXECUTIVE DILIGENCE DOSSIER", doc_title_style),
    Paragraph("CURIE.BIO COLLABORATION | 2026", doc_sub_style)
]
t_header = Table([[h_left, h_right]], colWidths=[330, 210])
t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('PADDING', (0,0), (-1,-1), 0)]))
story.append(t_header)
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceAfter=8))

# --- METADATA & HIGHLIGHT BADGES GRID ---
meta_text = [
    Paragraph("<b>Entity:</b> Nilus Lab Ltd.", body_style),
    Paragraph("<b>Founder & CEO:</b> Alaa Aldeen", body_style),
    Paragraph("<b>Program:</b> HomeLab Cohort 5", body_style),
    Paragraph("<b>Ask:</b> $500,000 Pre-Seed", body_style)
]

b1 = [Paragraph("<b>EPIGENETIC RESET</b><br/><font size=11 color='#0F172A'><b>-13.0 Years</b></font><br/><font size=7 color='#64748B'>EnsembleAge Multi-Clock</font>", badge_text_style)]
b2 = [Paragraph("<b>SARCOMERE SAFETY</b><br/><font size=11 color='#0F172A'><b>>94% Retention</b></font><br/><font size=7 color='#64748B'>TNNT2 & Cx43 Identity</font>", badge_text_style)]
b3 = [Paragraph("<b>CYTOPROTECTION</b><br/><font size=11 color='#0F172A'><b>>90% Safe</b></font><br/><font size=7 color='#64748B'>ACSL4 Ferro-Aging Gate</font>", badge_text_style)]

t_badges = Table([[b1, b2, b3]], colWidths=[175, 175, 175])
t_badges.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
    ('BOX', (0,0), (-1,-1), 0.5, c_border),
    ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
    ('PADDING', (0,0), (-1,-1), 6),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))

story.append(t_badges)
story.append(Spacer(1, 8))

# --- QUESTION 1 & 2 ---
story.append(Paragraph("1. LEAD PROGRAM & MOLECULAR MECHANISM", h1_style))
story.append(Paragraph("<b>Lead Therapeutic Candidate:</b> NL-101 (Transient mRNA-LNP Rejuvenation Cocktail)", h2_style))
story.append(Paragraph("Adult human ventricular cardiomyocytes exhibit near-zero natural regeneration (&lt;0.5%/yr). Following myocardial infarction (MI), wall stress and epigenetic drift cause progressive heart failure. NL-101 is a non-oncogenic transient mRNA-LNP cocktail containing pioneer transcription factors and sirtuin deacetylases: <b>SIRT1 + SIRT6 + GATA4 + ZBTB16</b>.", body_style))
story.append(Paragraph("<b>Biophysical Mode of Action:</b> Delivers a 2.0h Decaying Resonance Pulse (DRP) that deacetylates H3K9ac/H3K56ac, restores mitochondrial bioenergetics, and demethylates hypermethylated cardiac loci. Multi-scale validation across 2.42M cardiac single cells demonstrates a <b>-13.0 year biological age reversal</b> (EnsembleAge Multi-Clock, Haghani 2026 / Horvath 2013) while maintaining &gt;94% Troponin T (<i>TNNT2</i>) and Connexin-43 (<i>GJA1</i>) gap junction expression — eliminating arrhythmia risk and enforcing zero pluripotency induction (<i>OCT4</i> &le; 0.35, <i>MYC</i> &le; 0.30).", body_style))
story.append(Spacer(1, 4))

story.append(Paragraph("2. GENERATIVE AI DISCOVERY APPROACH (ZENITH v31.0 GOLD)", h1_style))
story.append(Paragraph("Zenith is a deep generative variational autoencoder (scVI) foundation model trained across a 5,009D transcriptomic embedding space over 2.42 million human cardiac single cells (Litviňuková et al., <i>Nature</i> 2020).", body_style))
story.append(Paragraph("• <b>ACSL4 Ferro-Aging Protection Engine:</b> Audits ACSL4/GPX4 catalytic ratios (Liu et al., <i>Cell Metabolism</i> 2026) to prevent iron-catalyzed lipid peroxidation during factor expression (&gt;90% cytoprotection).", bullet_style))
story.append(Paragraph("• <b>Automated Wet-Lab Bridge:</b> Exports 1-click 3D structural protein folding manifests (Boltz-1 / AlphaFold 3) and liquid-handling robotics CSV scripts (Opentrons OT-2) for rapid execution.", bullet_style))
story.append(Spacer(1, 4))

# --- QUESTION 3 & 4 ---
story.append(Paragraph("3. PRECLINICAL & CLINICAL PROOF OF CONCEPT", h1_style))
story.append(Paragraph("<b>Definitive Animal Model:</b> Mouse LAD Coronary Artery Ligation Model of Myocardial Infarction.", h2_style))
story.append(Paragraph("<b>Targeted LNP Delivery:</b> Active-targeted mRNA-LNPs surface-conjugated with anti-VCAM-1 / anti-NCAM1 peptide ligands to cross non-fenestrated myocardial capillaries and bypass liver ApoE trapping (&gt;80% myocardial uptake).", body_style))
story.append(Paragraph("• <b>Ejection Fraction Recovery:</b> Statistically significant LVEF recovery (+15%) measured by cardiac MRI at 28 days.", bullet_style))
story.append(Paragraph("• <b>Histology & Telemetry Safety:</b> &gt;50% reduction in ventricular scar area by Masson's trichrome staining, with 24/7 telemetric ECG confirming zero ventricular arrhythmia episodes.", bullet_style))
story.append(Paragraph("<b>Target Clinical Population:</b> Post-Myocardial Infarction Ischemic Heart Failure (NYHA Class II-IV). Demonstrating &gt;30% plasma NT-proBNP stress reduction and functional NYHA class improvement (Class III &rarr; Class I/II).", body_style))
story.append(Spacer(1, 4))

# --- PIPELINE MATRIX TABLE ---
story.append(Paragraph("4. THERAPEUTIC PIPELINE MATRIX", h1_style))
pipe_data = [
    [Paragraph("<b>Program</b>", ParagraphStyle('PH', parent=body_style, fontName='Helvetica-Bold')), 
     Paragraph("<b>Target Modality</b>", ParagraphStyle('PH', parent=body_style, fontName='Helvetica-Bold')), 
     Paragraph("<b>Indication</b>", ParagraphStyle('PH', parent=body_style, fontName='Helvetica-Bold')), 
     Paragraph("<b>Stage</b>", ParagraphStyle('PH', parent=body_style, fontName='Helvetica-Bold'))],
    [Paragraph("<b>NL-101</b>", body_style), Paragraph("SIRT1+SIRT6+GATA4+ZBTB16 mRNA-LNP", body_style), Paragraph("Post-MI Heart Failure", body_style), Paragraph("In-Vitro Validated / In-Vivo Ready", body_style)],
    [Paragraph("<b>NL-102</b>", body_style), Paragraph("VE-Cadherin/CD31 Endothelial Rejuvenator", body_style), Paragraph("Ischemic Microvascular Angina", body_style), Paragraph("In-Silico Target Discovery", body_style)],
    [Paragraph("<b>NL-103</b>", body_style), Paragraph("Autonomic Synaptic Preservation Factors", body_style), Paragraph("Age-Related Cardiac Denervation", body_style), Paragraph("In-Silico Target Discovery", body_style)]
]
t_pipe = Table(pipe_data, colWidths=[65, 200, 140, 135])
t_pipe.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), c_bg_light),
    ('GRID', (0,0), (-1,-1), 0.5, c_border),
    ('PADDING', (0,0), (-1,-1), 4),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(t_pipe)
story.append(Spacer(1, 6))

# --- QUESTION 5, 6 & 7 ---
story.append(Paragraph("5. WHY NOW, DIFFERENTIATION & TEAM", h1_style))
story.append(Paragraph("• <b>Market Convergence:</b> 2026 multi-clock EnsembleAge frameworks (Haghani et al. 2026) and ACSL4 ferro-aging discovery (Liu et al. 2026) solve the key measurement and cytotoxicity bottlenecks in cardiac reprogramming.", bullet_style))
story.append(Paragraph("• <b>Competitive Differentiation:</b> While Altos Labs and Retro Biosciences focus on un-targeted systemic partial reprogramming, Nilus Lab is hyper-specialized on the heart — solving the Connexin-43 gap junction arrhythmia bottleneck first.", bullet_style))
story.append(Paragraph("• <b>Team & Network:</b> Led by Alaa Aldeen (HomeLab Cohort 5), integrating deep scVI generative AI with cloud-automated liquid handling. Supported by an institutional advisory network across cardiac electrophysiology and healthspan strategy.", bullet_style))

doc.build(story)
print(f"✅ Generated Creative Executive Curie.Bio PDF Dossier at: {pdf_path}")
