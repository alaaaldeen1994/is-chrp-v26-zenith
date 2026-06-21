import re
import os

def update_file(filepath, replacements):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        print(f"Successfully updated: {filepath}")
        return True
    else:
        print(f"No changes made to: {filepath}")
        return False

def main():
    workspace_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"
    
    # Define file-specific replacements to maintain exact semantics
    
    # 1. technical_catalog.html
    repl_catalog = [
        (r"167\.6M", "500M"),
        (r"167,600,000", "500,000,000"),
        (r"285 Million", "500 Million"),
        (r"285,420,000", "500,000,000"),
        (r"285M", "500M"),
        (r"0\.285 Billion", "0.5 Billion"),
        (r"~285", "~500"),
        (r"ULTRA-~500M", "ULTRA-500M"),
    ]
    update_file(os.path.join(workspace_dir, "technical_catalog.html"), repl_catalog)
    
    # 2. about.html
    repl_about = [
        (r"285\.4 Million parameter", "500 Million parameter"),
        (r"285M", "500M"),
    ]
    update_file(os.path.join(workspace_dir, "about.html"), repl_about)
    
    # 3. 3d_view.html
    repl_3d = [
        (r"167\.6M Param", "500M Param"),
    ]
    update_file(os.path.join(workspace_dir, "3d_view.html"), repl_3d)
    
    # 4. discovery_mockup.html
    repl_mockup = [
        (r"285\.4M Architecture", "500M Architecture"),
    ]
    update_file(os.path.join(workspace_dir, "discovery_mockup.html"), repl_mockup)
    
    # 5. evidence.html
    repl_evidence = [
        (r"0\.285", "0.500"),
    ]
    update_file(os.path.join(workspace_dir, "evidence.html"), repl_evidence)
    
    # 6. pilot_dashboard.html
    repl_pilot = [
        (r"167\.6M GOLD", "500M GOLD"),
        (r"167\.6M parameter", "500M parameter"),
    ]
    update_file(os.path.join(workspace_dir, "pilot_dashboard.html"), repl_pilot)
    
    # 7. regulatory.html
    repl_regulatory = [
        (r"167\.6M parameter", "500M parameter"),
    ]
    update_file(os.path.join(workspace_dir, "regulatory.html"), repl_regulatory)
    
    # 8. whitepaper.html
    repl_whitepaper = [
        (r"167\.6M parameter", "500M parameter"),
        (r"167\.6M", "500M"),
        (r"285\.4 Million parameter", "500 Million parameter"),
    ]
    update_file(os.path.join(workspace_dir, "whitepaper.html"), repl_whitepaper)

if __name__ == "__main__":
    main()
