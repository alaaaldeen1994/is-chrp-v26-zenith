/**
 * NilusLab Zenith v26.1 - Profile 'Elite' DNA Helix (DIAGONAL FIX)
 * Diagonal orientation (Above-Left to Below-Right) with reduced size.
 */

class ProfileDNARenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(35, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

        this.init();
        this.createEliteDiagonalHelix();
        this.animate();

        window.addEventListener('resize', () => this.onResize());
    }

    init() {
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        this.camera.position.z = 35;

        // Premium Studio Lighting (Matching Mockup Glow)
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const pointLight1 = new THREE.PointLight(0x3b82f6, 1.2); // Intense Blue Glow
        pointLight1.position.set(-20, 20, 10);
        this.scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0x2dd4bf, 0.8); // Teal Accent
        pointLight2.position.set(20, -20, 10);
        this.scene.add(pointLight2);
    }

    createEliteDiagonalHelix() {
        const sphereSize = 0.28; // Reduced Size
        const helixRadius = 2.8; // Reduced Radius
        const ySpacing = 0.38;   // Tightened Spacing
        const twist = 0.4;

        const strandGeometry = new THREE.SphereGeometry(sphereSize, 32, 32);
        const strandMaterial = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.1,
            metalness: 0.2,
            emissive: 0xffffff,
            emissiveIntensity: 0.05
        });

        const barMaterial = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.3,
            transparent: true,
            opacity: 0.3
        });

        this.helixGroup = new THREE.Group();

        const numPoints = 80;

        for (let i = 0; i < numPoints; i++) {
            const angle = i * twist;
            const y = (i - numPoints / 2) * ySpacing;

            // Strand 1
            const x1 = Math.cos(angle) * helixRadius;
            const z1 = Math.sin(angle) * helixRadius;
            const sphere1 = new THREE.Mesh(strandGeometry, strandMaterial);
            sphere1.position.set(x1, y, z1);
            this.helixGroup.add(sphere1);

            // Strand 2
            const x2 = Math.cos(angle + Math.PI) * helixRadius;
            const z2 = Math.sin(angle + Math.PI) * helixRadius;
            const sphere2 = new THREE.Mesh(strandGeometry, strandMaterial);
            sphere2.position.set(x2, y, z2);
            this.helixGroup.add(sphere2);

            // Connecting Bars
            if (i % 3 === 0) {
                const barGeometry = new THREE.CylinderGeometry(0.08, 0.08, helixRadius * 2);
                const bar = new THREE.Mesh(barGeometry, barMaterial);
                bar.position.set(0, y, 0);
                bar.rotation.z = Math.PI / 2;
                bar.rotation.y = -angle;
                this.helixGroup.add(bar);
            }
        }

        this.scene.add(this.helixGroup);

        // DIAGONAL ROTATION (AS REQUESTED: Above-Left to Below-Right)
        this.helixGroup.rotation.z = -Math.PI / 4.8; // -38 degrees tilt
        this.helixGroup.position.set(-2, 1, 0);     // Subtle offset for framing
    }

    onResize() {
        if (!this.container) return;
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        if (this.helixGroup) {
            this.helixGroup.rotation.y += 0.007; // Slow constant rotation
        }
        this.renderer.render(this.scene, this.camera);
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    window.dnaRenderer = new ProfileDNARenderer('dna-animation-container');
});
