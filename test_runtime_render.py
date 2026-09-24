import subprocess, os

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
js_path = os.path.join(base, 'js', 'script.js')

test_runner_js = os.path.join(base, 'test_runtime_harness.js')

harness_code = """
const fs = require('fs');
const code = fs.readFileSync('./js/script.js', 'utf-8');

const mockNode = {
    innerText: '',
    style: {},
    classList: { add: () => {}, remove: () => {} },
    addEventListener: () => {},
    setAttribute: () => {},
    appendChild: () => {}
};

// Mock browser globals
global.window = global;
global.window.addEventListener = () => {};
global.document = {
    addEventListener: () => {},
    getElementById: (id) => {
        if (id === 'canvas') {
            return {
                getContext: () => ({
                    save: () => {},
                    restore: () => {},
                    translate: () => {},
                    rotate: () => {},
                    beginPath: () => {},
                    moveTo: () => {},
                    lineTo: () => {},
                    bezierCurveTo: () => {},
                    arc: () => {},
                    ellipse: () => {},
                    closePath: () => {},
                    fill: () => {},
                    stroke: () => {},
                    fillRect: () => {},
                    createRadialGradient: () => ({ addColorStop: () => {} }),
                    createLinearGradient: () => ({ addColorStop: () => {} }),
                    parentElement: { clientWidth: 800, clientHeight: 600 }
                }),
                parentElement: { clientWidth: 800, clientHeight: 600 },
                width: 800,
                height: 600,
                addEventListener: () => {}
            };
        }
        return mockNode;
    },
    querySelector: () => mockNode,
    querySelectorAll: () => [mockNode],
    createElementNS: () => mockNode,
    createElement: () => mockNode,
    body: { classList: { add: () => {}, remove: () => {} } }
};
global.navigator = {};
global.localStorage = { getItem: () => null, setItem: () => {} };
global.location = { origin: 'http://localhost:3000', hash: '' };
global.requestAnimationFrame = (fn) => {};
global.fetch = async () => ({ ok: true, json: async () => ({ gene_symbols: Array(4908).fill('GENE') }) });

try {
    eval(code);
    console.log("Script loaded cleanly into environment.");

    if (typeof window.BiosimEngine !== 'undefined') {
        console.log("BiosimEngine exists. Calling BiosimEngine.init()...");
        window.BiosimEngine.init();
        console.log("BiosimEngine booted. Agents count:", window.BiosimEngine.agents.length);
        
        console.log("Testing single frame of loop()...");
        window.BiosimEngine.loop();
        console.log("BiosimEngine.loop() executed WITHOUT CRASH!");
    } else {
        console.error("ERROR: BiosimEngine is undefined!");
    }
} catch (err) {
    console.error("RUNTIME EXCEPTION DETECTED:");
    console.error(err);
}
"""

with open(test_runner_js, 'w', encoding='utf-8') as f:
    f.write(harness_code)

res = subprocess.run(['node', test_runner_js], capture_output=True, text=True, cwd=base)
print("Runtime Harness Output:")
print("Exit code:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)

if os.path.exists(test_runner_js):
    os.remove(test_runner_js)
