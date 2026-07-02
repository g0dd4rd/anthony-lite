import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"


# ---------------------------------------------------------------------------
# Mock classes
# ---------------------------------------------------------------------------

SAMPLE_WINDOWS = [
    {
        "id": 1001,
        "title": "Untitled Document - Text Editor",
        "wmClass": "org.gnome.TextEditor",
        "focused": True,
        "maximized": False,
        "minimized": False,
    },
    {
        "id": 1002,
        "title": "Mozilla Firefox",
        "wmClass": "firefox",
        "focused": False,
        "maximized": False,
        "minimized": False,
    },
    {
        "id": 1003,
        "title": "Terminal",
        "wmClass": "org.gnome.Ptyxis",
        "focused": False,
        "maximized": False,
        "minimized": False,
    },
]

DEFAULT_MCP_RESPONSES = {
    "list_windows": lambda args: json.dumps(SAMPLE_WINDOWS),
    "focus_window": lambda args: "OK",
    "close_window": lambda args: "OK",
    "minimize_window": lambda args: "OK",
    "maximize_window": lambda args: "OK",
    "unmaximize_window": lambda args: "OK",
    "unminimize_window": lambda args: "OK",
    "move_resize_window": lambda args: "OK",
    "get_monitors": lambda args: json.dumps(
        [{"width": 1920, "height": 1080, "x": 0, "y": 0, "scale": 1, "primary": True}]
    ),
    "screenshot": lambda args: "/tmp/test_screenshot.png",
    "screenshot_window": lambda args: "/tmp/test_window_screenshot.png",
    "get_volume": lambda args: json.dumps({"volume": 50, "muted": False}),
    "set_volume": lambda args: "OK",
    "mute_volume": lambda args: "OK",
    "get_media_status": lambda args: json.dumps(
        {"status": "Playing", "title": "Test Song", "artist": "Test Artist"}
    ),
    "media_control": lambda args: "OK",
    "key_combo": lambda args: "OK",
    "key_press": lambda args: "OK",
    "type_text": lambda args: "OK",
    "mouse_click": lambda args: "OK",
    "mouse_double_click": lambda args: "OK",
    "mouse_scroll": lambda args: "OK",
    "mouse_drag": lambda args: "OK",
    "quick_settings": lambda args: (
        f"Set {args.get('setting', 'setting')} to {args.get('enabled', True)}"
    ),
    "set_brightness": lambda args: f"Brightness set to {args.get('level', '50%')}",
    "get_power_profile": lambda args: "Current profile: balanced",
    "set_power_profile": lambda args: f"Profile set to {args.get('profile', 'balanced')}",
    "lock_screen": lambda args: "Screen locked",
    "power_action": lambda args: f"{args.get('action', 'unknown')} initiated",
    "send_notification": lambda args: f"Notification scheduled: {args.get('summary', '')}",
    "get_battery_status": lambda args: "Battery: 75%, discharging",
    "gnome_search": lambda args: f"Launched {args.get('query', 'app')}",
    "open_file": lambda args: f"Opened {args.get('path', 'file')}",
    "search_files": lambda args: json.dumps({"count": 0, "results": []}),
    "cleanup_screenshots": lambda args: "Removed 3 screenshots",
    "list_workspaces": lambda args: json.dumps(
        [{"index": 0, "active": True}, {"index": 1, "active": False}]
    ),
    "activate_workspace": lambda args: "OK",
    "pick_color": lambda args: json.dumps({"r": 255, "g": 0, "b": 0}),
    "set_wallpaper": lambda args: "Wallpaper set",
    "ping": lambda args: "alive",
    "get_enabled": lambda args: "enabled",
    "set_enabled": lambda args: "OK",
}


class MockMCPClient:
    def __init__(self, responses=None):
        self.calls = []
        self.responses = responses or {}
        self.windows = [dict(w) for w in SAMPLE_WINDOWS]

    def call_tool(self, tool_name, arguments, timeout=10.0):
        self.calls.append((tool_name, dict(arguments)))
        self._update_window_state(tool_name, arguments)
        if tool_name == "list_windows":
            return json.dumps(self.windows)
        if tool_name in self.responses:
            resp = self.responses[tool_name]
            return resp(arguments) if callable(resp) else resp
        if tool_name in DEFAULT_MCP_RESPONSES:
            resp = DEFAULT_MCP_RESPONSES[tool_name]
            return resp(arguments) if callable(resp) else resp
        return "{}"

    def _update_window_state(self, tool_name, arguments):
        wid = arguments.get("window_id")
        if not wid:
            return
        win = next((w for w in self.windows if w["id"] == wid), None)
        if not win:
            return
        if tool_name == "close_window":
            self.windows = [w for w in self.windows if w["id"] != wid]
        elif tool_name == "minimize_window":
            win["minimized"] = True
        elif tool_name == "unminimize_window":
            win["minimized"] = False
        elif tool_name == "maximize_window":
            win["maximized"] = True
        elif tool_name == "unmaximize_window":
            win["maximized"] = False
        elif tool_name == "focus_window":
            for w in self.windows:
                w["focused"] = w["id"] == wid

    def get_calls(self, tool_name=None):
        if tool_name:
            return [c for c in self.calls if c[0] == tool_name]
        return self.calls

    def reset(self):
        self.calls.clear()
        self.responses.clear()
        self.windows = [dict(w) for w in SAMPLE_WINDOWS]


