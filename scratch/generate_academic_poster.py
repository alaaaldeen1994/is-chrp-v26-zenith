import os
import shutil
from fpdf import FPDF

class WorkflowChartPosterPDF(FPDF):
    def __init__(self):
        # A3 Landscape format: 420mm wide, 297mm high
        super().__init__(orientation='L', unit='mm', format='A3')
        self.set_margin(15)
        
        # Load Outfit custom fonts
        font_dir = os.path.dirname(os.path.dirname(__file__))
        reg_font = os.path.join(font_dir, "Outfit-Regular.ttf")
        bold_font = os.path.join(font_dir, "Outfit-Bold.ttf")
        
        if os.path.exists(reg_font) and os.path.exists(bold_font):
            self.add_font('Outfit', '', reg_font)
            self.add_font('Outfit', 'B', bold_font)
            self.has_custom_font = True
        else:
            self.has_custom_font = False

    def get_font_name(self):
        return 'Outfit' if self.has_custom_font else 'Helvetica'

    def draw_bg(self):
        # Slate 50 background for clean scientific look
        self.set_fill_color(248, 250, 252)
        self.rect(0, 0, 420, 297, 'F')

    def draw_header(self):
        # Top banner (Slate 950)
        self.set_fill_color(11, 15, 25)
        self.rect(0, 0, 420, 48, 'F')
        
        # Bottom highlight strip of header (Indigo 600)
        self.set_fill_color(79, 70, 229)
        self.rect(0, 46, 420, 2.5, 'F')

        # Brand Text
        self.set_xy(15, 10)
        self.set_font(self.get_font_name(), 'B', 14)
        self.set_text_color(99, 102, 241) # Light Indigo
        self.cell(200, 5, 'NILUS LAB  |  SCIENTIFIC DISCOVERY PLATFORM')

        # Main Title (Massive line font)
        self.set_xy(15, 17)
        self.set_font(self.get_font_name(), 'B', 24)
        self.set_text_color(255, 255, 255)
        self.cell(300, 10, 'Zenith v29.0 discovery-to-validation pipeline')

        # Sub-title
        self.set_xy(15, 34)
        self.set_font(self.get_font_name(), '', 10)
        self.set_text_color(148, 163, 184) # Slate 400
        self.cell(300, 5, 'IN-SILICO TRANSCRIPTION MODELING TO PHYSICAL WETLAB TRANSLATION WORKFLOW')

        # Version Badge
        self.set_fill_color(30, 41, 59)
        self.rect(355, 15, 50, 9, 'F', round_corners=True, corner_radius=4.5)
        self.set_xy(355, 15)
        self.set_font(self.get_font_name(), 'B', 10)
        self.set_text_color(52, 211, 153) # Emerald 400
        self.cell(50, 9, 'Zenith v29.0 GOLD', 0, 0, 'C')

    def draw_card(self, x, y, w, h, bg_color=(255, 255, 255), border_color=(15, 23, 42), r=3, border_w=0.8):
        self.set_fill_color(*bg_color)
        if border_color:
            self.set_draw_color(*border_color)
            self.set_line_width(border_w)
            style = 'DF'
        else:
            style = 'F'
        self.rect(x, y, w, h, style, round_corners=True, corner_radius=r)

    def draw_diamond(self, cx, cy, w, h, bg_color=(255, 255, 255), border_color=(15, 23, 42), border_w=0.8):
        points = [
            (cx, cy - h/2),     # Top
            (cx + w/2, cy),     # Right
            (cx, cy + h/2),     # Bottom
            (cx - w/2, cy)      # Left
        ]
        self.set_fill_color(*bg_color)
        self.set_draw_color(*border_color)
        self.set_line_width(border_w)
        self.polygon(points, fill=True, style='DF')

    def draw_pill(self, x, y, w, h, bg_color=(255, 255, 255), border_color=(15, 23, 42), border_w=0.8):
        self.draw_card(x, y, w, h, bg_color=bg_color, border_color=border_color, r=h/2, border_w=border_w)

    def draw_arrow(self, x1, y1, x2, y2, color=(15, 23, 42), border_w=1.8, direction='R'):
        # Draw the bold line
        self.set_draw_color(*color)
        self.set_line_width(border_w)
        self.line(x1, y1, x2, y2)
        
        # Draw the arrowhead triangle
        self.set_fill_color(*color)
        if direction == 'R':
            points = [(x2, y2), (x2 - 3.5, y2 - 2), (x2 - 3.5, y2 + 2)]
        elif direction == 'U':
            points = [(x2, y2), (x2 - 2, y2 + 3.5), (x2 + 2, y2 + 3.5)]
        elif direction == 'D':
            points = [(x2, y2), (x2 - 2, y2 - 3.5), (x2 + 2, y2 - 3.5)]
        elif direction == 'L':
            points = [(x2, y2), (x2 + 3.5, y2 - 2), (x2 + 3.5, y2 + 2)]
        self.polygon(points, fill=True)

