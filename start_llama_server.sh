#!/bin/bash
# Start llama-server with Gemma 4 and Vulkan GPU acceleration
#
# Usage:
#   ./start_llama_server.sh          # default: e2b
#   ./start_llama_server.sh e2b      # Gemma 4 E2B Q8_0 (faster, ~12-15 tok/s)
#   ./start_llama_server.sh e4b      # Gemma 4 E4B Q4_K_M (slower, ~6-7 tok/s)

VARIANT="${1:-e2b}"
LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"
PORT=8081

case "$VARIANT" in
    e2b)
        MODEL_PATH="$HOME/models/gemma-4-E2B-it-Q8_0.gguf"
        MMPROJ_PATH="$HOME/models/mmproj-BF16.gguf"
        ;;
    e4b)
        MODEL_PATH="$HOME/models/gemma4-e4b-q4km.gguf"
        MMPROJ_PATH="$HOME/models/mmproj-gemma-4-E4B-it-Q8_0.gguf"
        ;;
    *)
        echo "Unknown variant: $VARIANT (use e2b or e4b)"
        exit 1
        ;;
esac

echo "Starting llama-server with Vulkan GPU acceleration"
echo "=================================================="
echo "Variant: $VARIANT"
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
    --metrics

echo ""
echo "Server started!"
echo ""
echo "Test with:"
echo "  curl http://127.0.0.1:$PORT/health"
echo ""
