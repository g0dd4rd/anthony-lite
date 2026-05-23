# Anthony Lite

Lightweight voice-driven desktop orchestrator for GNOME/Linux.

Anthony Lite listens to natural voice commands and controls the GNOME desktop -- managing windows, typing text, adjusting settings, launching apps, describing the screen, and more. Everything runs locally: speech recognition, pattern matching, and text-to-speech. No cloud services, no API keys.

This is the lightweight fork of [anthony](https://github.com/g0dd4rd/anthony), optimized for hardware with limited GPU. The full anthony uses an LLM for all command routing; anthony-lite replaces that with `@step` decorated handlers and semantic fallback, achieving ~1ms response times for most commands.

## Requirements

- Fedora (or RPM-based distro) with GNOME desktop
- 16GB+ RAM
- Vulkan-capable GPU (tested on Intel Arc A770M)
- Working microphone and speakers
- [anthony-mcp](https://github.com/g0dd4rd/anthony-mcp) -- GNOME Shell extension + MCP server

## Quick Start

```bash
git clone https://github.com/g0dd4rd/anthony-lite.git ~/anthony-lite
cd ~/anthony-lite
./install.sh
./orchestrator.py
```

The install script handles system packages, Python dependencies, the Piper voice model, and anthony-mcp setup. First run downloads the Whisper STT model (~1.5GB) and Silero VAD (~2MB) automatically.

llama-server with a Gemma 4 model must be running on port 8081 for conversation mode and vision features. See `start_llama_server.sh` for the recommended launch command.

## Usage

Speak naturally -- Anthony Lite uses voice activity detection (no wake word). Say "switch to chat mode" for open-ended conversation, "switch to command mode" to return to desktop control. Say "help" for available commands.

```
./orchestrator.py           # continuous listening
./orchestrator.py --ptt     # push-to-talk (press Enter to record)
./orchestrator.py --debug   # verbose logging
```

## Voice Commands

| Say this | Does this |
|----------|-----------|
| "open firefox" | Launches or focuses Firefox |
| "close terminal" | Closes the window (with save dialog handling) |
| "tile left" | Snaps the focused window to the left half |
| "take a screenshot" | Full-screen screenshot |
| "type hello world" | Types into the focused application |
| "mute" / "volume to 50" | Audio control via PulseAudio/MPRIS |
| "turn on dark mode" | Toggles GNOME dark theme |
| "describe the screen" | Vision analysis via Gemma 4 |
| "what time is it" | Instant response (no LLM) |
| "set brightness to 70" | Screen brightness via MCP |
| "help" / "help with audio" | Lists available commands |

See [commands.txt](commands.txt) for the full command reference.

## How It Works

1. **Silero VAD** detects speech, **Faster-Whisper** transcribes it
2. **Pattern matching** via `@step` decorated handlers extracts typed params from patterns (~1ms)
3. If no pattern matches, **sentence-transformers** semantic fallback finds the closest command (~50ms, threshold 0.55)
4. Compound commands are split on "and"/"then" with verb carry-forward and pronoun resolution
5. Tools execute through **anthony-mcp** (GNOME Shell extension) via MCP protocol
6. **Piper TTS** speaks the result

The LLM (Gemma 4 via llama-server) is only used for conversation mode and vision -- not for command routing.

## Project Structure

```
orchestrator.py         Main entry point, server lifecycle, voice loop
command_matcher.py      Two-tier matching: parse patterns + semantic fallback
voice_io.py             VAD, STT (Whisper), TTS (Piper)
app_index.py            App indexing, window matching, embedding model
conversation.py         Chat mode with conversation history
dialog_handler.py       Save dialog detection via AT-SPI
mcp_client.py           MCP protocol client
commands/               @step decorated handlers (window, audio, input, etc.)
config/                 Aliases, prompts
shortcuts/              Curated keyboard shortcut data per app
tools/                  AT-SPI discovery script
```

## Documentation

- [commands.txt](commands.txt) -- Full voice command reference
- [ANTHONY-LITE.md](ANTHONY-LITE.md) -- Project map for AI agents
- [INSTALL.md](INSTALL.md) -- Detailed installation guide
- [DEPENDENCIES.md](DEPENDENCIES.md) -- Complete dependency list
- [SETUP-OFFLINE.md](SETUP-OFFLINE.md) -- Offline setup for embedding model

## Related

- [anthony](https://github.com/g0dd4rd/anthony) -- Full LLM-routed version (for faster hardware)
- [anthony-mcp](https://github.com/g0dd4rd/anthony-mcp) -- GNOME Shell extension and MCP server
