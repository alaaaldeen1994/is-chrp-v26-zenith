import os, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# 1. FIX js/script.js
script_path = os.path.join(base, 'js', 'script.js')
with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
    js_content = f.read()

js_orig = js_content

# Enhance BiosimEngine.resize
old_resize = """    resize() {
        const p = this.canvas.parentElement;
        const w = p.clientWidth;
        const h = p.clientHeight;
        // Don't zero out canvas when it's hidden (microscope mode)
        if (w > 0 && h > 0) {
            this.canvas.width = w;
            this.canvas.height = h;
        }
    },"""

new_resize = """    resize() {
        if (!this.canvas) this.canvas = document.getElementById('canvas');
        if (this.canvas && !this.ctx) this.ctx = this.canvas.getContext('2d');
        if (!this.canvas) return;
        const p = this.canvas.parentElement;
        if (!p) return;
        const w = p.clientWidth;
        const h = p.clientHeight;
        if (w > 0 && h > 0) {
            this.canvas.width = w;
            this.canvas.height = h;
        }
    },"""

js_content = js_content.replace(old_resize, new_resize)

# Enhance BiosimEngine.loop null canvas check
old_loop_start = """    loop() {
        try {
            // Physics & Logic
            // Simple N^2 repulsion for this demo (optimized with grid in full version)
            const w = this.canvas.width || 800;  // fallback when canvas hidden (microscope mode)
            const h = this.canvas.height || 600;"""

new_loop_start = """    loop() {
        try {
            if (!this.canvas) this.canvas = document.getElementById('canvas');
            if (this.canvas && !this.ctx) this.ctx = this.canvas.getContext('2d');
            if (!this.canvas || !this.ctx) {
                requestAnimationFrame(() => this.loop());
                return;
            }
            const w = this.canvas.width || 800;  // fallback when canvas hidden (microscope mode)
            const h = this.canvas.height || 600;"""

js_content = js_content.replace(old_loop_start, new_loop_start)

if js_content != js_orig:
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("SUCCESS: Enhanced BiosimEngine canvas null checks in js/script.js!")
else:
    print("WARNING: Target code in js/script.js not found")


# 2. FIX index.html
idx_path = os.path.join(base, 'index.html')
with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    idx_content = f.read()

idx_orig = idx_content

# Add class to canvas tag
idx_content = idx_content.replace('<canvas id="canvas"></canvas>', '<canvas id="canvas" class="w-full h-full block"></canvas>')

# Enhance enterSimulation to guarantee BiosimEngine init & boot
old_enter_sim_boot = """    // STEP 1: Force 2D canvas to have real dimensions (wait for CSS transition)
    setTimeout(function() {
        if (typeof BiosimEngine !== 'undefined') {
            BiosimEngine.resize();
            // Re-boot so agents exist and physics runs
            if (BiosimEngine.agents.length === 0) {
                BiosimEngine.boot();
            }
        }
    }, 200);"""

new_enter_sim_boot = """    // STEP 1: Force 2D canvas to have real dimensions & ensure engine is booted
    setTimeout(function() {
        if (typeof BiosimEngine !== 'undefined') {
            if (!BiosimEngine.isInitialized || !BiosimEngine.canvas) {
                BiosimEngine.init();
                BiosimEngine.isInitialized = true;
            }
            BiosimEngine.resize();
            if (!BiosimEngine.agents || BiosimEngine.agents.length === 0) {
                BiosimEngine.boot();
            }
        }
    }, 100);"""

idx_content = idx_content.replace(old_enter_sim_boot, new_enter_sim_boot)

if idx_content != idx_orig:
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(idx_content)
    print("SUCCESS: Updated index.html canvas tag and enterSimulation boot logic!")
else:
    print("WARNING: Target code in index.html not found")

print("DONE!")
