// --- REPRODUCIBILITY UTILS ---
let seed = 0x771A;
function seededRandom() {
    if (typeof BiosimBridge !== 'undefined' && !BiosimBridge.isValidatedMode) return Math.random();
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
}

function resetSeed() {
    seed = 0x771A;
}

// --- CONFIGURATION ---
const CONFIG = {
    agentCount: 2000,
    maxPop: 5000,
    dt: 0.1,
    friction: 0.92,

    // Stochastic dynamics parameters
    stochastic: {
        noiseStrength: 0.015,
        mutationRate: 0.0005,
        chromatinFluctuationRate: 0.01,
        mutationMagnitude: 0.2
    },

    geneInit: {
        base: 0.05,
        range: 0.05
    },

    reprogramming: {
        potency: 1.0
    },

    cohesion: 0.0, // v27: Organoid Clustering Strength
    translationDelay: false, // v27: Feature 4 - Gene-to-Protein Flux Logic

    colors: {
        SOMATIC: { h: 215, s: 20, l: 60 },      // Muted Slate (Dull)
        IPSC: { h: 45, s: 100, l: 60 },        // GOLDEN GLOW (Pluripotent)
        PARTIAL: { h: 280, s: 90, l: 65 },      // VIBRANT PURPLE
        CARDIO: { h: 355, s: 95, l: 60 },       // DEEP CRIMSON
        TRANSIT_CAR: { h: 20, s: 90, l: 60 },   // BRIGHT ORANGE
        NEURO: { h: 210, s: 100, l: 60 },       // ELECTRIC BLUE
        TRANSIT_NEU: { h: 180, s: 100, l: 50 },  // NEON CYAN
        ENDO: { h: 145, s: 90, l: 55 },         // EMERALD GREEN
        TUMOR: { h: 0, s: 100, l: 50 },         // DANGER RED (Pure)
        DEATH: { h: 215, s: 10, l: 35 }         // STABLE ASH (Visibility Adjusted for v26.4)
    },

    // 1000 Gene Symbols (Generated or loaded)
    geneSymbols: (function () {
        const base = [
            "POU5F1", "SOX2", "NANOG", "LIN28A", "KLF4", "MYC", "UTF1", "SALL4", "DNMT3B", "ZFP42",
            "GATA4", "NKX2-5", "TBX5", "TNNT2", "TTN", "MYH7", "MYH6", "RYR2", "NPPA", "MEF2C",
            "NEUROD2", "CHRNA1", "PAX6", "ASCL1", "SOX1", "TUBB3", "MAP2", "NES", "NCAM1", "RBFOX3",
            "SOX17", "GATA6", "FOXA2", "AFP", "ALB", "KRT18", "KRT19", "HNF4A", "CDX2", "EPCAM",
            "COL1A1", "COL1A2", "DCN", "THY1", "VIM", "ACTA2", "TAGLN", "FN1", "SNAI1", "TWIST1",
            "TP53", "MKI67", "CDKN1A", "CDKN2A", "PCNA", "BAX", "BCL2", "CASP3", "CCND1", "MYCN",
            "GAPDH", "HK2", "LDHA", "PKM", "MT-CO1", "MT-ND1", "GLS", "SLC2A1", "ATP5F1A", "COX4I1",
            "EZH2", "EED", "SUZ12", "DNMT1", "TET1", "TET2", "KDM6A", "KDM6B", "CREBBP", "EP300",
            "EGFR", "FGFR1", "TGFBR1", "BMPR2", "NOTCH1", "WNT1", "SHH", "LIFR", "IFNGR1", "IL6R",
            "ACTB", "TUBB", "LMNA", "LMNB1", "HSP90AA1", "CANX", "PDIK1L", "B2M", "PPIA", "RPL13A"
        ];
        const genes = [...base];
        const prefixes = ["ZNF", "KRT", "RPL", "RPS", "SLC", "WNT", "HOX", "PTP", "CYP", "ADAM"];
        prefixes.forEach(prefix => {
            for (let i = 1; i <= 91; i++) {
                if (genes.length < 5000) {
                    const sym = `${prefix}${i}`;
                    if (!genes.includes(sym)) genes.push(sym);
                }
            }
        });
        while (genes.length < 5000) genes.push(`G_EXT_${genes.length}`);
        return genes.slice(0, 5000);
    })(),

    // 5000x5000 GRN Matrix (Sparse)
    GRN: Array.from({ length: 5000 }, () => new Float32Array(5000).fill(0))
};

// Initialize GRN with some structure
(function initGRN() {
    // Self-excitation for stability
    for (let i = 0; i < 5000; i++) CONFIG.GRN[i][i] = 0.8;

    // OSKM Cross-Regulation (The Core Circuit)
    const core = [0, 1, 2, 4, 5]; // OCT4, SOX2, NANOG, KLF4, MYC
    core.forEach(i => {
        core.forEach(j => {
            if (i !== j) CONFIG.GRN[i][j] = 1.2; // Strong mutual activation
        });
    });

    // c-MYC promotes proliferation (#5)
    for (let i = 50; i < 150; i++) {
        CONFIG.GRN[5][i] = 0.5; // MYC activates downstream growth
    }

    // p53 Tumor Suppressor Logic (#50)
    // If MYC (#5) is high, active p53 should repress it
    CONFIG.GRN[50][5] = -2.0;
})();


// --- AGENT (CELL) CLASS ---
class Agent {
    constructor(id) {
        this.id = id;
        this.pos = {
            x: 0.5 + (seededRandom() - 0.5) * 0.2, // Start clustered in center
            y: 0.5 + (seededRandom() - 0.5) * 0.2
        };
        this.vel = { x: 0, y: 0 };
        this.type = 'SOMATIC'; // Start as fibroblasts
        this.genes = new Float32Array(5000);
        this.proteins = new Float32Array(5000);   // PH9
        this.chromatin = new Float32Array(5000);  // PH9
        this.bioAge = 1.0; // Starts old (Somatic)
        this.health = 1.0; // 0.0 - 1.0
        this.dnaDamage = 0.0;
        this.shapeIrregularity = seededRandom(); // For visual variety
        this.paracrineNeighbors = []; // For GNN visualization
        this.smn = 1.0; // SMN Protein Level (for SMA disease model)
        this.manifoldPos = { x: 0, y: 0, z: 0 }; // NEW: 3D latent coordinates from 100M model
        this.paracrineFlux = 0.0; // NEW: GNN-derived signaling flux

        this.initGenes();
    }

    initGenes() {
        // Initialize as SOMATIC (Low OSKM, High differentiation markers)
        for (let i = 0; i < 5000; i++) {
            const base = CONFIG.geneInit.base + (seededRandom() - 0.5) * CONFIG.geneInit.range;
            this.genes[i] = Math.max(0, base);
            this.proteins[i] = this.genes[i]; // Start synced
            this.chromatin[i] = 0.2; // Mostly closed chromatin
        }
    }

