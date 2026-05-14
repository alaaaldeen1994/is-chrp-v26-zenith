"""
Clinical Digital Twin - PDF Report Generator
Generates professional research-grade PDF reports from simulation sessions
Uses fpdf2 for pure Python PDF generation without external dependencies
"""

import os
import io
import base64
from datetime import datetime
from typing import Dict, List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF

# OpenAI Integration
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    GPT_ENABLED = True
except:
    GPT_ENABLED = False
    client = None


def generate_population_chart(population_stats: Dict[str, int]) -> str:
    """Generate a base64-encoded bar chart of population statistics"""
    fig, ax = plt.subplots(figsize=(8, 4), facecolor='#0a0a0a')
    ax.set_facecolor('#0a0a0a')
    
    colors = {
        'SOMATIC': '#64748b',
        'IPSC': '#fbbf24',
        'CARDIO': '#fb7185',
        'NEURO': '#60a5fa',
        'TUMOR': '#ef4444'
    }
    
    cell_types = list(population_stats.keys())
    counts = list(population_stats.values())
    bar_colors = [colors.get(ct, '#888888') for ct in cell_types]
    
    ax.bar(cell_types, counts, color=bar_colors, edgecolor='white', linewidth=0.5)
    ax.set_ylabel('Cell Count', color='white', fontsize=11)
    ax.set_xlabel('Cell Type', color='white', fontsize=11)
    ax.set_title('Population Distribution', color='white', fontsize=13, fontweight='bold', pad=15)
    ax.tick_params(colors='white', labelsize=9)
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.2, color='white')
    
    # Save to temp file
    temp_path = os.path.join(os.path.dirname(__file__), "temp_chart.png")
    plt.tight_layout()
    plt.savefig(temp_path, format='png', dpi=150, facecolor='#0a0a0a', edgecolor='none')
    plt.close()
    
    return temp_path


