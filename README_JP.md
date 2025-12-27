[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# 🎯 SHARP - 単眼ビュー合成

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fsharp-blue?logo=docker)](https://hub.docker.com/r/neosun/sharp)
[![Version](https://img.shields.io/badge/version-v1.0.0-green)](https://github.com/neosun100/sharp/releases)
[![License](https://img.shields.io/badge/license-Apple%20Sample%20Code-lightgrey)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-2512.10685-b31b1b.svg)](https://arxiv.org/abs/2512.10685)

> 1枚の画像から1秒以内にインタラクティブな3Dシーンを生成

![Demo](assets/demo.gif)

## ✨ SHARPとは？

SHARPはApple Researchが発表したAIモデルで、1枚の2D写真を3Dガウシアンスプラット表現に変換します。

- **写真から3D**：任意の写真をインタラクティブな3Dシーンに変換
- **リアルタイムレンダリング**：生成された3DGSはリアルタイムでレンダリング可能
- **超高速**：GPU推論は1秒未満
- **ゼロショット汎化**：ファインチューニング不要、あらゆる画像に対応

### ユースケース

| 業界 | 用途 |
|------|------|
| Eコマース | 1枚の写真から360°商品ビュー |
| 不動産 | バーチャル物件ツアー |
| SNS | 3D写真エフェクト |
| ゲーム/VFX | 高速3Dアセットプロトタイピング |
| AR/VR | 高速環境生成 |

> ⚠️ **注意**：SHARPは小範囲のビュー合成（±15-30°）を生成し、完全な360°再構築ではありません。視差効果や深度認識レンダリングに最適です。

## 🚀 クイックスタート

### Docker（推奨）

```bash
# プルして実行（All-in-One、モデル込み約15GB）
docker run -d --gpus all -p 8080:8080 --name sharp neosun/sharp:latest

# Web UIにアクセス
open http://localhost:8080

# APIドキュメント
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

## 📦 機能

このDockerイメージは3つのインターフェースを提供：

| インターフェース | ポート | 説明 |
|------------------|--------|------|
| Web UI | 8080 | 画像アップロード、3D結果表示 |
| REST API | 8080 | プログラムアクセス、Swaggerドキュメント付き |
| MCP Server | stdio | AIアシスタント統合 |

## 🌐 Webインターフェース

`http://localhost:8080` にアクセス：

- ドラッグ＆ドロップで画像アップロード
- リアルタイム3Dプレビュー（ループ動画）
- PLYとMP4ファイルのダウンロード
- GPUステータス監視
- 多言語対応（英語/中国語）

## 📡 REST API

### エンドポイント

| メソッド | エンドポイント | 説明 |
|----------|----------------|------|
| GET | `/health` | ヘルスチェック |
| POST | `/api/predict` | 画像から3D生成 |
| GET | `/api/files/{id}.ply` | PLYファイルダウンロード |
| GET | `/api/files/{id}.mp4` | 動画ダウンロード |
| GET | `/api/gpu/status` | GPUステータス |
| POST | `/api/gpu/offload` | GPUメモリ解放 |
| GET | `/docs` | Swaggerドキュメント |

### 例：3Dシーン生成

```bash
# 画像をアップロードして3D生成
curl -X POST http://localhost:8080/api/predict \
  -F "file=@photo.jpg" \
  -F "render_video=true"

# レスポンス
{
  "task_id": "abc123",
  "ply_url": "/api/files/abc123.ply",
  "video_url": "/api/files/abc123.mp4"
}

# 結果をダウンロード
curl -O http://localhost:8080/api/files/abc123.ply
curl -O http://localhost:8080/api/files/abc123.mp4
```

## 🤖 MCP統合

SHARPにはAIアシスタント統合用のMCP（Model Context Protocol）サーバーが含まれています。

### 設定方法

MCPクライアント設定に追加（例：Claude Desktop）：

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

### 利用可能なツール

| ツール | 説明 |
|--------|------|
| `predict` | 1枚の画像から3D生成 |
| `batch_predict` | 複数画像のバッチ処理 |
| `gpu_status` | GPUステータス確認 |
| `gpu_offload` | GPUメモリ解放 |
| `get_supported_formats` | サポート画像形式一覧 |

## ⚙️ 設定

### 環境変数

| 変数 | デフォルト | 説明 |
|------|------------|------|
| `PORT` | 8080 | サーバーポート |
| `GPU_IDLE_TIMEOUT` | 300 | 自動オフロードまでのアイドル時間（秒） |
| `MODEL_PATH` | (内蔵) | カスタムモデルパス |

### ハードウェア要件

| コンポーネント | 最小 | 推奨 |
|----------------|------|------|
| GPU | 4GB VRAM | 8GB+ VRAM |
| RAM | 8GB | 16GB |
| ストレージ | 20GB | 30GB |

## 📊 パフォーマンス

| 指標 | 値 |
|------|-----|
| 推論時間 | ~1秒 |
| 動画レンダリング | ~80秒 |
| GPUメモリ | ~2.7 GB |
| PLYファイルサイズ | ~60 MB |

## 📝 変更履歴

### v1.0.0 (2024-12-27)
- 初回リリース
- Web UI動画プレビュー
- REST API + Swaggerドキュメント
- MCPサーバー統合
- 自動GPUメモリ管理

## 📄 ライセンス

このプロジェクトはAppleサンプルコードライセンスを使用しています。詳細は[LICENSE](LICENSE)を参照。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/sharp&type=Date)](https://star-history.com/#neosun100/sharp)

## 📱 公式アカウント

![公式アカウント](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
