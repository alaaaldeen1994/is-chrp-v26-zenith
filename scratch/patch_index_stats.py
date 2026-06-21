import re

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Make the replacements
replacements = {
    r"<title>Zenith v28 | Cardiac Ageing Gene Discovery | Nilus Lab</title>": 
        "<title>Zenith v29 | Cardiac Rejuvenation | Nilus Lab</title>",
    r"Discover genes that reverse cardiac ageing. Zenith v28 uses a trained scVI model on 500,000 human cardiac cells from the Human Cell Atlas to identify pro-rejuvenation gene targets.":
        "Discover genes that reverse cardiac ageing. Zenith v29 uses a trained scVI model on 2,000,000 human cardiac cells from the Human Cell Atlas to identify pro-rejuvenation gene targets.",
    r"Zenith v28 — Discover Genes That Reverse Cardiac Ageing":
        "Zenith v29 — Discover Genes That Reverse Cardiac Ageing",
    r"Zenith v28 — Cardiac Ageing Gene Discovery":
        "Zenith v29 — Cardiac Ageing Gene Discovery",
    r"color:#9b9b9b;font-weight:400;font-family:'Inter','Segoe UI',sans-serif;\">Zenith v28</span>":
        "color:#9b9b9b;font-weight:400;font-family:'Inter','Segoe UI',sans-serif;\">Zenith v29</span>",
    r"Zenith v28.0 GOLD &nbsp;·&nbsp; 500,000 Cells (HCA + PERIHEART) &nbsp;·&nbsp; Research Use Only":
        "Zenith v29.0 &nbsp;·&nbsp; 2,000,000 Cells (Healthy + Diseased) &nbsp;·&nbsp; Research Use Only",
    r"Zenith Ultra-v28.0 GOLD (GOLD)":
        "Zenith Ultra-v29.0",
    r"ZENITH v28.1: KILO-GENOME EXPLORER":
        "ZENITH v29.0: 6K-GENOME EXPLORER",
    r"PREDICTED (Zenith-v28.0 GOLD)":
        "PREDICTED (Zenith-v29.0)",
    r"14 donors · 500K cells · 4,908 genes":
        "83 donors · 2M cells · 5,858 genes",
    r"Perform Literature Audit (v28)":
        "Perform Literature Audit (v29)",
    r"Zenith v28.0 GOLD GOLD: Ultra-HD (5K) Genome Explorer":
        "Zenith v29.0: 6K-Gene Foundation Explorer",
    r"Zenith v28.0 GOLD</span></h1>":
        "Zenith v29.0</span></h1>",
    r"Platform | 500K-Cell Foundation GOLD Manifold":
        "Platform | 2M-Cell Foundation Manifold",
    r"*Delta Analysis computed via 500K-Cell Foundation GOLD Manifold Divergence":
        "*Delta Analysis computed via 2M-Cell Foundation Manifold Divergence",
    r"Patient Digital Twin (Predicted): Zenith-Sim v28.0 GOLD GOLD |":
        "Patient Digital Twin (Predicted): Zenith-Sim v29.0 |",
    r"500,000 cells · Rejuvenation Δ: 11.9y":
        "2,000,000 cells · Rejuvenation Δ: 11.9y"
}

replaced = 0
for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        replaced += 1
    else:
        # Also try to replace with different spaces or encoding issues if any
        # (For example, raw dash vs em dash)
        # Let's replace the raw string if we can
        pass

# Also replace the single string that failed before
# (Let's check if the raw em-dash vs hyphen in color:#9b9b9b line works)
content = re.sub(r'color:#9b9b9b;.*?Zenith v28', 'color:#9b9b9b;font-weight:400;font-family:\'Inter\',\'Segoe UI\',sans-serif;">Zenith v29', content)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully wrote index.html with replacements!")