def generate_poster():
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    pdf_path = os.path.join(reports_dir, "Nilus_Lab_Scientific_Poster.pdf")
    
    pdf = WorkflowChartPosterPDF()
    pdf.add_page()
    pdf.draw_bg()
    pdf.draw_header()
    
    # ============================================================
    # SECTION 1: VISUAL FLOWCHART WORKFLOW (y = 52 to y = 168)
    # ============================================================
    
    # Title for Flowchart Section
    pdf.set_xy(15, 52)
    pdf.set_font(pdf.get_font_name(), 'B', 12)
    pdf.set_text_color(15, 23, 42) # Pure dark slate
    pdf.cell(390, 6, 'VISUAL PIPELINE FLOWCHART', 0, 0, 'L')
    
    # Coordinates Math
    # Step 1: Start Pill at 15. Width 58. Right = 73.
    # Arrow 1: 73 to 81 (gap 8)
    # Step 2: Card at 81. Width 58. Right = 139.
    # Arrow 2: 139 to 148 (gap 9)
    # Step 3: Diamond centered at cx = 167, cy = 118. Width 38, Height 38.
    #   Left tip = 148. Right tip = 186. Top tip = 167, 99. Bottom tip = 167, 137.
    # Arrow 5 (NO Branch): 186 to 198 (gap 12)
    # Step 4: Card at 198. Width 50. Right = 248.
    # Arrow 6: 248 to 258 (gap 10)
    # Step 5: Card at 258. Width 54. Right = 312.
    # Arrow 7: 312 to 322 (gap 10)
    # Step 6: Pill at 322. Width 82. Right = 404.
    card_y = 106
    card_h = 24
    
    # ── Step 1: Start Pill (HCA DATA SOURCE) ──
    s1_x, s1_w = 15, 58
    pdf.draw_pill(s1_x, card_y, s1_w, card_h, bg_color=(239, 246, 255), border_color=(37, 99, 235), border_w=0.8) # Blue
    pdf.set_xy(s1_x, card_y + 4.5)
    pdf.set_font(pdf.get_font_name(), 'B', 12) 
    pdf.set_text_color(0, 0, 0) # Pure Black text
    pdf.cell(s1_w, 6, '01. HCA DATA SOURCE', 0, 1, 'C')
    pdf.set_x(s1_x)
    pdf.set_font(pdf.get_font_name(), 'B', 11.5) 
    pdf.set_text_color(0, 0, 0) # Pure Black text
    pdf.cell(s1_w, 5, '500,000 Cells', 0, 0, 'C')
    
    # Arrow 1: s1 -> s2 (Bold, Dark)
    pdf.draw_arrow(s1_x + s1_w, 118, 81, 118, color=(15, 23, 42), border_w=1.8, direction='R')
    
    # ── Step 2: VAE Core Box (scVI AUTOENCODER) ──
    s2_x, s2_w = 81, 58
    pdf.draw_card(s2_x, card_y, s2_w, card_h, bg_color=(255, 255, 255), border_color=(79, 70, 229), r=3, border_w=0.8) # Indigo
    pdf.set_xy(s2_x, card_y + 4.5)
    pdf.set_font(pdf.get_font_name(), 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(s2_w, 6, '02. VAE COMPRESSION', 0, 1, 'C')
    pdf.set_x(s2_x)
    pdf.set_font(pdf.get_font_name(), 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(s2_w, 5, '20-Dimensional Latent', 0, 0, 'C')
    
    # Arrow 2: s2 -> s3 (Bold, Dark)
    pdf.draw_arrow(s2_x + s2_w, 118, 148, 118, color=(15, 23, 42), border_w=1.8, direction='R')
    
    # ── Step 3: Decision Diamond (SAFETY GATING) ──
    # Diamond centered at cx = 167, cy = 118. Width = 38, Height = 38.
    pdf.draw_diamond(167, 118, 38, 38, bg_color=(254, 243, 199), border_color=(217, 119, 6), border_w=0.8) # Amber
    pdf.set_xy(148, 110)
    pdf.set_font(pdf.get_font_name(), 'B', 10) 
    pdf.set_text_color(0, 0, 0) # Pure Black
    pdf.cell(38, 5, '03. SAFETY GATE', 0, 1, 'C')
    pdf.set_x(148)
    pdf.set_font(pdf.get_font_name(), 'B', 9) 
    pdf.set_text_color(180, 83, 9)
    pdf.cell(38, 4.5, 'MYC/OCT4 detected?', 0, 0, 'C') # Explicitly mention MYC/OCT4
    
    # Branch Labels
    # YES branch (Up) - Bold Red
    pdf.set_xy(169, 90)
    pdf.set_font(pdf.get_font_name(), 'B', 12)
    pdf.set_text_color(220, 38, 38)
    pdf.cell(10, 5, 'YES')
    
    # NO branch (Right) - Bold Green (Shifted up to y=109 with (MYC-Free) subtitle, using the 12mm gap)
    pdf.set_xy(186, 109)
    pdf.set_font(pdf.get_font_name(), 'B', 10.5)
    pdf.set_text_color(5, 150, 105)
    pdf.cell(12, 4.5, 'NO', 0, 1, 'C')
    pdf.set_x(186)
    pdf.set_font(pdf.get_font_name(), 'B', 8.5)
    pdf.cell(12, 4, '(MYC-Free)', 0, 0, 'C')
    
    # Arrow 3 (YES Branch): Up from Diamond top (167, 99) to Discard card bottom (167, 78)
    pdf.draw_arrow(167, 99, 167, 78, color=(220, 38, 38), border_w=1.8, direction='U')
    
    # ── Step 3a: Discard Card (Redesign feedback) ──
    s3a_x, s3a_y, s3a_w, s3a_h = 143, 60, 48, 18
    pdf.draw_card(s3a_x, s3a_y, s3a_w, s3a_h, bg_color=(254, 226, 226), border_color=(220, 38, 38), r=2, border_w=0.8) # Red
    pdf.set_xy(s3a_x, s3a_y + 3.5)
    pdf.set_font(pdf.get_font_name(), 'B', 11)
    pdf.set_text_color(153, 27, 27)
    pdf.cell(s3a_w, 5, 'DISCARD PROTOCOL', 0, 1, 'C')
    pdf.set_x(s3a_x)
    pdf.set_font(pdf.get_font_name(), 'B', 9.5)
    pdf.set_text_color(185, 28, 28)
    pdf.cell(s3a_w, 4, 'Trigger Factor Redesign', 0, 0, 'C')
    
    # Arrow 4 (Feedback loopback): from Left of Discard card (143, 69) to left to x=110, then down to top of VAE Core box (110, 106)
    pdf.set_draw_color(220, 38, 38)
    pdf.set_line_width(1.2)
    pdf.line(143, 69, 110, 69)
    pdf.draw_arrow(110, 69, 110, 106, color=(220, 38, 38), border_w=1.2, direction='D')
    
    # Arrow 5 (NO Branch): Right from Diamond right tip (186, 118) to AF3 box left (198, 118)
    pdf.draw_arrow(186, 118, 198, 118, color=(15, 23, 42), border_w=1.8, direction='R')
    
    # ── Step 4: AF3 Box (AlphaFold 3 Audit) ──
    s4_x, s4_w = 198, 50
    pdf.draw_card(s4_x, card_y, s4_w, card_h, bg_color=(255, 255, 255), border_color=(13, 148, 136), r=3, border_w=0.8) # Teal
    pdf.set_xy(s4_x, card_y + 4.5)
    pdf.set_font(pdf.get_font_name(), 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(s4_w, 6, '04. MOLECULAR AUDIT', 0, 1, 'C')
    pdf.set_x(s4_x)
    pdf.set_font(pdf.get_font_name(), 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(s4_w, 5, 'AlphaFold 3 DNA Valency', 0, 0, 'C')
    
    # Arrow 6: s4 -> s5 (Bold, Dark)
    pdf.draw_arrow(s4_x + s4_w, 118, 258, 118, color=(15, 23, 42), border_w=1.8, direction='R')
    
    # ── Step 5: Clock Box (Epigenetic Reversal Metric) ──
    s5_x, s5_w = 258, 54
    pdf.draw_card(s5_x, card_y, s5_w, card_h, bg_color=(240, 253, 250), border_color=(16, 185, 129), r=3, border_w=1.0) # Emerald
    pdf.set_xy(s5_x, card_y + 3)
    pdf.set_font(pdf.get_font_name(), 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(s5_w, 5, '05. EPIGENETIC CLOCK', 0, 1, 'C')
    pdf.set_x(s5_x)
    pdf.set_font(pdf.get_font_name(), 'B', 12.5) 
    pdf.set_text_color(6, 95, 70) 
    pdf.cell(s5_w, 5, '-11.9 Years Reversal', 0, 1, 'C')
    pdf.set_x(s5_x)
    pdf.set_font(pdf.get_font_name(), 'B', 8.5)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(s5_w, 4, 'ElasticNet Horvath MAE=6y', 0, 0, 'C')
    
    # Arrow 7: s5 -> s6
    pdf.draw_arrow(s5_x + s5_w, 118, 322, 118, color=(15, 23, 42), border_w=1.8, direction='R')
    
    # ── Step 6: End Pill (WETLAB TRANSLATION ASK) ──
    s6_x, s6_w = 322, 82
    pdf.draw_pill(s6_x, card_y, s6_w, card_h, bg_color=(250, 245, 255), border_color=(139, 92, 246), border_w=1.0) # Purple
    pdf.set_xy(s6_x, card_y + 3)
    pdf.set_font(pdf.get_font_name(), 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(s6_w, 5, '06. WETLAB VALIDATION ASK', 0, 1, 'C')
    pdf.set_x(s6_x)
    pdf.set_font(pdf.get_font_name(), 'B', 13) 
    pdf.set_text_color(109, 40, 217) 
    pdf.cell(s6_w, 5, '$500,000 Seed Investment', 0, 1, 'C')
    pdf.set_x(s6_x)
    pdf.set_font(pdf.get_font_name(), 'B', 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(s6_w, 4, 'Target presentation: BIO 2026', 0, 0, 'C')

    # ============================================================
    # SECTION 2: DETAILED SPECIFICATIONS GRID (y = 172 to y = 265)
    # ============================================================
    
    # Title for Details Section
    pdf.set_xy(15, 170)
    pdf.set_font(pdf.get_font_name(), 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(390, 6, 'DETAILED PIPELINE SPECIFICATIONS & PARAMETERS', 0, 0, 'L')
    
    # Thin divider line
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.4)
    pdf.line(15, 177, 405, 177)
    
    card_y = 181
    card_h = 80
    
    # Card 1: Data & VAE Core Detail
    pdf.draw_card(15, card_y, 120, card_h, bg_color=(255, 255, 255), border_color=(203, 213, 225), r=4, border_w=0.4)
    pdf.set_xy(20, card_y + 5)
    pdf.set_font(pdf.get_font_name(), 'B', 11.5)
    pdf.set_text_color(30, 58, 138) # Blue
    pdf.cell(110, 5, '01. COMPUTATION & AI AUTOENCODER', 0, 1)
    
    pdf.ln(2.5)
    pdf.set_x(20)
    pdf.set_font(pdf.get_font_name(), 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.write(4.5, "•  Human Heart Atlas Data:\n")
    pdf.set_x(25)
    pdf.set_font(pdf.get_font_name(), '', 9.5)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(105, 4.2, 
        "Trained on 500,000+ real cardiac cells from the Human Cell Atlas (Litvinukova et al., Nature 2020) and the PERIHEART dataset. "
        "Baseline manifolds map healthy 'Young' (ages 40-55) and senescent 'Aged' (ages 55-75) ventricular cell states."
    )
    
    pdf.ln(2.5)
    pdf.set_x(20)
    pdf.set_font(pdf.get_font_name(), 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.write(4.5, "•  scVI Manifold VAE Core:\n")
    pdf.set_x(25)
    pdf.set_font(pdf.get_font_name(), '', 9.5)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(105, 4.2, 
        "Compresses high-dimensional single-cell expression matrices into a 20-dimensional latent manifold, "
        "reducing 50GB raw inputs into 53.7MB neural model weights. Trajectory simulation predicts target reprogramming combinations."
    )

    # Card 2: Safety Gating & AlphaFold Detail
    pdf.draw_card(145, card_y, 120, card_h, bg_color=(255, 255, 255), border_color=(203, 213, 225), r=4, border_w=0.4)
    pdf.set_xy(150, card_y + 5)
    pdf.set_font(pdf.get_font_name(), 'B', 11.5)
    pdf.set_text_color(180, 83, 9) # Amber
    pdf.cell(110, 5, '02. SAFETY GATING & STRUCTURAL AUDITING', 0, 1)
    
    pdf.ln(2.5)
    pdf.set_x(150)
    pdf.set_font(pdf.get_font_name(), 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.write(4.5, "•  Oncogene & Dedifferentiation Gating:\n")
    pdf.set_x(155)
    pdf.set_font(pdf.get_font_name(), '', 9.5)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(105, 4.2, 
        "Built-in in-silico safety ceilings automatically exclude oncogenic factors like MYC and OCT4. "
        "Simulates short transient transfection dosage cycles (e.g., 2h ON / 21h OFF) to avoid cell identity loss."
    )
    
    pdf.ln(2.5)
    pdf.set_x(150)
    pdf.set_font(pdf.get_font_name(), 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.write(4.5, "•  AlphaFold 3 DNA Valency Audit:\n")
    pdf.set_x(155)
    pdf.set_font(pdf.get_font_name(), '', 9.5)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(105, 4.2, 
        "Verifies structural docking affinity between transcription factors and target genomic DNA sequences "
        "(such as the POU5F1-SOX2 DNA complex) to confirm physical binding capabilities prior to synthesis."
    )

    # Card 3: Reversal Metric & Funding Ask Detail
    pdf.draw_card(275, card_y, 130, card_h, bg_color=(255, 255, 255), border_color=(139, 92, 246), r=4, border_w=0.5)
    pdf.set_xy(280, card_y + 5)
    pdf.set_font(pdf.get_font_name(), 'B', 11.5)
    pdf.set_text_color(107, 33, 168) # Purple
    pdf.cell(120, 5, '03. EPIGENETIC AGE RESET & SEED MILESTONES', 0, 1)
    
    pdf.ln(2.5)
    pdf.set_x(280)
    pdf.set_font(pdf.get_font_name(), 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.write(4.5, "•  Epigenetic Clock Age Reset (-11.9 Years):\n")
    pdf.set_x(285)
    pdf.set_font(pdf.get_font_name(), '', 9.5)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(115, 4.2, 
        "Achieves a deterministic -11.9 year rejuvenation, measured by a cross-validated ElasticNet molecular clock "
        "trained on HCA cardiac donor ages (Mean Absolute Error of 6.0 years). Preserves beating lineage functional identity."
    )
    
    pdf.ln(2.5)
    pdf.set_x(280)
    pdf.set_font(pdf.get_font_name(), 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.write(4.5, "•  Wetlab Translation Funding Ask ($500,000):\n")
    pdf.set_x(285)
    pdf.set_font(pdf.get_font_name(), '', 9.5)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(115, 4.2, 
        "Securing capital specifically to synthesize predicted gated transcription factor cocktails, execute "
        "calcium-transient imaging, run ATAC-seq accessibility tests, and complete rodent trials for the San Diego BIO 2026 Summit."
    )

    # Draw Page Footer
    pdf.set_xy(15, 274)
    pdf.set_font(pdf.get_font_name(), 'B', 8.5)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, 'CONFIDENTIAL RESEARCH | NILUS LAB CO-FOUNDERS ACCELERATOR PRESENTATION | COPYRIGHT 2026', 0, 0, 'C')

    # Save PDF
    pdf.output(pdf_path)
    print(f"Workflow Chart Poster compiled at: {pdf_path}")
    
    # Synchronize to artifacts
    artifact_path = r"C:\Users\alaaa\.gemini\antigravity\brain\5ec8c43a-d26b-4eb0-9bbf-a4f8e4b3ed96\Nilus_Lab_Scientific_Poster.pdf"
    shutil.copy(pdf_path, artifact_path)
    print(f"Synchronized poster to conversation artifacts: {artifact_path}")
    return pdf_path

if __name__ == '__main__':
    generate_poster()
