#!/bin/bash
#
# Quantize gemma4:e4b to Q4/Q5 variants for faster inference
#
# This script:
# 1. Builds llama.cpp with Vulkan support (Intel Arc GPU)
# 2. Exports gemma4:e4b from Ollama
# 3. Quantizes to Q5_K_M and Q4_K_M variants
# 4. Imports back into Ollama as gemma4:q5 and gemma4:q4
#

set -e  # Exit on error

WORK_DIR="$HOME/gemma4-quantize"
LLAMA_CPP_DIR="$WORK_DIR/llama.cpp"

echo "======================================================================="
echo "GEMMA4 QUANTIZATION SCRIPT"
echo "======================================================================="
echo ""
echo "This will create faster Q5 and Q4 variants of gemma4:e4b"
echo ""
echo "Expected sizes:"
echo "  gemma4:e4b (Q8)     - 9.6 GB  (current)"
echo "  gemma4:q5 (Q5_K_M)  - 6.5 GB  (20% faster, minimal quality loss)"
echo "  gemma4:q4 (Q4_K_M)  - 5.5 GB  (35% faster, noticeable quality loss)"
echo ""
echo "Working directory: $WORK_DIR"
echo "======================================================================="
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Create working directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Step 1: Check/Build llama.cpp
echo ""
echo "[1/6] Checking llama.cpp..."
if [ -d "$LLAMA_CPP_DIR" ]; then
    echo "✓ llama.cpp already exists at $LLAMA_CPP_DIR"

    # Check if quantize binary exists
    if [ ! -f "$LLAMA_CPP_DIR/build/bin/llama-quantize" ]; then
        echo "⚠️  quantize binary not found, rebuilding..."
        cd "$LLAMA_CPP_DIR"
        git pull
        rm -rf build
    else
        echo "✓ quantize binary found"
        cd "$LLAMA_CPP_DIR"
    fi
else
    echo "Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp "$LLAMA_CPP_DIR"
    cd "$LLAMA_CPP_DIR"
fi

# Build if needed
if [ ! -f "$LLAMA_CPP_DIR/build/bin/llama-quantize" ]; then
    echo ""
    echo "Building llama.cpp with Vulkan support (for Intel Arc GPU)..."
    echo "This may take 5-10 minutes..."

    # Install dependencies
    echo "Installing build dependencies..."
    sudo dnf install -y cmake gcc-c++ vulkan-headers vulkan-loader-devel

    # Build
    cmake -B build -DGGML_VULKAN=ON
    cmake --build build --config Release -j$(nproc)

    echo "✓ Build complete"
else
    echo "✓ llama.cpp already built"
fi

# Verify quantize tool
if [ ! -f "$LLAMA_CPP_DIR/build/bin/llama-quantize" ]; then
    echo "❌ Error: quantize binary not found after build"
    exit 1
fi

echo "✓ llama.cpp ready"

# Step 2: Export gemma4:e4b from Ollama
echo ""
echo "[2/6] Exporting gemma4:e4b from Ollama..."

# Find model blob
MODEL_BLOB=$(ollama show gemma4:e4b --modelfile | grep "^FROM" | awk '{print $2}')

if [ -z "$MODEL_BLOB" ]; then
    echo "❌ Error: Could not find gemma4:e4b model"
    echo "Make sure gemma4:e4b is installed: ollama list | grep gemma4"
    exit 1
fi

echo "Found model blob: $MODEL_BLOB"

# Copy to working directory
ORIGINAL_MODEL="$WORK_DIR/gemma4-e4b-original.gguf"

if [ -f "$ORIGINAL_MODEL" ]; then
    echo "✓ Original model already exported"
else
    echo "Copying model (9.6GB, may take a minute)..."
    cp "$MODEL_BLOB" "$ORIGINAL_MODEL"
    echo "✓ Model exported"
fi

