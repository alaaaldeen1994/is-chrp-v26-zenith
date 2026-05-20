content = open('index.html', encoding='utf-8', errors='replace').read()

# The corruption: the right panel HTML was injected inside a <div class="legend-item">
# Replace the corrupted section with correct HTML

bad = '''                    <div class="legend-item">
        <!-- RIGHT: AI PROTOCOL DISCOVERY PANEL -->'''

good = '''                    <div class="legend-item">
                        <div class="swatch" style="background: #6366f1; width:8px; height:8px; border-radius:2px; box-shadow: 0 0 8px #6366f1;"></div>
                        <span class="text-[8px]">DAPI (Nuclear DNA)</span>
                    </div>

                </div>

            </div>

        </div>

        <!-- RIGHT: AI PROTOCOL DISCOVERY PANEL -->'''

if bad in content:
    content = content.replace(bad, good, 1)
    open('index.html', 'w', encoding='utf-8').write(content)
    print('Fixed corruption!')
else:
    print('Pattern not found, trying with CRLF...')
    bad2 = bad.replace('\n', '\r\n')
    if bad2 in content:
        content = content.replace(bad2, good, 1)
        open('index.html', 'w', encoding='utf-8').write(content)
        print('Fixed (CRLF)!')
    else:
        print('Still not found')
        # Show what IS there
        idx = content.find('<!-- RIGHT: AI PROTOCOL DISCOVERY PANEL -->')
        print(repr(content[idx-200:idx+50]))
