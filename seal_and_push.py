import os
import subprocess
import time

def run_command(command):
    print(f"Executing: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(result.stdout)
    return result.returncode

def main():
    model_path = "driftmlp.pt"
    
    # 1. Wait for model file to be fully written or appearing
    print("Waiting for driftmlp.pt to appear and be finalized...")
    while not os.path.exists(model_path):
        time.sleep(30)
    
    # Wait another minute to ensure file handles are closed
    time.sleep(60)
    
    print("Model found. Starting sealing process...")
    
    # 2. Split the model
    # Zenith Ultra is ~285MB, so we split into ~50MB chunks
    chunk_size = 50 * 1024 * 1024 # 50MB
    with open(model_path, "rb") as f:
        chunk_idx = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_name = f"{model_path}.part{chunk_idx:03d}"
            with open(chunk_name, "wb") as chunk_f:
                chunk_f.write(chunk)
            print(f"Created {chunk_name}")
            chunk_idx += 1

    # 3. Git operations
    print("Committing and pushing to GitHub...")
    run_command("git add .")
    run_command("git commit -m \"Phase 4: Zenith Ultra Deployment - 150k Cell Foundation Model [Academic Route]\"")
    run_command("git push origin main")

    print("DEPLOYMENT COMPLETE. ZENITH ULTRA IS LIVE.")

if __name__ == "__main__":
    main()
