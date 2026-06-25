import os
import shutil

def main():
    print("=== STARTING WEBSITE CASE STUDY UPGRADES ===")
    
    # 1. Copy the high-fidelity 3D structure image to the assets folder
    src_img = "osk_3d.png"
    dest_img = os.path.join("assets", "osk_3d.png")
    if os.path.exists(src_img):
        try:
            shutil.copy(src_img, dest_img)
            print(f"Successfully copied {src_img} to {dest_img}")
        except Exception as e:
            print(f"Error copying image: {e}")
    else:
        print(f"Warning: Source image {src_img} not found.")

    # 2. Define files and their replacements
    replacements = {
        "profile.html": [
            # Case Study 02 updates
            ("new test 2.png", "osk_3d.png"),
            ("Manifold-12", "Manifold-11.9"),
            ("Reverse biological age by 12 years. Strictly maintain ESI above 95%.", "Reverse biological age by 11.9 years. Strictly maintain ESI above 99%."),
            ('0.61 <span class="text-blue-600 text-[10px] font-bold">ipTM</span>', '0.80 <span class="text-blue-600 text-[10px] font-bold">ipTM</span>'),
            ('0.61 ipTM', '0.80 ipTM'),
            ('>95%', '>99%')
        ],
        "technical_catalog.html": [
            ("ipTM: 0.61", "ipTM: 0.80"),
            ('0.61</div>', '0.80</div>')
        ],
        "whitepaper.html": [
            ("ipTM 0.61", "ipTM 0.80")
        ],
        "v26_clinical_report.html": [
            ("0.61 (Confident)", "0.80 (Very High)")
        ],
        "v28_clinical_report.html": [
            ("0.61 (Confident)", "0.80 (Very High)")
        ],
        "v29_clinical_report.html": [
            ("0.61 (Confident)", "0.80 (Very High)")
        ]
    }

    # 3. Apply replacements to each file
    for filename, file_reps in replacements.items():
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                original_content = content
                for old, new in file_reps:
                    content = content.replace(old, new)
                
                if content != original_content:
                    with open(filename, "w", encoding="utf-8", newline="\n") as f:
                        f.write(content)
                    print(f"Successfully updated {filename}")
                else:
                    print(f"No changes needed for {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        else:
            print(f"File {filename} not found.")

    print("\n=== WEBSITE UPGRADES COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