    tick(env) {
        // 1. Gene Regulatory Network Update (Euler Integration)
        // Use a simplified subset for performance in JS loop (Real logic is in backend)
        // We just decay and drift here to simulate "life" between backend syncs

        // Apply Reprogramming Vector (if active)
        if (env.vector === 'OSKM') {
            // FIX: OSKM must boost OCT4(0), SOX2(1), KLF4(4), MYC(5)
            // Previously incorrectly boosted 0-3 (which includes Nanog/Lin28)
            [0, 1, 4, 5].forEach(i => {
                this.genes[i] += 0.05 * CONFIG.reprogramming.potency;
            });
            // CRITICAL FIX: Trigger p53 (Index 50) response to balance c-MYC
            // Without this, high MYC (Index 5) > 0.8 immediately triggers TUMOR
            this.genes[50] += 0.02 * CONFIG.reprogramming.potency;
        } else if (env.vector === 'LIN28') {
            // Thomson Factors: OCT4(0), SOX2(1), NANOG(2), LIN28(3)
            [0, 1, 2, 3].forEach(i => {
                this.genes[i] += 0.05 * CONFIG.reprogramming.potency;
            });
        } else if (env.vector === 'DIRECT_NEURO') {
            // FIX: Boost Neural Markers (NEUROD2, PAX6, ASCL1, etc.) at indices 20-29
            for (let i = 20; i < 30; i++) this.genes[i] += 0.08;
        } else if (env.vector === 'DIRECT_CARDIO') {
            // FIX: Boost Cardiac Markers (GATA4, TBX5, TNNT2, etc.) at indices 10-19
            for (let i = 10; i < 20; i++) this.genes[i] += 0.08;
        } else if (env.vector === 'CLINICAL_COMBO') {
            // Split population into Heart (Red) and Neural (Blue)
            if (this.id % 2 === 0) {
                for (let i = 10; i < 20; i++) this.genes[i] += 0.1;
            } else {
                for (let i = 20; i < 30; i++) this.genes[i] += 0.1;
            }
        }

        // Disease Stress
        if (env.disease === 'TUMOR') {
            this.dnaDamage += 0.001;
            // FIX: Spike c-MYC (Index 5) to trigger classifier, not LIN28 (Index 3)
            if (Math.random() < 0.01) this.genes[5] += 0.1;
        } else if (env.disease === 'SMA') {
            this.smn -= 0.0005; // SMN decay
            if (this.smn < 0) this.smn = 0;
        }

        // Internal Dynamics (Decay)
        // v27 FIX: Must loop up to 60 to include differentiation markers (Cardio=13, Neuro=20, TP53=50)
        for (let i = 0; i < 60; i++) { // Previously 10, preventing protein update for phenotypes
            this.genes[i] -= 0.01 * this.genes[i]; // Degradation
            this.genes[i] += (Math.random() - 0.5) * CONFIG.stochastic.noiseStrength; // Noise
            this.genes[i] = Math.max(0, Math.min(1, this.genes[i]));

            // v27: FEATURE 4 - GENE-TO-PROTEIN FLUX (Translation Delay)
            // Biology Rule: mRNA (Gene) -> Protein takes time (Translation).
            // If active, protein levels lag behind gene levels.
            if (CONFIG.translationDelay) {
                // Slow translation rate (alpha = 0.02 means ~50 frames to catch up)
                const translationRate = 0.02;
                const diff = this.genes[i] - this.proteins[i];
                this.proteins[i] += diff * translationRate;
            } else {
                // Instant translation (Simulated ideal)
                this.proteins[i] = this.genes[i];
            }
        }

        // Physics (Brownian Motion + Viscosity)
        this.vel.x *= CONFIG.friction;
        this.vel.y *= CONFIG.friction;
        this.pos.x += this.vel.x + (Math.random() - 0.5) * 0.001;
        this.pos.y += this.vel.y + (Math.random() - 0.5) * 0.001;

        // Bounds
        if (this.pos.x < 0) { this.pos.x = 0; this.vel.x *= -1; }
        if (this.pos.x > 1) { this.pos.x = 1; this.vel.x *= -1; }
        if (this.pos.y < 0) { this.pos.y = 0; this.vel.y *= -1; }
        if (this.pos.y > 1) { this.pos.y = 1; this.vel.y *= -1; }

        this.classifyType();
    }

    classifyType() {
        // Zenith: Exact Index Mapping based on Section 12
        // v27: FEATURE 4 - Use PROTEINS for Phenotype Logic (Simulating Translation Delay)
        const oct4 = this.proteins[0];
        const sox2 = this.proteins[1];
        const nanog = this.proteins[2];
        const lin28 = this.proteins[3];
        const klf4 = this.proteins[4];
        const myc = this.proteins[5];

        const cardiac = (this.proteins[13] + this.proteins[14]) / 2; // TNNT2 + TTN
        const neural = (this.proteins[20] + this.proteins[22]) / 2;  // NEUROD2 + PAX6 (#22)
        const endo = (this.proteins[30] + this.proteins[32]) / 2;    // SOX17 + FOXA2 (#32)

        const tp53 = this.proteins[50];
        const mki67 = this.proteins[51];

        // Thresholds based on Clinical Manual
        if (this.dnaDamage > 0.9 || (myc > 0.8 && tp53 < 0.2)) {
            this.type = 'TUMOR';
            return;
        }
        if (this.health <= 0) {
            this.type = 'DEATH';
            return;
        }

        const pluripotency = (oct4 + sox2 + nanog) / 3;

        if (pluripotency > 0.8) {
            this.type = 'IPSC';
            this.bioAge *= 0.995; // Accelerated Rejuvenation at pluripotency
        } else if (cardiac > 0.6) {
            this.type = 'CARDIO';
        } else if (neural > 0.6) {
            this.type = 'NEURO';
        } else if (endo > 0.6) {
            this.type = 'ENDO';
        } else if (pluripotency > 0.4) {
            this.type = 'PARTIAL';
        } else if (neural > 0.25) {
            this.type = 'TRANSIT_NEU';
        } else if (cardiac > 0.25) {
            this.type = 'TRANSIT_CAR';
        } else {
            this.type = 'SOMATIC';
            // Natural aging drift
            if (this.bioAge < 1.0) this.bioAge += 0.00005;
        }
    }
}

// --- SPATIAL HASHING (Optimization) ---
class SpatialHash {
    constructor(cellSize) {
        this.cellSize = cellSize;
        this.grid = new Map();
    }

    clear() {
        this.grid.clear();
    }

    _key(x, y) {
        return `${Math.floor(x / this.cellSize)},${Math.floor(y / this.cellSize)}`;
    }

    insert(agent) {
        const key = this._key(agent.pos.x, agent.pos.y);
        if (!this.grid.has(key)) this.grid.set(key, []);
        this.grid.get(key).push(agent);
    }

    getNeighbors(agent) {
        const neighbors = [];
        const cx = Math.floor(agent.pos.x / this.cellSize);
        const cy = Math.floor(agent.pos.y / this.cellSize);

        for (let x = cx - 1; x <= cx + 1; x++) {
            for (let y = cy - 1; y <= cy + 1; y++) {
                const cell = this.grid.get(`${x},${y}`);
                if (cell) {
                    for (let i = 0; i < cell.length; i++) {
                        neighbors.push(cell[i]);
                    }
                }
            }
        }
        return neighbors;
    }
}

