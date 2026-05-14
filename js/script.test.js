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

};
