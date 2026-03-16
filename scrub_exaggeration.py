import glob

replacements = {
    # Novel Design -> Calculated Vector
    '"UNCATEGORIZED PROTOCOL"': '"UNCATEGORIZED PROTOCOL"',
    'UNCATEGORIZED PROTOCOL': 'UNCATEGORIZED PROTOCOL',
    'computed trajectory': 'computed trajectory',
    
    # Identified -> Computed / Calculated
    'Zenith computed': 'Zenith computed',
    'optimal trajectory computed': 'optimal trajectory computed',
    'Optimal Protocol Computed': 'Optimal Protocol Computed',
    'Zenith-calculated': 'Zenith-calculated',
    
    # Discovery -> Analysis / Calculation
    'Scientific Analysis: We calculated': 'Scientific Analysis: We calculated',
    'AI analysis': 'AI analysis',
    'AI Protocol calculation': 'AI Protocol calculation',
    'computed factor cocktails': 'computed factor cocktails',
    'The Neural SDE optimization computed a robust': 'The Neural SDE optimization computed a robust',
    
    # Found -> Calculated
    'Zenith calculated': 'Zenith calculated'
}

files_to_check = glob.glob('**/*.html', recursive=True) + \
                 glob.glob('**/*.md', recursive=True) + \
                 glob.glob('**/*.js', recursive=True) + \
                 glob.glob('**/*.py', recursive=True)

for file_path in files_to_check:
    if "clean_up" in file_path or "fix_" in file_path or file_path.startswith("."):
        continue
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for old, new in replacements.items():
            new_content = new_content.replace(old, new)
            
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Cleaned exaggeration in {file_path}")
    except Exception as e:
        pass

print("Cleanup complete.")
