content = open('index.html', encoding='utf-8', errors='replace').read()

# Remove the corrupted fragment between lines ~3158-3168
bad = (
    '\n                <!-- 3. Gene Lookup -->\n'
    'input id="bio-age-slider" type="range" min="0" max="1" step="0.05" value="0.5" oninput="document.getElementById(\'bio-age-val\').textContent=this.value" class="w-full" style="accent-color:#f59e0b;">\r\n'
    '                    </div>\r\n'
    '                </div>\r\n'
    '\r\n'
    '                <!-- ═══════════════════════════════════════════════ -->\r\n'
    '\r\n'
    '\r\n'
    '\r\n'
    '\r\n'
    '\r\n'
)

if bad in content:
    content = content.replace(bad, '\n', 1)
    print('Cleaned!')
else:
    # Try character by character search
    idx = content.find('input id="bio-age-slider"')
    if idx > 0:
        # Find the line containing this - go back to previous newline
        start = content.rfind('\n', 0, idx)
        # Find forward to the next Gene Lookup comment
        end = content.find('<!-- 3. Gene Lookup', idx)
        if end > 0:
            print(f'Found artifact at chars {start}-{end}')
            print(repr(content[start:end+25]))
        else:
            print('Could not find end marker')
    else:
        print('bio-age-slider artifact not found - already clean')

open('index.html', 'w', encoding='utf-8').write(content)