class CaptureSpeaker:
    def __init__(self):
        self.messages = []

    def __call__(self, text):
        self.messages.append(text)

    @property
    def last(self):
        return self.messages[-1] if self.messages else None

    def reset(self):
        self.messages.clear()


class MockListener:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.call_count = 0

    def __call__(self):
        if self.call_count < len(self.responses):
            result = self.responses[self.call_count]
            self.call_count += 1
            return result
        return None

    def set_responses(self, *responses):
        self.responses = list(responses)
        self.call_count = 0

    def reset(self):
        self.responses.clear()
        self.call_count = 0


class MockDialogHandler:
    def __init__(self, has_dialog=False):
        self.has_dialog = has_dialog

    def detect_save_dialog(self, app_name=None, timeout=2.0):
        if not self.has_dialog:
            return None
        return {
            "dialog": {
                "element": None,
                "name": "Save Changes?",
                "role": "alert",
                "app": app_name or "test-app",
            },
            "info": {
                "title": "Save Changes?",
                "message": "Do you want to save changes?",
                "buttons": [
                    {"text": "Cancel", "element": None},
                    {"text": "Discard", "element": None},
                    {"text": "Save", "element": None},
                ],
            },
        }

    def activate_button_by_keyboard(
        self, dialog_data, button_choice, use_fallback=True, key_callback=None
    ):
        return True

    def verify_dialog_closed(self, dialog_data, timeout=2.0):
        return True

    def reset(self):
        self.has_dialog = False


# ---------------------------------------------------------------------------
# Test app data (replaces Gio-based build_app_index)
# ---------------------------------------------------------------------------

TEST_APP_NAME_MAP = {
    "firefox": "firefox",
    "mozilla firefox": "firefox",
    "text editor": "gnome-text-editor",
    "gnome-text-editor": "gnome-text-editor",
    "terminal": "ptyxis",
    "ptyxis": "ptyxis",
    "files": "nautilus",
    "nautilus": "nautilus",
    "calculator": "gnome-calculator",
    "gnome-calculator": "gnome-calculator",
}

TEST_APP_NAMES_ONLY = {
    "firefox",
    "mozilla firefox",
    "text editor",
    "terminal",
    "files",
    "nautilus",
    "calculator",
}

TEST_APP_FRIENDLY_NAMES = {
    "firefox": "Firefox",
    "gnome-text-editor": "Text Editor",
    "ptyxis": "Terminal",
    "nautilus": "Files",
    "gnome-calculator": "Calculator",
}


# ---------------------------------------------------------------------------
# Behave hooks
# ---------------------------------------------------------------------------


def before_all(context):
    import app_index
    import command_matcher
    import commands

    context.embedding_model = app_index.embedding_model

    context.mock_mcp = MockMCPClient()
    context.speaker = CaptureSpeaker()
    context.listener = MockListener()
    context.mock_dialog = MockDialogHandler()

    app_index.app_name_map.clear()
    app_index.app_name_map.update(TEST_APP_NAME_MAP)
    app_index.app_names_only.clear()
    app_index.app_names_only.update(TEST_APP_NAMES_ONLY)
    app_index.app_friendly_name.clear()
    app_index.app_friendly_name.update(TEST_APP_FRIENDLY_NAMES)

    def mock_smart_match(name, windows):
        return app_index.smart_match_window(name, windows)

    def mock_friendly_name(wm_class):
        return app_index.get_friendly_app_name(wm_class)

    def mock_get_installed_apps():
        return {"count": 5, "samples": ["Firefox", "Text Editor", "Files"], "categorized": {}}

    def mock_check_health(auto_enable=True):
        return (True, "Automation is healthy")

    commands.init(
        mcp_client=context.mock_mcp,
        speak_fn=context.speaker,
        listen_fn=context.listener,
        smart_match_fn=mock_smart_match,
        friendly_name_fn=mock_friendly_name,
        dialog_handler=context.mock_dialog,
        check_health_fn=mock_check_health,
        get_installed_gui_apps_fn=mock_get_installed_apps,
    )

    command_matcher.init(
        registry=commands.registry,
        mcp_client=context.mock_mcp,
        speak_fn=context.speaker,
        embedding_model=context.embedding_model,
        detect_app_fn=app_index.detect_app_in_input,
        check_health_fn=mock_check_health,
    )

    context.execute = command_matcher.execute


def before_scenario(context, scenario):
    context.mock_mcp.reset()
    context.speaker.reset()
    context.listener.reset()
    context.mock_dialog.reset()
