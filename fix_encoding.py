import os

def fix_file(path):
    with open(path, 'rb') as f:
        content = f.read()
    
    # Remove BOM if present
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
    
    # Replace CRLF with LF
    content = content.replace(b'\r\n', b'\n')
    # Replace solo CR with LF
    content = content.replace(b'\r', b'\n')
    
    # Remove non-ASCII
    sanitized = "".join(chr(b) if b < 128 else " " for b in content)
    
    with open(path, 'w', encoding='ascii', newline='\n') as f:
        f.write(sanitized)

if __name__ == "__main__":
    fix_file('bridge_server.py')
    print("Fixed bridge_server.py")
