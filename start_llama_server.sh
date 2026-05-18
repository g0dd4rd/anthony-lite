#!/bin/bash
# Start llama-server with Gemma 4 E4B and Vulkan GPU acceleration

MODEL_PATH="$HOME/models/gemma4-e4b-q4km.gguf"
MMPROJ_PATH="$HOME/models/mmproj-gemma-4-E4B-it-Q8_0.gguf"
LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"
PORT=8081

echo "🚀 Starting llama-server with Vulkan GPU acceleration"
echo "=================================================="
echo "Model: $MODEL_PATH"
echo "Port: $PORT"
echo "API: http://127.0.0.1:$PORT"
echo ""

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Model not found: $MODEL_PATH"
    exit 1
fi

# Check if server binary exists
if [ ! -f "$LLAMA_SERVER" ]; then
    echo "❌ llama-server not found: $LLAMA_SERVER"
    exit 1
fi

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port $PORT already in use"
    echo "Kill existing server? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        kill $(lsof -t -i:$PORT)
        sleep 1
    else
        exit 1
    fi
fi

# Start server
echo "Starting server..."
"$LLAMA_SERVER" \
    --model "$MODEL_PATH" \
    --ctx-size 4096 \
    --n-gpu-layers 99 \
    --device Vulkan0 \
    --port $PORT \
    --host 127.0.0.1 \
    --threads 6 \
    --parallel 1 \
    --cont-batching \
    --flash-attn auto \
    --mmproj "$MMPROJ_PATH" \
    --log-format text \
    --metrics

echo ""
echo "Server started!"
echo ""
echo "Test with:"
echo "  curl http://127.0.0.1:$PORT/health"
echo ""
