# SHARP MCP Guide

## Overview

SHARP provides a Model Context Protocol (MCP) interface for programmatic access to the 3D Gaussian Splat generation capabilities.

## Available Tools

### 1. `predict`
Generate 3D Gaussian Splat from a single image.

**Parameters:**
- `file_path` (required): Path to input image (JPEG, PNG, HEIC, etc.)
- `output_path` (optional): Output path for PLY file

**Returns:**
```json
{
  "status": "success",
  "output_path": "/tmp/sharp/output/image.ply",
  "image_info": {
    "width": 1920,
    "height": 1080,
    "focal_length_px": 1234.5
  }
}
```

### 2. `batch_predict`
Process multiple images in a directory.

**Parameters:**
- `input_dir` (required): Directory containing input images
- `output_dir` (optional): Output directory for PLY files

**Returns:**
```json
{
  "status": "success",
  "processed": 5,
  "results": [...]
}
```

### 3. `gpu_status`
Get current GPU status and memory usage.

**Returns:**
```json
{
  "model_loaded": true,
  "device": "cuda",
  "gpu_memory_allocated_mb": 4096.5,
  "gpu_memory_reserved_mb": 5120.0,
  "idle_timeout": 300
}
```

### 4. `gpu_offload`
Force offload model from GPU to free VRAM.

### 5. `get_supported_formats`
Get list of supported input image formats.

## Configuration

### MCP Server Config (for Claude Desktop, etc.)

```json
{
  "mcpServers": {
    "sharp": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "GPU_IDLE_TIMEOUT": "300",
        "OUTPUT_DIR": "/tmp/sharp/output"
      }
    }
  }
}
```

### Docker MCP Config

```json
{
  "mcpServers": {
    "sharp": {
      "command": "docker",
      "args": ["exec", "-i", "sharp-service", "python", "mcp_server.py"],
      "env": {}
    }
  }
}
```

## Usage Examples

### Python Client
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Generate 3D Gaussian Splat
            result = await session.call_tool(
                "predict",
                {"file_path": "/path/to/image.jpg"}
            )
            print(result)

asyncio.run(main())
```

## API vs MCP Comparison

| Feature | REST API | MCP |
|---------|----------|-----|
| Access | HTTP requests | Direct tool calls |
| Use case | Web apps, integrations | AI assistants, automation |
| File handling | Upload via multipart | Local file paths |
| Batch processing | Multiple requests | Single tool call |
| GPU management | Shared | Shared |

## Environment Variables

- `GPU_IDLE_TIMEOUT`: Seconds before auto-offloading model (default: 300)
- `OUTPUT_DIR`: Default output directory (default: /tmp/sharp/output)
- `MODEL_PATH`: Path to model checkpoint (auto-downloads if not set)
