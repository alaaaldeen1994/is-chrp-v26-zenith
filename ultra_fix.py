import os

def ultra_fix():
    path = 'bridge_server.py'
    with open(path, 'rb') as f:
        data = f.read()
    
    # Identify the exact bytes of the bad line
    # result["protein_name"] = rec.get("fullName", {}).get("value") or \
    target = b'result["protein_name"] = rec.get("fullName", {}).get("value") or \\'
    # Replacement (join the lines)
    replacement = b'result["protein_name"] = rec.get("fullName", {}).get("value") or names.get("submissionNames", [{}])[0].get("fullName", {}).get("value")'
    
    if target in data:
        # We need to remove the following newline as well
        # Let's find the newline after target
        idx = data.find(target)
        eol = data.find(b'\n', idx)
        # Find next line start
        next_line_start = eol + 1
        # Find next line end
        next_line_end = data.find(b'\n', next_line_start)
        
        # Reconstruct
        new_data = data[:idx] + replacement + data[next_line_end:]
        
        # Sanitize non-ASCII in one pass
        sanitized = bytes([b if b < 128 else 32 for b in new_data])
        
        with open(path, 'wb') as f:
            f.write(sanitized)
        print("Surgically fixed bridge_server.py")
    else:
        print("Target bytes not found.")

if __name__ == "__main__":
    ultra_fix()
