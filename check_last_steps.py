import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

brain_dir = r"C:\Users\alaaa\.gemini\antigravity\brain"
ids = [
    ("98934553-9f87-4863-9d05-9ecd22974726", "Technical_catalog_updater"),
    ("48f70a88-3d8d-4c7f-b69e-4c4fb91d8acb", "HTML_Audit_Researcher"),
    ("0d1f5837-b87c-49d5-a2ba-c7538bd5d7f2", "Discovery_engine_code_researcher"),
    ("c5711a42-4abb-4561-9c11-402faac5e91b", "Frontend_Code_Auditor")
]

for sub_id, name in ids:
    print(f"\n================================================================================")
    print(f"SUBAGENT: {name} ({sub_id})")
    print(f"================================================================================")
    path = os.path.join(brain_dir, sub_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(path):
        print("No transcript")
        continue
    
    steps = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                steps.append(json.loads(line))
            except Exception:
                pass
                
    print(f"Total steps: {len(steps)}")
    for s in steps[-5:]:
        print(f"Step {s.get('step_index')} (Source: {s.get('source')}, Type: {s.get('type')}, Status: {s.get('status')})")
        if s.get("content"):
            content = s.get("content")
            if len(content) > 300:
                print(f"  Content: {content[:150]} ... [TRUNCATED] ... {content[-150:]}")
            else:
                print(f"  Content: {content}")
        if s.get("tool_calls"):
            print("  Tool calls:")
            for tc in s["tool_calls"]:
                print(f"    - {tc.get('name')}: {tc.get('args')}")
