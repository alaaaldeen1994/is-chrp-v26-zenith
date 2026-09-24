import os

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
with open(os.path.join(base, 'index.html'), encoding='utf-8', errors='ignore') as f:
    content = f.read()

idx = content.find('id="mob-nav"')
if idx != -1:
    print(content[idx:idx+400])
else:
    print("Not found")
