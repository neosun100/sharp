[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# 🎯 SHARP - 單目視圖合成

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fsharp-blue?logo=docker)](https://hub.docker.com/r/neosun/sharp)
[![Version](https://img.shields.io/badge/version-v1.0.0-green)](https://github.com/neosun100/sharp/releases)
[![License](https://img.shields.io/badge/license-Apple%20Sample%20Code-lightgrey)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-2512.10685-b31b1b.svg)](https://arxiv.org/abs/2512.10685)

> 一秒內從單張圖片生成互動式 3D 場景

![Demo](assets/demo.gif)

## ✨ 什麼是 SHARP？

SHARP 是 Apple Research 發布的 AI 模型，能將單張 2D 照片轉換為 3D 高斯點雲表示。

- **照片轉 3D**：任意照片轉換為可互動的 3D 場景
- **即時渲染**：生成的 3DGS 可即時渲染
- **超快速度**：GPU 推理不到 1 秒
- **零樣本泛化**：無需微調，適用於任何圖片

### 應用場景

| 產業 | 應用 |
|------|------|
| 電商 | 單張照片生成 360° 產品展示 |
| 房地產 | 虛擬房產導覽 |
| 社群媒體 | 3D 照片特效 |
| 遊戲/影視 | 快速 3D 資產原型 |
| AR/VR | 快速環境生成 |

> ⚠️ **注意**：SHARP 生成小範圍視角合成（±15-30°），不是完整 360° 重建。適合視差效果和深度感知渲染。

## 🚀 快速開始

### Docker（推薦）

```bash
# 拉取並執行（All-in-One，含模型約 15GB）
docker run -d --gpus all -p 8080:8080 --name sharp neosun/sharp:latest

# 存取 Web UI
open http://localhost:8080

# API 文件
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

本 Docker 映像提供三種介面：

| 介面 | 連接埠 | 說明 |
|------|--------|------|
| Web UI | 8080 | 上傳圖片，檢視 3D 結果 |
| REST API | 8080 | 程式化存取，含 Swagger 文件 |
| MCP Server | stdio | AI 助手整合 |

## 🌐 Web 介面

存取 `http://localhost:8080`：

- 拖曳上傳圖片
- 即時 3D 預覽（循環影片）
- 下載 PLY 和 MP4 檔案
- GPU 狀態監控
- 多語言支援（中/英）

## 📡 REST API

### 端點列表

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/health` | 健康檢查 |
| POST | `/api/predict` | 從圖片生成 3D |
| GET | `/api/files/{id}.ply` | 下載 PLY 檔案 |
| GET | `/api/files/{id}.mp4` | 下載影片 |
| GET | `/api/gpu/status` | GPU 狀態 |
| POST | `/api/gpu/offload` | 釋放 GPU 顯存 |
| GET | `/docs` | Swagger 文件 |

### 範例：生成 3D 場景

```bash
# 上傳圖片並生成 3D
curl -X POST http://localhost:8080/api/predict \
  -F "file=@photo.jpg" \
  -F "render_video=true"

# 回應
{
  "task_id": "abc123",
  "ply_url": "/api/files/abc123.ply",
  "video_url": "/api/files/abc123.mp4"
}

# 下載結果
curl -O http://localhost:8080/api/files/abc123.ply
curl -O http://localhost:8080/api/files/abc123.mp4
```

## 🤖 MCP 整合

SHARP 包含 MCP（Model Context Protocol）伺服器，用於 AI 助手整合。

### 設定方法

新增到 MCP 客戶端設定（如 Claude Desktop）：

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

| 工具 | 說明 |
|------|------|
| `predict` | 單張圖片生成 3D |
| `batch_predict` | 批次處理多張圖片 |
| `gpu_status` | 檢視 GPU 狀態 |
| `gpu_offload` | 釋放 GPU 顯存 |
| `get_supported_formats` | 取得支援的圖片格式 |

## ⚙️ 設定說明

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `PORT` | 8080 | 服務連接埠 |
| `GPU_IDLE_TIMEOUT` | 300 | 自動釋放顯存的閒置時間（秒） |
| `MODEL_PATH` | (內建) | 自訂模型路徑 |

### 硬體需求

| 元件 | 最低配置 | 建議配置 |
|------|----------|----------|
| GPU | 4GB 顯存 | 8GB+ 顯存 |
| 記憶體 | 8GB | 16GB |
| 儲存空間 | 20GB | 30GB |

## 📊 效能指標

| 指標 | 數值 |
|------|------|
| 推理時間 | ~1 秒 |
| 影片渲染 | ~80 秒 |
| GPU 顯存 | ~2.7 GB |
| PLY 檔案大小 | ~60 MB |

## 📝 更新日誌

### v1.0.0 (2024-12-27)
- 首次發布
- Web UI 影片預覽
- REST API + Swagger 文件
- MCP 伺服器整合
- 自動 GPU 顯存管理

## 📄 授權條款

本專案使用 Apple 範例程式碼授權。詳見 [LICENSE](LICENSE)。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/sharp&type=Date)](https://star-history.com/#neosun100/sharp)

## 📱 關注公眾號

![公眾號](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
