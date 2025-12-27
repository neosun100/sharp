#!/bin/bash
set -e

echo "🚀 SHARP Service Launcher"
echo "========================="

# Check nvidia-docker
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ nvidia-smi not found. Please install NVIDIA drivers."
    exit 1
fi

if ! docker info 2>/dev/null | grep -q "Runtimes.*nvidia"; then
    echo "⚠️  nvidia-docker runtime not detected, using deploy.resources instead"
fi

# Auto-select GPU with least memory usage
echo "🔍 Detecting GPUs..."
GPU_ID=$(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | \
         sort -t',' -k2 -n | head -1 | cut -d',' -f1 | tr -d ' ')
echo "✅ Selected GPU: $GPU_ID"

# Find available port starting from 8080
find_available_port() {
    local port=$1
    while ss -tlnp 2>/dev/null | grep -q ":$port "; do
        port=$((port + 1))
    done
    echo $port
}

DEFAULT_PORT=8080
PORT=$(find_available_port $DEFAULT_PORT)
echo "✅ Using port: $PORT"

# Export environment variables
export NVIDIA_VISIBLE_DEVICES=$GPU_ID
export CUDA_VISIBLE_DEVICES=$GPU_ID
export PORT=$PORT
export HOST_IP=0.0.0.0
export GPU_IDLE_TIMEOUT=${GPU_IDLE_TIMEOUT:-300}
export DATA_DIR=${DATA_DIR:-/tmp/sharp}

# Create data directories
mkdir -p "$DATA_DIR/input" "$DATA_DIR/output"

# Create .env file
cat > .env << EOF
PORT=$PORT
HOST_IP=$HOST_IP
GPU_IDLE_TIMEOUT=$GPU_IDLE_TIMEOUT
NVIDIA_VISIBLE_DEVICES=$GPU_ID
CUDA_VISIBLE_DEVICES=$GPU_ID
DATA_DIR=$DATA_DIR
EOF

echo "📦 Building and starting container..."
docker compose up --build -d

echo ""
echo "=========================================="
echo "✅ SHARP Service Started Successfully!"
echo "=========================================="
echo ""
echo "🌐 Web UI:     http://0.0.0.0:$PORT"
echo "📚 API Docs:   http://0.0.0.0:$PORT/docs"
echo "❤️  Health:    http://0.0.0.0:$PORT/health"
echo "🎮 GPU:        $GPU_ID"
echo ""
echo "📁 Data Dir:   $DATA_DIR"
echo "   - Input:    $DATA_DIR/input"
echo "   - Output:   $DATA_DIR/output"
echo ""
echo "🔧 Commands:"
echo "   docker compose logs -f    # View logs"
echo "   docker compose down       # Stop service"
echo ""
