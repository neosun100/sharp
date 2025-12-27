"""SHARP MCP Server - Model Context Protocol interface."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import torch
import torch.nn.functional as F
import numpy as np
from fastmcp import FastMCP

from gpu_manager import gpu_manager
from sharp.models import PredictorParams, create_predictor
from sharp.utils import io as sharp_io
from sharp.utils.gaussians import save_ply, unproject_gaussians

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

mcp = FastMCP("sharp")

MODEL_PATH = os.environ.get("MODEL_PATH", None)
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/tmp/sharp/output"))
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
def _predict_image(model, image: np.ndarray, f_px: float, device: torch.device):
    """Internal prediction function."""
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


@mcp.tool()
def predict(file_path: str, output_path: Optional[str] = None) -> dict:
    """
    Generate 3D Gaussian Splat from a single image.
    
    Args:
        file_path: Path to input image (JPEG, PNG, HEIC, etc.)
        output_path: Optional output path for PLY file. If not provided, saves to /tmp/sharp/output/
    
    Returns:
        dict with status, output_path, and image info
    """
    try:
        input_path = Path(file_path)
        if not input_path.exists():
            return {"status": "error", "error": f"File not found: {file_path}"}
        
        # Load image
        image, _, f_px = sharp_io.load_rgb(input_path)
        height, width = image.shape[:2]
        
        # Get model and predict
        model = gpu_manager.get_model(load_model)
        device = gpu_manager.device
        gaussians = _predict_image(model, image, f_px, device)
        
        # Save result
        if output_path:
            out_path = Path(output_path)
        else:
            out_path = OUTPUT_DIR / f"{input_path.stem}.ply"
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        save_ply(gaussians, f_px, (height, width), out_path)
        
        return {
            "status": "success",
            "output_path": str(out_path),
            "image_info": {
                "width": width,
                "height": height,
                "focal_length_px": f_px
            }
        }
    except Exception as e:
        LOGGER.exception("Prediction failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def batch_predict(input_dir: str, output_dir: Optional[str] = None) -> dict:
    """
    Process multiple images in a directory.
    
    Args:
        input_dir: Directory containing input images
        output_dir: Output directory for PLY files
    
    Returns:
        dict with status and list of processed files
    """
    try:
        input_path = Path(input_dir)
        if not input_path.is_dir():
            return {"status": "error", "error": f"Not a directory: {input_dir}"}
        
        out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        
        extensions = sharp_io.get_supported_image_extensions()
        image_files = []
        for ext in extensions:
            image_files.extend(input_path.glob(f"*{ext}"))
        
        if not image_files:
            return {"status": "error", "error": "No images found"}
        
        results = []
        model = gpu_manager.get_model(load_model)
        device = gpu_manager.device
        
        for img_path in image_files:
            try:
                image, _, f_px = sharp_io.load_rgb(img_path)
                height, width = image.shape[:2]
                gaussians = _predict_image(model, image, f_px, device)
                
                out_path = out_dir / f"{img_path.stem}.ply"
                save_ply(gaussians, f_px, (height, width), out_path)
                results.append({"file": str(img_path), "output": str(out_path), "status": "success"})
            except Exception as e:
                results.append({"file": str(img_path), "status": "error", "error": str(e)})
        
        return {"status": "success", "processed": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def gpu_status() -> dict:
    """
    Get current GPU status and memory usage.
    
    Returns:
        dict with GPU status information
    """
    return gpu_manager.get_status()


@mcp.tool()
def gpu_offload() -> dict:
    """
    Force offload model from GPU to free VRAM.
    
    Returns:
        dict with status
    """
    gpu_manager.force_offload()
    return {"status": "success", "message": "Model offloaded from GPU"}


@mcp.tool()
def get_supported_formats() -> dict:
    """
    Get list of supported input image formats.
    
    Returns:
        dict with supported extensions
    """
    return {
        "image_extensions": sharp_io.get_supported_image_extensions(),
        "output_format": ".ply (3D Gaussian Splat)"
    }


if __name__ == "__main__":
    mcp.run()
