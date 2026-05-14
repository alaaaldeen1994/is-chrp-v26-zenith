import os

def add_how_it_works_route():
    path = 'bridge_server.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_routes = """
@app.get("/how_it_works", response_class=HTMLResponse)
async def serve_how_it_works_root():
    return FileResponse("how_it_works.html")

@app.get("/how_it_works.html", response_class=HTMLResponse)
async def serve_how_it_works_file():
    return FileResponse("how_it_works.html")
"""
    
    # Insert after the pilot_dashboard routes (around line 2408)
    target = 'return FileResponse("pilot_dashboard.html")'
    
    if target in content:
        # Find the second occurrence of pilot_dashboard.html return to insert after the block
        parts = content.split(target)
        if len(parts) >= 3:
            new_content = parts[0] + target + parts[1] + target + new_routes + "".join(parts[2:])
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new_content)
            print("Added how_it_works routes to bridge_server.py")
        else:
            print("Could not find insertion point.")
    else:
        print("Target not found.")

if __name__ == "__main__":
    add_how_it_works_route()
