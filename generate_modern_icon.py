from PIL import Image
import os

def create_modern_favicon(source_path):
    if not os.path.exists(source_path):
        print(f"Error: {source_path} not found.")
        return

    try:
        img = Image.open(source_path).convert("RGBA")
        
        # Google specifically recommends a multiple of 48px. 192x192 is ideal for high-res.
        # We will create one called 'favicon.png' as the primary modern replacement.
        high_res = img.resize((192, 192), Image.Resampling.LANCZOS)
        high_res.save("favicon.png")
        print("Generated high-resolution favicon.png (192x192)")
        
        # Also create a 48x48 version specifically for Google's standard search snippet
        google_res = img.resize((48, 48), Image.Resampling.LANCZOS)
        google_res.save("favicon-48.png")
        print("Generated Google-optimized favicon-48.png")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_modern_favicon("logo_transparent.png")
