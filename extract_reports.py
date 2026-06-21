import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

brain_dir = r"C:\Users\alaaa\.gemini\antigravity\brain"
output_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\subagent_reports"
os.makedirs(output_dir, exist_ok=True)

subagents = [
    {"id": "98934553-9f87-4863-9d05-9ecd22974726", "role": "Technical_catalog_updater"},
    {"id": "ca83bf3d-75ab-4ba4-ad0a-c9bc2205ea0c", "role": "Index_HTML_updater"},
    {"id": "48f70a88-3d8d-4c7f-b69e-4c4fb91d8acb", "role": "HTML_Audit_Researcher"},
    {"id": "0d1f5837-b87c-49d5-a2ba-c7538bd5d7f2", "role": "Discovery_engine_code_researcher"},
    {"id": "788ad106-436b-4cc1-a00b-665dfd68cc2a", "role": "Backend_Code_Auditor"},
    {"id": "c5711a42-4abb-4561-9c11-402faac5e91b", "role": "Frontend_Code_Auditor"},
    {"id": "de8fc4d2-e5a3-4511-9f61-c351f80ab92e", "role": "Test_File_Auditor"}
]

for sa in subagents:
    path = os.path.join(brain_dir, sa['id'], ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(path):
        print(f"Subagent {sa['role']} transcript not found.")
        continue
    
    steps = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                steps.append(json.loads(line))
            except Exception:
                pass
                
    if not steps:
        print(f"Subagent {sa['role']} has empty transcript.")
        continue
        
    last_msg = None
    for step in steps:
        if step.get("type") == "PLANNER_RESPONSE" and step.get("tool_calls"):
            for tc in step["tool_calls"]:
                if tc.get("name") == "send_message":
                    try:
                        args = tc.get("args", {})
                        if isinstance(args, str):
                            args = json.loads(args)
                        if "Message" in args:
                            last_msg = args["Message"]
                    except Exception:
                        pass
                        
    out_file = os.path.join(output_dir, f"{sa['role']}_report.txt")
    if last_msg:
        with open(out_file, "w", encoding="utf-8") as f_out:
            f_out.write(last_msg)
        print(f"Saved report for {sa['role']} (Sent Message) to {out_file}")
    else:
        # Save last model response
        last_resp = None
        for step in reversed(steps):
            if step.get("source") == "MODEL" and step.get("content"):
                last_resp = step["content"]
                break
        if last_resp:
            with open(out_file, "w", encoding="utf-8") as f_out:
                f_out.write(f"--- LAST MODEL RESPONSE ---\n{last_resp}")
            print(f"Saved last response for {sa['role']} (No Sent Message) to {out_file}")
        else:
            print(f"No message or model response found for {sa['role']}")
            
    # Check if the subagent has ended or is still executing
    last_step = steps[-1]
    is_done = False
    if last_step.get("source") == "MODEL" and not last_step.get("tool_calls"):
        is_done = True
    elif last_step.get("source") == "SYSTEM" and "completed" in last_step.get("content", "").lower():
        is_done = True
        
    print(f"  Status: Done={is_done}, Last Step Index={last_step.get('step_index')}, Type={last_step.get('type')}")
