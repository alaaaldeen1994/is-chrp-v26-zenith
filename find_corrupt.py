content = open('index.html', encoding='utf-8', errors='replace').read()

# The corruption: RIGHT: AI PROTOCOL DISCOVERY PANEL is injected inside a legend-item div
# We need to:
# 1. Close the legend-item and its parents correctly
# 2. Then have the right panel

# Find the exact corruption
bad_start = content.find('                    <div class="legend-item">\n        <!-- RIGHT: AI PROTOCOL DISCOVERY PANEL -->')
if bad_start < 0:
    # Try with \r\n
    bad_start = content.find('                    <div class="legend-item">\r\n        <!-- RIGHT: AI PROTOCOL DISCOVERY PANEL -->')

if bad_start < 0:
    print('Pattern not found, searching...')
    idx = content.find('<!-- RIGHT: AI PROTOCOL DISCOVERY PANEL -->')
    print(f'Right panel at {idx}')
    print(repr(content[idx-300:idx]))
else:
    print(f'Found corruption at {bad_start}')
