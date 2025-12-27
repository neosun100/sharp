# SHARP - Monocular View Synthesis
# GPU-accelerated Docker image with UI + API + MCP support

FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-dev python3.11-venv python3-pip \
    git wget curl ffmpeg libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt pyproject.toml ./
COPY src ./src

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir \
    flask flask-cors flasgger gunicorn \
    fastmcp pillow-heif

# Download model checkpoint
RUN mkdir -p /root/.cache/torch/hub/checkpoints && \
    wget -q https://ml-site.cdn-apple.com/models/sharp/sharp_2572gikvuh.pt \
    -O /root/.cache/torch/hub/checkpoints/sharp_2572gikvuh.pt

# Copy application files
COPY app.py gpu_manager.py mcp_server.py ./
COPY templates ./templates
COPY static ./static

# Create directories
RUN mkdir -p /tmp/sharp/input /tmp/sharp/output

ENV PORT=8080
ENV GPU_IDLE_TIMEOUT=300
ENV MODEL_PATH=/root/.cache/torch/hub/checkpoints/sharp_2572gikvuh.pt

EXPOSE 8080

CMD ["python", "app.py"]
