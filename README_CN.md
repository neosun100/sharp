[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# 🎯 SHARP - 单目视图合成

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fsharp-blue?logo=docker)](https://hub.docker.com/r/neosun/sharp)
[![Version](https://img.shields.io/badge/version-v1.0.0-green)](https://github.com/neosun100/sharp/releases)
[![License](https://img.shields.io/badge/license-Apple%20Sample%20Code-lightgrey)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-2512.10685-b31b1b.svg)](https://arxiv.org/abs/2512.10685)

> 一秒内从单张图片生成交互式 3D 场景

![Demo](assets/demo.gif)

## ✨ 什么是 SHARP？

SHARP 是 Apple Research 发布的 AI 模型，能将单张 2D 照片转换为 3D 高斯点云表示。

- **照片转 3D**：任意照片转换为可交互的 3D 场景
- **实时渲染**：生成的 3DGS 可实时渲染
- **超快速度**：GPU 推理不到 1 秒
- **零样本泛化**：无需微调，适用于任何图片

### 应用场景

| 行业 | 应用 |
|------|------|
| 电商 | 单张照片生成 360° 产品展示 |
| 房地产 | 虚拟房产导览 |
| 社交媒体 | 3D 照片特效 |
| 游戏/影视 | 快速 3D 资产原型 |
| AR/VR | 快速环境生成 |

> ⚠️ **注意**：SHARP 生成小范围视角合成（±15-30°），不是完整 360° 重建。适合视差效果和深度感知渲染。

## 🚀 快速开始

### Docker（推荐）

```bash
# 拉取并运行（All-in-One，含模型约 15GB）
docker run -d --gpus all -p 8080:8080 --name sharp neosun/sharp:latest

# 访问 Web UI
open http://localhost:8080

# API 文档
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

## 📦 功能特性

本 Docker 镜像提供三种接口：

| 接口 | 端口 | 说明 |
|------|------|------|
| Web UI | 8080 | 上传图片，查看 3D 结果 |
| REST API | 8080 | 程序化访问，含 Swagger 文档 |
| MCP Server | stdio | AI 助手集成 |

## 🌐 Web 界面

访问 `http://localhost:8080`：

- 拖拽上传图片
- 实时 3D 预览（循环视频）
- 下载 PLY 和 MP4 文件
- GPU 状态监控
- 多语言支持（中/英）

## 📡 REST API

### 接口列表

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/predict` | 从图片生成 3D |
| GET | `/api/files/{id}.ply` | 下载 PLY 文件 |
| GET | `/api/files/{id}.mp4` | 下载视频 |
| GET | `/api/gpu/status` | GPU 状态 |
| POST | `/api/gpu/offload` | 释放 GPU 显存 |
| GET | `/docs` | Swagger 文档 |

### 示例：生成 3D 场景

```bash
# 上传图片并生成 3D
curl -X POST http://localhost:8080/api/predict \
  -F "file=@photo.jpg" \
  -F "render_video=true"

# 响应
{
  "task_id": "abc123",
  "ply_url": "/api/files/abc123.ply",
  "video_url": "/api/files/abc123.mp4"
}

# 下载结果
curl -O http://localhost:8080/api/files/abc123.ply
curl -O http://localhost:8080/api/files/abc123.mp4
```

### GPU 管理

```bash
# 查看 GPU 状态
curl http://localhost:8080/api/gpu/status
# {"device":"cuda","model_loaded":true,"gpu_memory_allocated_mb":2694}

# 释放 GPU 显存
curl -X POST http://localhost:8080/api/gpu/offload
# {"status":"offloaded"}
```

## 🤖 MCP 集成

SHARP 包含 MCP（Model Context Protocol）服务器，用于 AI 助手集成。

### 配置方法

添加到 MCP 客户端配置（如 Claude Desktop）：

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

### 可用工具

| 工具 | 说明 |
|------|------|
| `predict` | 单张图片生成 3D |
| `batch_predict` | 批量处理多张图片 |
| `gpu_status` | 查看 GPU 状态 |
| `gpu_offload` | 释放 GPU 显存 |
| `get_supported_formats` | 获取支持的图片格式 |

### MCP 使用示例

```
用户：从 /path/to/image.jpg 生成 3D 场景

助手：我来从这张图片生成 3D 高斯点云。
[调用 predict 工具，file_path="/path/to/image.jpg"]
结果：PLY 文件已保存到 /tmp/sharp/output/image.ply
```

## ⚙️ 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 8080 | 服务端口 |
| `GPU_IDLE_TIMEOUT` | 300 | 自动释放显存的空闲时间（秒） |
| `MODEL_PATH` | (内置) | 自定义模型路径 |

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| GPU | 4GB 显存 | 8GB+ 显存 |
| 内存 | 8GB | 16GB |
| 存储 | 20GB | 30GB |

## 📁 项目结构

```
sharp/
├── app.py              # Flask API 服务器
├── gpu_manager.py      # GPU 资源管理
├── mcp_server.py       # MCP 接口
├── templates/          # Web UI 模板
├── static/             # 前端资源
├── src/sharp/          # 核心模型代码
├── Dockerfile          # 容器定义
└── docker-compose.yml  # Compose 配置
```

## 🔧 技术栈

- **模型**：Apple SHARP（3D 高斯点云）
- **后端**：Flask + Gunicorn
- **GPU**：CUDA 12.4 + PyTorch
- **容器**：NVIDIA Docker
- **MCP**：FastMCP

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 推理时间 | ~1 秒 |
| 视频渲染 | ~80 秒 |
| GPU 显存 | ~2.7 GB |
| PLY 文件大小 | ~60 MB |

## 📝 更新日志

### v1.0.0 (2024-12-27)
- 首次发布
- Web UI 视频预览
- REST API + Swagger 文档
- MCP 服务器集成
- 自动 GPU 显存管理

## 📄 许可证

本项目使用 Apple 示例代码许可证。详见 [LICENSE](LICENSE)。

## 🙏 致谢

- [Apple Research](https://machinelearning.apple.com/) - SHARP 模型
- [3D Gaussian Splatting](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) - 渲染技术

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/sharp&type=Date)](https://star-history.com/#neosun100/sharp)

## 📱 关注公众号

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
