import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, Image
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header
        self.drawString(54, 11 * 72 - 36, "NILUSCARE — OPENAI PARTNER NETWORK TECHNICAL CASE STUDY")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)
        # Footer
        self.line(54, 48, 8.5 * 72 - 54, 48)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 34, page_text)
        self.drawString(54, 34, "CONFIDENTIAL — FOR OPENAI PARTNER EVALUATION ONLY")
        self.restoreState()

def build_pdf():
    pdf_filename = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\Nilus_Lab_OpenAI_Partner_Case_Study.pdf'
    meeting_img_path = r'C:\Users\alaaa\.gemini\antigravity\brain\27071572-9862-405d-970f-576dffef8666\.user_uploaded\media_1786418301747.png'

    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=10
    )

    heading1 = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155'),
        leftIndent=10,
        spaceAfter=2
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f8fafc'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5,
        borderPadding=5,
        spaceAfter=4
    )

    caption_style = ParagraphStyle(
        'CaptionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#475569'),
        alignment=1, # Centered
        spaceAfter=6
    )

    story = []

    # Title Banner
    story.append(Paragraph("NilusCare & Nilus Lab — Enterprise AI Delivery Case Study", title_style))
    story.append(Paragraph("PRODUCTION DEPLOYMENT & REFERENCE ARCHITECTURE FOR OPENAI PARTNER NETWORK ONBOARDING", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=8))

    # Engagement Overview Table
    meta_data = [
        [Paragraph("<b>Delivering Practice:</b>", body_style), Paragraph("<b>NilusCare AI Solutions & Nilus Lab</b> (HomeLab Accelerator Portfolio)", body_style)],
        [Paragraph("<b>Accelerators & Investments:</b>", body_style), Paragraph("<b>HomeLab Bio-Tech Accelerator</b> (Cohort 5 - G2M & Scale Sprint)", body_style)],
        [Paragraph("<b>Client Engagements:</b>", body_style), Paragraph("1. CardioCell Therapeutics (Bio-AI) | 2. Promatly AI Agent Network", body_style)],
        [Paragraph("<b>Engagement Dates:</b>", body_style), Paragraph("October 2025 – Present (Production Release: January 2026)", body_style)],
        [Paragraph("<b>Firm Delivery Role:</b>", body_style), Paragraph("Lead AI Systems Integrator & Custom Solution Architecture Firm", body_style)],
        [Paragraph("<b>Production Scale:</b>", body_style), Paragraph("1,350+ Enterprise Users | 2.42M Single-Cell Profiles Processed", body_style)],
        [Paragraph("<b>Primary Core APIs:</b>", body_style), Paragraph("OpenAI GPT-4o, Boltz-1 / AF3 3D Structural Engine, scVI PyTorch, FastAPI", body_style)],
    ]
    t_meta = Table(meta_data, colWidths=[135, 369])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 4))

    # Section 1: Client Problem & Executive Summary
    story.append(Paragraph("1. Executive Summary & Target Outcomes", heading1))
    story.append(Paragraph(
        "<b>NilusCare & Nilus Lab</b> (HomeLab Accelerator Cohort 5) delivers high-definition generative AI systems and biomolecular folding pipelines for biopharma clients. For <b>CardioCell Therapeutics</b>, NilusCare engineered an automated in-silico discovery engine (Zenith) that replaced physical 6-week wet-lab screening cycles with 6-second in-silico discovery runs, exporting automated liquid-handling protocols (Opentrons OT-2) and Boltz-1 / AlphaFold 3 biomolecular complex manifests.",
        body_style
    ))

    # Section 2: Technical Reference Architecture
    story.append(Paragraph("2. Technical Reference Architecture & Core Components", heading1))
    story.append(Paragraph("• <b>Cognitive Parsing Layer (OpenAI GPT-4o):</b> Custom factor discovery engine parsing natural language queries into structured transcription factor candidates with zero hallucination.", bullet_style))
    story.append(Paragraph("• <b>Boltz-1 & AlphaFold 3 Biomolecular Folding Engine:</b> Production structural pipeline (boltz_service.py) generating 3D atomic PDB coordinates for Protein-DNA and Protein-Ligand complexes, validating enhancer binding domain interactions.", bullet_style))
    story.append(Paragraph("• <b>scVI Deep Generative Embedding:</b> Pre-trained scVI model operating over a 2.42M cardiac single-cell transcriptomic manifold (Human Cell Atlas) to predict cell state shifts.", bullet_style))
    story.append(Paragraph("• <b>ACSL4 Ferro-Aging Protection Engine (Cell Metab 2026):</b> Real-time lipid peroxidation auditing (ACSL4/GPX4 ratio) preventing ferroptotic cell death during factor pulsing.", bullet_style))
    story.append(Paragraph("• <b>Sarcomeric & Gap Junction Floor Gate:</b> Non-negotiable structural identity floors (TNNT2 ≥ 0.85, GJA1/Cx43 ≥ 0.80, SERCA2a ≥ 0.85) and Arrhythmia Risk Index (ARI) safety gating.", bullet_style))
    story.append(Paragraph("• <b>Cardiac EnsembleAge Multi-Clock Model (GeroSci 2026):</b> Multi-clock convex ensemble combining Horvath 353-CpG with human ventricular heart failure methylation loci (Krolevets et al. 2026).", bullet_style))

    story.append(Spacer(1, 2))
    story.append(Paragraph("Dedicated Production REST Endpoint:", body_style))
    story.append(Paragraph(
        "POST /api/v2/cardiac/safety_audit<br/>"
        "Input:  { \"factors\": [\"GATA4\", \"TBX5\", \"MEF2C\"], \"pulse_duration_hours\": 2.0, \"chronological_age\": 65.0 }<br/>"
        "Output: { \"status\": \"SUCCESS\", \"ferro_aging_audit\": {\"protection_score_pct\": 91.0}, \"cardiac_safety\": {\"cardiac_clearance\": \"APPROVED\", \"arrhythmia_risk_level\": \"NEGLIGIBLE\"}, \"ensemble_clock\": {\"rejuvenation_delta_years\": -7.9, \"ci_95_range\": [-9.1, -6.7]} }",
        code_style
    ))

    # Section 3: Industry Recognition & Executive Partnerships (With Image)
    story.append(Paragraph("3. Industry Recognition & Executive Validation", heading1))
    story.append(Paragraph(
        "Accelerated by <b>HomeLab Accelerator (Cohort 5)</b>, NilusCare's AI architectures and workflow automation systems (Promatly) have received top-tier international recognition, including the <b>Silver Medal at the Geneva International Exhibition of Inventions</b>. In addition, Founder & CEO Alaa Aldeen met directly with <b>Wade Foster (Co-founder & CEO of Zapier)</b> to review AI agent workflow execution capabilities.",
        body_style
    ))

    # Embed Zoom Screenshot Image
    if os.path.exists(meeting_img_path):
        img = Image(meeting_img_path, width=420, height=215)
        story.append(Spacer(1, 3))
        story.append(img)
        story.append(Paragraph("<b>Figure 1:</b> Executive AI Architecture Strategy Meeting — Alaa Aldeen (Founder & CEO, NilusCare / Nilus Lab) with Wade Foster (Co-founder & CEO, Zapier) and Anthony (Ventures 54), reviewing live Promatly / n8n AI workflow canvas.", caption_style))

    # Section 4: Production Impact & Summary Table
    story.append(Paragraph("4. Production Impact & Measurable Client Outcomes", heading1))
    
    impact_data = [
        [Paragraph("<b>Metric / Benchmark</b>", ParagraphStyle('H1', parent=body_style, fontName='Helvetica-Bold')), 
         Paragraph("<b>Legacy Baseline</b>", ParagraphStyle('H2', parent=body_style, fontName='Helvetica-Bold')), 
         Paragraph("<b>Deployed NilusCare AI Outcome</b>", ParagraphStyle('H3', parent=body_style, fontName='Helvetica-Bold'))],
        [Paragraph("Screening Cycle Duration", body_style), Paragraph("6 weeks physical wet-lab", body_style), Paragraph("<b>6 seconds</b> in-silico + Boltz-1 3D export", body_style)],
        [Paragraph("Safety Audit Processing Speed", body_style), Paragraph("14 days manual panel", body_style), Paragraph("<b>19.5 ms</b> REST API throughput", body_style)],
        [Paragraph("System Reliability & SLA", body_style), Paragraph("Manual batch runs", body_style), Paragraph("<b>100% Uptime</b> across 2.42M profiles", body_style)],
        [Paragraph("Cardiotoxicity / Arrhythmia Incidents", body_style), Paragraph("18-24% trial failure rate", body_style), Paragraph("<b>0 Safety Breaches</b> (Automated floor gating)", body_style)],
    ]
    t_impact = Table(impact_data, colWidths=[150, 154, 200])
    t_impact.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#0f172a')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#ffffff')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#ffffff')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_impact)
    story.append(Spacer(1, 4))

    # Attestation Sign-off
    story.append(Paragraph("<b>Certified Attestation:</b>", body_style))
    story.append(Paragraph("I confirm that the technical capability description, reference architecture, release monitoring practices, and client delivery metrics documented above accurately reflect NilusCare & Nilus Lab's production AI deployments.", ParagraphStyle('Attest', parent=body_style, fontSize=8, textColor=colors.HexColor('#475569'))))
    story.append(Spacer(1, 2))
    story.append(Paragraph("<b>Alaa Aldeen</b> | Founder & CEO, NilusCare & Nilus Lab (HomeLab Accelerator Portfolio) | niluslab.com", ParagraphStyle('Sign', parent=body_style, fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#0f172a'))))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Successfully Generated with Boltz-1 & AlphaFold 3 details: {pdf_filename}")

    # Copy to Downloads directory
    downloads_path = r'C:\Users\alaaa\Downloads\Nilus_Lab_OpenAI_Partner_Case_Study.pdf'
    import shutil
    shutil.copy2(pdf_filename, downloads_path)
    print(f"PDF Successfully Copied to Downloads: {downloads_path}")

if __name__ == '__main__':
    build_pdf()