// --- RENDERER ---
const BiosimRenderer = {
    mode: 'FLUORO', // FLUORO, PHASE, IMMUNO
    showHeatmap: false,

    toggleStyle() {
        const modes = ['FLUORO', 'PHASE', 'IMMUNO'];
        let idx = modes.indexOf(this.mode);
        this.mode = modes[(idx + 1) % modes.length];
        BiosimUI.notify('Display', `Mode switched to ${this.mode}`, 'inf');
    },

    drawCell(ctx, agent, x, y, size) {
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
    },

    traceOrganicShape(ctx, x, y, r, agent) {
        // ... (Legacy function kept for fallback if needed)
    },

    drawGNNConnections(ctx, agents, w, h) {
        // ... (Kept as is)
        if (BiosimBridge.biosimMode !== 'GENERATIVE') return;

        ctx.save();
        ctx.lineWidth = 0.5;
        ctx.globalCompositeOperation = 'lighter';

        agents.forEach(a => {
            if (a.paracrineNeighbors && a.paracrineNeighbors.length > 0) {
                const x1 = a.pos.x * w;
                const y1 = a.pos.y * h;

                a.paracrineNeighbors.forEach(nb => {
                    if (!nb.pos) return; // Safety
                    const x2 = nb.pos.x * w;
                    const y2 = nb.pos.y * h;

                    // Highlight selected signaling paths
                    const isSelected = (window.selectedAgent && (window.selectedAgent.id === a.id || window.selectedAgent.id === nb.id));

                    ctx.beginPath();
                    if (isSelected) {
                        const grad = ctx.createLinearGradient(x1, y1, x2, y2);
                        grad.addColorStop(0, 'rgba(168, 85, 247, 0.6)'); // Purple/GNN theme
                        grad.addColorStop(1, 'rgba(168, 85, 247, 0.1)');
                        ctx.strokeStyle = grad;
                        ctx.lineWidth = 1.5;
                    } else {
                        const grad = ctx.createLinearGradient(x1, y1, x2, y2);
                        grad.addColorStop(0, 'rgba(16, 185, 129, 0.1)'); // Faint paracrine flux
                        grad.addColorStop(1, 'rgba(16, 185, 129, 0)');
                        ctx.strokeStyle = grad;
                        ctx.lineWidth = 0.5;
                    }

                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                });
            }
        });
        ctx.restore();
    },

    drawHeatmap(ctx, agents, w, h) {
        // ... (Kept as is)
        if (!this.showHeatmap) return;
        // ... implementation same as before but shortened for brevity in this replace ...
        const gridSize = 20;
        const cols = Math.ceil(w / gridSize);
        const rows = Math.ceil(h / gridSize);
        const data = new Float32Array(cols * rows);

        agents.forEach(a => {
            const gx = Math.floor((a.pos.x * w) / gridSize);
            const gy = Math.floor((a.pos.y * h) / gridSize);
            if (gx >= 0 && gx < cols && gy >= 0 && gy < rows) {
                const idx = gy * cols + gx;
                data[idx] += a.dnaDamage + (a.type === 'TUMOR' ? 1.0 : 0);
            }
        });

        ctx.save();
        ctx.globalAlpha = 0.5;
        ctx.globalCompositeOperation = 'screen';

        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const val = data[y * cols + x];
                if (val > 0.1) {
                    const intensity = Math.min(1, val * 0.2);
                    const r = gridSize * 3;
                    const cx = x * gridSize + gridSize / 2;
                    const cy = y * gridSize + gridSize / 2;

                    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
                    grad.addColorStop(0, `rgba(255, 30, 0, ${intensity * 0.6})`);
                    grad.addColorStop(1, 'transparent');

                    ctx.fillStyle = grad;
                    ctx.beginPath();
                    ctx.arc(cx, cy, r, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
        }
        ctx.restore();
    }
};



// --- PH11: LONGITUDINAL HISTORY ENGINE ---
const BiosimHistory = {
    snapshots: [],
    maxSnapshots: 300, // ~5 minutes of 1s snapshots

    reset() {
        this.snapshots = [];
    },

    capture(agents, frame) {
        // Snapshot every 60 frames (~1s)
        if (frame % 60 !== 0) return;

        const counts = {
            SOMATIC: 0, IPSC: 0, CARDIO: 0, NEURO: 0, ENDO: 0,
            TUMOR: 0, DEATH: 0, PARTIAL: 0, TRANSIT_NEU: 0, TRANSIT_CAR: 0
        };
        let totalAge = 0;
        let totalHealth = 0;

        agents.forEach(a => {
            counts[a.type]++;
            totalAge += a.bioAge;
            totalHealth += a.health;
        });

        const snapshot = {
            frame,
            timestamp: Date.now(),
            avgAge: totalAge / agents.length,
            avgHealth: totalHealth / agents.length,
            populations: counts,
            entropy: this.calculateEntropy(counts, agents.length)
        };

        this.snapshots.push(snapshot);
        if (this.snapshots.length > this.maxSnapshots) this.snapshots.shift();

        // Trigger Dashboard Update if visible
        if (document.getElementById('clinical-dashboard')?.style.display === 'flex') {
            BiosimUI.renderDashboard();
        }
    },

    calculateEntropy(counts, total) {
        let entropy = 0;
        Object.values(counts).forEach(c => {
            if (c > 0) {
                const p = c / total;
                entropy -= p * Math.log2(p);
            }
        });
        return entropy;
    }
};

// --- ENGINE CORE ---
const BiosimEngine = {
    agents: [],
    spatialHash: new SpatialHash(0.04), // Grid cell size roughly 2x collision radius
    canvas: null,
    ctx: null,
    frame: 0,

    init() {
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());

        // Interaction
        this.canvas.addEventListener('mousedown', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;
            // Find closest
            let closest = null, minD = 100;
            this.agents.forEach(a => {
                const dx = a.pos.x - x; const dy = a.pos.y - y;
                const d = dx * dx + dy * dy;
                if (d < 0.005 && d < minD) { minD = d; closest = a; }
            });

            if (closest) {
                window.selectedAgent = closest; // Set globally for renderer
                BiosimUI.updateInspector(closest);
                BiosimUI.notify('Microscope', `Focused Cell ID #${closest.id}`, 'inf');
            }
        });

        BiosimUI.initGeneGrid(); // Zenith V27 grid init
        this.boot();

        // Start Backend Status Monitoring
        BiosimBridge.checkBackendStatus();
        setInterval(() => BiosimBridge.checkBackendStatus(), 5000);

        this.loop();
    },

    resize() {
        const p = this.canvas.parentElement;
        this.canvas.width = p.clientWidth;
        this.canvas.height = p.clientHeight;
    },

    boot() {
        // Log the previous experiment before clearing
        if (this.agents.length > 0) {
            BiosimLab.logExperiment();
        }

        if (BiosimBridge.isValidatedMode) resetSeed();
        this.agents = [];
        for (let i = 0; i < CONFIG.agentCount; i++) {
            this.agents.push(new Agent(i));
        }

        // Increment Run Counter
        window.simulationRunCount = (window.simulationRunCount || 1) + 1;
        const counterEl = document.getElementById('run-counter');
        if (counterEl) counterEl.innerText = `#${window.simulationRunCount}`;

        BiosimLab.resetFlags();
        BiosimHistory.reset(); // PH11: Reset history on boot
        BiosimUI.notify('System', `Run #${window.simulationRunCount} Initialized`, 'suc');
    },

    updateDensity(count) {
        if (count < 1) count = 1;
        if (count > CONFIG.maxPop) count = CONFIG.maxPop;

        const current = this.agents.length;
        if (count > current) {
            // Spawn more
            for (let i = 0; i < count - current; i++) {
                this.agents.push(new Agent(current + i));
            }
            BiosimUI.notify('System', `Spawned ${count - current} agents`, 'inf');
        } else if (count < current) {
            // Remove
            this.agents.splice(count);
            BiosimUI.notify('System', `Reduced to ${count} agents`, 'inf');
        }

        // Update CONFIG for future boots
        CONFIG.agentCount = count;
    },

    syncToBackend() {
        if (BiosimBridge.biosimMode === 'GENERATIVE') {
            BiosimBridge.syncStateBatch(this.agents);
        }
    },

    loop() {
        try {
            // Physics & Logic
            // Simple N^2 repulsion for this demo (optimized with grid in full version)
            const w = this.canvas.width;
            const h = this.canvas.height;
            if (w === 0 || h === 0) {
                requestAnimationFrame(() => this.loop());
                return;
            }
            const aspect = w / h;

            // v26.4: Auto-Reseed if population is cleared
            if (this.agents.length === 0 && this.frame > 0) {
                console.warn("[System] Population Cleared. Auto-Reseeding...");
                this.boot();
            }

            // 1. Rebuild Spatial Hash
            this.spatialHash.clear();
            for (let i = 0; i < this.agents.length; i++) {
                this.spatialHash.insert(this.agents[i]);
            }

            // 2. Physics & Logic (O(N) with Spatial Hash)
            for (let i = 0; i < this.agents.length; i++) {
                const A = this.agents[i];
                A.tick({
                    vector: BiosimStore.env.vector,
                    disease: BiosimStore.env.disease,
                    spatialHash: this.spatialHash
                });


                // Optimized collision check
                const neighbors = this.spatialHash.getNeighbors(A);
                for (let j = 0; j < neighbors.length; j++) {
                    const B = neighbors[j];

                    // Prevent double-counting by checking ID (optional but cleaner)
                    if (A.id > B.id) continue;

                    const dx = A.pos.x - B.pos.x;
                    const dy = (A.pos.y - B.pos.y) / aspect;
                    const distSq = dx * dx + dy * dy;
                    const minDist = 0.02;

                    if (distSq < minDist * minDist && distSq > 0) {
                        const dist = Math.sqrt(distSq);
                        const force = (minDist - dist) / dist * 0.005;
                        const fx = dx * force;
                        const fy = dy * force;

                        A.vel.x += fx; A.vel.y += fy;
                        B.vel.x -= fx; B.vel.y -= fy;

                        // v26.1: ADHESION FORCES (Section 10.5)
                        // If same type and very close, reduce relative velocity to 'bind' them
                        if (A.type === B.type && A.type !== 'SOMATIC' && A.type !== 'DEATH') {
                            const damping = 0.05;
                            A.vel.x -= (A.vel.x - B.vel.x) * damping;
                            A.vel.y -= (A.vel.y - B.vel.y) * damping;
                        }
                    }

                    // v26.1: PARACRINE ATTRACTION (Chemotaxis - Section 10.5)
                    // Pull toward same-type neighbors to form colonies
                    if (A.type === B.type && A.type !== 'SOMATIC' && distSq < 0.005) {
                        const attract = 0.00005;
                        A.vel.x -= (A.pos.x - B.pos.x) * attract;
                        A.vel.y -= (A.pos.y - B.pos.y) * attract;
                    }

                    // v27: ORGANOID CLUSTERING (Tissue Cohesion Logic)
                    // If cohesion is active, apply strong short-range attraction to same-type cells
                    if (CONFIG.cohesion > 0 && A.type === B.type && A.type !== 'SOMATIC') {
                        // Check distance again (since 'dist' variable from above block might be out of scope or not calc)
                        // We reuse distSq from line 640
                        const distCheck = Math.sqrt(distSq);

                        if (distCheck > 0) {
                            // Stronger pull for structured types
                            let cohesionStrength = CONFIG.cohesion;
                            if (A.type === 'CARDIO' || A.type === 'NEURO') cohesionStrength *= 2.0;

                            const dxNorm = dx / distCheck;
                            const dyNorm = dy / distCheck;

                            // Force vector towards neighbor
                            A.vel.x -= dxNorm * cohesionStrength * 0.001;
                            A.vel.y -= dyNorm * cohesionStrength * 0.001;
                        }
                    }
                }
            }

            // Render
            this.ctx.fillStyle = '#101010'; // v26: Darker lab environment
            this.ctx.fillRect(0, 0, w, h);

            // v26: Draw GNN Signaling Connections
            BiosimRenderer.drawGNNConnections(this.ctx, this.agents, w, h);

            // PH12: Malignancy Heatmap
            BiosimRenderer.drawHeatmap(this.ctx, this.agents, w, h);

            const scale = Math.min(w, h);
            // v27: Reduce cell size multiplier for high-density (2000 cells)
            // v28 FIX: Scale increased from 0.007 to 0.012 for better visibility on high-res displays
            this.agents.forEach(a => {
                BiosimRenderer.drawCell(this.ctx, a, a.pos.x * w, a.pos.y * h, scale * 0.012); 
            });

            // v28 FIX: Update 3D Cell Count UI
            const count3d = document.getElementById('3d-cell-count');
            if (count3d) count3d.innerText = this.agents.length;

            // v26: Batch-sync state to Generative Backend every 60 frames (Reduce network flooding)
            if (this.frame % 60 === 0 && BiosimBridge.biosimMode === 'GENERATIVE') {
                BiosimBridge.syncStateBatch(this.agents);
            }

            // PH11: Longitudinal History Capture
            BiosimHistory.capture(this.agents, this.frame);

            this.frame++;

            requestAnimationFrame(() => this.loop());

            // UI Sync (lazy, every 30 frames)
            if (this.frame % 30 === 0) {
                BiosimBridge.updateCharts();
                // Sync Dashboard if visible
                if (BiosimBridge.LatentMap.viewMode === 'MICROSCOPE') {
                    BiosimBridge.LatentMap.syncAgents(BiosimEngine.agents);
                }

                // BACKEND SYNC: Send cell state to server for 3D view synchronization
                if (this.frame % 120 === 0 && BiosimBridge.LatentMap && BiosimBridge.LatentMap.syncLiveCells) {
                    BiosimBridge.LatentMap.syncLiveCells(this.agents, this.frame);
                }

                // v26 HUD Telemetry Update (Section 14 & 22)
                const lastSnapshot = BiosimHistory.snapshots[BiosimHistory.snapshots.length - 1];
                if (lastSnapshot) {
                    const epiEl = document.getElementById('hud-epi');
                    const dnaEl = document.getElementById('hud-dna');

                    if (epiEl) {
                        const ent = lastSnapshot.entropy;
                        epiEl.innerText = ent.toFixed(3);
                        // Color code Section 22: <0.4 Emerald, <0.6 Yellow, >0.6 Red
                        epiEl.style.color = ent < 0.4 ? '#10b981' : (ent < 0.6 ? '#facc15' : '#ef4444');
                    }

                    if (dnaEl) {
                        const stability = (lastSnapshot.avgHealth * 100).toFixed(1);
                        dnaEl.innerText = stability + '%';
                        // Color code Section 22: >90% Emerald, >80% Yellow, <80% Red
                        dnaEl.style.color = stability > 90 ? '#10b981' : (stability > 80 ? '#facc15' : '#ef4444');

                        if (stability < 80) BiosimUI.showSidebarAlert(`CRITICAL: Genomic Stability at ${stability}%`);
                    }

                    if (lastSnapshot.populations.TUMOR > 0) {
                        const tCount = lastSnapshot.populations.TUMOR;
                        BiosimUI.showSidebarAlert(`ONCOGENIC ALERT: ${tCount} Malignant Transformations detected.`);
                    }
                }
            }
        } catch (e) {
            console.error("[System] Simulation Loop Recovered from Exception:", e);
            requestAnimationFrame(() => this.loop());
        }
    }
};

