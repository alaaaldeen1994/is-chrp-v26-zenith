import os

log_path = "server_log.txt"
if os.path.exists(log_path):
    # Try reading as UTF-16LE, then fallback
    try:
        with open(log_path, 'r', encoding='utf-16') as f:
            print(f.read())
    except Exception as e:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            print(f.read())
else:
    print("Log file not found.")
