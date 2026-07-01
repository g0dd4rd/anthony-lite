# ANTHONY-LITE.md — Project Map for AI Agents

> **Audience:** LLMs and AI coding agents.
> Read this file first to understand the codebase before making changes.

## What This Project Is

Anthony Lite is a voice-driven desktop orchestrator for GNOME/Linux. Users speak natural language commands to control windows, launch apps, manage audio, take screenshots, and more. Commands are handled by fast pattern matching (~1ms). A local LLM (gemma4 via llama-server) is only used for conversation mode and vision — not for command routing.

This is the lightweight fork of [anthony](https://github.com/g0dd4rd/anthony), optimized for hardware with limited GPU. The full anthony uses an embedding model for semantic command fallback; anthony-lite uses pure pattern matching via `@step` decorated handlers.

## Architecture Overview

```
Voice Input (mic)
    │
    ▼
┌──────────────┐     ┌─────────────────┐
│  voice_io.py │     │  orchestrator.py │ ◄── entry point
│  (STT + TTS) │────►│  (main loop)     │
└──────────────┘     └────────┬─────────┘
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
          ┌──────────────────┐   ┌─────────────┐
          │ command_matcher  │   │ conversation │
          │ .py              │   │ .py          │
          │ (pattern + sem.) │   │ (LLM chat)   │
          └────────┬─────────┘   └─────────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  commands/       │
          │  (@step handlers │
          │   → MCP calls)   │
          └────────┬─────────┘
                   │ MCP protocol (stdio)
                   ▼
          ┌──────────────────┐
          │  anthony-mcp     │
          │  (GNOME extension│
          │  + MCP server)   │
          └──────────────────┘
```

## Request Flow

1. **Voice capture** — `voice_io.py` uses Silero VAD for continuous listening, then Whisper (faster-whisper) for transcription
2. **Mode routing** — `orchestrator.py` checks current mode: `command` (default) or `conversation`
3. **Command path:**
   - `command_matcher.execute()` preprocesses input (number words, dashes, percent)
   - Splits compound commands on "and"/"then" with pronoun resolution
   - For each segment: exact pattern match → verb carry-forward
   - Validates required handler params via `inspect.signature()` before calling
   - Handler calls `mcp_client.call_tool()` directly — no facade layer
4. **Conversation path:** `conversation.handle_conversation()` sends to llama-server for LLM response
5. **Voice output** — `voice_io.py` synthesizes response with Piper TTS

## Module Map

### Core

| File | Purpose |
|---|---|
| `orchestrator.py` | Entry point. llama-server lifecycle, module init, voice loop. CLI: `--ptt`, `--debug`, `--restart-server`, `--kill-server` |
| `voice_io.py` | STT (faster-whisper + Silero VAD) and TTS (Piper). Exports `speak()`, `listen_and_transcribe()`, `check_audio_health()` |
| `command_matcher.py` | Pattern matching via `registry.match()` (~1ms). Handles compound commands, segment splitting, pronoun resolution, verb carry-forward, auto-recovery |
| `app_index.py` | App indexing via Gio.AppInfo. Builds `app_name_map` (name→exec), `smart_match_window()`, `get_friendly_app_name()`, `detect_app_in_input()` |
| `conversation.py` | LLM chat mode. Multi-turn conversation via llama-server |
| `dialog_handler.py` | Safe close handling via dogtail (AT-SPI/a11y). Detects save/discard dialogs filtered by app name, reads options, activates buttons via keyboard |
| `mcp_client.py` | Standalone MCP client for testing |
| `utils.py` | Logging setup and `log_and_print()` helper |

### commands/ — Step Handlers

Each module registers `@step` decorated handlers with patterns, category, and help_text. Handlers receive `(context, **params)` and return a string for TTS.

| File | Category | Examples |
|---|---|---|
| `window.py` | window | focus, close, minimize, maximize, restore, tile, list windows, screenshot |
| `audio.py` | audio | volume set/up/down, mute/unmute, play/pause, next/previous track |
| `input.py` | input | click, double-click, right-click, drag, type text, key combos, scroll |
| `search.py` | search | open app/URL/file, search files |
| `system.py` | system | time, notifications, reminders, list apps, cleanup screenshots, enable/disable automation |
| `vision.py` | vision | screenshot, describe window/screen, pick color, monitor info |
| `workspace.py` | workspace | list/switch workspaces |
| `settings.py` | settings | dark mode, night light, DND, wifi, bluetooth, wallpaper |
| `brightness.py` | brightness | set/increase/decrease brightness |
| `power.py` | power | lock, sleep, restart, shut down |
| `apps.py` | apps | install/uninstall apps, keyboard shortcuts lookup |
| `help.py` | help | "help", "help with {category}" — lists available commands from registry |
| `__init__.py` | — | `CommandRegistry` class, `step` decorator, `init()` wiring |

### config/

| File | Purpose |
|---|---|
| `aliases.py` | `APP_SHORTCUT_ALIASES` (friendly name → shortcut JSON key) and `APP_A11Y_NAMES` (exec_name → AT-SPI name for dialog handler) |
| `prompts.py` | LLM prompts: intent classifier, conversation system prompt |

### shortcuts/

| File | Purpose |
|---|---|
| `gnome_shortcuts.py` | Reads keyboard shortcuts from gsettings schemas at runtime |
| `app_shortcuts.json` | Curated per-app shortcut database |

### tools/

| File | Purpose |
|---|---|
| `discover_a11y.py` | Standalone script: launches each GUI app, discovers its AT-SPI name via dogtail, writes `APP_A11Y_NAMES` to `config/aliases.py` |

## Key Design Patterns

### @step Decorator (commands/)
Commands are defined as decorated functions. The decorator registers patterns, category, and help text in a central `CommandRegistry`. The same definitions serve as pattern matcher input, help system source, and (future) BDD test targets.

```python
@step('set volume to {level:d}', 'volume {level:d}',
      category='audio', help_text='Set volume to a specific level')
def handle_set_volume(context, level):
    _mcp_client.call_tool("set_volume", {"level": level})
    return f"Volume set to {level}"
```

### Pattern Matching (command_matcher.py)
`parse` library extracts typed params from ~95 patterns across 13 command modules (~1ms). Compound commands are split on "and"/"then", with verb carry-forward ("minimize firefox and chrome" → minimize firefox, minimize chrome) and pronoun resolution.

### Dependency Injection
Modules use `init()` functions to receive runtime dependencies (mcp_client, speak, etc.). The orchestrator wires everything at startup. Command handlers access shared state via module-level globals set by `commands.init()`.

### Safe Close Protocol (dialog_handler.py + commands/window.py)
When closing a window: (1) resolve AT-SPI name from `APP_A11Y_NAMES`, (2) send close_window via MCP, (3) `dialog_handler.find_dialogs(app_name=...)` searches only that app's a11y tree, (4) speak button options, (5) listen for user choice, (6) activate button via keyboard.

## External Dependencies

### ML Models (loaded at startup)
- **faster-whisper** `medium.en` — speech-to-text (CPU, int8)
- **Silero VAD** — voice activity detection (torch)
- **Piper** `en_US-lessac-medium` — text-to-speech (ONNX)

### LLM Server (separate process)
- **llama-server** (llama.cpp) running gemma4-e4b with Vulkan GPU on port 8081
- Only used for conversation mode — not for command routing

### Companion Repo
- **anthony-mcp** — GNOME Shell extension + MCP server providing desktop automation tools (window management, input simulation, screenshots, system settings, audio, etc.)

## Running

```bash
# Default: continuous VAD listening
python orchestrator.py

# Push-to-talk mode
python orchestrator.py --ptt

# With debug output
python orchestrator.py --debug

# Discover AT-SPI names for dialog handler
python tools/discover_a11y.py
```

Requires: llama-server running (auto-started), anthony-mcp installed, GNOME accessibility enabled (auto-enabled).
