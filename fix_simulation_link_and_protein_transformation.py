import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# 1. FIX DIRECT SIMULATION HASH LINK IN index.html
idx_path = os.path.join(base, 'index.html')
with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    idx_content = f.read()

idx_orig = idx_content

old_hash_check = """                // Auto-redirect to simulation lab if flag is set or hash is present
                if (window._isAuthenticated && (localStorage.getItem('auth_redirect') === 'sim' || window.location.hash === '#simulation')) {
                    localStorage.removeItem('auth_redirect');
                    setTimeout(() => {
                        if (typeof enterSimulation === 'function') enterSimulation();
                    }, 100);
                }"""

new_hash_check = """                // Auto-redirect to simulation lab if flag is set or hash is present
                if (localStorage.getItem('auth_redirect') === 'sim' || window.location.hash === '#simulation' || window.location.hash.includes('simulation')) {
                    localStorage.removeItem('auth_redirect');
                    setTimeout(() => {
                        const enterFn = window.enterSimulation || (typeof enterSimulation === 'function' ? enterSimulation : null);
                        if (enterFn) enterFn();
                        else document.body.classList.add('sim-mode');
                    }, 50);
                }"""

idx_content = idx_content.replace(old_hash_check, new_hash_check)

# Add immediate hash check right on DOMContentLoaded so #simulation works instantly without waiting for firebase
immediate_hash_script = """
    <script>
    // Immediate Hash Check for Direct Simulation Links (#simulation)
    function handleDirectSimulationLink() {
        if (window.location.hash === '#simulation' || window.location.hash.includes('simulation') || localStorage.getItem('auth_redirect') === 'sim') {
            document.body.classList.add('sim-mode');
            setTimeout(function() {
                const enterFn = window.enterSimulation || (typeof enterSimulation === 'function' ? enterSimulation : null);
                if (enterFn) enterFn();
            }, 100);
        }
    }
    window.addEventListener('hashchange', handleDirectSimulationLink);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', handleDirectSimulationLink);
    } else {
        handleDirectSimulationLink();
    }
    </script>
"""

if "handleDirectSimulationLink" not in idx_content:
    idx_content = idx_content.replace("</head>", immediate_hash_script + "\n</head>")

with open(idx_path, 'w', encoding='utf-8') as f:
    f.write(idx_content)

print("SUCCESS: Fixed direct #simulation link resolution in index.html!")

# 2. UPDATE js/script.js TO ANIMATE TRANSFORMATION FROM SPHERE TO 3D PROTEIN RIBBON
js_path = os.path.join(base, 'js', 'script.js')
with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    js_content = f.read()

js_orig = js_content

old_draw_cell_logic = """    drawCell(ctx, agent, x, y, size) {
        if (!agent.angle) agent.angle = (agent.id * 0.77) % (Math.PI * 2);
        agent.angle += 0.012; // Continuous 3D rotation

        if (this.mode === '3D_MOLECULAR') {
            this.drawUnifiedMolecular3D(ctx, agent, x, y, size * 2.2);
        } else {
            this.drawSphere2D(ctx, agent, x, y, size);
        }
    },"""

new_draw_cell_logic = """    drawCell(ctx, agent, x, y, size) {
        if (!agent.angle) agent.angle = (agent.id * 0.77) % (Math.PI * 2);
        agent.angle += 0.012; // Continuous 3D rotation

        // Animate Transformation: Morph from initial sphere state to full 3D protein ribbon by the end
        if (typeof agent.morphProgress === 'undefined') {
            agent.morphProgress = 0.0;
        }
        // Smoothly increase transformation progress over time up to 1.0 (100% protein structure)
        if (agent.morphProgress < 1.0) {
            agent.morphProgress += 0.005;
        }

        if (this.mode === '3D_MOLECULAR') {
            const morph = agent.morphProgress;
            ctx.save();
            // Blended opacity & scale morphing to 3D protein structure
            ctx.globalAlpha = 0.3 + 0.7 * morph;
            this.drawUnifiedMolecular3D(ctx, agent, x, y, size * (1.2 + 1.0 * morph));
            ctx.restore();
        } else {
            this.drawSphere2D(ctx, agent, x, y, size);
        }
    },"""

js_content = js_content.replace(old_draw_cell_logic, new_draw_cell_logic)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

print("SUCCESS: Added progressive sphere-to-protein 3D ribbon transformation to js/script.js!")

# Run Node syntax checks
res1 = subprocess.run(['node', '-c', js_path], capture_output=True, text=True)
print("js/script.js Node check exit code:", res1.returncode)
if res1.returncode != 0:
    print("Stderr:", res1.stderr)
