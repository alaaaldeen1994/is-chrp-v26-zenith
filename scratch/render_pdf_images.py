import sys
import os

pdf_path = r"C:\Users\alaaa\Downloads\Nilus_Lab_CurieBio_Executive_Dossier_2026.pdf"
output_dir = r"C:\Users\alaaa\.gemini\antigravity\brain\27071572-9862-405d-970f-576dffef8666"

try:
    import fitz # PyMuPDF
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    image_paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        img_name = f"pdf_preview_page_{i+1}.png"
        img_path = os.path.join(output_dir, img_name)
        pix.save(img_path)
        image_paths.append(img_path)
        print(f"Saved: {img_path}")
except Exception as e:
    print("PyMuPDF failed:", e)
    # Try pypdfium2 or pdf2image or pdf2png
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_path)
        for i, page in enumerate(pdf):
            image = page.render(scale=2).to_pil()
            img_name = f"pdf_preview_page_{i+1}.png"
            img_path = os.path.join(output_dir, img_name)
            image.save(img_path)
            print(f"Saved via pdfium: {img_path}")
    except Exception as e2:
        print("pdfium failed:", e2)