# Verify file size
ORIGINAL_SIZE=$(du -h "$ORIGINAL_MODEL" | cut -f1)
echo "Original model size: $ORIGINAL_SIZE"

# Step 3: Quantize to Q5_K_M
echo ""
echo "[3/6] Quantizing to Q5_K_M (recommended)..."

Q5_MODEL="$WORK_DIR/gemma4-q5_k_m.gguf"

if [ -f "$Q5_MODEL" ]; then
    echo "✓ Q5_K_M model already exists"
else
    echo "This will take 2-5 minutes..."
    "$LLAMA_CPP_DIR/build/bin/llama-quantize" "$ORIGINAL_MODEL" "$Q5_MODEL" Q5_K_M
    echo "✓ Q5_K_M quantization complete"
fi

Q5_SIZE=$(du -h "$Q5_MODEL" | cut -f1)
echo "Q5_K_M model size: $Q5_SIZE"

# Step 4: Quantize to Q4_K_M
echo ""
echo "[4/6] Quantizing to Q4_K_M (fastest)..."

Q4_MODEL="$WORK_DIR/gemma4-q4_k_m.gguf"

if [ -f "$Q4_MODEL" ]; then
    echo "✓ Q4_K_M model already exists"
else
    echo "This will take 2-5 minutes..."
    "$LLAMA_CPP_DIR/build/bin/llama-quantize" "$ORIGINAL_MODEL" "$Q4_MODEL" Q4_K_M
    echo "✓ Q4_K_M quantization complete"
fi

Q4_SIZE=$(du -h "$Q4_MODEL" | cut -f1)
echo "Q4_K_M model size: $Q4_SIZE"

# Step 5: Import Q5 to Ollama
echo ""
echo "[5/6] Importing Q5_K_M to Ollama as gemma4:q5..."

cat > "$WORK_DIR/Modelfile.q5" << 'EOF'
FROM ./gemma4-q5_k_m.gguf
TEMPLATE {{ .Prompt }}
RENDERER gemma4
PARSER gemma4
PARAMETER temperature 1
PARAMETER top_k 64
PARAMETER top_p 0.95
EOF

ollama create gemma4:q5 -f "$WORK_DIR/Modelfile.q5"
echo "✓ gemma4:q5 imported"

# Step 6: Import Q4 to Ollama
echo ""
echo "[6/6] Importing Q4_K_M to Ollama as gemma4:q4..."

cat > "$WORK_DIR/Modelfile.q4" << 'EOF'
FROM ./gemma4-q4_k_m.gguf
TEMPLATE {{ .Prompt }}
RENDERER gemma4
PARSER gemma4
PARAMETER temperature 1
PARAMETER top_k 64
PARAMETER top_p 0.95
EOF

ollama create gemma4:q4 -f "$WORK_DIR/Modelfile.q4"
echo "✓ gemma4:q4 imported"

# Summary
echo ""
echo "======================================================================="
echo "QUANTIZATION COMPLETE!"
echo "======================================================================="
echo ""
echo "Available models:"
ollama list | grep gemma4
echo ""
echo "Quick test:"
echo "  ollama run gemma4:q5 'What is 2+2?'"
echo "  ollama run gemma4:q4 'What is 2+2?'"
echo ""
echo "Update orchestrator to use Q5:"
echo "  Edit voice-driven-orchestrator-mcp-conversational.py"
echo "  Change model='gemma4:e4b' to model='gemma4:q5'"
echo ""
echo "Expected improvements with Q5:"
echo "  - 20% faster inference"
echo "  - 32% smaller (9.6GB → 6.5GB)"
echo "  - Minimal quality loss"
echo ""
echo "Expected improvements with Q4:"
echo "  - 35% faster inference"
echo "  - 43% smaller (9.6GB → 5.5GB)"
echo "  - Noticeable quality loss (not recommended for vision)"
echo ""
echo "Files saved in: $WORK_DIR"
echo "======================================================================="
