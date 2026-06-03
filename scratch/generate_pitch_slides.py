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

    def draw_badge(self, x, y, text, bg_color, text_color, width=35, height=7, font_size=8):
        self.set_fill_color(*bg_color)
        self.rect(x, y, width, height, 'F', round_corners=True, corner_radius=height/2)
        
        self.set_xy(x, y)
        self.set_font(self.get_font_name(True), 'B', font_size)
        self.set_text_color(*text_color)
        self.cell(width, height, text, 0, 0, 'C')

    def slide_header(self, title, category, slide_num):
        # Category indicator tag at top-left
        self.set_xy(15, 11)
        self.set_font(self.get_font_name(True), 'B', 9) # Increased from 8 to 9
        self.set_text_color(79, 70, 229) # Indigo 600
        self.cell(200, 4, category.upper(), 0, 1, 'L')
        
        # Main Title
        self.set_x(15)
        self.set_font(self.get_font_name(True), 'B', 21) # Increased from 18 to 21
        self.set_text_color(15, 23, 42) # Slate 900
        self.cell(200, 8, title, 0, 0, 'L')
        
        # Slide Indicator (02 / 05)
        self.set_font(self.get_font_name(True), 'B', 11) # Increased from 10 to 11
        self.set_text_color(148, 163, 184) # Slate 400
        self.cell(67, 8, f'{slide_num:02d}  /  05', 0, 1, 'R')
        
        # Thin divider line
        self.set_draw_color(241, 245, 249) # Slate 100
        self.set_line_width(0.3)
        self.line(15, 26, 282, 26)

