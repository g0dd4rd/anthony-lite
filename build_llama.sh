#!/bin/bash
# Build llama.cpp from source (auto-detects Vulkan GPU or builds CPU-only)
#
# Usage:
#   ./build_llama.sh           # clone + build
#   ./build_llama.sh --update  # pull latest + rebuild

set -euo pipefail

LLAMA_DIR="$HOME/llama.cpp"
BUILD_DIR="$LLAMA_DIR/build"
UPDATE=false

if [[ "${1:-}" == "--update" ]]; then
    UPDATE=true
fi

# Build dependencies
PACKAGES_TO_INSTALL=()
if ! command -v cmake &>/dev/null; then
    PACKAGES_TO_INSTALL+=("cmake")
fi
if ! command -v g++ &>/dev/null; then
    PACKAGES_TO_INSTALL+=("gcc-c++")
fi
if ! command -v gcc &>/dev/null; then
    PACKAGES_TO_INSTALL+=("gcc")
fi

if [ ${#PACKAGES_TO_INSTALL[@]} -gt 0 ]; then
    echo "Installing build dependencies: ${PACKAGES_TO_INSTALL[*]}"
    sudo dnf install -y "${PACKAGES_TO_INSTALL[@]}"
fi

# Clone or update
if [ ! -d "$LLAMA_DIR" ]; then
    echo "Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp.git "$LLAMA_DIR"
elif [ "$UPDATE" = true ]; then
    echo "Updating llama.cpp..."
    git -C "$LLAMA_DIR" pull --ff-only
fi

# Detect Vulkan
CMAKE_ARGS=()
if vulkaninfo --summary 2>&1 | grep -q "deviceName" && ! vulkaninfo --summary 2>&1 | grep -q "PHYSICAL_DEVICE_TYPE_CPU"; then
    echo "Vulkan GPU detected — building with GPU support"
    CMAKE_ARGS+=(-DGGML_VULKAN=ON)

    if ! rpm -q vulkan-headers &>/dev/null; then
        echo "Installing Vulkan development headers..."
        sudo dnf install -y vulkan-headers vulkan-loader-devel
    fi
else
    echo "No Vulkan GPU — building CPU-only"
fi

# Configure + build
echo "Configuring..."
cmake -B "$BUILD_DIR" -S "$LLAMA_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    "${CMAKE_ARGS[@]}"

THREADS=$(nproc)
echo "Building with $THREADS threads..."
cmake --build "$BUILD_DIR" --config Release -j"$THREADS" -- llama-server

echo ""
echo "Done! Binary at: $BUILD_DIR/bin/llama-server"
"$BUILD_DIR/bin/llama-server" --version
