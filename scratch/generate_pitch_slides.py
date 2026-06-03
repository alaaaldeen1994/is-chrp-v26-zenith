import os
from fpdf import FPDF

class PitchDeckPDF(FPDF):
    def __init__(self):
        # Initialize in Landscape mode (A4: 297mm wide, 210mm high)
        super().__init__(orientation='L', unit='mm', format='A4')
        self.set_margin(15)
        
        # Load premium custom fonts (Outfit is a modern, high-end sans-serif typeface)
        font_dir = os.path.dirname(os.path.dirname(__file__))
        reg_font = os.path.join(font_dir, "Outfit-Regular.ttf")
        bold_font = os.path.join(font_dir, "Outfit-Bold.ttf")
        
        if os.path.exists(reg_font) and os.path.exists(bold_font):
            self.add_font('Outfit', '', reg_font)
            self.add_font('Outfit', 'B', bold_font)
            self.has_custom_font = True
        else:
            self.has_custom_font = False

    def get_font_name(self, is_bold=False):
        if self.has_custom_font:
            return 'Outfit'
        return 'Helvetica'

    def draw_dark_slide_bg(self):
        # Premium Deep slate background (Slate 950)
        self.set_fill_color(11, 15, 25) 
        self.rect(0, 0, 297, 210, 'F')
        
        # Subtle glowing accent violet circle at bottom right
        self.set_fill_color(17, 24, 39) 
        self.ellipse(180, 110, 180, 180, 'F')

    def draw_light_slide_bg(self):
        # Sleek, clean background for readability (Slate 50)
        self.set_fill_color(248, 250, 252) 
        self.rect(0, 0, 297, 210, 'F')

    def draw_card(self, x, y, w, h, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=4):
        # Set colors
        self.set_fill_color(*bg_color)
        if border_color:
            self.set_draw_color(*border_color)
            self.set_line_width(0.3)
            style = 'DF'
        else:
            style = 'F'
        
        # Draw rounded card rectangle
        self.rect(x, y, w, h, style, round_corners=True, corner_radius=r)

    def draw_badge(self, x, y, text, bg_color, text_color, width=35, height=8, font_size=9):
        self.set_fill_color(*bg_color)
        self.rect(x, y, width, height, 'F', round_corners=True, corner_radius=height/2)
        
        self.set_xy(x, y)
        self.set_font(self.get_font_name(True), 'B', font_size)
        self.set_text_color(*text_color)
        self.cell(width, height, text, 0, 0, 'C')

    def slide_header(self, title, category, slide_num):
        # Category indicator tag at top-left
        self.set_xy(15, 11)
        self.set_font(self.get_font_name(True), 'B', 10) # Increased from 9 to 10
        self.set_text_color(79, 70, 229) # Indigo 600
        self.cell(200, 4, category.upper(), 0, 1, 'L')
        
        # Main Title (Bold and dark)
        self.set_x(15)
        self.set_font(self.get_font_name(True), 'B', 24) # Increased from 21 to 24
        self.set_text_color(0, 0, 0) # High-contrast black
        self.cell(200, 8, title, 0, 0, 'L')
        
        # Slide Indicator (02 / 05)
        self.set_font(self.get_font_name(True), 'B', 12) # Increased from 11 to 12
        self.set_text_color(71, 85, 105) # Slate 600
        self.cell(67, 8, f'{slide_num:02d}  /  05', 0, 1, 'R')
        
        # Thin divider line
        self.set_draw_color(226, 232, 240) # Slate 200 (darker line)
        self.set_line_width(0.4)
        self.line(15, 26, 282, 26)

