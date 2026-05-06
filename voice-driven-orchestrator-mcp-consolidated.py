#!/usr/bin/env python3
"""
Voice-Driven Desktop Orchestrator with CONSOLIDATED TOOLS

This is a REFERENCE implementation showing the facade pattern for tool consolidation.
Reduces 34 individual tools to 6 facade tools while maintaining all functionality.

Key changes from conversational version:
- 34 tools → 6 facade tools (window_control, input_control, audio_control, system_settings, vision_control, workspace_control)
- search (gnome_search) kept as-is
- Expected performance: ~17-20s inference (vs 41-69s with 34 tools)
- RAG retrieval benefits from fewer, clearer choices
"""

import os
import sys

# Force offline mode for sentence-transformers BEFORE import
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

import ollama
import sounddevice
import pyaudio
import shutil, subprocess
import wave
import asyncio
import json
import threading
import time
import collections
import numpy as np
import torch
from queue import Queue
from sentence_transformers import SentenceTransformer

from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dialog_handler import DialogHandler

# ========================================
# 🎯 MODEL CONFIGURATION
# ========================================
COMMAND_MODEL = 'gemma4:e4b'
VISION_MODEL = 'gemma4:e4b'
CONVERSATION_MODEL = 'gemma4:e4b'
CLASSIFIER_MODEL = 'gemma4:e4b'

