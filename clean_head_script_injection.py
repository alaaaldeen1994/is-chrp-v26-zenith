import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
idx_path = os.path.join(base, 'index.html')

with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Remove misplaced handleDirectSimulationLink from printWin HTML
content = content.replace("""    <script>
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
    </script>""", "")

content = content.replace("<' + 'script>window.onload = function() { window.print(); };<' + '/script>", "<script>window.onload = function() { window.print(); };</" + "script>")

# Place handleDirectSimulationLink script cleanly before firebase auth script
clean_sim_link_script = """
<script>
// Immediate Hash Check for Direct Simulation Links (#simulation)
function handleDirectSimulationLink() {
    if (window.location.hash === '#simulation' || window.location.hash.includes('simulation') || localStorage.getItem('auth_redirect') === 'sim') {
        document.body.classList.add('sim-mode');
        setTimeout(function() {
            const enterFn = window.enterSimulation || (typeof enterSimulation === 'function' ? enterSimulation : null);
            if (enterFn) enterFn();
        }, 80);
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

if "function handleDirectSimulationLink" not in content:
    content = content.replace("<script src=\"js/firebase_config.js\"></script>", "<script src=\"js/firebase_config.js\"></script>\n" + clean_sim_link_script)

with open(idx_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Cleaned up script tags in index.html!")

res = subprocess.run(['python', 'check_inline_scripts.py'], capture_output=True, text=True, cwd=base)
print("check_inline_scripts output:")
print(res.stdout)
