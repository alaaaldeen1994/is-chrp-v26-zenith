import os
import subprocess

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"STDOUT: {res.stdout}")
    print(f"STDERR: {res.stderr}")
    return res.returncode == 0

# 1. Rename files using git
run_cmd("git mv index.html profile.html")
run_cmd("git mv discovery.html index.html")

# 2. Refactor references in other files
files_to_update = [
    "3d_view.html", "about.html", "api.html", "colony_microscopy_demo.html", 
    "contact.html", "index.html", "profile.html", "evidence.html", "how_it_works.html", 
    "legal.html", "login.html", "regulatory.html", 
    "scientific_qna.html", "structure.html", "technical_catalog.html", 
    "trials.html", "whitepaper.html", "js/auth_handler.js", "js/script.js"
]

for fpath in files_to_update:
    if not os.path.exists(fpath):
        print(f"File not found: {fpath}")
        continue
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # We do a two-stage replacement to avoid swap collision:
    # Replace "discovery.html" with a placeholder
    # Replace "index.html" with "profile.html"
    # Replace placeholder with "index.html"
    placeholder = "___DISCOVERY_HTML_PLACEHOLDER___"
    new_content = content.replace("discovery.html", placeholder)
    new_content = new_content.replace("index.html", "profile.html")
    new_content = new_content.replace(placeholder, "index.html")
    
    # In index.html (which is now the simulation lab):
    # If there is a redirect back to 'discovery.html', it should now redirect back to 'index.html'
    # The login.html redirect param redirect=discovery.html should become redirect=index.html
    new_content = new_content.replace("redirect=discovery.html", "redirect=index.html")
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated {fpath}")

# 3. Refactor bridge_server.py explicitly
with open("bridge_server.py", "r", encoding="utf-8") as f:
    server_code = f.read()

# Replace the FileResponse("discovery.html") and FileResponse("index.html") explicitly
# in the route handlers.
# Let's inspect where they are and replace them precisely.
# In serve_profile:
server_code = server_code.replace(
    'async def serve_profile():\n\n    return FileResponse("index.html")',
    'async def serve_profile():\n\n    return FileResponse("profile.html")'
)
server_code = server_code.replace(
    'async def serve_profile_html():\n\n    return FileResponse("index.html")',
    'async def serve_profile_html():\n\n    return FileResponse("profile.html")'
)

# In serve_discovery:
server_code = server_code.replace(
    'async def serve_discovery():\n\n    return FileResponse("discovery.html")',
    'async def serve_discovery():\n\n    return FileResponse("index.html")'
)
server_code = server_code.replace(
    'async def serve_discovery_html():\n\n    return FileResponse("discovery.html")',
    'async def serve_discovery_html():\n\n    return FileResponse("index.html")'
)

# In get_profile:
server_code = server_code.replace(
    'async def get_profile():\n\n    return FileResponse("index.html")',
    'async def get_profile():\n\n    return FileResponse("profile.html")'
)
server_code = server_code.replace(
    'async def get_profile_path():\n\n    return FileResponse("index.html")',
    'async def get_profile_path():\n\n    return FileResponse("profile.html")'
)

# In get_discovery:
server_code = server_code.replace(
    'async def get_discovery():\n\n    return FileResponse("discovery.html")',
    'async def get_discovery():\n\n    return FileResponse("index.html")'
)
server_code = server_code.replace(
    'async def get_discovery_path():\n\n    return FileResponse("discovery.html")',
    'async def get_discovery_path():\n\n    return FileResponse("index.html")'
)

with open("bridge_server.py", "w", encoding="utf-8") as f:
    f.write(server_code)
print("Updated bridge_server.py explicitly")
