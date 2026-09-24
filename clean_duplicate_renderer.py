import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
js_path = os.path.join(base, 'js', 'script.js')

with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

dup_block = """        ctx.restore();
    },
        // v26.5: High-Fidelity "Granulation" Rendering (Sphere Effect)
        // Matches user reference: Glossy, volumetrically shaded spheres
        const type = agent.type;
        const color = CONFIG.colors[type];

        ctx.save();
        ctx.translate(x, y);

        // 1. Base Sphere Gradient (3D look)
        const grad = ctx.createRadialGradient(-size * 0.3, -size * 0.3, size * 0.1, 0, 0, size);
        // Highlight (Top-Left)
        grad.addColorStop(0, '#ffffff');
        // Body Color (Lighter center)
        grad.addColorStop(0.2, `hsl(${color.h}, ${color.s}%, ${Math.min(100, color.l + 20)}%)`);
        // Core Color
        grad.addColorStop(0.5, `hsl(${color.h}, ${color.s}%, ${color.l}%)`);
        // Shadow (Edges)
        grad.addColorStop(1, `hsl(${color.h}, ${color.s}%, ${Math.max(0, color.l - 20)}%)`);

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(0, 0, size, 0, Math.PI * 2);
        ctx.fill();

        // 2. Specular Reflection (Glossy "Wet" Look)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.beginPath();
        ctx.ellipse(-size * 0.3, -size * 0.35, size * 0.3, size * 0.15, -Math.PI / 4, 0, Math.PI * 2);
        ctx.fill();

        // 3. Internal "Granulation" Texture (Subtle dots inside)
        if (size > 3) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
            for (let i = 0; i < 3; i++) {
                const gx = (Math.random() - 0.5) * size * 1.0;
                const gy = (Math.random() - 0.5) * size * 1.0;
                ctx.beginPath();
                ctx.arc(gx, gy, size * 0.15, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        ctx.restore();
    },"""

clean_block = """        ctx.restore();
    },"""

if dup_block in content:
    content = content.replace(dup_block, clean_block)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Cleaned duplicate renderer code in js/script.js!")
else:
    print("Duplicate block not found")

res = subprocess.run(['node', '-c', js_path], capture_output=True, text=True)
print("Node syntax check exit code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("🎉 SYNTAX 100% PERFECT! 0 ERRORS IN js/script.js!")
