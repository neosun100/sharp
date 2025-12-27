// SHARP App - Main JavaScript
const i18n = {
    en: { subtitle: "Sharp Monocular View Synthesis - Generate Interactive 3D from Single Image", upload: "Upload Image", upload_hint: "Click or drag image here", generate: "Generate 3D Scene", viewer: "3D Viewer", viewer_hint: "Upload an image to generate interactive 3D scene", gpu: "GPU Status", release: "Release", download_ply: "⬇️ Download PLY", download_video: "🎬 Download Video", ply_info: "PLY file can be viewed in 3DGS viewers", controls_hint: "🖱️ Drag to rotate • Scroll to zoom • Right-click to pan", processing: "Processing...", loading_viewer: "Loading 3D viewer...", completed: "Completed!" },
    "zh-CN": { subtitle: "单目视图合成 - 从单张图片生成交互式3D场景", upload: "上传图片", upload_hint: "点击或拖拽图片到此处", generate: "生成 3D 场景", viewer: "3D 查看器", viewer_hint: "上传图片以生成交互式3D场景", gpu: "GPU 状态", release: "释放", download_ply: "⬇️ 下载 PLY", download_video: "🎬 下载视频", ply_info: "PLY 文件可在 3DGS 查看器中查看", controls_hint: "🖱️ 拖动旋转 • 滚轮缩放 • 右键平移", processing: "处理中...", loading_viewer: "加载3D查看器...", completed: "完成!" }
};

let currentLang = localStorage.getItem('lang') || 'en';
let selectedFile = null;
let plyUrl = null;
let videoUrl = null;
let viewer = null;

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (i18n[lang] && i18n[lang][key]) el.textContent = i18n[lang][key];
    });
}

function toggleTheme() {
    const t = document.body.getAttribute('data-theme') === 'light' ? '' : 'light';
    document.body.setAttribute('data-theme', t);
    localStorage.setItem('theme', t);
}

document.addEventListener('DOMContentLoaded', () => {
    setLanguage(currentLang);
    document.getElementById('language').value = currentLang;
    if (localStorage.getItem('theme') === 'light') document.body.setAttribute('data-theme', 'light');
    refreshGPU();
    
    const dz = document.getElementById('dropZone');
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
    dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('dragover'); if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); });
});

function handleFile(file) {
    if (!file) return;
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = e => {
        const img = document.getElementById('previewImage');
        img.src = e.target.result;
        img.style.display = 'block';
        document.getElementById('processBtn').disabled = false;
    };
    reader.readAsDataURL(file);
}

async function processImage() {
    if (!selectedFile) return;
    const btn = document.getElementById('processBtn');
    const progress = document.getElementById('progressBar');
    const fill = document.getElementById('progressFill');
    const status = document.getElementById('statusText');
    
    btn.disabled = true;
    progress.style.display = 'block';
    fill.style.width = '20%';
    status.textContent = i18n[currentLang].processing;
    document.getElementById('downloadSection').style.display = 'none';
    document.getElementById('viewerControls').style.display = 'none';
    
    const placeholder = document.getElementById('viewerPlaceholder');
    placeholder.innerHTML = '<div class="loader"></div><p>' + i18n[currentLang].processing + '</p>';

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('render_video', 'true');

    try {
        fill.style.width = '40%';
        const response = await fetch('/api/predict', { method: 'POST', body: formData });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed');
        }

        fill.style.width = '70%';
        const data = await response.json();
        
        plyUrl = data.ply_url;
        videoUrl = data.video_url;
        
        // Setup downloads
        document.getElementById('downloadPly').onclick = () => window.open(plyUrl, '_blank');
        if (videoUrl) {
            document.getElementById('downloadVideo').onclick = () => window.open(videoUrl, '_blank');
            document.getElementById('downloadVideo').style.display = 'block';
        } else {
            document.getElementById('downloadVideo').style.display = 'none';
        }
        document.getElementById('downloadSection').style.display = 'block';

        fill.style.width = '85%';
        status.textContent = i18n[currentLang].loading_viewer;
        
        // Load 3D viewer
        await loadSplatViewer(plyUrl);
        
        fill.style.width = '100%';
        status.textContent = i18n[currentLang].completed;
        document.getElementById('viewerControls').style.display = 'flex';
        placeholder.style.display = 'none';
        
        refreshGPU();
    } catch (e) {
        status.textContent = 'Error: ' + e.message;
        placeholder.innerHTML = '<p>❌</p><p>Error: ' + e.message + '</p>';
        fill.style.width = '0%';
    }
    
    btn.disabled = false;
}

async function loadSplatViewer(url) {
    const canvas = document.getElementById('viewer-canvas');
    const container = document.getElementById('viewerContainer');
    
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    
    if (window.SplatViewer) {
        if (viewer) viewer.dispose();
        viewer = new SplatViewer(canvas, url);
        await viewer.load();
    } else {
        // Fallback: show video if available
        if (videoUrl) {
            const placeholder = document.getElementById('viewerPlaceholder');
            placeholder.innerHTML = `<video src="${videoUrl}" autoplay loop muted playsinline style="max-width:100%;max-height:100%;border-radius:8px"></video>`;
            placeholder.style.display = 'flex';
        }
    }
}

function resetCamera() { if (viewer) viewer.resetCamera(); }
function toggleAutoRotate() { if (viewer) viewer.toggleAutoRotate(); }
function enterFullscreen() {
    const c = document.getElementById('viewerContainer');
    if (c.requestFullscreen) c.requestFullscreen();
}

async function refreshGPU() {
    try {
        const res = await fetch('/api/gpu/status');
        const data = await res.json();
        document.getElementById('gpuDot').classList.toggle('active', data.model_loaded);
        document.getElementById('gpuText').textContent = data.model_loaded ? `Loaded (${data.gpu_memory_allocated_mb?.toFixed(0) || 0} MB)` : 'Idle';
    } catch (e) {}
}

async function offloadGPU() {
    await fetch('/api/gpu/offload', { method: 'POST' });
    refreshGPU();
}
