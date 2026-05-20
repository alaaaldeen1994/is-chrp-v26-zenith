content = open('index.html', encoding='utf-8', errors='replace').read()

# Find and remove the corrupted fragment
idx = content.find('\n                        <input id="bio-age-slider"')
if idx > 0:
    # This is the artifact input slider outside of its proper container
    # Find its context - check what's before it
    before = content[idx-200:idx]
    print('Before artifact:')
    print(repr(before[-80:]))
    
    # Find the end of this artifact section (next <!-- 3. Gene Lookup --> that's on its own)
    search_from = idx + 10
    end_markers = [
        '\n                <!-- 3. Gene Lookup',
        '\n\n                <!-- 3. Gene'
    ]
    end_idx = -1
    for m in end_markers:
        pos = content.find(m, search_from)
        if pos > 0:
            end_idx = pos
            print(f'Found end at {pos}')
            break
    
    if end_idx > 0:
        fragment = content[idx:end_idx]
        print('Fragment to remove:')
        print(repr(fragment))
        content = content[:idx] + '\n' + content[end_idx:]
        open('index.html', 'w', encoding='utf-8').write(content)
        print('DONE - cleaned!')
    else:
        print('No end found')
else:
    print('Already clean')
