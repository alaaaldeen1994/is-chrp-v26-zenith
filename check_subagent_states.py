import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

brain_dir = r"C:\Users\alaaa\.gemini\antigravity\brain"
subagents = [
    {"id": "98934553-9f87-4863-9d05-9ecd22974726", "role": "Technical catalog updater"},
    {"id": "ca83bf3d-75ab-4ba4-ad0a-c9bc2205ea0c", "role": "Index HTML updater"},
    {"id": "48f70a88-3d8d-4c7f-b69e-4c4fb91d8acb", "role": "HTML Audit Researcher"},
    {"id": "0d1f5837-b87c-49d5-a2ba-c7538bd5d7f2", "role": "Discovery engine code researcher"},
    {"id": "788ad106-436b-4cc1-a00b-665dfd68cc2a", "role": "Backend Code Auditor"},
    {"id": "c5711a42-4abb-4561-9c11-402faac5e91b", "role": "Frontend Code Auditor"},
    {"id": "de8fc4d2-e5a3-4511-9f61-c351f80ab92e", "role": "Test File Auditor"}
]

for sa in subagents:
    print(f"\n================================================================================")
    print(f"SUBAGENT: {sa['role']} ({sa['id']})")
    print(f"================================================================================")
    path = os.path.join(brain_dir, sa['id'], ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(path):
        print("Transcript file does not exist.")
        continue
    
    steps = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                steps.append(json.loads(line))
            except Exception:
                pass
    
    print(f"Total steps: {len(steps)}")
    if not steps:
        continue
        
    # Get last 3 steps
    for step in steps[-3:]:
        print(f"\n--- Step {step.get('step_index')} ({step.get('source')} -> {step.get('type')}) status={step.get('status')} ---")
        content = step.get("content", "")
        if content:
            # Print first 200 and last 200 chars if long
            if len(content) > 600:
                print(content[:300] + "\n... [TRUNCATED] ...\n" + content[-300:])
            else:
                print(content)
        if step.get("tool_calls"):
            print("Tool calls:")
            for tc in step["tool_calls"]:
                print(f"  - {tc.get('name')}: {tc.get('args')}")
