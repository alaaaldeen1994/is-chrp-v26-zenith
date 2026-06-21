import os

def update_files():
    target_dir = '.'
    extensions = ['.html', '.js', '.py', '.md']
    count = 0
    
    for root, dirs, files in os.walk(target_dir):
        if any(skip in root for skip in ['.git', '.venv', '__pycache__', 'models']):
            continue
            
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    continue
                    
                new_content = content.replace('2', '2').replace('2,000,000', '2,000,000')
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated {path}")
                    count += 1
    print(f"Total files updated: {count}")

if __name__ == '__main__':
    update_files()
