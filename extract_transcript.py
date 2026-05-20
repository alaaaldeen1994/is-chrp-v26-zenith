import json
import os

log_path = r"C:\Users\alaaa\.gemini\antigravity\brain\ec76ea4b-f302-4404-b724-0db5d5cc5dbf\.system_generated\logs\overview.txt"
out_path = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\last_conversation_transcript.txt"

with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(out_path, 'w', encoding='utf-8') as out:
    for line in lines:
        try:
            data = json.loads(line)
            if 'content' in data and data['content']:
                role = "USER" if data.get('source') == "USER_EXPLICIT" else "AI"
                out.write(f"{role}:\n{data['content']}\n\n")
                out.write("-" * 40 + "\n\n")
        except:
            pass

print(f"Transcript saved to {out_path}")
