from PIL import Image, ImageDraw
import os

def draw_dna_icon(size=512):
    # Deep slate background
    bg_color = (15, 23, 42) 
    # Teal colors
    teal_main = (45, 212, 191)
    
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded background
    padding = size // 10
    draw.rounded_rectangle([padding, padding, size-padding, size-padding], radius=size//6, fill=bg_color)
    
    import math
    points1 = []
    points2 = []
    center_x = size // 2
    height = size - (padding * 3)
    start_y = padding * 1.5
    amplitude = size // 6
    periods = 1.6 # Slighly more for helix look
    
    steps = 100
    for i in range(steps + 1):
        y = start_y + (i / steps) * height
        angle = (i / steps) * periods * 2 * math.pi
        x1 = center_x + math.sin(angle) * amplitude
        x2 = center_x - math.sin(angle) * amplitude
        points1.append((x1, y))
        points2.append((x2, y))

    # Draw Rungs
    for i in range(0, steps, 12):
        y = start_y + (i / steps) * height
        angle = (i / steps) * periods * 2 * math.pi
        x1 = center_x + math.sin(angle) * amplitude
        x2 = center_x - math.sin(angle) * amplitude
        op = int(255 * (0.6 + 0.4 * math.cos(angle)))
        draw.line([(x1, y), (x2, y)], fill=(45, 212, 191, op), width=size//35)

    # Draw Strands
    draw.line(points1, fill=teal_main, width=size//20, joint='curve')
    draw.line(points2, fill=(45, 212, 191, 150), width=size//20, joint='curve')
    
    # Save as master
    img.save("dna_master.png")
    
    # Overwrite the files that HTML already points to
    mapping = {
        "favicon.ico": [(16,16), (32,32), (48,48)],
        "favicon-16x16.png": (16,16),
        "favicon-32x32.png": (32,32),
        "favicon-48.png": (48,48),
        "favicon-48x48.png": (48,48),
        "favicon-180x180.png": (180,180),
        "favicon-192x192.png": (192,192),
        "favicon-512x512.png": (512,512),
        "apple-touch-icon.png": (180,180),
        "favicon.png": (192,192)
    }
    
    for filename, s_info in mapping.items():
        if filename.endswith(".ico"):
            img.save(filename, format="ICO", sizes=s_info)
        else:
            img.resize(s_info, Image.Resampling.LANCZOS).save(filename)
        print(f"Overwritten {filename} with sharp DNA icon.")

    print("Success: All institutional icons updated to DNA-only sharp versions.")

if __name__ == "__main__":
    draw_dna_icon()
