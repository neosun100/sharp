"""SHARP Web Application - UI + API Server with Video Rendering."""

import logging
import os
import uuid
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from flask import Flask, jsonify, render_template, request, send_file, send_from_directory
from flask_cors import CORS
from flasgger import Swagger

from gpu_manager import gpu_manager
from sharp.models import PredictorParams, create_predictor
from sharp.utils import io as sharp_io
from sharp.utils.gaussians import Gaussians3D, SceneMetaData, save_ply, unproject_gaussians

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

swagger_config = {
    "headers": [],
    "specs": [{"endpoint": "apispec", "route": "/apispec.json"}],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs",
}
swagger_template = {
    "info": {
        "title": "SHARP API",
        "description": "Sharp Monocular View Synthesis API",
        "version": "1.0.0",
    }
}
Swagger(app, config=swagger_config, template=swagger_template)

MODEL_PATH = os.environ.get("MODEL_PATH", None)
OUTPUT_DIR = Path("/tmp/sharp/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_model(device: torch.device):
    """Load SHARP model."""
    if MODEL_PATH and Path(MODEL_PATH).exists():
        state_dict = torch.load(MODEL_PATH, weights_only=True, map_location=device)
    else:
        url = "https://ml-site.cdn-apple.com/models/sharp/sharp_2572gikvuh.pt"
        state_dict = torch.hub.load_state_dict_from_url(url, progress=True, map_location=device)
    
    model = create_predictor(PredictorParams())
    model.load_state_dict(state_dict)
    model.eval()
    model.to(device)
    return model


@torch.no_grad()
def predict_image(model, image: np.ndarray, f_px: float, device: torch.device) -> Gaussians3D:
    """Run prediction on image."""
    internal_shape = (1536, 1536)
    image_pt = torch.from_numpy(image.copy()).float().to(device).permute(2, 0, 1) / 255.0
    _, height, width = image_pt.shape
    disparity_factor = torch.tensor([f_px / width]).float().to(device)

    image_resized = F.interpolate(
        image_pt[None], size=internal_shape, mode="bilinear", align_corners=True
    )
    gaussians_ndc = model(image_resized, disparity_factor)

    intrinsics = torch.tensor([
        [f_px, 0, width / 2, 0],
        [0, f_px, height / 2, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]).float().to(device)
    
    intrinsics_resized = intrinsics.clone()
    intrinsics_resized[0] *= internal_shape[0] / width
    intrinsics_resized[1] *= internal_shape[1] / height

    return unproject_gaussians(gaussians_ndc, torch.eye(4).to(device), intrinsics_resized, internal_shape)


def render_video(gaussians: Gaussians3D, metadata: SceneMetaData, output_path: Path):
    """Render trajectory video if CUDA available."""
    if not torch.cuda.is_available():
        return None
    
    try:
        from sharp.utils import camera, gsplat
        import imageio.v2 as iio
        
        (width, height) = metadata.resolution_px
        f_px = metadata.focal_length_px
        device = torch.device("cuda")

        intrinsics = torch.tensor([
            [f_px, 0, (width - 1) / 2.0, 0],
            [0, f_px, (height - 1) / 2.0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], device=device, dtype=torch.float32)

        params = camera.TrajectoryParams()
        camera_model = camera.create_camera_model(gaussians, intrinsics, resolution_px=metadata.resolution_px)
        trajectory = camera.create_eye_trajectory(gaussians, params, resolution_px=metadata.resolution_px, f_px=f_px)
        renderer = gsplat.GSplatRenderer(color_space=metadata.color_space)
        
        output_path.parent.mkdir(exist_ok=True, parents=True)
        writer = iio.get_writer(str(output_path), fps=30)

        for eye_position in trajectory:
            camera_info = camera_model.compute(eye_position)
            rendering_output = renderer(
                gaussians.to(device),
                extrinsics=camera_info.extrinsics[None].to(device),
                intrinsics=camera_info.intrinsics[None].to(device),
                image_width=camera_info.width,
                image_height=camera_info.height,
            )
            color = (rendering_output.color[0].permute(1, 2, 0) * 255.0).to(dtype=torch.uint8)
            writer.append_data(color.cpu().numpy())
        writer.close()
        return output_path
    except Exception as e:
        LOGGER.warning(f"Video rendering failed: {e}")
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)


@app.route("/health")
def health():
    """Health check."""
    return jsonify({"status": "healthy", "service": "sharp"})


@app.route("/api/gpu/status")
def gpu_status():
    """Get GPU status."""
    return jsonify(gpu_manager.get_status())


@app.route("/api/gpu/offload", methods=["POST"])
def gpu_offload():
    """Force offload model from GPU."""
    gpu_manager.force_offload()
    return jsonify({"status": "offloaded"})


@app.route("/api/predict", methods=["POST"])
def api_predict():
    """Generate 3D Gaussian Splat from image.
    ---
    tags:
      - Prediction
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
      - name: render_video
        in: formData
        type: boolean
        default: true
    responses:
      200:
        description: URLs to generated files
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    render_video_flag = request.form.get("render_video", "true").lower() == "true"

    try:
        # Save uploaded file
        task_id = str(uuid.uuid4())[:8]
        input_path = OUTPUT_DIR / f"{task_id}_input{Path(file.filename).suffix}"
        file.save(input_path)

        # Load and process
        image, _, f_px = sharp_io.load_rgb(input_path)
        height, width = image.shape[:2]

        model = gpu_manager.get_model(load_model)
        device = gpu_manager.device
        gaussians = predict_image(model, image, f_px, device)

        # Save PLY
        ply_path = OUTPUT_DIR / f"{task_id}.ply"
        save_ply(gaussians, f_px, (height, width), ply_path)

        result = {
            "task_id": task_id,
            "ply_url": f"/api/files/{task_id}.ply",
            "video_url": None
        }

        # Render video if requested and CUDA available
        if render_video_flag and torch.cuda.is_available():
            video_path = OUTPUT_DIR / f"{task_id}.mp4"
            metadata = SceneMetaData(f_px, (width, height), "linearRGB")
            if render_video(gaussians, metadata, video_path):
                result["video_url"] = f"/api/files/{task_id}.mp4"

        # Cleanup input
        input_path.unlink(missing_ok=True)

        return jsonify(result)

    except Exception as e:
        LOGGER.exception("Prediction failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/files/<filename>")
def serve_file(filename):
    """Serve generated files."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, as_attachment=True)


@app.route("/api/result/<task_id>")
def get_result(task_id):
    """Get result files for a task."""
    ply_path = OUTPUT_DIR / f"{task_id}.ply"
    video_path = OUTPUT_DIR / f"{task_id}.mp4"
    
    if not ply_path.exists():
        return jsonify({"error": "Result not found"}), 404
    
    return jsonify({
        "task_id": task_id,
        "ply_url": f"/api/files/{task_id}.ply",
        "video_url": f"/api/files/{task_id}.mp4" if video_path.exists() else None
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