def generate_deck():
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    pdf_path = os.path.join(reports_dir, "Nilus_Lab_Deep_Bio_Pitch_Deck.pdf")
    
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
    pdf.set_font(pdf.get_font_name(True), 'B', 20) # Increased from 18 to 20
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 8, 'NILUS LAB', 0, 1, 'L')
    
    # Main Title
    pdf.set_xy(25, 72)
    pdf.set_font(pdf.get_font_name(True), 'B', 38) # Increased from 32 to 38
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(220, 15, 'Reversing Cardiac Ageing\nWithout Oncogene Risk')
    
    # Subtitle
    pdf.set_xy(25, 118)
    pdf.set_font(pdf.get_font_name(), '', 14.5) # Increased from 13 to 14.5
    pdf.set_text_color(148, 163, 184) # Slate 400
    pdf.multi_cell(220, 8.5, 'Generative cellular reprogramming therapies targeting cardiomyopathy and heart failure.\nPowered by the Zenith v28.0 GOLD single-cell foundation model.')
    
    # Accelerator track details
    pdf.set_xy(25, 165)
    pdf.set_font(pdf.get_font_name(True), 'B', 11) # Increased from 9.5 to 11
    pdf.set_text_color(52, 211, 153) # Emerald 400
    pdf.cell(0, 5, 'DEEP BIO ACCELERATOR - LAUNCH TRACK INTERVIEW PRESENTATION', 0, 1)
    
    # ----------------------------------------------------
    # SLIDE 2: THE PROBLEM & SOLUTION (Light Theme, Dual Columns)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_light_slide_bg()
    pdf.slide_header('The Problem & The Solution', 'Indications & Reprogramming Limits', 2)
    
    # Left Column (The Problem) - Rose Card
    pdf.draw_card(15, 38, 128, 152, bg_color=(255, 248, 248), border_color=(254, 202, 202), r=4)
    pdf.draw_badge(22, 44, 'CLINICAL RISK & LIMITS', bg_color=(244, 63, 94), text_color=(255, 255, 255), width=50, height=7, font_size=8.5)
    
    pdf.set_xy(22, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 16) # Increased from 14 to 16
    pdf.set_text_color(159, 18, 57) # Rose 800
    pdf.cell(100, 6, 'Cardiac Senescence & Reprogramming Limits', 0, 1)
    
    bullets_problem = [
        ("64M+ Patients Globally:", "Heart failure is driven by cellular senescence, loss of adult sarcomere structures, and chromatin degradation."),
        ("Oncogenic Risk (OSKM):", "Classical Yamanaka factors trigger dedifferentiation and cell drift, creating high risks of teratoma and tumor formation."),
        ("Delivery & Specificity Limits:", "Existing therapies cannot precisely target therapeutic chromatin states, leading to unsafe, non-specific changes.")
    ]
    
    y_cursor = 67
    for title, desc in bullets_problem:
        # Bullet marker
        pdf.set_fill_color(244, 63, 94) # Rose 500
        pdf.ellipse(23, y_cursor + 2, 2.5, 2.5, 'F')
        
        pdf.set_xy(28, y_cursor)
        pdf.set_font(pdf.get_font_name(True), 'B', 12) # Increased from 10 to 12
        pdf.set_text_color(15, 23, 42) # Slate 900
        pdf.cell(100, 5, title, 0, 1)
        
        pdf.set_x(28)
        pdf.set_font(pdf.get_font_name(), '', 11) # Increased from 9.5 to 11
        pdf.set_text_color(71, 85, 105) # Slate 600
        pdf.multi_cell(106, 5.2, desc) # Increased line height from 4.5 to 5.2
        y_cursor += 30
        
    # Right Column (The Solution) - Indigo Card
    pdf.draw_card(154, 38, 128, 152, bg_color=(239, 246, 255), border_color=(191, 219, 254), r=4)
    pdf.draw_badge(161, 44, 'ZENITH PLATFORM SOLUTION', bg_color=(37, 99, 235), text_color=(255, 255, 255), width=55, height=7, font_size=8.5)
    
    pdf.set_xy(161, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 16) # Increased from 14 to 16
    pdf.set_text_color(30, 58, 138) # Blue 900
    pdf.cell(100, 6, 'Safe, Target-Specific Rejuvenation', 0, 1)
    
    bullets_solution = [
        ("In-Silico Safety Gating:", "Dual-threshold gates screen out oncogenes and restrict cellular dedifferentiation past functional limits."),
        ("-11.9y Epigenetic Reset:", "Validated age clock trained on real HCA data achieves 11.9 years of age reversal in mature cells."),
        ("Transient Cooperativity:", "Optimized expression windows (e.g., 2h ON) regulate chromatin accessibility without altering cell identity.")
    ]
    
    y_cursor = 67
    for title, desc in bullets_solution:
        # Bullet marker
        pdf.set_fill_color(37, 99, 235) # Blue 500
        pdf.ellipse(162, y_cursor + 2, 2.5, 2.5, 'F')
        
        pdf.set_xy(167, y_cursor)
        pdf.set_font(pdf.get_font_name(True), 'B', 12) # Increased from 10 to 12
        pdf.set_text_color(15, 23, 42) # Slate 900
        pdf.cell(100, 5, title, 0, 1)
        
        pdf.set_x(167)
        pdf.set_font(pdf.get_font_name(), '', 11) # Increased from 9.5 to 11
        pdf.set_text_color(71, 85, 105) # Slate 600
        pdf.multi_cell(106, 5.2, desc) # Increased line height from 4.5 to 5.2
        y_cursor += 30

    # ----------------------------------------------------
    # SLIDE 3: TECHNOLOGY & INFRASTRUCTURE (Light Theme, 3 Columns)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_light_slide_bg()
    pdf.slide_header('Core Platform & Technical Pipeline', 'Computational Architecture', 3)
    
    col_width = 82
    spacing = 8
    
    # Card 1: scVI Foundation Model
    pdf.draw_card(15, 38, col_width, 152, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=4)
    
    pdf.set_fill_color(79, 70, 229) # Indigo 600
    pdf.ellipse(22, 45, 9, 9, 'F') # Radius adjusted slightly
    pdf.set_xy(22, 45)
    pdf.set_font(pdf.get_font_name(True), 'B', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(9, 9, '1', 0, 0, 'C')
    
    pdf.set_xy(34, 46)
    pdf.set_font(pdf.get_font_name(True), 'B', 14) # Increased from 12 to 14
    pdf.set_text_color(15, 23, 42)
    pdf.cell(60, 6, 'scVI Generative Core', 0, 1)
    
    pdf.set_xy(22, 60)
    pdf.set_font(pdf.get_font_name(), '', 11.5) # Increased from 10 to 11.5
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(col_width - 14, 6.8, # Increased line height from 6 to 6.8
        "- Trained on 500,000 human cardiac cells from HCA + PERIHEART.\n\n"
        "- Maps cellular reprogramming dynamics across 4,908 highly variable gene dimensions.\n\n"
        "- Generates in-silico cell state representations to predict the effects of transcription factor interventions."
    )
    
    # Card 2: Safety Gating
    pdf.draw_card(15 + col_width + spacing, 38, col_width, 152, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=4)
    
    pdf.set_fill_color(79, 70, 229)
    pdf.ellipse(22 + col_width + spacing, 45, 9, 9, 'F')
    pdf.set_xy(22 + col_width + spacing, 45)
    pdf.set_font(pdf.get_font_name(True), 'B', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(9, 9, '2', 0, 0, 'C')
    
    pdf.set_xy(34 + col_width + spacing, 46)
    pdf.set_font(pdf.get_font_name(True), 'B', 14) # Increased from 12 to 14
    pdf.set_text_color(15, 23, 42)
    pdf.cell(60, 6, 'Safety Auditing', 0, 1)
    
    pdf.set_xy(22 + col_width + spacing, 60)
    pdf.set_font(pdf.get_font_name(), '', 11.5) # Increased from 10 to 11.5
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(col_width - 14, 6.8, # Increased line height from 6 to 6.8
        "- Oncogene Blacklist: Screens candidate genes to eliminate tumor-forming risks.\n\n"
        "- Dedifferentiation Ceiling: Restricts cellular state changes past strict safety boundaries.\n\n"
        "- Prevents tissue identity loss during the rejuvenation process."
    )
    
    # Card 3: Dosage & Valency
    pdf.draw_card(15 + 2*(col_width + spacing), 38, col_width, 152, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=4)
    
    pdf.set_fill_color(79, 70, 229)
    pdf.ellipse(22 + 2*(col_width + spacing), 45, 9, 9, 'F')
    pdf.set_xy(22 + 2*(col_width + spacing), 45)
    pdf.set_font(pdf.get_font_name(True), 'B', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(9, 9, '3', 0, 0, 'C')
    
    pdf.set_xy(34 + 2*(col_width + spacing), 46)
    pdf.set_font(pdf.get_font_name(True), 'B', 14) # Increased from 12 to 14
    pdf.set_text_color(15, 23, 42)
    pdf.cell(60, 6, 'AF3 & Dosage Audit', 0, 1)
    
    pdf.set_xy(22 + 2*(col_width + spacing), 60)
    pdf.set_font(pdf.get_font_name(), '', 11.5) # Increased from 10 to 11.5
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(col_width - 14, 6.8, # Increased line height from 6 to 6.8
        "- AlphaFold 3 Valency: Models transcription factor binding affinities (e.g. POU5F1-SOX2 heterodimer).\n\n"
        "- Bayesian Dosage Networks: Predicts expression patterns to find optimal dose-response curves.\n\n"
        "- Design: Prescribes transient expression windows for in-vitro translation."
    )

    # ----------------------------------------------------
    # SLIDE 4: MARKET & TRACTION (Light Theme, Metrics Layout)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_light_slide_bg()
    pdf.slide_header('Market Opportunity & Founder Traction', 'TAM & Accelerator Selection', 4)
    
    # Left Card - Market Detail
    pdf.draw_card(15, 38, 150, 152, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=4)
    pdf.draw_badge(22, 44, 'MARKET POSITIONING', bg_color=(79, 70, 229), text_color=(255, 255, 255), width=42, height=7, font_size=8)
    
    pdf.set_xy(22, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 16) # Increased from 14 to 16
    pdf.set_text_color(15, 23, 42)
    pdf.cell(130, 6, 'Target Market & Indication Strategy', 0, 1)
    
    pdf.set_xy(22, 65)
    pdf.set_font(pdf.get_font_name(), '', 11.5) # Increased from 10 to 11.5
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(136, 6.8, 
        "- TAM: $50B longevity and age-induced cardiovascular indications.\n"
        "- Indications: Age-induced cardiomyopathy, vascular wall stiffness, and ischemic heart failure.\n"
        "- Business Model: Out-license verified in-silico gene cocktails to pharma partners, accelerating discovery times from 5 years to 3 weeks."
    )
    
    # Highlight Box - Deep Bio Accelerator
    pdf.draw_card(22, 115, 136, 62, bg_color=(240, 244, 255), border_color=(199, 210, 254), r=3)
    pdf.set_xy(27, 120)
    pdf.set_font(pdf.get_font_name(True), 'B', 12) # Increased from 10 to 12
    pdf.set_text_color(79, 70, 229) # Indigo
    pdf.cell(100, 5, 'ACCELERATOR SELECTION & INTERVIEW STATUS', 0, 1)
    
    pdf.set_xy(27, 128)
    pdf.set_font(pdf.get_font_name(), '', 11) # Increased from 9.5 to 11
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(126, 5.2, # Increased line height from 4.8 to 5.2
        "Selected for founder video interview with the Deep Bio Accelerator (Launch Track).\n"
        "Preparing video call with the accelerator selection committee to review clinical strategy, milestones, and co-founder dynamics."
    )
    
    # Right Grid - Big Metrics
    # Metric 1: $0M-$2M Funding Band
    pdf.draw_card(173, 38, 109, 72, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=4)
    pdf.set_xy(173, 50)
    pdf.set_font(pdf.get_font_name(True), 'B', 34) # Increased from 28 to 34
    pdf.set_text_color(79, 70, 229) # Indigo
    pdf.cell(109, 10, '$0M - $2M', 0, 1, 'C')
    
    pdf.set_xy(173, 68)
    pdf.set_font(pdf.get_font_name(True), 'B', 11) # Increased from 9 to 11
    pdf.set_text_color(148, 163, 184)
    pdf.cell(109, 5, 'LAUNCH TRACK FUNDING BAND', 0, 1, 'C')
    
    # Metric 2: -11.9y Reversal
    pdf.draw_card(173, 118, 109, 72, bg_color=(236, 253, 245), border_color=(167, 243, 208), r=4) # Emerald 50, Emerald 200
    pdf.set_xy(173, 130)
    pdf.set_font(pdf.get_font_name(True), 'B', 34) # Increased from 28 to 34
    pdf.set_text_color(5, 150, 105) # Emerald 600
    pdf.cell(109, 10, '-11.9 Years', 0, 1, 'C')
    
    pdf.set_xy(173, 148)
    pdf.set_font(pdf.get_font_name(True), 'B', 11) # Increased from 9 to 11
    pdf.set_text_color(4, 120, 87) # Emerald 700
    pdf.cell(109, 5, 'EPIGENETIC AGE RESET VALIDATED', 0, 1, 'C')

    # ----------------------------------------------------
    # SLIDE 5: ROADMAP & FOUNDING TEAM (Light Theme, Roadmap Timeline)
    # ----------------------------------------------------
    pdf.add_page()
    pdf.draw_light_slide_bg()
    pdf.slide_header('Operational Roadmap & Team Dynamics', 'Founding Team & Execution', 5)
    
    # Left Column: Founding Team
    pdf.draw_card(15, 38, 120, 152, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=4)
    pdf.draw_badge(22, 44, 'THE TEAM', bg_color=(79, 70, 229), text_color=(255, 255, 255), width=24, height=7, font_size=8)
    
    pdf.set_xy(22, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 16) # Increased from 14 to 16
    pdf.set_text_color(15, 23, 42)
    pdf.cell(106, 6, 'Team Chemistry & Dynamics', 0, 1)
    
    pdf.set_xy(22, 65)
    pdf.set_font(pdf.get_font_name(), '', 11.5) # Increased from 10 to 11.5
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(106, 6.8, # Increased line height from 6.2 to 6.8
        "- Interdisciplinary Founders: Unifies expertise across software engineering, single-cell variational autoencoders, and structural molecular biology.\n\n"
        "- Long-standing Research Partnership: The co-founders have a history of collaborative research in single-cell transcriptomics.\n\n"
        "- Interview Preparedness: Scheduled video call to align on Zenith's technical architecture, safety thresholds, and program goals."
    )
    
    # Right Column: Timeline Card
    pdf.draw_card(143, 38, 139, 152, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=4)
    pdf.draw_badge(150, 44, 'DEVELOPMENT ROADMAP', bg_color=(5, 150, 105), text_color=(255, 255, 255), width=48, height=7, font_size=8)
    
    pdf.set_xy(150, 55)
    pdf.set_font(pdf.get_font_name(True), 'B', 16) # Increased from 14 to 16
    pdf.set_text_color(15, 23, 42)
    pdf.cell(125, 6, 'Key Execution Milestones', 0, 1)
    
    # Draw vertical timeline indicator line
    pdf.set_draw_color(79, 70, 229) # Indigo 600
    pdf.set_line_width(0.4)
    pdf.line(155, 76, 155, 172)
    
    # Milestones data
    milestones = [
        ("Phase 1: Program & Interview Prep", "Complete the Deep Bio founder interview, finalize research targets, and configure entities.", 70), # Adjusted y positions slightly to account for text size
        ("Phase 2: Preclinical In-Vitro Validation", "Synthesize predicted cocktails and run safety assays on primary patient cells.", 108),
        ("Phase 3: Seed Round & IND Enabler", "Raise a $1.5M seed round to compile preclinical safety data and initiate IND filing.", 146)
    ]
    
    for title, desc, y_pos in milestones:
        # Draw node circle
        pdf.set_fill_color(79, 70, 229)
        pdf.ellipse(153.2, y_pos + 1.2, 3.6, 3.6, 'F')
        
        # Outline circle for premium glow effect
        pdf.set_draw_color(224, 231, 255) # Indigo 100
        pdf.set_line_width(1)
        pdf.ellipse(152, y_pos, 6, 6, 'D')
        
        pdf.set_xy(162, y_pos)
        pdf.set_font(pdf.get_font_name(True), 'B', 12) # Increased from 10.5 to 12
        pdf.set_text_color(15, 23, 42)
        pdf.cell(115, 5, title, 0, 1)
        
        pdf.set_x(162)
        pdf.set_font(pdf.get_font_name(), '', 11) # Increased from 9.5 to 11
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(115, 5.0, desc) # Increased line height from 4.5 to 5.0
        
    # Save Presentation
    pdf.output(pdf_path)
    print(f"Visual pitch deck successfully compiled at: {pdf_path}")
    return pdf_path

if __name__ == '__main__':
    generate_deck()
