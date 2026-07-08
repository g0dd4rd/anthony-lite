# Installation Guide

## Quick Install

Run the automated installation script:

```bash
cd ~/anthony-lite
./install.sh
```

The script will:
1. Install system packages (ALSA, PortAudio, PipeWire utils, playerctl)
2. Install Python packages (PyAudio, Whisper, Piper, MCP, etc.)
3. Install Anthony MCP server (GNOME/KDE desktop automation)
4. Download Piper voice model
5. Enable accessibility (required for dialog detection)
6. Build llama.cpp (auto-detects CUDA / Vulkan / CPU)
7. Check for LLM model files
8. Verify all dependencies

## What Gets Installed

### System Packages (via dnf)
- `alsa-utils` - Audio playback (aplay for TTS)
- `portaudio-devel` - Audio I/O library (required by PyAudio)
- `python3-devel` - Python development headers
- `pipewire-utils` - Volume control (pactl)
- `playerctl` - Media player control (MPRIS)

### Python Packages (via pip)
- `faster-whisper` - Speech-to-text (Whisper medium.en)
- `piper-tts` - Neural text-to-speech
- `torch` - PyTorch (for Silero VAD)
- `pyaudio` - Microphone recording
- `sounddevice` - ALSA warning suppression
- `numpy` - Numerical operations
- `webcolors` - Color name lookup for pick_color
- `mcp` - Model Context Protocol client
- `dogtail` - GNOME accessibility / dialog handling

### Anthony MCP
- GNOME Shell extension / KDE KWin scripting for window/input/settings/media control
- Python MCP server wrapping the D-Bus interface
- System control tools (battery, brightness, power profile, lock, power actions)

### LLM Inference
- **llama.cpp** - Built from source with CUDA, Vulkan, or CPU backend
- **Gemma 4 QAT** - Download with `./download_model.sh` from Unsloth (no login required)

### Models
- **Piper en_US-lessac-medium** - Neural voice (~60MB, downloaded by install script)
- **Whisper medium.en** - STT (~1.5GB, auto-downloads on first run)
- **Silero VAD** - Voice activity detection (~2MB, auto-downloads on first run)

## Manual Installation

If you prefer to install manually or the script fails:

### 1. System Packages
```bash
sudo dnf install -y alsa-utils portaudio-devel python3-devel pipewire-utils playerctl
```

### 2. Python Packages
```bash
pip install sounddevice pyaudio faster-whisper piper-tts mcp torch numpy \
    webcolors dogtail parse
```

### 3. Anthony MCP
```bash
git clone https://github.com/g0dd4rd/anthony-mcp.git ~/anthony-lite-mcp
cd ~/anthony-lite-mcp && ./install.sh
```

### 4. Piper Voice Model
```bash
cd ~/anthony-lite
python3 -m piper.download_voices --download-dir . en_US-lessac-medium
```

### 5. Enable Accessibility
```bash
gsettings set org.gnome.desktop.interface toolkit-accessibility true
```

### 6. llama.cpp + LLM Model
```bash
cd ~/anthony-lite
./build_llama.sh        # auto-detects CUDA / Vulkan / CPU
./download_model.sh     # downloads Gemma 4 E2B QAT from Unsloth
./download_model.sh e4b # or E4B for higher quality (larger)
```

## Verification

```bash
# Check commands
which python3 pip anthony-mcp aplay pactl playerctl

# Check Python modules
python3 -c "import sounddevice, pyaudio, faster_whisper, piper, mcp, torch, \
    webcolors, dogtail, parse"

# Check Piper model
ls -lh ~/anthony-lite/en_US-lessac-medium.onnx*

# Check accessibility
gsettings get org.gnome.desktop.interface toolkit-accessibility

# Check llama-server (Unix socket)
curl -s --unix-socket /run/user/$(id -u)/anthony/llama.sock http://localhost/health
```

## First Run

```bash
cd ~/anthony-lite
./orchestrator.py
```

First run will auto-download Whisper and Silero VAD models.

## Troubleshooting

### PyAudio build fails
```bash
sudo dnf install portaudio-devel python3-devel
pip install --upgrade pip setuptools wheel
pip install pyaudio
```

### MCP server not found
```bash
cd ~/anthony-lite-mcp && pip install -e mcp-server
which anthony-mcp  # Should return a path
```

### Accessibility not working
```bash
gsettings set org.gnome.desktop.interface toolkit-accessibility true
# May need to log out/in for full effect
```

## System Requirements

- **OS**: Fedora (or compatible RPM-based distro)
- **RAM**: 16GB+ recommended (32GB for comfortable CPU-only inference)
- **GPU**: CUDA or Vulkan-capable (tested on Intel Arc A770M, NVIDIA GPUs); CPU-only also works
- **Disk**: ~10GB free (llama.cpp, LLM model, voice models)
- **Audio**: Bluetooth headset recommended for best voice recognition accuracy and privacy
- **Desktop**: GNOME or KDE Plasma (Wayland or X11)

## Uninstallation

```bash
cd ~/anthony-lite
./uninstall.sh       # interactive — asks before each step
./uninstall.sh --all # remove everything without prompting
```
