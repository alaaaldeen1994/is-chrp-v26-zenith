import os
import re

def sanitize_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')
            
        # Replace common non-ASCII symbols with English equivalents
        text = text.replace('â€”', ' -- ')
        text = text.replace('â†’', ' -> ')
        text = text.replace('â”€', ' - ')
        text = text.replace('Â', '')
        
        # Strip all other non-ASCII characters BUT KEEP NEWLINES AND SPACES
        sanitized = "".join(i if (ord(i) < 128) else " " for i in text)
        
        # DO NOT use re.sub(r' +', ' ', sanitized) as it breaks Python indentation
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sanitized)
        print(f"Sanitized: {filepath}")
    except Exception as e:
        print(f"Failed to sanitize {filepath}: {e}")

files_to_sanitize = [
    'bridge_server.py',
    'index.html',
    'technical_catalog.html',
    'profile.html',
    'trials.html',
    'robotic_bridge.py',
    'dosage_optimization_engine.py',
    'af3_automation_bridge.py'
]

for f in files_to_sanitize:
    if os.path.exists(f):
        sanitize_file(f)