def generate_scientific_narrative(session_data: Dict) -> Dict[str, str]:
    """
    Use GPT-4o to generate scientific narrative sections
    Returns: {introduction, methods, results, discussion}
    """
    if not GPT_ENABLED or not client:
        return {
            "introduction": "This clinical digital twin simulation models cellular reprogramming dynamics using stochastic gene regulatory networks.",
            "methods": "The simulation employed a 12-gene regulatory network with Hill kinetics to model cellular state transitions.",
            "results": f"The experiment generated {sum(session_data['population_stats'].values())} total cells with the distribution shown in Figure 1.",
            "discussion": "The observed dynamics align with expected reprogramming trajectories. Further optimization may improve yield."
        }
    
    try:
        # Prepare context
        interventions_str = ", ".join(session_data.get('interventions', [])) or "None"
        pop_str = ", ".join([f"{k}: {v}" for k, v in session_data['population_stats'].items()])
        
        prompt = f"""You are a senior research scientist writing a clinical report for a cellular reprogramming experiment.

**Experimental Details:**
- Run ID: {session_data.get('run_id', 'N/A')}
- Interventions Performed: {interventions_str}
- Final Population: {pop_str}
- Number of scVI Analyses: {len(session_data.get('scvi_analyses', []))}

Generate four concise sections for the scientific report:

1. **Introduction** (2-3 sentences): Context and objective
2. **Methods** (2-3 sentences): Computational approach and interventions
3. **Results** (3-4 sentences): Key findings from population data
4. **Discussion** (3-4 sentences): Scientific interpretation and implications

Use formal academic language. Be specific about the cell types and numbers observed.

Format your response as JSON:
{{"introduction": "...", "methods": "...", "results": "...", "discussion": "..."}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a computational biology expert writing scientific reports."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        import json
        narrative = json.loads(response.choices[0].message.content)
        return narrative
        
    except Exception as e:
        print(f"Warning: GPT-4o narrative generation failed: {e}")
        return {
            "introduction": "This report documents a computational cellular reprogramming experiment.",
            "methods": f"Interventions applied: {interventions_str}.",
            "results": f"Final population distribution: {pop_str}.",
            "discussion": "Results demonstrate expected cellular dynamics."
        }


class ClinicalReportPDF(FPDF):
    """Custom PDF class for clinical reports"""
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(30, 41, 59)
        self.cell(0, 10, 'Clinical Digital Twin Report', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, 'Computational Cellular Reprogramming Analysis', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Generated by IS-CHRP v27.0 GOLD | Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 41, 59)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.set_text_color(26, 26, 26)
        self.multi_cell(0, 5, body)
        self.ln()


def generate_clinical_report(session_data: Dict) -> str:
    """
    Main function to generate a clinical PDF report
    
    Args:
        session_data: Dictionary containing session information
    
    Returns:
        Path to generated PDF file
    """
    # Create reports directory
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate timestamp filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"clinical_report_{timestamp}.pdf"
    pdf_path = os.path.join(reports_dir, pdf_filename)
    
    # Generate chart
    chart_path = generate_population_chart(session_data['population_stats'])
    
    # Generate narrative
    narrative = generate_scientific_narrative(session_data)
    
    # Calculate total cells
    total_cells = sum(session_data['population_stats'].values())
    
    # Create PDF
    pdf = ClinicalReportPDF()
    pdf.add_page()
    
   # Metadata section
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(37, 99, 235)
    pdf.set_line_width(1)
    pdf.rect(10, pdf.get_y(), 190, 35, 'D')
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(30, 41, 59)
    
    metadata_y = pdf.get_y() + 5
    pdf.set_xy(15, metadata_y)
    pdf.cell(0, 5, f"Session ID: {session_data.get('session_id', 'Unknown')}", 0, 1)
    pdf.set_x(15)
    pdf.cell(0, 5, f"Run ID: {session_data.get('run_id', '#1')}", 0, 1)
    pdf.set_x(15)
    pdf.cell(0, 5, f"Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.set_x(15)
    bio_age_str = f"{session_data.get('bio_age', 0.5)*100:.1f}y" if session_data.get('bio_age') is not None else "N/A"
    pdf.cell(0, 5, f"Total Cells: {total_cells} | Model Mode: {session_data.get('model_mode', 'CLINICAL')} | Avg BioAge: {bio_age_str}", 0, 1)
    pdf.ln(10)
    
    # Introduction
    pdf.chapter_title('1. Introduction')
    pdf.chapter_body(narrative['introduction'])
    
    # Methods
    pdf.chapter_title('2. Materials and Methods')
    pdf.chapter_body(narrative['methods'])
    
    # Interventions
    if session_data.get('interventions'):
        pdf.set_fill_color(254, 243, 199)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(180, 83, 9)
        pdf.cell(0, 6, 'Experimental Interventions:', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(26, 26, 26)
        for intervention in session_data['interventions']:
            pdf.set_x(15)
            # Clean intervention text for latin-1 compatibility
            clean_intervention = intervention.encode('latin-1', 'ignore').decode('latin-1')
            pdf.cell(0, 5, f"  - {clean_intervention}", 0, 1)
        pdf.ln(5)
    
    # Results
    pdf.chapter_title('3. Results')
    pdf.chapter_body(narrative['results'])
    
    # Population chart
    pdf.chapter_title('3.1 Population Distribution')
    if os.path.exists(chart_path):
        pdf.image(chart_path, x=10, w=190)
        os.remove(chart_path)  # Clean up temp file
    pdf.ln(5)
    
    # Population table
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(60, 7, 'Cell Type', 1)
    pdf.cell(40, 7, 'Count', 1)
    pdf.cell(40, 7, 'Percentage', 1, 1)
    
    pdf.set_font('Arial', '', 9)
    for cell_type, count in session_data['population_stats'].items():
        percentage = (count / total_cells * 100) if total_cells > 0 else 0
        pdf.cell(60, 6, cell_type, 1)
        pdf.cell(40, 6, str(count), 1)
        pdf.cell(40, 6, f"{percentage:.1f}%", 1, 1)
    pdf.ln(5)
    
    # scVI analyses
    if session_data.get('scvi_analyses'):
        pdf.chapter_title('3.2 Transcriptomic Analysis (scVI)')
        scvi_count = len(session_data['scvi_analyses'])
        pdf.set_fill_color(219, 234, 254)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(29, 78, 216)
        pdf.cell(0, 6, f'High-Resolution Gene Expression Analyses Performed: {scvi_count}', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(26, 26, 26)
        pdf.multi_cell(0, 5, "Cells were expanded to high-dimensional transcriptomic space using a pre-trained variational autoencoder model on Human Cell ATLAS data.")
        pdf.ln(5)
    
    # Discussion
    pdf.chapter_title('4. Discussion')
    pdf.chapter_body(narrative['discussion'])
    
    # Footer note
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(0, 4, 'This report was automatically generated by the IS-CHRP v27.0 GOLD Clinical AI Bridge platform. The data represents computational simulation results from a high-fidelity cellular reprogramming model.')
    
    # Save PDF
    pdf.output(pdf_path)
    
    print(f"âœ… Clinical report generated: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    # Test report generation
    mock_data = {
        "session_id": "test_session_20260101",
        "run_id": "#1",
        "model_mode": "CLINICAL",
        "agents": [],
        "interventions": ["OSKM Transfection (Yamanaka)", "P53 Therapeutic Intervention"],
        "population_stats": {
            "SOMATIC": 45,
            "IPSC": 152,
            "CARDIO": 12,
            "NEURO": 8,
            "TUMOR": 0
        },
        "chart_data": {},
        "scvi_analyses": [
            {"timestamp": "2026-01-01", "cell_type": "IPSC", "top_genes": [], "summary": "Test"}
        ]
    }
    
    pdf_path = generate_clinical_report(mock_data)
    print(f"Test report saved to: {pdf_path}")



