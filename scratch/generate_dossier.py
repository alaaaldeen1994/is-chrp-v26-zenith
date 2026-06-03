import os
from datetime import datetime
from fpdf import FPDF

class BriefingPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_margins(15, 15, 15)
        
        # Load premium custom fonts
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
        if self.has_custom_font:
            return 'Outfit'
        return 'Helvetica'

    def header(self):
        # Header background banner (Slate 950)
        self.set_fill_color(11, 15, 25) 
        self.rect(0, 0, 210, 36, 'F')
        
        # Decorative colored indicator line
        self.set_fill_color(79, 70, 229) # Indigo
        self.rect(0, 34, 210, 2, 'F')
        
        # Title text inside banner
        self.set_text_color(255, 255, 255)
        self.set_font(self.get_font_name(), 'B', 14)
        self.set_xy(15, 10)
        self.cell(0, 6, 'NILUS LAB  |  DEEP BIO INTERVIEW DOSSIER', 0, 1, 'L')
        
        self.set_font(self.get_font_name(), '', 9.5)
        self.set_text_color(148, 163, 184) # Light slate
        self.set_x(15)
        self.cell(0, 4, f'HomeLab Selection Briefing  -  Generated: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'L')
        
        # Reset colors and positions for main content
        self.set_text_color(15, 23, 42)
        self.set_y(44)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.get_font_name(), '', 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f'Nilus Lab Team Confidential  |  Deep Bio Interview Pack  |  Page {self.page_no()}', 0, 0, 'C')

    def draw_card(self, x, y, w, h, bg_color=(255, 255, 255), border_color=(226, 232, 240), r=3):
        self.set_fill_color(*bg_color)
        if border_color:
            self.set_draw_color(*border_color)
            self.set_line_width(0.3)
            style = 'DF'
        else:
            style = 'F'
        self.rect(x, y, w, h, style, round_corners=True, corner_radius=r)

    def section_header(self, label):
        self.ln(5)
        self.set_font(self.get_font_name(), 'B', 12)
        self.set_text_color(79, 70, 229) # Indigo
        self.cell(0, 8, label, 'B', 1, 'L')
        self.ln(2)

    def text_block(self, text):
        self.set_font(self.get_font_name(), '', 10)
        self.set_text_color(71, 85, 105) # Slate 600
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bold_label(self, label, text):
        self.set_font(self.get_font_name(), 'B', 10)
        self.set_text_color(15, 23, 42) # Slate 900
        self.write(5.5, label + ": ")
        self.set_font(self.get_font_name(), '', 10)
        self.set_text_color(71, 85, 105)
        self.write(5.5, text + "\n")
        self.ln(1)