def generate_deck():
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    pdf_path = os.path.join(reports_dir, "Nilus_Lab_Pitch_Deck.pdf")
    
    pdf = PitchDeckPDF()
    
    # ----------------------------------------------------
    # SLIDE 1: TITLE SLIDE (Dark Theme)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_dark_slide_bg()
    
    # Left accent bar
    pdf.set_fill_color(79, 70, 229) # Indigo 600
    pdf.rect(10, 0, 2.5, 210, 'F')
    
    # Brand logo mark (Overlapping rounded blocks)
    pdf.set_fill_color(79, 70, 229) # Indigo
    pdf.rect(25, 38, 12, 12, 'F', round_corners=True, corner_radius=3)
    pdf.set_fill_color(5, 150, 105) # Emerald
    pdf.rect(31, 44, 12, 12, 'F', round_corners=True, corner_radius=3)
    
    pdf.set_xy(48, 43)
    pdf.set_font(pdf.get_font_name(True), 'B', 22) # Increased from 20 to 22
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 8, 'NILUS LAB', 0, 1, 'L')
    
    # Main Title
    pdf.set_xy(25, 72)
    pdf.set_font(pdf.get_font_name(True), 'B', 40) # Increased from 38 to 40
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(220, 16, 'Reversing Cardiac Ageing\nWithout Oncogene Risk')
    
    # Subtitle
    pdf.set_xy(25, 118)
    pdf.set_font(pdf.get_font_name(), '', 16) # Increased from 14.5 to 16
    pdf.set_text_color(203, 213, 225) # Slate 300 (brighter text)
    pdf.multi_cell(220, 9, 'Generative cellular reprogramming therapeutics targeting cardiomyopathy.\nPowered by the Zenith v28.0 GOLD single-cell foundation model.')
    
    # Accelerator track details
    pdf.set_xy(25, 165)
    pdf.set_font(pdf.get_font_name(True), 'B', 12) # Increased from 11 to 12
    pdf.set_text_color(52, 211, 153) # Emerald 400
    pdf.cell(0, 5, 'DEEP BIO ACCELERATOR - LAUNCH TRACK INTERVIEW PRESENTATION', 0, 1)
    
    # ----------------------------------------------------
    # SLIDE 2: THE PROBLEM & SOLUTION (Clean Dual Columns)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_light_slide_bg()
    pdf.slide_header('The Problem & The Solution', 'Indications & Reprogramming Limits', 2)
    
    # Left Column (The Problem) - Rose Card
    pdf.draw_card(15, 38, 128, 152, bg_color=(255, 248, 248), border_color=(254, 202, 202), r=4)
    pdf.draw_badge(22, 44, 'CLINICAL RISK & LIMITS', bg_color=(244, 63, 94), text_color=(255, 255, 255), width=50, height=8, font_size=9)
    
    pdf.set_xy(22, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 18) # Increased from 16 to 18
    pdf.set_text_color(159, 18, 57) # Rose 800 (very dark)
    pdf.cell(100, 6, 'Cardiac Senescence & Reprogramming Limits', 0, 1)
    
    bullets_problem = [
        ("64M+ Heart Failure Patients", "Epigenetic decay and loss of contractility drive global mortality."),
        ("Oncogenic Risk of OSKM Factors", "Classic Yamanaka factors trigger uncontrolled dedifferentiation."),
        ("Delivery & Specificity Barriers", "Current therapies lack safe, cardiac-specific lineage targets.")
    ]
    
    y_cursor = 70
    for title, desc in bullets_problem:
        pdf.set_fill_color(244, 63, 94) # Rose 500
        pdf.ellipse(23, y_cursor + 2, 2.5, 2.5, 'F')
        
        pdf.set_xy(28, y_cursor)
        pdf.set_font(pdf.get_font_name(True), 'B', 14) # Increased from 12 to 14
        pdf.set_text_color(0, 0, 0) # High-contrast black
        pdf.cell(100, 5, title, 0, 1)
        
        pdf.set_x(28)
        pdf.set_font(pdf.get_font_name(), '', 13) # Increased from 11 to 13
        pdf.set_text_color(30, 41, 59) # Slate 800 (very dark)
        pdf.cell(100, 5, desc, 0, 1)
        y_cursor += 30
        
    # Right Column (The Solution) - Indigo Card
    pdf.draw_card(154, 38, 128, 152, bg_color=(239, 246, 255), border_color=(191, 219, 254), r=4)
    pdf.draw_badge(161, 44, 'ZENITH PLATFORM SOLUTION', bg_color=(37, 99, 235), text_color=(255, 255, 255), width=55, height=8, font_size=9)
    
    pdf.set_xy(161, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 18) # Increased from 16 to 18
    pdf.set_text_color(30, 58, 138) # Blue 900
    pdf.cell(100, 6, 'Safe, Target-Specific Rejuvenation', 0, 1)
    
    bullets_solution = [
        ("In-Silico Safety Gating", "Dual-threshold gates eliminate oncogenes and preserve lineage."),
        ("Trained on 500,000 Single Cells", "Maps cardiac manifolds via scVI variational autoencoders."),
        ("-11.9y Epigenetic Age Reversal", "Trained on real donor ages with a cross-validated MAE of 6.0y.")
    ]
    
    y_cursor = 70
    for title, desc in bullets_solution:
        pdf.set_fill_color(37, 99, 235) # Blue 500
        pdf.ellipse(162, y_cursor + 2, 2.5, 2.5, 'F')
        
        pdf.set_xy(167, y_cursor)
        pdf.set_font(pdf.get_font_name(True), 'B', 14) # Increased from 12 to 14
        pdf.set_text_color(0, 0, 0) # High-contrast black
        pdf.cell(100, 5, title, 0, 1)
        
        pdf.set_x(167)
        pdf.set_font(pdf.get_font_name(), '', 13) # Increased from 11 to 13
        pdf.set_text_color(30, 41, 59) # Slate 800
        pdf.cell(100, 5, desc, 0, 1)
        y_cursor += 30

    # ----------------------------------------------------
    # SLIDE 3: TECHNOLOGY & INFRASTRUCTURE (Clean PPT Blocks)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_light_slide_bg()
    pdf.slide_header('Core Platform & Technical Pipeline', 'Computational Architecture', 3)
    
    col_width = 82
    spacing = 8
    
    # Card 1: scVI Foundation Model
    pdf.draw_card(15, 38, col_width, 152, bg_color=(255, 255, 255), border_color=(194, 205, 217), r=4) # Darker border
    
    pdf.set_fill_color(79, 70, 229) # Indigo 600
    pdf.ellipse(22, 45, 9, 9, 'F') 
    pdf.set_xy(22, 45)
    pdf.set_font(pdf.get_font_name(True), 'B', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(9, 9, '1', 0, 0, 'C')
    
    pdf.set_xy(34, 46)
    pdf.set_font(pdf.get_font_name(True), 'B', 16) # Increased from 14 to 16
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 6, 'scVI Generative Core', 0, 1)
    
    bullets_t1 = [
        "In-Silico Modeling Core",
        "Trained on 500,000 cells",
        "4,908 variable gene inputs",
        "20-dimensional latent VAE",
        "HCA + PERIHEART data"
    ]
    y_c = 64
    for b in bullets_t1:
        pdf.set_fill_color(79, 70, 229) # Indigo square bullet
        pdf.rect(22, y_c + 2.2, 2.0, 2.0, 'F')
        pdf.set_xy(27, y_c)
        pdf.set_font(pdf.get_font_name(True), 'B', 13) # Increased from 11.5 to 13, Bold for contrast
        pdf.set_text_color(30, 41, 59) # Slate 800
        pdf.cell(60, 5, b, 0, 1)
        y_c += 22 # Generous spacing
    
    # Card 2: Safety Gating
    pdf.draw_card(15 + col_width + spacing, 38, col_width, 152, bg_color=(255, 255, 255), border_color=(194, 205, 217), r=4)
    
    pdf.set_fill_color(79, 70, 229)
    pdf.ellipse(22 + col_width + spacing, 45, 9, 9, 'F')
    pdf.set_xy(22 + col_width + spacing, 45)
    pdf.set_font(pdf.get_font_name(True), 'B', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(9, 9, '2', 0, 0, 'C')
    
    pdf.set_xy(34 + col_width + spacing, 46)
    pdf.set_font(pdf.get_font_name(True), 'B', 16) # Increased from 14 to 16
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 6, 'Safety Auditing', 0, 1)
    
    bullets_t2 = [
        "Oncogene Blacklist Check",
        "Blocks MYC / OCT4 factors",
        "Dedifferentiation limits gated",
        "Ensures cell identity stability",
        "Monitors TNNT2 / ACTN2"
    ]
    y_c = 64
    for b in bullets_t2:
        pdf.set_fill_color(79, 70, 229)
        pdf.rect(22 + col_width + spacing, y_c + 2.2, 2.0, 2.0, 'F')
        pdf.set_xy(27 + col_width + spacing, y_c)
        pdf.set_font(pdf.get_font_name(True), 'B', 13) # Increased from 11.5 to 13
        pdf.set_text_color(30, 41, 59)
        pdf.cell(60, 5, b, 0, 1)
        y_c += 22
    
    # Card 3: Dosage & Valency
    pdf.draw_card(15 + 2*(col_width + spacing), 38, col_width, 152, bg_color=(255, 255, 255), border_color=(194, 205, 217), r=4)
    
    pdf.set_fill_color(79, 70, 229)
    pdf.ellipse(22 + 2*(col_width + spacing), 45, 9, 9, 'F')
    pdf.set_xy(22 + 2*(col_width + spacing), 45)
    pdf.set_font(pdf.get_font_name(True), 'B', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(9, 9, '3', 0, 0, 'C')
    
    pdf.set_xy(34 + 2*(col_width + spacing), 46)
    pdf.set_font(pdf.get_font_name(True), 'B', 16) # Increased from 14 to 16
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 6, 'AF3 & ElasticNet Clock', 0, 1)
    
    bullets_t3 = [
        "AlphaFold 3 Valency models",
        "Models 3D TF-DNA docking",
        "ElasticNet age clock",
        "MAE = 6.0y on real HCA",
        "Transient dose windows"
    ]
    y_c = 64
    for b in bullets_t3:
        pdf.set_fill_color(79, 70, 229)
        pdf.rect(22 + 2*(col_width + spacing), y_c + 2.2, 2.0, 2.0, 'F')
        pdf.set_xy(27 + 2*(col_width + spacing), y_c)
        pdf.set_font(pdf.get_font_name(True), 'B', 13) # Increased from 11.5 to 13
        pdf.set_text_color(30, 41, 59)
        pdf.cell(60, 5, b, 0, 1)
        y_c += 22

    # ----------------------------------------------------
    # SLIDE 4: MARKET, COMPETITION & TRACTION (Clean PPT Blocks)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_light_slide_bg()
    pdf.slide_header('Market Focus, Competition & Wetlab Target', 'TAM & Funding Parameters', 4)
    
    # Left Card - Market Detail
    pdf.draw_card(15, 38, 150, 152, bg_color=(255, 255, 255), border_color=(194, 205, 217), r=4)
    pdf.draw_badge(22, 44, 'MARKET POSITIONING & COMPETITION', bg_color=(79, 70, 229), text_color=(255, 255, 255), width=60, height=8, font_size=8.5)
    
    pdf.set_xy(22, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 18) # Increased to 18
    pdf.set_text_color(0, 0, 0)
    pdf.cell(130, 6, 'Target Market, Competition & Differentiation', 0, 1)
    
    bullets_market = [
        ("CVD Longevity Market", "$50B addressable cardiomyopathy indication targets."),
        ("Altos Bio & Retro Labs", "Broad systemic vectors. Nilus focuses on cardiac specificity."),
        ("Turn Biotechnologies", "Dermatology focus. Nilus is optimized for cardiac lineages."),
        ("Wetlab Commercialization", "Bringing science out of the lab and into the market.")
    ]
    y_c = 68
    for title, desc in bullets_market:
        pdf.set_fill_color(79, 70, 229)
        pdf.ellipse(23, y_c + 2, 2.5, 2.5, 'F')
        pdf.set_xy(28, y_c)
        pdf.set_font(pdf.get_font_name(True), 'B', 13.5) # Increased from 11.5 to 13.5
        pdf.set_text_color(0, 0, 0)
        pdf.cell(55, 5, title + " -", 0, 0)
        pdf.set_font(pdf.get_font_name(), '', 13) # Increased to 13
        pdf.set_text_color(30, 41, 59)
        pdf.cell(75, 5, desc, 0, 1)
        y_c += 12
    
    # Highlight Box - $500,000 Wetlab Funding Ask
    pdf.draw_card(22, 122, 136, 55, bg_color=(240, 244, 255), border_color=(199, 210, 254), r=3)
    pdf.set_xy(27, 126)
    pdf.set_font(pdf.get_font_name(True), 'B', 12.5) # Increased from 11.5 to 12.5
    pdf.set_text_color(79, 70, 229) # Indigo
    pdf.cell(100, 5, 'WETLAB VALIDATION FUNDING ASK', 0, 1)
    
    pdf.set_xy(27, 133)
    pdf.set_font(pdf.get_font_name(), '', 12) # Increased from 11 to 12
    pdf.set_text_color(0, 0, 0) # High-contrast black
    pdf.multi_cell(126, 5.2, 
        "Raising $500,000 Seed round specifically to fund cocktail synthesis, calcium imaging, ATAC-seq chromatin profiling, and rodent safety assays."
    )
    
    # Right Grid - Big Metrics
    # Metric 1: $500,000 Funding Ask
    pdf.draw_card(173, 38, 109, 72, bg_color=(255, 255, 255), border_color=(194, 205, 217), r=4)
    pdf.set_xy(173, 48)
    pdf.set_font(pdf.get_font_name(True), 'B', 42) # Increased from 34 to 42 (Huge stat)
    pdf.set_text_color(79, 70, 229) # Indigo
    pdf.cell(109, 10, '$500K Ask', 0, 1, 'C')
    
    pdf.set_xy(173, 68)
    pdf.set_font(pdf.get_font_name(True), 'B', 13) # Increased from 11 to 13
    pdf.set_text_color(15, 23, 42) # High contrast label
    pdf.cell(109, 5, 'WETLAB FUNDING ASK', 0, 1, 'C')
    
    # Metric 2: -11.9y Reversal (6.0y MAE)
    pdf.draw_card(173, 118, 109, 72, bg_color=(236, 253, 245), border_color=(167, 243, 208), r=4) 
    pdf.set_xy(173, 128)
    pdf.set_font(pdf.get_font_name(True), 'B', 42) # Increased from 34 to 42
    pdf.set_text_color(5, 150, 105) # Emerald 600
    pdf.cell(109, 10, '-11.9 Years', 0, 1, 'C')
    
    pdf.set_xy(173, 148)
    pdf.set_font(pdf.get_font_name(True), 'B', 13) # Increased from 11 to 13
    pdf.set_text_color(15, 23, 42) 
    pdf.cell(109, 5, 'EPIGENETIC AGE RESET (MAE=6.0y)', 0, 1, 'C')

    # ----------------------------------------------------
    # SLIDE 5: ROADMAP & FOUNDING TEAM (Clean PPT Blocks)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_light_slide_bg()
    pdf.slide_header('Operational Roadmap & Team Dynamics', 'Founding Team & Wetlab Pipeline', 5)
    
    # Left Column: Founding Team
    pdf.draw_card(15, 38, 120, 152, bg_color=(255, 255, 255), border_color=(194, 205, 217), r=4)
    pdf.draw_badge(22, 44, 'THE TEAM', bg_color=(79, 70, 229), text_color=(255, 255, 255), width=24, height=8, font_size=8.5)
    
    pdf.set_xy(22, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 18) # Increased to 18
    pdf.set_text_color(0, 0, 0)
    pdf.cell(106, 6, 'Team Chemistry & Dynamics', 0, 1)
    
    bullets_team = [
        ("Computational VAE Core", "Expertise in deep latent manifolds."),
        ("Molecular Biology Lab", "Specialists in cell transfections."),
        ("Long-Term Synergy", "Collaborated on single-cell research."),
        ("BIO 2026 Summit Target", "Preparing to showcase wetlab data.")
    ]
    y_c = 68
    for title, desc in bullets_team:
        pdf.set_fill_color(79, 70, 229)
        pdf.rect(22, y_c + 2.5, 2.0, 2.0, 'F')
        pdf.set_xy(27, y_c)
        pdf.set_font(pdf.get_font_name(True), 'B', 13.5) # Increased to 13.5
        pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 5, title + ":", 0, 1)
        pdf.set_x(27)
        pdf.set_font(pdf.get_font_name(), '', 13) # Increased to 13
        pdf.set_text_color(30, 41, 59)
        pdf.cell(50, 5, desc, 0, 1)
        y_c += 16
    
    # Right Column: Timeline Card
    pdf.draw_card(143, 38, 139, 152, bg_color=(255, 255, 255), border_color=(194, 205, 217), r=4)
    pdf.draw_badge(150, 44, 'DEVELOPMENT ROADMAP', bg_color=(5, 150, 105), text_color=(255, 255, 255), width=48, height=8, font_size=8.5)
    
    pdf.set_xy(150, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 18) # Increased to 18
    pdf.set_text_color(0, 0, 0)
    pdf.cell(125, 6, 'Key Execution Milestones', 0, 1)
    
    # Draw vertical timeline indicator line
    pdf.set_draw_color(79, 70, 229) # Indigo 600
    pdf.set_line_width(0.4)
    pdf.line(155, 76, 155, 172)
    
    # Milestones data
    milestones = [
        ("Phase 1: Cocktail Synthesis & Wetlab Setup", "Synthesize target cocktails and setup primary cardiomyocyte models.", 70), 
        ("Phase 2: Preclinical In-Vitro Assaying", "Calcium-transient imaging & chromatin accessibility (ATAC-seq) profiles.", 108),
        ("Phase 3: In-Vivo Rodent Assays & Seed Close", "Conclude rodent cardiomyopathy trials and close $500,000 seed funding.", 146)
    ]
    
    for title, desc, y_pos in milestones:
        pdf.set_fill_color(79, 70, 229)
        pdf.ellipse(153.2, y_pos + 1.2, 3.6, 3.6, 'F')
        
        pdf.set_draw_color(224, 231, 255) # Indigo 100
        pdf.set_line_width(1)
        pdf.ellipse(152, y_pos, 6, 6, 'D')
        
        pdf.set_xy(162, y_pos)
        pdf.set_font(pdf.get_font_name(True), 'B', 14) # Increased to 14
        pdf.set_text_color(0, 0, 0)
        pdf.cell(115, 5, title, 0, 1)
        
        pdf.set_x(162)
        pdf.set_font(pdf.get_font_name(), '', 13) # Increased to 13
        pdf.set_text_color(30, 41, 59)
        pdf.cell(115, 5, desc, 0, 1)
        
    # Save Presentation
    pdf.output(pdf_path)
    print(f"Visual pitch deck successfully compiled at: {pdf_path}")
    return pdf_path

if __name__ == '__main__':
    generate_deck()