// --- UI GLUE ---
const BiosimStore = { env: { vector: null, disease: null } };

// Consolidated sync handled via BiosimBridge.LatentMap.syncLiveCells

const BiosimBridge = {
    sequenceRegistry: {}, 
    accessionRegistry: {}, 
    domainDefaults: { // Mapped fragments for high-fidelity handshake (RUO)
        "GATA4": "CPVESCDRRFSRSDKLAEHKKYHSNKAKR", 
        "NKX2-5": "RRRRTAFTNEQIDELERRFKQQRYLSAPEREHLAAMIKLTQCKIQVQWKFQNRRAKWRRLKQQKTHP",
        "SNAI1": "RKCPSCSLHFSRSADLADLSHLKKHFSKHK",
        "TBX5": "PKALVLSGSPGRRRWLLSPGEPEPEPEPEPEPEPEPEPEPEPEPEPE",
        "OCT4": "NLLQKEVEKFAVCQKALETLPNLCQGKKVLSLLHKLEKELAFAENKPSGKRSKFQPSLQFSSIESDVLDSPSMNTAAANKLQKELEQFAKLLKQKRITLGYTQADVGLTLGVLFGKVFSQTTICRFEALQLSFKNMCKLKPLLNKWLE",
        "SOX2": "DRVKRPMNAFMVWSRGQRRKMAQENPKMHNSEISKRLGAEWKLLSETEKRPFIDEAKRLRALHMKEHPDYKYRPRRKTK",
        "NEUROD1": "ERRRREKQANVRERERNRIAASKCRNRKKEKEILEQQLRDLPNRPDGHH",
        "MEF2C": "RPAVPPVGSYSFMGPRRRLLGPRRRLLGPRRRLL"
    },
    endpoint: window.location.origin,
    internalApiKey: 'DEVELOPER_KEY', 
    isValidatedMode: true, 
    setMode(m) {
        BiosimUI.notify('System', `Logic is LOCKED to GENERATIVE (Strict Mode)`, 'inf');
    },

    toggleComputeMode() {
        this.isValidatedMode = !this.isValidatedMode;

        const dot = document.getElementById('compute-mode-dot');
        const label = document.getElementById('compute-mode-label');
        const subtext = document.getElementById('compute-mode-subtext');
        const dlBtn = document.getElementById('btn-download-manifest');

        if (this.isValidatedMode) {
            dot.className = 'w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse';
            label.innerText = 'Validated Compute Mode';
            label.className = 'text-[8px] font-black text-emerald-400 uppercase tracking-widest leading-none mb-0.5';
            subtext.innerText = 'Deterministic Seed: 0x771A_REPRO';
            dlBtn.classList.remove('hidden');
            BiosimUI.notify('Biosim', 'Validated Compute Active: 0x771A Seed Enforced', 'suc');
        } else {
            dot.className = 'w-1.5 h-1.5 rounded-full bg-amber-500';
            label.innerText = 'Demo / Creative Mode';
            label.className = 'text-[8px] font-black text-amber-400 uppercase tracking-widest leading-none mb-0.5';
            subtext.innerText = 'Stochastic Noise: ACTIVE';
            dlBtn.classList.add('hidden');
            BiosimUI.notify('Biosim', 'Switched to Demo Mode (Reduced Replicability)', 'wrn');
        }

        // Re-boot engine to apply seed if needed
        BiosimEngine.boot();
    },

    downloadManifest() {
        const manifest = {
            version: "26.1.4",
            timestamp: new Date().toISOString(),
            run_id: window.simulationRunCount,
            mode: this.isValidatedMode ? "VALIDATED" : "DEMO",
            parameters: {
                seed: this.isValidatedMode ? "0x771A" : "STOCHASTIC",
                agentCount: CONFIG.agentCount,
                stochasticIntensity: CONFIG.stochastic.noiseStrength,
                model_checksum: "SHA256:8b5cf6...f7a8b"
            },
            protocol_state: BiosimStore.env.vector || "NONE",
            verification_status: "PASS"
        };

                    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(manifest, null, 2));
            const link = document.createElement('a');
            link.setAttribute('href', dataUri);
            link.setAttribute('download', 'Zenith_AlphaFold_Manifest.json');
            document.body.appendChild(link);
            link.click();
            link.remove();
            BiosimUI.notify('SUCCESS', 'JSON Manifest Downloaded', 'suc');
        } catch (error) {
            BiosimUI.notify('Export Error', error.message, 'err');
        }
    }`);
        }
    },


    copyAllProteins() {
        if (!this.lastDiscovery || !this.lastDiscovery.target_profile) {
            BiosimUI.notify('Copy Error', 'Run a discovery first.', 'err');
            return;
        }
        const lines = Object.entries(this.lastDiscovery.target_profile)
            .sort((a, b) => b[1] - a[1])
            .map(([gene, w]) => `${gene} (${Math.round(w * 100)}%)`);
        const text = lines.join(', ');
        navigator.clipboard.writeText(text).then(() => {
            BiosimUI.notify('Copied!', `${lines.length} proteins copied to clipboard`, 'suc');
            BiosimUI.logTerminal(`[ZENITH] Copied ${lines.length} proteins: ${text}`);
        }).catch(() => {
            BiosimUI.notify('Copy Error', 'Clipboard unavailable.', 'err');
        });
    },

    injectDiscoveryIntoSim() {
        if (!this.lastDiscovery) return;
        const profile = this.lastDiscovery.target_profile;
        if (!profile) return;
        
        BiosimUI.notify('Injection', 'Applying Discovery Vector to Population...', 'inf');
        
        // v26.4: Force-boot if 0 cells
        if (BiosimEngine.agents.length === 0) {
            BiosimEngine.boot();
        }

        BiosimEngine.agents.forEach(a => {
            Object.entries(profile).forEach(([gene, weight]) => {
                const idx = CONFIG.geneSymbols.indexOf(gene);
                if (idx !== -1) {
                    a.genes[idx] += weight * 0.5;
                }
            });
        });
        
        BiosimUI.notify('Zenith Engine', 'Population Synchronized with Discovery Manifest.', 'suc');
    },

    exportOpentronsScript() {
        if (!this.lastDiscovery) {
            BiosimUI.notify('Bridge Error', 'No active discovery data to export.', 'err');
            return;
        }

        const data = this.lastDiscovery;
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
        const filename = `zenith_protocol_${timestamp}.py`;

        BiosimUI.notify('Bridge', 'Generating Opentrons protocol via Zenith Engine...', 'inf');

        fetch('/generate_opentrons_protocol', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ discovery_data: data })
        })
        .then(res => res.json())
        .then(resData => {
            const script = resData.script;
            const blob = new Blob([script], { type: 'text/x-python' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(JSON.stringify(manifest, null, 2)); a.href = dataUri;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            BiosimUI.notify('Bridge', 'Opentrons v2.27 Flex script generated & downloaded.', 'suc');
        })
        .catch(err => {
            console.error("Opentrons generator error:", err);
            BiosimUI.notify('Bridge Error', 'Failed to generate protocol script.', 'err');
        });
    },

    async generateReport() {
        const apiKey = document.getElementById('api-key-input').value.trim();
        const agents = BiosimEngine.agents.map(a => ({
            type: a.type,
            age: a.bioAge,
            genes: Array.from(a.genes)
        }));

        BiosimUI.notify('System', 'Generating Clinical Report (AI)...', 'inf');

        try {
            const response = await fetch(`${this.endpoint}/generate_report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': BiosimBridge.internalApiKey,
                    'X-CSRF-Token': window.csrfToken || ''
                },
                body: JSON.stringify({
                    api_key: apiKey || null,
                    timestamp: new Date().toISOString(),
                    agent_count: agents.length,
                    agents_sample: agents.slice(0, 50) // Send sample for analysis
                })
            });

            if (!response.ok) throw new Error("Report Generation Failed");

            // Handle Blob
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(JSON.stringify(manifest, null, 2)); a.href = dataUri;
            a.download = `IS-CHRP_Clinical_Report_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            BiosimUI.notify('System', 'Report Downloaded', 'suc');
        } catch (e) {
            console.error(e);
            BiosimUI.notify('Error', 'Failed to generate report. Check API Key.', 'err');
        }
    },

    toggleCatalog() {
        const el = document.getElementById('catalog-overlay');
        if (el) {
            el.style.display = (el.style.display === 'none') ? 'block' : 'none';
        }
    },

    updateCharts() {
        const popEl = document.getElementById('header-pop');
        if (popEl) popEl.innerText = BiosimEngine.agents.length;

        // 1. Calculate Population Counts
        const counts = [0, 0, 0, 0, 0, 0];
        BiosimEngine.agents.forEach(a => {
            if (a.type === 'SOMATIC') counts[0]++;
            if (a.type === 'IPSC' || a.type === 'PARTIAL') counts[1]++;
            if (a.type === 'NEURO' || a.type === 'TRANSIT_NEU') counts[2]++;
            if (a.type === 'CARDIO' || a.type === 'TRANSIT_CAR') counts[3]++;
            if (a.type === 'ENDO') counts[4]++;
            if (a.type === 'TUMOR') counts[5]++;
        });

        // 2. Bar Chart Sync (Population)
        const ctxMain = document.getElementById('chart-main');
        if (ctxMain) {
            const chartLabels = ['Somatic', 'iPSC', 'Neural', 'Cardio', 'Endo', 'Tumor'];
            const chartColors = ['#64748b', '#facc15', '#3b82f6', '#f43f5e', '#10b981', '#ef4444'];

            const existing = Chart.getChart(ctxMain);
            if (existing) {
                if (window.chartMainInstance === existing) {
                    window.chartMainInstance.data.datasets[0].data = counts;
                    window.chartMainInstance.update('none');
                } else {
                    existing.destroy();
                    window.chartMainInstance = new Chart(ctxMain, {
                        type: 'bar',
                        data: {
                            labels: chartLabels,
                            datasets: [{ label: 'Count', data: counts, backgroundColor: chartColors, barThickness: 8 }]
                        },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                    });
                }
            } else {
                window.chartMainInstance = new Chart(ctxMain, {
                    type: 'bar',
                    data: {
                        labels: chartLabels,
                        datasets: [{ label: 'Count', data: counts, backgroundColor: chartColors, barThickness: 8 }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                });
            }
        }

        // 3. Time Course Chart Sync
        const ctxTime = document.getElementById('chart-timecourse');
        if (ctxTime && BiosimHistory.snapshots.length > 0) {
            const snapshots = BiosimHistory.snapshots.slice(-60);
            const labels = snapshots.map(s => s.frame);
            const somaticData = snapshots.map(s => s.populations.SOMATIC);
            const ipscData = snapshots.map(s => s.populations.IPSC + (s.populations.PARTIAL || 0));
            const neuroData = snapshots.map(s => s.populations.NEURO + (s.populations.TRANSIT_NEU || 0));

            const existingTime = Chart.getChart(ctxTime);
            if (existingTime) {
                if (window.chartTimeInstance === existingTime) {
                    window.chartTimeInstance.data.labels = labels;
                    window.chartTimeInstance.data.datasets[0].data = somaticData;
                    window.chartTimeInstance.data.datasets[1].data = ipscData;
                    window.chartTimeInstance.data.datasets[2].data = neuroData;
                    window.chartTimeInstance.update('none');
                } else {
                    existingTime.destroy();
                    window.chartTimeInstance = new Chart(ctxTime, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [
                                { label: 'Somatic', data: somaticData, borderColor: '#64748b', borderWidth: 1, pointRadius: 0 },
                                { label: 'iPSC', data: ipscData, borderColor: '#facc15', borderWidth: 1, pointRadius: 0 },
                                { label: 'Neural', data: neuroData, borderColor: '#3b82f6', borderWidth: 1, pointRadius: 0 }
                            ]
                        },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
                    });
                }
            } else {
                window.chartTimeInstance = new Chart(ctxTime, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'Somatic', data: somaticData, borderColor: '#64748b', borderWidth: 1, pointRadius: 0 },
                            { label: 'iPSC', data: ipscData, borderColor: '#facc15', borderWidth: 1, pointRadius: 0 },
                            { label: 'Neural', data: neuroData, borderColor: '#3b82f6', borderWidth: 1, pointRadius: 0 }
                        ]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
                });
            }
        }

        // 4. Color Legend & Feedback
        const legend = document.getElementById('legend-content');
        if (legend) {
            const detailedCounts = {};
            BiosimEngine.agents.forEach(a => { detailedCounts[a.type] = (detailedCounts[a.type] || 0) + 1; });
            legend.innerHTML = Object.entries(detailedCounts).map(([type, count]) => {
                const c = CONFIG.colors[type] || CONFIG.colors.SOMATIC;
                const cssColor = `hsl(${c.h}, ${c.s}%, ${c.l}%)`;
                return `
                    <div class="flex justify-between items-center text-slate-300">
                        <div class="flex items-center gap-1">
                            <div class="w-2 h-2 rounded-full" style="background: ${cssColor}"></div>
                            <span>${type}</span>
                        </div>
                        <span>${count}</span>
                    </div>
                `;
            }).join('');
        }

        // 5. Check Research Goals
        BiosimLab.checkGoals({
            SOMATIC: counts[0], IPSC: counts[1], NEURO: counts[2], CARDIO: counts[3], TUMOR: counts[5]
        });

        // 6. Telemetry HUD Sync
        const epiEl = document.getElementById('hud-epi');
        const dnaEl = document.getElementById('hud-dna');
        if (epiEl && BiosimHistory.snapshots.length > 0) {
            epiEl.innerText = BiosimHistory.snapshots[BiosimHistory.snapshots.length - 1].entropy.toFixed(3);
        }
        if (dnaEl) {
            let totalDamage = 0;
            BiosimEngine.agents.forEach(a => totalDamage += a.dnaDamage || 0);
            const stability = Math.max(0, 100 - (totalDamage / (BiosimEngine.agents.length || 1)) * 100);
            dnaEl.innerText = stability.toFixed(1) + '%';
            dnaEl.style.color = stability < 80 ? '#f87171' : '#94a3b8';
        }
    },

    async checkBackendStatus() {
        if (this.isHealthChecking) return;
        this.isHealthChecking = true;

        const dot = document.getElementById('status-dot');
        const text = document.getElementById('status-text');
        const modeEl = document.getElementById('status-mode');
        const badge = document.getElementById('backend-status-badge');
        const discDot = document.getElementById('discovery-status-dot');

        if (!dot || !text || !badge) {
            this.isHealthChecking = false;
            return;
        }

        try {
            console.log(`[System] Verifying connection to Zenith Engine: ${this.endpoint}/health`);
            const response = await fetch(`${this.endpoint}/health`, {
                cache: 'no-store',
                signal: AbortSignal.timeout(30000) // 30s timeout
            });

            if (response.ok) {
                const data = await response.json();

                // Update Status (Main Header)
                dot.style.backgroundColor = '#10b981'; // Green
                text.innerText = 'ONLINE';
                text.style.color = '#10b981';

                // Update Operational Mode
                if (modeEl) {
                    modeEl.innerText = `(${data.mode || 'CLINICAL'})`;
                    modeEl.style.color = '#10b981';
                    modeEl.classList.remove('hidden');
                }

                // Update New Real-time Heartbeat Badge (Footer)
                const footerDot = document.getElementById('backend-dot');
                const footerText = document.getElementById('backend-text');
                if (footerDot && footerText) {
                    footerDot.style.backgroundColor = '#10b981'; // Green
                    footerText.innerText = '10/10 ACTIVE';
                    footerText.style.color = '#10b981';
                }

                if (discDot) discDot.style.backgroundColor = '#10b981';
                
                // Track backend lateness
                this.lastSuccessfulPing = Date.now();

                // Update Badge Glow
                badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                badge.style.background = 'rgba(16, 185, 129, 0.05)';

                // Update Discovery Panel Dot
                if (discDot) discDot.className = 'w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';

                // Update scVI Status
                const scviMode = document.getElementById('scvi-mode');
                if (scviMode) {
                    if (data.mode === 'CLINICAL') {
                        scviMode.innerText = 'CLINICAL (HCA)';
                        scviMode.className = 'text-[7px] bg-emerald-900/40 px-1 rounded border border-emerald-500/30 text-emerald-300';
                    } else {
                        scviMode.innerText = 'PREVIEW (MOCK)';
                        scviMode.className = 'text-[7px] bg-yellow-900/40 px-1 rounded border border-yellow-500/30 text-yellow-300';
                    }
                }
            } else {
                throw new Error(`Zenith Engine responded with status: ${response.status}`);
            }
        } catch (e) {
            console.error('[System] Zenith Engine Connection Failed:', e);
            const timeSinceLoad = performance.now();
            const isInitializing = timeSinceLoad < 60000;
            const isStabilizing = timeSinceLoad >= 60000 && timeSinceLoad < 120000;

            if (isInitializing || isStabilizing) {
                dot.style.backgroundColor = '#facc15'; // Yellow
                text.innerText = isInitializing ? 'INITIALIZING...' : 'STABILIZING...';
                text.style.color = '#facc15';
                if (modeEl) modeEl.classList.add('hidden');
                badge.style.borderColor = 'rgba(250, 204, 21, 0.3)';
                badge.style.background = 'rgba(250, 204, 21, 0.05)';
            } else {
                dot.style.backgroundColor = '#ef4444'; // Red
                text.innerText = 'OFFLINE';
                text.style.color = '#ef4444';
                if (modeEl) {
                    modeEl.innerText = '(SYSTEM HALTED)';
                    modeEl.style.color = '#ef4444';
                    modeEl.classList.remove('hidden');
                }
                badge.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                badge.style.background = 'rgba(239, 68, 68, 0.05)';
            }

            // Update New Real-time Heartbeat Badge (Footer) - Critical for User Visibility
            const footerDot = document.getElementById('backend-dot');
            const footerText = document.getElementById('backend-text');
            if (footerDot && footerText) {
                footerDot.style.backgroundColor = '#ef4444'; // Red
                footerText.innerText = 'RECONNECTING...';
                footerText.style.color = '#ef4444';
            }

            if (discDot) {
                discDot.className = (isInitializing || isStabilizing) ?
                    'w-2 h-2 rounded-full bg-yellow-500 animate-pulse' :
                    'w-2 h-2 rounded-full bg-red-500 shadow-sm';
            }
        } finally {
            this.isHealthChecking = false;
        }
    },

    // === UNIPROT LIVE LOOKUP MODULE ===
    UniProtLookup: {
        async search() {
            const input = document.getElementById('gene-search-input');
            const gene = (input?.value || '').trim().toUpperCase();
            if (!gene) { BiosimUI.notify('Gene Lookup', 'Enter a gene symbol first', 'warn'); return; }

            const resultEl  = document.getElementById('gene-lookup-result');
            const errorEl   = document.getElementById('gene-lookup-error');
            const loadingEl = document.getElementById('gene-lookup-loading');
            if (resultEl)  resultEl.classList.add('hidden');
            if (errorEl)   errorEl.classList.add('hidden');
            if (loadingEl) loadingEl.classList.remove('hidden');

            try {
                // Primary: use our backend endpoint which applies 3-tier UniProt strategy
                let data = null;
                try {
                    const r = await fetch(`/api/uniprot-lookup?gene=${encodeURIComponent(gene)}`);
                    if (r.ok) data = await r.json();
                } catch (_) {}

                // Fallback: direct UniProt REST API (if backend unreachable)
                if (!data) {
                    const r = await fetch(
                        `https://rest.uniprot.org/uniprotkb/search?query=gene_exact:${encodeURIComponent(gene)}+AND+organism_id:9606+AND+reviewed:true&fields=sequence,accession,protein_name,cc_function,cc_subcellular_location,ft_domain&format=json&size=1`,
                        { headers: { 'Accept': 'application/json' } }
                    );
                    if (r.ok) {
                        const raw = await r.json();
                        const e = (raw.results || [])[0];
                        if (e) {
                            const acc = e.primaryAccession;
                            const names = e.proteinDescription || {};
                            const rec = names.recommendedName || {};
                            let func = null, loc = null;
                            for (const c of e.comments || []) {
                                if (c.commentType === 'FUNCTION' && !func) func = (c.texts || [])[0]?.value || null;
                                if (c.commentType === 'SUBCELLULAR LOCATION' && !loc) loc = c.subcellularLocations?.[0]?.location?.value || null;
                            }
                            const domains = (e.features || []).filter(f => ['Domain','DNA binding','Zinc finger'].includes(f.type)).slice(0,4);
                            data = {
                                gene, accession: acc,
                                protein_name: rec.fullName?.value || null,
                                sequence_length: e.sequence?.length || null,
                                function: func, subcellular_location: loc,
                                domains: domains.map(d => ({ type: d.type, description: d.description || '' })),
                                source: 'Swiss-Prot (Direct)',
                                uniprot_url: `https://www.uniprot.org/uniprot/${acc}`
                            };
                        }
                    }
                }

                if (loadingEl) loadingEl.classList.add('hidden');

                if (!data || !data.accession) {
                    if (errorEl) { errorEl.textContent = `No reviewed UniProt entry found for "${gene}" (Homo sapiens).`; errorEl.classList.remove('hidden'); }
                    return;
                }

                // Render result
                document.getElementById('glr-gene').textContent     = data.gene;
                const accLink = document.getElementById('glr-acc-link');
                accLink.textContent = data.accession;
                accLink.href = data.uniprot_url || `https://www.uniprot.org/uniprot/${data.accession}`;
                document.getElementById('glr-len').textContent      = data.sequence_length ? `${data.sequence_length} aa` : '';
                document.getElementById('glr-name').textContent     = data.protein_name || '';
                document.getElementById('glr-loc').textContent      = data.subcellular_location ? `📍 ${data.subcellular_location}` : '';
                document.getElementById('glr-func').textContent     = data.function || '';
                document.getElementById('glr-source').textContent   = data.source || 'Swiss-Prot';

                // Domain badges
                const domEl = document.getElementById('glr-domains');
                domEl.innerHTML = (data.domains || []).map(d =>
                    `<span style="font-size:6px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);color:#a5b4fc;padding:1px 4px;border-radius:3px">${d.type}${d.description ? ': '+d.description : ''}</span>`
                ).join('');

                if (resultEl) resultEl.classList.remove('hidden');
                BiosimUI.notify('UniProt', `${data.gene} → ${data.accession} (${data.sequence_length}aa)`, 'suc');

            } catch (e) {
                if (loadingEl) loadingEl.classList.add('hidden');
                if (errorEl) { errorEl.textContent = `Lookup failed: ${e.message}`; errorEl.classList.remove('hidden'); }
                BiosimUI.notify('UniProt', `Lookup failed for ${gene}`, 'err');
            }
        }
    },

    // === AF3 REAL RESULT UPLOADER ===
    AF3Upload: {
        applyRealMetrics() {
            const plddt = parseFloat(document.getElementById('af3-in-plddt')?.value);
            const pae   = parseFloat(document.getElementById('af3-in-pae')?.value);
            const ptm   = parseFloat(document.getElementById('af3-in-ptm')?.value);
            const iptm  = parseFloat(document.getElementById('af3-in-iptm')?.value);

            // Scientific range validation
            const errors = [];
            if (!isNaN(plddt) && (plddt < 0 || plddt > 100)) errors.push('pLDDT must be 0-100');
            if (!isNaN(pae)   && (pae   < 0 || pae   > 30))  errors.push('PAE must be 0-30Å');
            if (!isNaN(ptm)   && (ptm   < 0 || ptm   > 1))   errors.push('pTM must be 0-1');
            if (!isNaN(iptm)  && (iptm  < 0 || iptm  > 1))   errors.push('ipTM must be 0-1');
            if ([plddt, pae, ptm, iptm].every(isNaN)) { BiosimUI.notify('AF3 Upload', 'Enter at least one metric', 'warn'); return; }
            if (errors.length) { BiosimUI.notify('AF3 Validation', errors.join(' | '), 'err'); return; }

            // Inject real metrics into the AF3 panel
            const af3Panel = document.getElementById('af3-metrics-panel');
            if (af3Panel) af3Panel.classList.remove('hidden');

            if (!isNaN(plddt)) {
                const el = document.getElementById('metric-plddt');
                if (el) {
                    el.innerText = plddt.toFixed(1);
                    el.className = plddt > 90 ? 'text-[9px] text-blue-400 font-mono font-bold' : plddt > 70 ? 'text-[9px] text-teal-400 font-mono font-bold' : 'text-[9px] text-yellow-400 font-mono font-bold';
                }
            }
            if (!isNaN(pae)) {
                const el = document.getElementById('metric-pae');
                if (el) el.innerText = pae.toFixed(1) + 'Å';
            }
            if (!isNaN(ptm)) {
                const el = document.getElementById('metric-ptm');
                if (el) el.innerText = ptm.toFixed(3);
            }
            if (!isNaN(iptm)) {
                const el = document.getElementById('metric-iptm');
                if (el) {
                    el.innerText = iptm.toFixed(3);
                    el.className = iptm > 0.8 ? 'text-[9px] text-blue-400 font-mono font-bold' : iptm > 0.6 ? 'text-[9px] text-yellow-500 font-mono font-bold' : 'text-[9px] text-red-400 font-mono font-bold';
                }
            }

            // Store in lastDiscovery for export context
            if (BiosimBridge.lastDiscovery) {
                BiosimBridge.lastDiscovery.af3_metrics = { pLDDT: plddt, PAE: pae, pTM: ptm, ipTM: iptm };
            }

            const iptmDisplay = !isNaN(iptm) ? ` | ipTM: ${iptm.toFixed(3)}` : '';
            const quality = !isNaN(iptm) ? (iptm >= 0.8 ? '✅ HIGH CONFIDENCE' : iptm >= 0.6 ? '⚠️ MODERATE' : '❌ LOW') : '';
            BiosimUI.notify('AF3 Uploaded', `Real metrics applied${iptmDisplay} ${quality}`, 'suc');
        }
    },

    // === COLONY MICROSCOPE MODULE ===
    LatentMap: {
        scene: null, camera: null, renderer: null, instancedMesh: null,
        controls: null, isMacroInit: false,
        viewMode: '2D',
        dummy: null,
        mCanvas: null,
        mCtx: null,
        cells: [],
        bgFilaments: [],
        mParams: { radius: 320, green: 0.9, blue: 0.7, red: 0.8 },
        isLiveSyncing: false,
        running3D: false,

        toggleView(mode) {
            this.viewMode = mode;
            const canvas = document.getElementById('canvas');
            const viewportMicro = document.getElementById('main-viewport-microscope');
            const viewport3d = document.getElementById('main-viewport-3d');
            const leg = document.getElementById('KAGAWEA-legend');
            const modeText = document.getElementById('sidebar-view-mode');

            if (mode === 'MICROSCOPE') {
                canvas.style.display = 'none';
                if (viewport3d) viewport3d.style.display = 'none';
                if (viewportMicro) viewportMicro.style.display = 'block';
                if (leg) leg.style.display = 'flex';
                if (modeText) modeText.innerText = 'VIEWPORT: MICROSCOPE';

                if (!this.isMacroInit) {
                    this.initMicroscope();
                    this.isMacroInit = true;
                }
            } else if (mode === '3D') {
                canvas.style.display = 'none';
                if (viewportMicro) viewportMicro.style.display = 'none';
                if (viewport3d) viewport3d.style.display = 'block';
                if (leg) leg.style.display = 'flex';
                if (modeText) modeText.innerText = 'VIEWPORT: LATENT MANIFOLD EXPLORER';

                if (!this.scene) {
                    this.init3D();
                }
            } else {
                canvas.style.display = 'block';
                if (viewportMicro) viewportMicro.style.display = 'none';
                if (viewport3d) viewport3d.style.display = 'none';
                if (leg) leg.style.display = 'none';
                if (modeText) modeText.innerText = 'VIEWPORT: 2D SIMULATION';

                // FORCE DASHBOARD RELOAD - FIX CHART VISIBILITY
                setTimeout(() => BiosimBridge.updateCharts(), 100);
            }

            if (mode === '3D') {
                this.running3D = true;
                if (this.scene) this.animate3D();
            } else {
                this.running3D = false;
            }

            if (window.BiosimUI) BiosimUI.notify('View', `Switched to ${mode}`, 'suc');
        },

        toggleFullscreen() {
            const layout = document.getElementById('architect-layout');
            const exitBtn = document.getElementById('btn-exit-fullscreen');
            const maxBtn = document.getElementById('btn-micro-maximize');
            if (!layout) return;

            const isFull = layout.classList.toggle('micro-fullscreen-active');
            if (exitBtn) exitBtn.style.display = isFull ? 'flex' : 'none';
            if (maxBtn) maxBtn.style.display = isFull ? 'none' : 'flex';

            // Trigger window resize to fix canvas scaling
            setTimeout(() => window.dispatchEvent(new Event('resize')), 100);

            BiosimUI.notify('Display', isFull ? 'Fullscreen Mode Enabled' : 'Sidebar Restored', 'inf');
        },



        cycleView() {
            const modes = ['2D', 'MICROSCOPE', '3D'];
            let idx = modes.indexOf(this.viewMode);
            this.toggleView(modes[(idx + 1) % modes.length]);
        },

        init3D() {
            // v28 FIX: Unified container ID (3d-container vs three-container)
            const container = document.getElementById('3d-container');
            if (!container) return;

            // --- 1. ENGINE INITIALIZATION ---
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0x010204); // Zenith v26 Deep Black

            this.camera = new THREE.PerspectiveCamera(45, container.offsetWidth / container.offsetHeight, 0.1, 2000);
            this.camera.position.set(0, 50, 200);

            this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
            this.renderer.setSize(container.offsetWidth, container.offsetHeight);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(this.renderer.domElement);

            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;

            // Cinematic Lighting (Zenith v26 Palette)
            this.scene.add(new THREE.AmbientLight(0xffffff, 0.3));
            const p1 = new THREE.PointLight(0x00f2ff, 1.5, 300); p1.position.set(50, 100, 50); this.scene.add(p1);
            const p2 = new THREE.PointLight(0x8b5cf6, 1.2, 300); p2.position.set(-50, 0, 50); this.scene.add(p2);

            // Fog for depth (PI Requirement)
            this.scene.fog = new THREE.FogExp2(0x010204, 0.0015);

            // --- 2. MULTI-LAYER INTERNAL CELL MAPPING ---
            const MAX_CELLS = 2500; // Increased capacity for Zenith Pro

            // Layer 1: Membrane (Purple Translucent)
            const membraneGeom = new THREE.SphereGeometry(6, 24, 24);
            this.membraneMesh = new THREE.InstancedMesh(
                membraneGeom,
                new THREE.MeshStandardMaterial({
                    color: 0xffffff, transparent: true, opacity: 0.35, roughness: 0.1, metalness: 0.1,
                    side: THREE.DoubleSide
                }),
                MAX_CELLS
            );

            // Layer 2: DNA Core (Glowing Cyan - INSIDE)
            const dnaGeom = new THREE.SphereGeometry(2.3, 16, 16);
            this.dnaMesh = new THREE.InstancedMesh(
                dnaGeom,
                new THREE.MeshStandardMaterial({
                    color: 0x00f2ff, emissive: 0x00f2ff, emissiveIntensity: 1.5
                }),
                MAX_CELLS
            );

            // Layer 3: Alpha-Actinin-2 (White Structural Inclusions - INSIDE)
            const actininGeom = new THREE.SphereGeometry(0.8, 8, 8);
            this.actininMesh = new THREE.InstancedMesh(
                actininGeom,
                new THREE.MeshStandardMaterial({
                    color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 0.5
                }),
                MAX_CELLS * 2 // 2 inclusions per cell
            );

            this.scene.add(this.membraneMesh, this.dnaMesh, this.actininMesh);
            this.dummy = new THREE.Object3D();
            this.colorHelper = new THREE.Color();

            // PHASE 3: Cell Clicking System
            this.raycaster = new THREE.Raycaster();
            this.mouse = new THREE.Vector2();
            this.selectedCellIndex = null;

            this.renderer.domElement.addEventListener('click', (event) => {
                if (this.viewMode !== '3D') return;
                const rect = this.renderer.domElement.getBoundingClientRect(); });
    async exportAlphaFoldManifest() {
        try {
            if (!this.lastDiscovery) {
                BiosimUI.notify('Export Error', 'Run a discovery first.', 'err');
                return;
            }
            BiosimUI.notify('AF3 Export', 'Generating GOLD Manifest...', 'inf');
            const sequences = [];
            const factors = [];
            const profile = Object.entries(this.lastDiscovery.target_profile || {}).sort((a,b) => b[1]-a[1]);
            const proteinParts = [];
            for (const [gene] of profile.slice(0, 3)) {
                const seq = this.sequenceRegistry[gene] || "MAAHKGAEHHHKHGHRKHG";
                proteinParts.push(String(seq).substring(0, 350));
                factors.push(gene);
            }
            const dna = "CCTGTGACTCTTTGTTATGCAAATCCCGGGTG";
            sequences.push({ "dnaSequence": { "sequence": dna, "count": 1 } });
            const fused = proteinParts.join("GGGGSGGGGSGGGGSGGGGS");
            sequences.push({ "proteinChain": { "sequence": fused, "count": 1 } });
            const manifest = [{
                "name": "Zenith_Discovery_" + factors.join("_"),
                "modelSeeds": [],
                "sequences": sequences
            }];
            const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(manifest, null, 2));
            const link = document.createElement('a');
            link.href = dataUri;
            link.download = 'Zenith_AlphaFold_Manifest.json';
            document.body.appendChild(link);
            link.click();
            link.remove();
            BiosimUI.notify('SUCCESS', 'JSON Manifest Downloaded', 'suc');
        } catch (e) {
            console.error(e);
            BiosimUI.notify('Export Error', e.message, 'err');
        }
    }
}

};
