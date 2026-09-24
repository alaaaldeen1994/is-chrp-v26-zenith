import subprocess

result = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
tracked_files = result.stdout.splitlines()

pyc_files = [f for f in tracked_files if f.endswith(".pyc") or "/__pycache__/" in f or f.startswith("__pycache__/")]
print(f"Found {len(pyc_files)} tracked pyc files.")

if pyc_files:
    # Remove them in batches
    for i in range(0, len(pyc_files), 50):
        batch = pyc_files[i:i+50]
        subprocess.run(["git", "rm", "--cached"] + batch)
    print("Successfully untracked all pyc files from git.")
