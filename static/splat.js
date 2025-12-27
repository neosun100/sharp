// SHARP Splat Viewer Wrapper
class SplatViewer {
    constructor(canvas, url) {
        this.canvas = canvas;
        this.url = url;
        this.autoRotate = false;
        this.disposed = false;
    }

    async load() {
        // Initialize WebGL context
        const gl = this.canvas.getContext('webgl2', { antialias: false });
        if (!gl) {
            console.error('WebGL2 not supported');
            return this.loadFallback();
        }
        this.gl = gl;
        
        // Load the PLY file
        try {
            const response = await fetch(this.url);
            const buffer = await response.arrayBuffer();
            await this.initRenderer(buffer);
        } catch (e) {
            console.error('Failed to load splat:', e);
            return this.loadFallback();
        }
    }

    async initRenderer(buffer) {
        // Parse PLY and initialize WebGL rendering
        // This is a simplified version - for full implementation use the splat-core.js
        if (window.initSplatRenderer) {
            this.renderer = await window.initSplatRenderer(this.canvas, buffer);
        }
    }

    loadFallback() {
        // Show message that WebGL viewer couldn't load
        const container = this.canvas.parentElement;
        const placeholder = container.querySelector('.viewer-placeholder');
        if (placeholder) {
            placeholder.innerHTML = '<p>🎬</p><p>3D viewer requires WebGL2. Download the PLY file to view in a dedicated viewer.</p>';
            placeholder.style.display = 'flex';
        }
    }

    resetCamera() {
        if (this.renderer && this.renderer.resetCamera) {
            this.renderer.resetCamera();
        }
    }

    toggleAutoRotate() {
        this.autoRotate = !this.autoRotate;
        if (this.renderer && this.renderer.setAutoRotate) {
            this.renderer.setAutoRotate(this.autoRotate);
        }
    }

    dispose() {
        this.disposed = true;
        if (this.renderer && this.renderer.dispose) {
            this.renderer.dispose();
        }
    }
}

window.SplatViewer = SplatViewer;