def build_dossier():
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    pdf_path = os.path.join(reports_dir, "Nilus_Lab_Deep_Bio_Accelerator_Dossier.pdf")
    
    pdf = BriefingPDF()
    pdf.add_page()
    
    # ----------------------------------------------------
    # Selection Card (Top highlights)
    # ----------------------------------------------------
    pdf.draw_card(15, 42, 180, 42, bg_color=(255, 248, 248), border_color=(254, 202, 202), r=4) # Rose 50 background
    
    pdf.set_xy(20, 46)
    pdf.set_font(pdf.get_font_name(), 'B', 11)
    pdf.set_text_color(225, 29, 72) # Rose Red
    pdf.cell(0, 6, 'INVITATION DETAILED: DEEP BIO ACCELERATOR FOUNDER INTERVIEW', 0, 1)
    
    pdf.set_x(20)
    pdf.set_font(pdf.get_font_name(), '', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(170, 5, 'Invitation received from the Accelerator Success Team at HomeLab (Powered By LabFellows) for the Founder Interview. Focus indicates Launch Track parameter alignment ($0M - $2M funding targets).')
    
    pdf.set_x(20)
    pdf.ln(1.5)
    pdf.set_font(pdf.get_font_name(), 'B', 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 5, 'Host: HomeLab Team (startup@homelab.com)  |  Format: 30-Min Video Call (All Co-founders Required)', 0, 1)
    
    pdf.set_y(90)
    
    pdf.section_header('1. Executive Summary & Value Proposition')
    pdf.text_block(
        "Nilus Lab is commercializing high-impact science to reverse cardiac ageing without tumor risk (oncogene-free). "
        "Our proprietary platform, Zenith v28.0, leverages a deep foundation manifold trained on 500,000+ single cardiac cells "
        "from the Human Cell Atlas (HCA) and the PERIHEART dataset. By utilizing variational autoencoders (scVI) and "
        "in-silico modeling & simulation tools, Zenith identifies combinatorial gene networks that restore youthful "
        "chromatin profiles and contractility in senescent cells, moving biology out of the lab and into the clinic."
    )
    
    pdf.section_header('2. Technology & Platform Validation (Traction)')
    pdf.bold_label('In-Silico Modeling', 'Trained on 500k integrated cells across 4,908 Highly Variable Genes (HVGs) using scVI deep learning to compress 50GB matrices into 53.7MB neural weights.')
    pdf.bold_label('Epigenetic Reset', 'Achieved a deterministic -11.9 year epigenetic age reversal in mature cells verified via molecular clocks.')
    pdf.bold_label('Safety Gating', 'Built-in safety ceilings automatically filter out oncogenes and restrict dedifferentiation to protect functional cell identity.')
    pdf.bold_label('AF3 Valency Audit', 'Integrates automated AlphaFold 3 structured motifs to verify target binding affinity (e.g., POU5F1-SOX2 complex).')

    pdf.section_header('3. Competitive Landscape')
    pdf.bold_label('Retro Bio & Altos Labs', 'Focus on broad, systemic rejuvenation which requires hundreds of millions in funding. Nilus targets tissue-specific (cardiac) indications with lean, computational efficiency.')
    pdf.bold_label('Turn Biotechnologies', 'Utilizes mRNA-based epigenetic restoration but focuses on dermatology and skin indications. Nilus is optimized specifically for the cardiac lineage.')
    pdf.bold_label('The Nilus Edge', 'In-silico dosage networks predict transient transcription factor windows (e.g., 2h ON / 21h OFF) to resolve oncogene and cell drift risks before lab synthesis.')

    # ----------------------------------------------------
    # PAGE 2: Interview Prep Guidelines
    # ----------------------------------------------------
    pdf.add_page()
    
    pdf.section_header('4. Founder Interview Preparation Guide (Julio de Unamuno IV Focus)')
    pdf.text_block(
        "The Founder Interview is a highly focused 30-minute video call with Julio de Unamuno IV and the HomeLab team. "
        "Julio\'s background is centered on bringing high-impact science out of the lab and into the market. Key preparation points:"
    )
    
    pdf.bold_label('In-Silico to Wetlab Transition', 'Julio values in-silico modeling and simulations (Discovery Studio, Maestro). Be prepared to explain how Zenith\'s predictions directly guide your wetlab assay setups.')
    pdf.bold_label('Market indications & TAM', 'Position Nilus against the $50B longevity market. Initial clinical focus is on cardiomyopathy and age-induced heart failure, productized as an out-licensing platform for pharma.')
    pdf.bold_label('Competition & Barriers', 'Demonstrate how Nilus bypasses Altman-style reprogramming risks (oncogenesis, cell drift) computationally, creating strong IP and high safety barriers compared to Altos/Retro.')
    pdf.bold_label('Team Chemistry & Dynamics', 'Since all co-founders are required to join, show the interdisciplinary synergy across computation (VAE architectures), systems engineering, and molecular biology.')
    pdf.bold_label('Accelerator Goals', 'Secure next round of funding ($0M - $2M Launch Track parameters), leverage HomeLab lab networks for early animal trials, and target a cohort presentation at the BIO 2026 Innovation Summit in San Diego.')

    pdf.section_header('5. HomeLab Contact & Follow-up Details')
    pdf.text_block(
        "The video call is scheduled using the booking link in the invite. In case of schedule shifts or coordinator follow-ups, "
        "the Accelerator Success Team coordinates via HomeLab Powered By LabFellows:\n"
        "  - Email contact: startup@homelab.com\n"
        "  - Tel contact: +1 (833) 452-2677 ext. 500\n"
        "  - HomeLab homebase website links local tools and preparation documents."
    )
    
    pdf.output(pdf_path)
    print(f"Briefing dossier successfully compiled at: {pdf_path}")
    return pdf_path

if __name__ == '__main__':
    build_dossier()
