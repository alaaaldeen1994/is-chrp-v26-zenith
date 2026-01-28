from PIL import Image
import numpy as np
import os

def remove_white_bg(input_path, output_path):
    print(f"Processing {input_path}...")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    try:
        img = Image.open(input_path).convert("RGBA")
        data = np.array(img)
        
        # Define white threshold (allow slight off-white)
        # 240 is a safe threshold for "white background"
        red, green, blue, alpha = data.T
        white_areas = (red > 240) & (green > 240) & (blue > 240)
        
        # Set alpha to 0 for white areas
        data[..., 3][white_areas.T] = 0
        
        img_new = Image.fromarray(data)
        
        # Crop transparent borders (autocrop)
        bbox = img_new.getbbox()
        if bbox:
            img_new = img_new.crop(bbox)
            print("Cropped empty margins.")
        else:
            print("Warning: Image is fully transparent after processing.")

        img_new.save(output_path)
        print(f"Success: Saved transparent logo to {output_path}")
        
    except Exception as e:
        print(f"Error processing image: {e}")

if __name__ == "__main__":
    # We use the file we copied in the previous step
    remove_white_bg("logo_v2.png", "logo_transparent.png")
