#!/bin/bash
# Download Gemma 4 QAT model from Unsloth (no login required)
#
# Usage:
#   ./download_model.sh           # E2B (2.44 GB model + 940 MB mmproj)
#   ./download_model.sh e4b       # E4B (3.93 GB model + 945 MB mmproj)
#   ./download_model.sh --force   # re-download even if files exist

set -euo pipefail

VARIANT="e2b"
FORCE=false
MODELS_DIR="$HOME/models"

for arg in "$@"; do
    case "$arg" in
        e2b) VARIANT="e2b" ;;
        e4b) VARIANT="e4b" ;;
        --force) FORCE=true ;;
        *)
            echo "Usage: $0 [e2b|e4b] [--force]"
            exit 1
            ;;
    esac
done

HF_BASE="https://huggingface.co/unsloth"

case "$VARIANT" in
    e2b)
        REPO="gemma-4-E2B-it-QAT-GGUF"
        MODEL_FILE="gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf"
        MMPROJ_REMOTE="mmproj-BF16.gguf"
        MMPROJ_LOCAL="mmproj-e2b-bf16.gguf"
        ;;
    e4b)
        REPO="gemma-4-E4B-it-QAT-GGUF"
        MODEL_FILE="gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"
        MMPROJ_REMOTE="mmproj-BF16.gguf"
        MMPROJ_LOCAL="mmproj-e4b-bf16.gguf"
        ;;
esac

MODEL_URL="$HF_BASE/$REPO/resolve/main/$MODEL_FILE"
MMPROJ_URL="$HF_BASE/$REPO/resolve/main/$MMPROJ_REMOTE"

mkdir -p "$MODELS_DIR"

echo "=================================================="
echo "Downloading Gemma 4 ${VARIANT^^} QAT (Unsloth)"
echo "=================================================="
echo "Model:  $MODEL_FILE"
echo "mmproj: $MMPROJ_REMOTE → $MMPROJ_LOCAL"
echo "Target: $MODELS_DIR/"
echo ""

download_file() {
    local url="$1"
    local dest="$2"
    local label="$3"

    if [ -f "$dest" ] && [ "$FORCE" = false ]; then
        echo "✓ $label already exists, skipping (use --force to re-download)"
        return 0
    fi

    echo "Downloading $label..."
    if curl -L -C - --progress-bar -o "$dest" "$url"; then
        local size
        size=$(stat --format=%s "$dest" 2>/dev/null || stat -f%z "$dest" 2>/dev/null)
        echo "✓ $label downloaded ($(( size / 1048576 )) MB)"
    else
        echo "✗ Failed to download $label"
        rm -f "$dest"
        return 1
    fi
}

download_file "$MODEL_URL" "$MODELS_DIR/$MODEL_FILE" "$MODEL_FILE"
download_file "$MMPROJ_URL" "$MODELS_DIR/$MMPROJ_LOCAL" "$MMPROJ_LOCAL"

echo ""
echo "Done! Models are in $MODELS_DIR/"
ls -lh "$MODELS_DIR/"*.gguf 2>/dev/null
