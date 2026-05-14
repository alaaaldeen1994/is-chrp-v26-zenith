
import os
import sys

CHUNK_SIZE = 45 * 1024 * 1024  # 45MB chunks (Safe for GitHub)

def split_file(file_path):
    if not os.path.exists(file_path):
        print(f"âŒ File not found: {file_path}")
        return

    file_size = os.path.getsize(file_path)
    print(f"ðŸ“¦ Splitting {file_path} ({file_size / 1024 / 1024:.2f} MB)...")

    with open(file_path, 'rb') as f:
        part_num = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            
            part_name = f"{file_path}.part{part_num:03d}"
            with open(part_name, 'wb') as p:
                p.write(chunk)
            
            print(f"   Created {part_name}")
            part_num += 1
    
    print("âœ… Split complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        split_file(sys.argv[1])
    else:
        split_file("data/real/reprogramming_timecourse.h5ad")
        split_file("models/scvi_model_hca/adata.h5ad")
