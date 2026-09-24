import os

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
path = os.path.join(base, 'profile.html')

with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

orig = content

# Replace hiding coreModules when logged in with showing coreModules
old_code = """                    if (coreModules) {
                        coreModules.classList.add('hidden');
                        coreModules.style.display = 'none';
                    }"""

new_code = """                    if (coreModules) {
                        coreModules.classList.remove('hidden');
                        coreModules.style.display = 'block';
                    }"""

content = content.replace(old_code, new_code)

if content != orig:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fixed profile.html so core modules & all details remain visible when logged in!")
else:
    print("WARNING: Target code block not found in profile.html")
