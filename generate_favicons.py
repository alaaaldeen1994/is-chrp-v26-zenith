from PIL import Image
import os

def generate_icons(source_path):
    if not os.path.exists(source_path):
        print(f"Error: {source_path} not found.")
        return

    try:
        img = Image.open(source_path).convert("RGBA")
        
        # Standard Favicon Sizes
        sizes = [16, 32, 48, 180, 192, 512]
        
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            output_name = f"favicon-{size}x{size}.png"
            resized.save(output_name)
            print(f"Generated {output_name}")
            
        # specifically for apple-touch-icon
        img.resize((180, 180), Image.Resampling.LANCZOS).save("apple-touch-icon.png")
        print("Generated apple-touch-icon.png")

        # Create a real favicon.ico (multi-size)
        img.save("favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
        print("Generated favicon.ico (multi-resolution)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_icons("logo_transparent.png")
