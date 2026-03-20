/**
 * NilusLab Zenith v26.1 - Profile DNA Helix Renderer
 * High-end 3D Double Helix with Soft-White Medical Shading
 */

class ProfileDNARenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

        this.init();
        this.createHelix();
        this.animate();

        window.addEventListener('resize', () => this.onResize());
    }

    init() {
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        this.camera.position.z = 25;

        // Medical-Grade Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        this.scene.add(ambientLight);

        const pointLight1 = new THREE.PointLight(0xffffff, 1);
        pointLight1.position.set(10, 10, 10);
        this.scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0x3b82f6, 0.3); // Subtle Nilus Blue hint
        pointLight2.position.set(-10, -10, 5);
        this.scene.add(pointLight2);
    }

    createHelix() {
        const strandGeometry = new THREE.SphereGeometry(0.2, 16, 16);
        const strandMaterial = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.1,
            metalness: 0.5,
            emissive: 0x000000
        });

        const barMaterial = new THREE.MeshStandardMaterial({
            color: 0xeeeeee,
            roughness: 0.3,
            metalness: 0.2,
            transparent: true,
            opacity: 0.8
        });

        this.helixGroup = new THREE.Group();

        const numPoints = 60;
        const radius = 3;
        const twist = 0.4;
        const ySpacing = 0.5;

        for (let i = 0; i < numPoints; i++) {
            const angle = i * twist;
            const y = (i - numPoints / 2) * ySpacing;

            // Strand 1 (Sine)
            const x1 = Math.cos(angle) * radius;
            const z1 = Math.sin(angle) * radius;
            const sphere1 = new THREE.Mesh(strandGeometry, strandMaterial);
            sphere1.position.set(x1, y, z1);
            this.helixGroup.add(sphere1);

            // Strand 2 (Cosine Offset)
            const x2 = Math.cos(angle + Math.PI) * radius;
            const z2 = Math.sin(angle + Math.PI) * radius;
            const sphere2 = new THREE.Mesh(strandGeometry, strandMaterial);
            sphere2.position.set(x2, y, z2);
            this.helixGroup.add(sphere2);

            // Connecting BarsEvery 2 points
            if (i % 2 === 0) {
                const barGeometry = new THREE.CylinderGeometry(0.05, 0.05, radius * 2);
                const bar = new THREE.Mesh(barGeometry, barMaterial);
                bar.position.set(0, y, 0);
                bar.rotation.z = Math.PI / 2;
                bar.rotation.y = -angle;
                this.helixGroup.add(bar);
            }
        }

        this.scene.add(this.helixGroup);
    }

    onResize() {
        if (!this.container) return;
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        if (this.helixGroup) {
            this.helixGroup.rotation.y += 0.005; // Slow professional rotation
            this.helixGroup.rotation.x += 0.001;
        }
        this.renderer.render(this.scene, this.camera);
    }
}

// Initializing on load
document.addEventListener('DOMContentLoaded', () => {
    window.dnaRenderer = new ProfileDNARenderer('dna-animation-container');
});
