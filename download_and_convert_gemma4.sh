#!/bin/bash
# Download and convert Gemma 4 E4B to GGUF format for llama.cpp

set -e  # Exit on error

MODEL_NAME="google/gemma-4-E4B-it"
DOWNLOAD_DIR="$HOME/models/gemma-4-E4B-it-hf"
OUTPUT_DIR="$HOME/models"
LLAMA_CPP_DIR="$HOME/llama.cpp"

echo "🚀 Gemma 4 E4B Download and Conversion"
echo "========================================"
echo ""
echo "Model: $MODEL_NAME"
echo "Download to: $DOWNLOAD_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Create directories
mkdir -p "$DOWNLOAD_DIR"
mkdir -p "$OUTPUT_DIR"

# Step 1: Download model from Hugging Face
echo "📥 Step 1: Downloading Gemma 4 E4B from Hugging Face..."
echo "   (This will download ~16GB - may take several minutes)"
echo ""

cd "$DOWNLOAD_DIR"
hf download "$MODEL_NAME" --local-dir .

if [ $? -ne 0 ]; then
    echo "❌ Download failed!"
    exit 1
fi

echo ""
echo "✅ Download complete!"
echo ""

# Step 2: Convert to GGUF (FP16 - full precision)
echo "🔄 Step 2: Converting to GGUF format..."
echo "   Output: $OUTPUT_DIR/gemma4-e4b-fp16.gguf"
echo ""

cd "$LLAMA_CPP_DIR"
python3 convert_hf_to_gguf.py "$DOWNLOAD_DIR" \
    --outfile "$OUTPUT_DIR/gemma4-e4b-fp16.gguf" \
    --outtype f16

if [ $? -ne 0 ]; then
    echo "❌ Conversion failed!"
    exit 1
fi

echo ""
echo "✅ Conversion to FP16 complete!"
echo ""

# Step 3: Quantize to Q4_K_M (matches Ollama's 9GB model)
echo "⚙️  Step 3: Quantizing to Q4_K_M..."
echo "   This reduces size from ~16GB to ~9GB"
echo "   Output: $OUTPUT_DIR/gemma4-e4b-q4km.gguf"
echo ""

cd "$LLAMA_CPP_DIR"
"$LLAMA_CPP_DIR/build/bin/llama-quantize" \
    "$OUTPUT_DIR/gemma4-e4b-fp16.gguf" \
    "$OUTPUT_DIR/gemma4-e4b-q4km.gguf" \
    Q4_K_M

if [ $? -ne 0 ]; then
    echo "❌ Quantization failed!"
    exit 1
fi

echo ""
echo "✅ Quantization complete!"
echo ""

# Step 4: Test the model with llama.cpp + Vulkan
echo "🧪 Step 4: Testing model with Vulkan GPU..."
echo ""

"$LLAMA_CPP_DIR/build/bin/llama-cli" \
    --model "$OUTPUT_DIR/gemma4-e4b-q4km.gguf" \
    --prompt "Hello, how are you?" \
    --n-predict 50 \
    --gpu-layers 99 \
    --device Vulkan0 \
    --ctx-size 2048

if [ $? -ne 0 ]; then
    echo "❌ Test failed!"
    exit 1
fi

echo ""
echo "✅ Test successful!"
echo ""

# Summary
echo "========================================"
echo "🎉 SUCCESS! Model ready for use"
echo "========================================"
echo ""
echo "Files created:"
echo "  FP16 (full):  $OUTPUT_DIR/gemma4-e4b-fp16.gguf (~16GB)"
echo "  Q4_K_M (opt): $OUTPUT_DIR/gemma4-e4b-q4km.gguf (~9GB) ⭐"
echo ""
echo "Use the Q4_K_M version in your orchestrator!"
echo ""
echo "Cleanup (optional):"
echo "  rm $OUTPUT_DIR/gemma4-e4b-fp16.gguf  # Remove FP16 to save space"
echo "  rm -rf $DOWNLOAD_DIR  # Remove HF model files"
echo ""