# ----------------------------------------
# MCP Client Setup (same as before)
# ----------------------------------------
class MCPClient:
    """Manages connection to gnome-desktop-mcp server"""

    def __init__(self):
        self.session = None
        self.read = None
        self.write = None
        self.loop = None
        self.thread = None
        self.command_queue = Queue()
        self.result_queue = Queue()

    def start(self):
        """Start MCP client in background thread"""
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        time.sleep(2)

    def _run_loop(self):
        """Run async event loop in background thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_and_process())

    async def _connect_and_process(self):
        """Connect to MCP server and process commands"""
        server_params = StdioServerParameters(
            command="gnome-desktop-mcp",
            args=[],
            env=os.environ.copy()
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.session = session
                print("[SYSTEM] MCP connected to gnome-desktop-mcp")

                while True:
                    if not self.command_queue.empty():
                        tool_name, arguments = self.command_queue.get()
                        try:
                            result = await session.call_tool(tool_name, arguments=arguments)
                            result_text = result.content[0].text
                            self.result_queue.put(("success", result_text))
                        except Exception as e:
                            self.result_queue.put(("error", str(e)))
                    await asyncio.sleep(0.01)

    def call_tool(self, tool_name: str, arguments: dict, timeout: float = 10.0) -> str:
        """Call MCP tool synchronously (blocks until result)"""
        self.command_queue.put((tool_name, arguments))

        start_time = time.time()
        while self.result_queue.empty():
            if time.time() - start_time > timeout:
                return f"Error: Tool call timed out after {timeout}s"
            time.sleep(0.01)

        status, result = self.result_queue.get()
        if status == "error":
            return f"Error: {result}"
        return result

mcp_client = MCPClient()

# Initialize dialog handler
print("[SYSTEM] Initializing dialog handler...")
dialog_handler = DialogHandler()

# Forward declarations for voice functions
def speak(text: str):
    pass

def listen_and_transcribe():
    pass

# ----------------------------------------
# Helper Functions (keeping existing ones)
# ----------------------------------------
def check_automation_health(auto_enable=True) -> tuple[bool, str]:
    """Check if GNOME automation extension is running and enabled."""
    try:
        ping_result = mcp_client.call_tool("ping", {})
        if "Error" in ping_result or "alive" not in ping_result.lower():
            return False, "GNOME automation extension not responding."

        enabled_result = mcp_client.call_tool("get_enabled", {})
        if "Error" in enabled_result:
            return False, f"Could not check automation status: {enabled_result}"

        is_enabled = "enabled" in enabled_result.lower() and "disabled" not in enabled_result.lower()

        if not is_enabled:
            if auto_enable:
                print("[SYSTEM] Automation is disabled. Auto-enabling...")
                enable_result = mcp_client.call_tool("set_enabled", {"enabled": True})
                if "Error" in enable_result:
                    return False, f"Failed to enable automation: {enable_result}"
                print("[SYSTEM] ✓ Automation enabled successfully")
                return True, "Automation was disabled but has been auto-enabled"
            else:
                return False, "Automation is disabled. Say 'enable automation' to turn it on."

        return True, "Automation is healthy and ready"

    except Exception as e:
        return False, f"Health check failed: {e}"

# ----------------------------------------
# App indexing (keeping existing implementation)
# ----------------------------------------
app_name_map = {}
app_friendly_name = {}

def build_app_index():
    """Build index of desktop applications from .desktop files."""
    global app_name_map, app_friendly_name
    app_name_map = {}
    app_friendly_name = {}

    desktop_dir = "/usr/share/applications"
    if not os.path.isdir(desktop_dir):
        print(f"[SYSTEM] Warning: {desktop_dir} not found")
        return

    apps = []
    for filename in os.listdir(desktop_dir):
        if not filename.endswith('.desktop'):
            continue

        filepath = os.path.join(desktop_dir, filename)
        is_gnome = filename.startswith('org.gnome.')

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            exec_name = None
            name = None
            generic_name = None
            keywords = []

            in_desktop_entry = False
            for line in content.split('\n'):
                line = line.strip()

                if line.startswith('['):
                    if line == '[Desktop Entry]':
                        in_desktop_entry = True
                        continue
                    elif in_desktop_entry:
                        break

                if not in_desktop_entry:
                    continue

                if line.startswith('Exec='):
                    exec_line = line[5:].strip()
                    exec_name = exec_line.split()[0] if exec_line else None
                    if exec_name:
                        exec_name = os.path.basename(exec_name)

                elif line.startswith('Name=') and not name:
                    name = line.split('=', 1)[1].strip()

                elif line.startswith('GenericName=') and not generic_name:
                    generic_name = line.split('=', 1)[1].strip()

                elif line.startswith('Keywords='):
                    keywords_str = line.split('=', 1)[1].strip()
                    keywords = [k.strip().rstrip(';') for k in keywords_str.split(';') if k.strip()]

            if exec_name:
                apps.append({
                    'exec': exec_name,
                    'name': name,
                    'generic_name': generic_name,
                    'keywords': keywords,
                    'is_gnome': is_gnome
                })
        except:
            continue

    # First pass: non-gnome apps
    for app in apps:
        if app['is_gnome']:
            continue

        exec_name = app['exec']
        if app['name']:
            app_friendly_name[exec_name] = app['name']
        elif app['generic_name']:
            app_friendly_name[exec_name] = app['generic_name']
        else:
            app_friendly_name[exec_name] = exec_name

        app_name_map[exec_name.lower()] = exec_name
        if app['name']:
            app_name_map[app['name'].lower()] = exec_name
        if app['generic_name']:
            app_name_map[app['generic_name'].lower()] = exec_name
        for keyword in app['keywords']:
            if keyword:
                app_name_map[keyword.lower()] = exec_name

    # Second pass: gnome apps (overwrite conflicts)
    gnome_count = 0
    for app in apps:
        if not app['is_gnome']:
            continue

        gnome_count += 1
        exec_name = app['exec']

        if app['name']:
            app_friendly_name[exec_name] = app['name']
        elif app['generic_name']:
            app_friendly_name[exec_name] = app['generic_name']
        else:
            app_friendly_name[exec_name] = exec_name

        app_name_map[exec_name.lower()] = exec_name
        if app['name']:
            app_name_map[app['name'].lower()] = exec_name
        if app['generic_name']:
            app_name_map[app['generic_name'].lower()] = exec_name
        for keyword in app['keywords']:
            if keyword:
                app_name_map[keyword.lower()] = exec_name

    print(f"[SYSTEM] ✓ Indexed {len(app_name_map)} app name mappings ({gnome_count} org.gnome with priority)")

def get_installed_gui_apps() -> list:
    """Get list of installed GUI applications."""
    apps = set()
    desktop_dir = "/usr/share/applications"

    if not os.path.isdir(desktop_dir):
        return []

    for filename in os.listdir(desktop_dir):
        if filename.endswith('.desktop'):
            filepath = os.path.join(desktop_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.startswith('Name='):
                            app_name = line.split('=', 1)[1].strip()
                            apps.add(app_name)
                            break
            except:
                continue

    return sorted(list(apps))

def smart_match_window(window_name: str, windows: list) -> dict:
    """Smart window matching that prioritizes app names over full window titles."""
    if not window_name or window_name.strip() == "":
        for w in windows:
            if w.get('state', {}).get('focused', False):
                return w
        return windows[0] if windows else None

    window_name_lower = window_name.lower()

    # Try app name matching first
    for w in windows:
        wm_class = w.get('wmClass', '')
        app_name = wm_class.lower()
        app_name = app_name.replace('org.gnome.', '')
        app_name = app_name.replace('org.', '')
        app_name = app_name.replace('-', '')
        app_name = app_name.replace('_', '')

        wm_class_lower = wm_class.lower()
        search_term = window_name_lower.replace(' ', '').replace('-', '').replace('_', '')

        if search_term in app_name or window_name_lower in wm_class_lower:
            return w

    # Fall back to title matching
    for w in windows:
        title = w.get('title', '').lower()
        if window_name_lower in title:
            return w

    return None

def get_friendly_app_name(wm_class: str) -> str:
    """Convert wmClass to friendly app name for voice output."""
    if not wm_class:
        return "Unknown App"

    name = wm_class
    name = name.replace('org.gnome.', '')
    name = name.replace('org.mozilla.', '')
    name = name.replace('org.', '')
    name = name.replace('-', ' ')
    name = name.replace('_', ' ')

    import re
    name = re.sub('([a-z])([A-Z])', r'\1 \2', name)
    name = ' '.join(word.capitalize() for word in name.split())

    return name

# ========================================
# 🔥 CONSOLIDATED FACADE TOOLS
# ========================================

def window_control(action: str, window_name: str = "", x: int = 0, y: int = 0,
                  width: int = 800, height: int = 600, include_frame: bool = True) -> str:
    """
    **FACADE TOOL**: Unified window management.

    Handles all window operations: list, focus, close, minimize, maximize, restore,
    screenshot (full or area), move, resize.

    Args:
        action: list | focus | close | minimize | maximize | restore | screenshot | screenshot_area | move_resize
        window_name: Application name (e.g., 'text editor'). Empty = current window.
        x, y: Position for move_resize or screenshot_area
        width, height: Size for move_resize or screenshot_area
        include_frame: Include window borders in screenshot
    """
    print(f"\n[WINDOW_CONTROL] Action: {action}, Window: {window_name or 'current'}")

    try:
        # LIST action
        if action == "list":
            result = mcp_client.call_tool("list_windows", {})
            if result.startswith("Error"):
                return result
            windows = json.loads(result)
            if not windows:
                return "No windows are currently open."
            window_titles = [w.get('title', 'Untitled') for w in windows[:10]]
            return f"Found {len(windows)} open windows: {', '.join(window_titles)}"

        # SCREENSHOT_AREA action (doesn't need window)
        if action == "screenshot_area":
            result = mcp_client.call_tool("screenshot_area", {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "include_cursor": False,
                "format": "path"
            })
            if result.startswith("Error"):
                return result
            return f"Area screenshot ({width}x{height}) saved to {result.strip()}"

        # All other actions need a window
        result = mcp_client.call_tool("list_windows", {})
        if result.startswith("Error"):
            return result
        windows = json.loads(result)

        target_window = smart_match_window(window_name, windows)
        if not target_window:
            return f"No window found matching '{window_name}'"

        window_id = target_window['id']
        wm_class = target_window.get('wmClass', 'Unknown')
        friendly_name = get_friendly_app_name(wm_class)

        # FOCUS
        if action == "focus":
            mcp_client.call_tool("focus_window", {"window_id": window_id})
            return f"Focused {friendly_name}"

        # CLOSE (with dialog handling)
        elif action == "close":
            mcp_client.call_tool("close_window", {"window_id": window_id})

            # Check for save dialog
            dialog = dialog_handler.detect_save_dialog(app_name=None, timeout=3.0)
            if not dialog:
                time.sleep(0.5)
                result = mcp_client.call_tool("list_windows", {})
                if not result.startswith("Error"):
                    windows_after = json.loads(result)
                    if not any(w['id'] == window_id for w in windows_after):
                        return f"Successfully closed {friendly_name}"
                return f"Window did not close (no dialog detected)"

            # Dialog detected - ask user
            buttons = dialog['info']['buttons']
            button_list = ', '.join([btn['text'] for btn in buttons]) if buttons else "Save, Discard, Cancel"
            voice_prompt = f"The window has unsaved changes. Options: {button_list}. What would you like to do?"

            speak(voice_prompt)
            user_choice = listen_and_transcribe()

            if not user_choice:
                speak("No response heard. Canceling close operation.")
                mcp_client.call_tool("key_combo", {"keys": "Escape"})
                return "Close operation canceled"

            success = dialog_handler.activate_button_by_keyboard(dialog, user_choice)
            if not success:
                speak(f"Could not understand choice {user_choice}")
                mcp_client.call_tool("key_combo", {"keys": "Escape"})
                return f"Unrecognized choice: {user_choice}"

            closed = dialog_handler.verify_dialog_closed(dialog, timeout=2.0)
            if closed:
                time.sleep(0.5)
                result = mcp_client.call_tool("list_windows", {})
                if not result.startswith("Error"):
                    windows_final = json.loads(result)
                    window_still_open = any(w['id'] == window_id for w in windows_final)
                    if window_still_open:
                        return f"Dialog closed. {friendly_name} is still open"
                    else:
                        return f"Successfully closed {friendly_name}"
                return "Dialog handled successfully"
            else:
                return "Dialog might still be open"

        # MINIMIZE
        elif action == "minimize":
            mcp_client.call_tool("minimize_window", {"window_id": window_id})
            return f"Minimized {friendly_name}"

        # MAXIMIZE
        elif action == "maximize":
            state = target_window.get('state', {})
            is_maximized = state.get('maximized', False)

            if is_maximized:
                mcp_client.call_tool("unmaximize_window", {"window_id": window_id})
                return f"Restored {friendly_name}"
            else:
                mcp_client.call_tool("maximize_window", {"window_id": window_id})
                return f"Maximized {friendly_name}"

        # RESTORE
        elif action == "restore":
            state = target_window.get('state', {})
            is_maximized = state.get('maximized', False)

            actions_taken = []
            mcp_client.call_tool("unminimize_window", {"window_id": window_id})
            mcp_client.call_tool("focus_window", {"window_id": window_id})

            if is_maximized:
                mcp_client.call_tool("unmaximize_window", {"window_id": window_id})
                actions_taken.append("unmaximized")

            return f"Restored {friendly_name}"

        # SCREENSHOT
        elif action == "screenshot":
            result = mcp_client.call_tool("screenshot_window", {
                "window_id": window_id,
                "include_frame": include_frame,
                "include_cursor": False,
                "format": "path"
            })
            if result.startswith("Error"):
                return result
            return f"Screenshot of {friendly_name} saved to {result.strip()}"

        # MOVE_RESIZE
        elif action == "move_resize":
            mcp_client.call_tool("move_resize_window", {
                "window_id": window_id,
                "x": x,
                "y": y,
                "width": width,
                "height": height
            })
            return f"Moved {friendly_name} to ({x}, {y}) with size {width}x{height}"

        else:
            return f"Unknown window action: {action}"

    except Exception as e:
        return f"Error in window_control: {str(e)}"


def input_control(action: str, text: str = "", keys: str = "",
                 x: int = 0, y: int = 0, to_x: int = 0, to_y: int = 0,
                 direction: str = "down", amount: int = 1, button: int = 1) -> str:
    """
    **FACADE TOOL**: Unified input control.

    Handles keyboard and mouse operations: type, key_combo, key_press, click,
    double_click, drag, scroll.

    Args:
        action: type | key_combo | key_press | click | double_click | drag | scroll
        text: Text to type (for 'type' action)
        keys: Key combo like 'Ctrl+c' (for 'key_combo' or 'key_press')
        x, y: Click position or drag start
        to_x, to_y: Drag end position
        direction: Scroll direction 'up' or 'down'
        amount: Scroll amount (number of times)
        button: Mouse button (1=left, 2=middle, 3=right)
    """
    print(f"\n[INPUT_CONTROL] Action: {action}")

    try:
        # TYPE
        if action == "type":
            mcp_client.call_tool("type_text", {"text": text})
            return f"Typed: {text}"

        # KEY_COMBO
        elif action == "key_combo":
            # Normalize key combo
            normalized = keys
            normalized = normalized.replace("control", "Ctrl").replace("Control", "Ctrl").replace("ctrl", "Ctrl")
            normalized = normalized.replace("alt", "Alt").replace("shift", "Shift").replace("super", "Super")
            if " " in normalized and "+" not in normalized:
                normalized = normalized.replace(" ", "+")

            mcp_client.call_tool("key_combo", {"keys": normalized})
            return f"Pressed {normalized}"

        # KEY_PRESS
        elif action == "key_press":
            mcp_client.call_tool("key_press", {"key": keys})
            return f"Pressed {keys}"

        # CLICK
        elif action == "click":
            mcp_client.call_tool("mouse_click", {"x": x, "y": y, "button": button})
            return f"Clicked at ({x}, {y})"

        # DOUBLE_CLICK
        elif action == "double_click":
            mcp_client.call_tool("mouse_double_click", {"x": x, "y": y, "button": button})
            return f"Double-clicked at ({x}, {y})"

        # DRAG
        elif action == "drag":
            mcp_client.call_tool("mouse_drag", {
                "x1": x,
                "y1": y,
                "x2": to_x,
                "y2": to_y,
                "button": button
            })
            return f"Dragged from ({x}, {y}) to ({to_x}, {to_y})"

        # SCROLL
        elif action == "scroll":
            is_down = "down" in direction.lower()

            # Try mouse scroll first
            dy = 100 * amount if is_down else -100 * amount
            result = mcp_client.call_tool("mouse_scroll", {
                "x": 960, "y": 540, "dx": 0, "dy": dy
            })

            if not result.startswith("Error"):
                return f"Scrolled {direction}"

            # Fall back to Page keys
            key = "Page_Down" if is_down else "Page_Up"
            for i in range(amount):
                mcp_client.call_tool("key_combo", {"keys": key})
                if i < amount - 1:
                    time.sleep(0.1)

            return f"Scrolled {direction}"

        else:
            return f"Unknown input action: {action}"

    except Exception as e:
        return f"Error in input_control: {str(e)}"


def audio_control(action: str, level: int = 0, relative: bool = False) -> str:
    """
    **FACADE TOOL**: Unified audio control.

    Handles volume and media playback: volume, mute, unmute, play, pause,
    play_pause, next, previous, stop.

    Args:
        action: volume | mute | unmute | play | pause | play_pause | next | previous | stop
        level: Volume level (0-100 absolute, or +/- for relative)
        relative: True for relative volume change
    """
    print(f"\n[AUDIO_CONTROL] Action: {action}")

    try:
        # VOLUME
        if action == "volume":
            result = mcp_client.call_tool("set_volume", {
                "volume": level,
                "relative": relative
            })
            return result

        # MUTE
        elif action == "mute":
            result = mcp_client.call_tool("mute_volume", {"mute": True})
            return result

        # UNMUTE
        elif action == "unmute":
            result = mcp_client.call_tool("mute_volume", {"mute": False})
            return result

        # MEDIA CONTROLS
        elif action in ["play", "pause", "play_pause", "next", "previous", "stop"]:
            result = mcp_client.call_tool("media_control", {"action": action.replace("_", "-")})
            return result

        else:
            return f"Unknown audio action: {action}"

    except Exception as e:
        return f"Error in audio_control: {str(e)}"


def system_settings(action: str, state: str = "toggle", path: str = "") -> str:
    """
    **FACADE TOOL**: Unified system settings.

    Handles quick settings toggles: dark_mode, night_light, do_not_disturb,
    wifi, bluetooth, wallpaper.

    Args:
        action: dark_mode | night_light | do_not_disturb | wifi | bluetooth | wallpaper
        state: 'on' | 'off' | 'toggle' (for toggles), or color/path (for wallpaper)
        path: Image path (for wallpaper action)
    """
    print(f"\n[SYSTEM_SETTINGS] Action: {action}, State: {state}")

    try:
        # WALLPAPER
        if action == "wallpaper":
            result = mcp_client.call_tool("set_wallpaper", {"image_path": path or state})
            return result

        # TOGGLES
        else:
            # Map action to setting name
            setting_map = {
                "dark_mode": "dark_style",
                "night_light": "night_light",
                "do_not_disturb": "do_not_disturb",
                "wifi": "wifi",
                "bluetooth": "bluetooth"
            }

            setting_name = setting_map.get(action)
            if not setting_name:
                return f"Unknown setting: {action}"

            # Convert state to boolean
            if state.lower() == "on":
                enabled = True
            elif state.lower() == "off":
                enabled = False
            else:
                # For 'toggle', we'd need to query current state first
                # For simplicity, assume the LLM provides explicit on/off
                return "Please specify 'on' or 'off' for this setting"

            result = mcp_client.call_tool("quick_settings", {
                "setting": setting_name,
                "enabled": enabled
            })
            return result

    except Exception as e:
        return f"Error in system_settings: {str(e)}"


def vision_control(action: str, x: int = 0, y: int = 0) -> str:
    """
    **FACADE TOOL**: Unified vision operations.

    Handles screen analysis and display info: describe, pick_color, get_monitors.

    Args:
        action: describe | pick_color | get_monitors
        x, y: Coordinates for pick_color
    """
    print(f"\n[VISION_CONTROL] Action: {action}")

    try:
        # DESCRIBE
        if action == "describe":
            result = mcp_client.call_tool("screenshot", {"include_cursor": False, "format": "path"})
            if result.startswith("Error"):
                return result

            screenshot_path = result.strip()

            with open(screenshot_path, 'rb') as img_file:
                import base64
                img_data = base64.b64encode(img_file.read()).decode('utf-8')

            response = ollama.chat(
                model=VISION_MODEL,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a screen reader for visually impaired users. Describe what you see in plain text without any formatting. Do not use markdown, asterisks, or special characters. Answer directly without explaining your reasoning process.'
                    },
                    {
                        'role': 'user',
                        'content': 'What applications and windows are visible on this desktop screenshot?',
                        'images': [img_data]
                    }
                ],
                options={
                    'num_ctx': 2048,
                    'num_predict': 800,
                    'temperature': 0.7,
                    'num_gpu': 99,
                }
            )

            message = response.message if hasattr(response, 'message') else response['message']
            description = message.content if hasattr(message, 'content') else message.get('content', '')

            try:
                os.remove(screenshot_path)
            except:
                pass

            return description

        # PICK_COLOR
        elif action == "pick_color":
            result = mcp_client.call_tool("pick_color", {"x": x, "y": y})
            return result

        # GET_MONITORS
        elif action == "get_monitors":
            result = mcp_client.call_tool("get_monitors", {})
            return result

        else:
            return f"Unknown vision action: {action}"

    except Exception as e:
        return f"Error in vision_control: {str(e)}"


def workspace_control(action: str, index: int = 0) -> str:
    """
    **FACADE TOOL**: Unified workspace management.

    Handles virtual desktop operations: list, activate.

    Args:
        action: list | activate
        index: Workspace index (0-based) for activate
    """
    print(f"\n[WORKSPACE_CONTROL] Action: {action}")

    try:
        # LIST
        if action == "list":
            result = mcp_client.call_tool("list_workspaces", {})
            if result.startswith("Error"):
                return result

            try:
                workspaces = json.loads(result)
                if not workspaces:
                    return "No workspaces found"

                active_workspace = None
                workspace_info = []

                for ws in workspaces:
                    ws_index = ws.get('index', 0)
                    is_active = ws.get('active', False)

                    if is_active:
                        active_workspace = ws_index
                        workspace_info.append(f"Workspace {ws_index} (current)")
                    else:
                        workspace_info.append(f"Workspace {ws_index}")

                total = len(workspaces)
                summary = f"You have {total} workspace{'s' if total > 1 else ''}. Current: workspace {active_workspace}. " + ", ".join(workspace_info)
                return summary

            except json.JSONDecodeError:
                return result

        # ACTIVATE
        elif action == "activate":
            result = mcp_client.call_tool("activate_workspace", {"index": index})
            if result.startswith("Error"):
                return result
            return f"Switched to workspace {index}"

        else:
            return f"Unknown workspace action: {action}"

    except Exception as e:
        return f"Error in workspace_control: {str(e)}"


# ========================================
# STANDALONE TOOLS (low frequency)
# ========================================

def list_installed_applications() -> str:
    """Lists all installed GUI applications on the system."""
    print(f"\n[SYSTEM] Scanning for installed applications...")
    try:
        apps = get_installed_gui_apps()
        app_count = len(apps)
        if app_count == 0:
            return "No applications found."
        return f"Found {app_count} installed applications including {', '.join(apps[:5])}, and others."
    except Exception as e:
        return f"Error listing applications: {str(e)}"

def send_notification(title: str, message: str = "") -> str:
    """Send a desktop notification."""
    print(f"\n[SYSTEM] Sending notification: {title}")
    try:
        result = mcp_client.call_tool("send_notification", {
            "title": title,
            "message": message
        })
        return result
    except Exception as e:
        return f"Error sending notification: {str(e)}"

def cleanup_screenshots() -> str:
    """Clean up temporary screenshot files."""
    print(f"\n[SYSTEM] Cleaning up screenshots...")
    try:
        result = mcp_client.call_tool("cleanup_screenshots", {})
        return result
    except Exception as e:
        return f"Error cleaning up: {str(e)}"


# ========================================
# TOOL REGISTRY
# ========================================

# Available tools (facade + standalone + direct MCP)
available_tools = {
    # Facade tools
    "window_control": window_control,
    "input_control": input_control,
    "audio_control": audio_control,
    "system_settings": system_settings,
    "vision_control": vision_control,
    "workspace_control": workspace_control,

    # Standalone tools
    "list_installed_applications": list_installed_applications,
    "send_notification": send_notification,
    "cleanup_screenshots": cleanup_screenshots,
}

# Direct MCP tools (forwarded without wrappers)
direct_mcp_tools = [
    "gnome_search",      # GNOME search overlay
    "ping",              # Health check
    "get_enabled",       # Check automation status
    "set_enabled",       # Enable/disable automation
]

# ========================================
# NAMESPACE ORGANIZATION + RAG
# ========================================

namespaces = {
    "search": {
        "description": "Launch applications, start programs, open files, navigate to websites. Commands like: open firefox, open text editor, start calculator, launch terminal, run files app. Open documents: open screenshot.png, open document.pdf, find image.jpg. Web navigation: go to amazon.com, visit github.com, browse seznam.cz, open google.com. Settings: open wifi settings, bluetooth settings. Use GNOME search to find and launch anything.",
        "tools": ["gnome_search"]
    },
    "window": {
        "description": "Managing already running windows - maximize, minimize, close, focus, move, resize, restore existing application windows. List what windows are currently running. Take window screenshots or area screenshots. NOT for launching new applications.",
        "tools": ["window_control"]
    },
    "input": {
        "description": "Keyboard input, typing text, pressing keys, key combinations, shortcuts, mouse clicks, double clicks, dragging, scrolling pages up and down",
        "tools": ["input_control"]
    },
    "audio": {
        "description": "Sound volume control, mute, unmute, audio levels. Media playback control - play, pause, stop, next track, previous track, music control, audio player control",
        "tools": ["audio_control"]
    },
    "settings": {
        "description": "System settings - dark mode, light mode, night light, notifications, do not disturb, WiFi, Bluetooth, wallpaper, background image, quick settings toggles",
        "tools": ["system_settings"]
    },
    "vision": {
        "description": "Analyzing current screen content, describing what's visible on desktop right now, color picking from display, monitor configuration. Not for opening files.",
        "tools": ["vision_control"]
    },
    "workspace": {
        "description": "Virtual desktops, workspace switching, multi-desktop management, listing workspaces",
        "tools": ["workspace_control"]
    },
    "system": {
        "description": "System automation control, notifications, reminders, cleanup, maintenance, listing installed applications",
        "tools": ["list_installed_applications", "send_notification", "cleanup_screenshots", "set_enabled"]
    }
}

# Load embedding model
print("[SYSTEM] Loading embedding model for tool retrieval...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

# Pre-compute namespace embeddings
namespace_names = list(namespaces.keys())
namespace_descriptions = [namespaces[ns]["description"] for ns in namespace_names]
namespace_embeddings = embedding_model.encode(namespace_descriptions, convert_to_tensor=True)
print(f"[SYSTEM] ✓ Loaded embeddings for {len(namespace_names)} namespaces")

def retrieve_relevant_namespaces(user_input: str, top_k: int = 2) -> list:
    """Retrieve most relevant namespaces using semantic similarity."""
    from sentence_transformers.util import cos_sim
    query_embedding = embedding_model.encode(user_input, convert_to_tensor=True)
    similarities = cos_sim(query_embedding, namespace_embeddings)[0]
    top_indices = similarities.argsort(descending=True)[:top_k]
    relevant_namespaces = [namespace_names[i] for i in top_indices]

    print(f"[RETRIEVAL] Query: '{user_input}'")
    for i, ns in enumerate(relevant_namespaces):
        score = similarities[namespace_names.index(ns)].item()
        print(f"  {i+1}. {ns} (score: {score:.3f}) - {len(namespaces[ns]['tools'])} tools")

    return relevant_namespaces

def build_filtered_tool_schema(relevant_namespaces: list) -> list:
    """Build filtered tool schema from relevant namespaces."""
    relevant_tool_names = set()
    for ns in relevant_namespaces:
        relevant_tool_names.update(namespaces[ns]["tools"])

    filtered_schema = [tool for tool in tool_schema_full
                      if tool["function"]["name"] in relevant_tool_names]

    print(f"[FILTER] Showing {len(filtered_schema)} tools from {len(relevant_namespaces)} namespaces")
    print(f"  Tools: {[t['function']['name'] for t in filtered_schema]}")

    return filtered_schema

# ========================================
# CONSOLIDATED TOOL SCHEMA (10 tools total)
# ========================================

tool_schema_full = [
    # 1. SEARCH (direct MCP)
    {"type": "function", "function": {"name": "gnome_search", "description": "Use GNOME search to find and open apps, files, or settings. Opens Activities search, types the query, and presses Enter. GNOME finds and opens the best match automatically.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Just the app name, file name, or domain. Examples: 'firefox', 'text editor', 'screenshot.png', 'amazon.com', 'wifi'"}}, "required": ["query"]}}},

    # 2. WINDOW_CONTROL (facade)
    {"type": "function", "function": {"name": "window_control", "description": "Unified window management: list windows, focus/close/minimize/maximize/restore windows, take window screenshots or area screenshots, move and resize windows. Matches windows by application name (e.g., 'text editor', 'firefox'). Empty window_name = current window.", "parameters": {"type": "object", "properties": {"action": {"type": "string", "description": "Action to perform: list | focus | close | minimize | maximize | restore | screenshot | screenshot_area | move_resize"}, "window_name": {"type": "string", "description": "Application name (e.g., 'text editor'). Leave empty for current window.", "default": ""}, "x": {"type": "integer", "description": "X position for move_resize or screenshot_area", "default": 0}, "y": {"type": "integer", "description": "Y position for move_resize or screenshot_area", "default": 0}, "width": {"type": "integer", "description": "Width for move_resize or screenshot_area", "default": 800}, "height": {"type": "integer", "description": "Height for move_resize or screenshot_area", "default": 600}, "include_frame": {"type": "boolean", "description": "Include window borders in screenshot", "default": True}}, "required": ["action"]}}},

    # 3. INPUT_CONTROL (facade)
    {"type": "function", "function": {"name": "input_control", "description": "Unified input control: type text, press key combos (Ctrl+C, Alt+Tab), press single keys, mouse click/double-click, drag and drop, scroll pages up/down. Handles all keyboard and mouse operations.", "parameters": {"type": "object", "properties": {"action": {"type": "string", "description": "Action: type | key_combo | key_press | click | double_click | drag | scroll"}, "text": {"type": "string", "description": "Text to type (for 'type' action)", "default": ""}, "keys": {"type": "string", "description": "Key combo like 'Ctrl+c' or single key like 'Enter'", "default": ""}, "x": {"type": "integer", "description": "X coordinate for click or drag start", "default": 0}, "y": {"type": "integer", "description": "Y coordinate for click or drag start", "default": 0}, "to_x": {"type": "integer", "description": "Drag end X coordinate", "default": 0}, "to_y": {"type": "integer", "description": "Drag end Y coordinate", "default": 0}, "direction": {"type": "string", "description": "Scroll direction: 'up' or 'down'", "default": "down"}, "amount": {"type": "integer", "description": "Scroll amount (number of times)", "default": 1}, "button": {"type": "integer", "description": "Mouse button: 1=left, 2=middle, 3=right", "default": 1}}, "required": ["action"]}}},

    # 4. AUDIO_CONTROL (facade)
    {"type": "function", "function": {"name": "audio_control", "description": "Unified audio control: volume (set/increase/decrease), mute, unmute, media playback (play, pause, play_pause toggle, next, previous, stop). Handles all sound and media controls.", "parameters": {"type": "object", "properties": {"action": {"type": "string", "description": "Action: volume | mute | unmute | play | pause | play_pause | next | previous | stop"}, "level": {"type": "integer", "description": "Volume level: 0-100 absolute, or +/- for relative change", "default": 0}, "relative": {"type": "boolean", "description": "True for relative volume change (+/-), false for absolute", "default": False}}, "required": ["action"]}}},

    # 5. SYSTEM_SETTINGS (facade)
    {"type": "function", "function": {"name": "system_settings", "description": "Unified system settings: toggle dark mode, night light, do not disturb, WiFi, Bluetooth, set wallpaper. Handles all quick settings and appearance controls.", "parameters": {"type": "object", "properties": {"action": {"type": "string", "description": "Setting: dark_mode | night_light | do_not_disturb | wifi | bluetooth | wallpaper"}, "state": {"type": "string", "description": "For toggles: 'on' or 'off'. For wallpaper: color name (red, blue) or path", "default": "toggle"}, "path": {"type": "string", "description": "Image path for wallpaper action", "default": ""}}, "required": ["action"]}}},

    # 6. VISION_CONTROL (facade)
    {"type": "function", "function": {"name": "vision_control", "description": "Unified vision operations: describe what's on screen using AI, pick color at coordinates, get monitor information. Handles all screen analysis and display queries.", "parameters": {"type": "object", "properties": {"action": {"type": "string", "description": "Action: describe | pick_color | get_monitors"}, "x": {"type": "integer", "description": "X coordinate for pick_color", "default": 0}, "y": {"type": "integer", "description": "Y coordinate for pick_color", "default": 0}}, "required": ["action"]}}},

    # 7. WORKSPACE_CONTROL (facade)
    {"type": "function", "function": {"name": "workspace_control", "description": "Unified workspace management: list all virtual desktops, switch to specific workspace by index. Handles all multi-desktop operations.", "parameters": {"type": "object", "properties": {"action": {"type": "string", "description": "Action: list | activate"}, "index": {"type": "integer", "description": "Workspace index (0-based) for activate action", "default": 0}}, "required": ["action"]}}},

    # 8. LIST_INSTALLED_APPLICATIONS (standalone)
    {"type": "function", "function": {"name": "list_installed_applications", "description": "Lists all installed GUI applications available on the Linux system. Use for 'what apps are installed', 'list all applications', 'show me installed programs'.", "parameters": {"type": "object", "properties": {}}}},

    # 9. SEND_NOTIFICATION (standalone)
    {"type": "function", "function": {"name": "send_notification", "description": "Send a desktop notification with title and message. Use for reminders, alerts, confirmations.", "parameters": {"type": "object", "properties": {"title": {"type": "string", "description": "Notification title"}, "message": {"type": "string", "description": "Notification message body", "default": ""}}, "required": ["title"]}}},

    # 10. CLEANUP_SCREENSHOTS (standalone)
    {"type": "function", "function": {"name": "cleanup_screenshots", "description": "Clean up temporary screenshot files to free disk space. Use for maintenance, cleanup tasks.", "parameters": {"type": "object", "properties": {}}}},
]

print(f"[SYSTEM] ✓ Consolidated tool schema: {len(tool_schema_full)} facade + standalone tools")
print(f"[SYSTEM]   - Reduced from 34 individual tools")
print(f"[SYSTEM]   - Expected performance: ~17-20s inference (vs 41-69s)")

# ========================================
# NOTE: Rest of the orchestrator implementation would go here
# (VAD, Whisper, Piper, conversation loop, etc.)
# For this reference implementation, we're focusing on the tool consolidation pattern
# ========================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CONSOLIDATED TOOL ORCHESTRATOR - REFERENCE IMPLEMENTATION")
    print("="*70)
    print(f"\nThis file demonstrates the facade pattern for tool consolidation:")
    print(f"  - 34 tools → 10 tools (6 facades + 3 standalone + 1 search)")
    print(f"  - All original functionality preserved")
    print(f"  - Clearer namespace organization")
    print(f"  - Faster LLM inference (fewer choices)")
    print(f"  - Better RAG retrieval (clearer descriptions)")
    print("\nTo use this in production:")
    print("  1. Copy the VAD/Whisper/Piper code from conversational orchestrator")
    print("  2. Replace tool definitions and schema")
    print("  3. Test with real commands")
    print("="*70)
