import re

prompts = [
    "Identify transcription factors and direct epigenetic modulators to reverse biological age in regular ventricular cardiac myocytes by 2 years while blocking pluripotency induction.",
    "reverse biological age by 2years while blocking pluripotency",
    "cap at 9 years",
    "target of 15 years"
]

for p in prompts:
    m = re.search(r'(?:by|cap\s*(?:at|of|to)?|target\s*(?:of)?)\s*(\d+\.?\d*)\s*years?', p, re.IGNORECASE)
    if not m:
        m = re.search(r'(\d+\.?\d*)\s*years?', p, re.IGNORECASE)
    val = float(m.group(1)) if m else None
    print(f"Parsed: {val}y | Prompt: {p[:60]}...")
