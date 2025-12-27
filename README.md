[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# 🎯 SHARP - Monocular View Synthesis

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fsharp-blue?logo=docker)](https://hub.docker.com/r/neosun/sharp)
[![Version](https://img.shields.io/badge/version-v1.0.0-green)](https://github.com/neosun100/sharp/releases)
[![License](https://img.shields.io/badge/license-Apple%20Sample%20Code-lightgrey)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-2512.10685-b31b1b.svg)](https://arxiv.org/abs/2512.10685)

> Generate interactive 3D scenes from a single image in less than a second.

![Demo](assets/demo.gif)

## ✨ What is SHARP?

SHARP (Sharp Monocular View Synthesis) is an AI model from Apple Research that converts a single 2D photograph into a 3D Gaussian Splat representation. This enables:

- **Photo to 3D**: Transform any photo into an interactive 3D scene
- **Real-time Rendering**: Generated 3DGS can be rendered in real-time
- **Ultra Fast**: Less than 1 second inference on GPU
- **Zero-shot Generalization**: Works on any image without fine-tuning

### Use Cases

| Industry | Application |
|----------|-------------|
| E-commerce | 360° product views from single photo |
| Real Estate | Virtual property tours |
| Social Media | 3D photo effects |
| Gaming/VFX | Rapid 3D asset prototyping |
| AR/VR | Quick environment generation |

> ⚠️ **Note**: SHARP generates small-range view synthesis (±15-30°), not full 360° reconstruction. It's ideal for parallax effects and depth-aware rendering.

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Pull and run (All-in-One, ~15GB with model)
docker run -d --gpus all -p 8080:8080 --name sharp neosun/sharp:latest

# Access Web UI
open http://localhost:8080

# API Documentation
open http://localhost:8080/docs
```

### Docker Compose

```yaml
version: '3.8'
services:
  sharp:
    image: neosun/sharp:latest
    container_name: sharp-service
    ports:
      - "8080:8080"
    environment:
      - GPU_IDLE_TIMEOUT=300
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

```bash
docker-compose up -d
```

## 📦 Features

This Docker image provides three interfaces:

| Interface | Port | Description |
|-----------|------|-------------|
| Web UI | 8080 | Upload images, view 3D results |
| REST API | 8080 | Programmatic access with Swagger docs |
| MCP Server | stdio | AI assistant integration |

## 🌐 Web UI

Access `http://localhost:8080` for the web interface:

- Drag & drop image upload
- Real-time 3D preview (looping video)
- Download PLY and MP4 files
- GPU status monitoring
- Multi-language support (EN/中文)

## 📡 REST API

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/predict` | Generate 3D from image |
| GET | `/api/files/{id}.ply` | Download PLY file |
| GET | `/api/files/{id}.mp4` | Download video |
| GET | `/api/gpu/status` | GPU status |
| POST | `/api/gpu/offload` | Release GPU memory |
| GET | `/docs` | Swagger documentation |

### Example: Generate 3D Scene

```bash
# Upload image and generate 3D
curl -X POST http://localhost:8080/api/predict \
  -F "file=@photo.jpg" \
  -F "render_video=true"

# Response
{
  "task_id": "abc123",
  "ply_url": "/api/files/abc123.ply",
  "video_url": "/api/files/abc123.mp4"
}

# Download results
curl -O http://localhost:8080/api/files/abc123.ply
curl -O http://localhost:8080/api/files/abc123.mp4
```

### GPU Management

```bash
# Check GPU status
curl http://localhost:8080/api/gpu/status
# {"device":"cuda","model_loaded":true,"gpu_memory_allocated_mb":2694}

# Release GPU memory
curl -X POST http://localhost:8080/api/gpu/offload
# {"status":"offloaded"}
```

## 🤖 MCP Integration

SHARP includes an MCP (Model Context Protocol) server for AI assistant integration.

### Configuration

Add to your MCP client config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "sharp": {
      "command": "docker",
      "args": ["exec", "-i", "sharp-service", "python", "mcp_server.py"]
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `predict` | Generate 3D from single image |
| `batch_predict` | Process multiple images |
| `gpu_status` | Check GPU status |
| `gpu_offload` | Release GPU memory |
| `get_supported_formats` | List supported image formats |

### MCP Usage Example

```
User: Generate a 3D scene from /path/to/image.jpg

Assistant: I'll generate a 3D Gaussian Splat from that image.
[Calls predict tool with file_path="/path/to/image.jpg"]
Result: PLY file saved to /tmp/sharp/output/image.ply
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | Server port |
| `GPU_IDLE_TIMEOUT` | 300 | Seconds before auto-offload |
| `MODEL_PATH` | (bundled) | Custom model path |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | 4GB VRAM | 8GB+ VRAM |
| RAM | 8GB | 16GB |
| Storage | 20GB | 30GB |

## 📁 Project Structure

```
sharp/
├── app.py              # Flask API server
├── gpu_manager.py      # GPU resource management
├── mcp_server.py       # MCP interface
├── templates/          # Web UI templates
├── static/             # Frontend assets
├── src/sharp/          # Core model code
├── Dockerfile          # Container definition
└── docker-compose.yml  # Compose config
```

## 🔧 Tech Stack

- **Model**: Apple SHARP (3D Gaussian Splatting)
- **Backend**: Flask + Gunicorn
- **GPU**: CUDA 12.4 + PyTorch
- **Container**: NVIDIA Docker
- **MCP**: FastMCP

## 📊 Performance

| Metric | Value |
|--------|-------|
| Inference Time | ~1 second |
| Video Rendering | ~80 seconds |
| GPU Memory | ~2.7 GB |
| PLY File Size | ~60 MB |

## 📝 Changelog

### v1.0.0 (2024-12-27)
- Initial release
- Web UI with video preview
- REST API with Swagger docs
- MCP server integration
- Auto GPU memory management

## 📄 License

This project uses Apple's sample code license. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

- [Apple Research](https://machinelearning.apple.com/) - SHARP model
- [3D Gaussian Splatting](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) - Rendering technique

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/sharp&type=Date)](https://star-history.com/#neosun100/sharp)

## 📱 关注公众号

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
