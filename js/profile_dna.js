/**
 * NilusLab Zenith v26.1 - Profile 'Elite' DNA Helix
 * High-fidelity 3D Volumetric Helix with Medical-Grade Shading
 */

class ProfileDNARenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(35, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

        this.init();
        this.createEliteHelix();
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

        const spotLight = new THREE.SpotLight(0xffffff, 1.5);
        spotLight.position.set(20, 40, 50);
        this.scene.add(spotLight);

        const pointLight1 = new THREE.PointLight(0x3b82f6, 0.8); // Nilus Blue Glow
        pointLight1.position.set(-20, 10, 10);
        this.scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0x2dd4bf, 0.5); // Teal Glow
        pointLight2.position.set(20, -10, 10);
        this.scene.add(pointLight2);
    }

    createEliteHelix() {
        const strandGeometry = new THREE.SphereGeometry(0.35, 32, 32); // Larger, smoother spheres
        const strandMaterial = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.05,
            metalness: 0.1,
            emissive: 0xffffff,
            emissiveIntensity: 0.1
        });

        const barMaterial = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.2,
            metalness: 0.1,
            transparent: true,
            opacity: 0.4
        });

        this.helixGroup = new THREE.Group();

        const numPoints = 80;
        const radius = 4;
        const twist = 0.35;
        const ySpacing = 0.45;

        for (let i = 0; i < numPoints; i++) {
            const angle = i * twist;
            const y = (i - numPoints / 2) * ySpacing;

            // Strand 1 (Sine Helix)
            const x1 = Math.cos(angle) * radius;
            const z1 = Math.sin(angle) * radius;
            const sphere1 = new THREE.Mesh(strandGeometry, strandMaterial);
            sphere1.position.set(x1, y, z1);
            this.helixGroup.add(sphere1);

            // Strand 2 (Offset Helix)
            const x2 = Math.cos(angle + Math.PI) * radius;
            const z2 = Math.sin(angle + Math.PI) * radius;
            const sphere2 = new THREE.Mesh(strandGeometry, strandMaterial);
            sphere2.position.set(x2, y, z2);
            this.helixGroup.add(sphere2);

            // High-Quality Connecting Bars
            if (i % 3 === 0) {
                const barGeometry = new THREE.CylinderGeometry(0.1, 0.1, radius * 2);
                const bar = new THREE.Mesh(barGeometry, barMaterial);
                bar.position.set(0, y, 0);
                bar.rotation.z = Math.PI / 2;
                bar.rotation.y = -angle;
                this.helixGroup.add(bar);
            }
        }

        this.scene.add(this.helixGroup);
        this.helixGroup.rotation.z = Math.PI / 8; // Slight diagonal tilt for 'Agency' aesthetic
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
            this.helixGroup.rotation.y += 0.006; // Slow premium rotation
        }
        this.renderer.render(this.scene, this.camera);
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    window.dnaRenderer = new ProfileDNARenderer('dna-animation-container');
});
