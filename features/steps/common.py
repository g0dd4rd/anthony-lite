import json

from behave import given, when, then


@when('I say "{command}"')
def step_say_command(context, command):
    context.result = context.execute(command)


@then('the response should contain "{text}"')
def step_response_contains(context, text):
    assert context.result is not None, \
        f"Expected response containing '{text}' but got None (no match)"
    assert text.lower() in context.result.lower(), \
        f"Expected '{text}' in response: {context.result}"


@then('the response should be "{text}"')
def step_response_exact(context, text):
    assert context.result is not None, \
        f"Expected response '{text}' but got None"
    assert context.result.strip() == text.strip(), \
        f"Expected '{text}' but got: {context.result}"


@then('there is no match')
def step_no_match(context):
    assert context.result is None, \
        f"Expected no match but got: {context.result}"


@then('MCP tool "{tool}" was called')
def step_mcp_called(context, tool):
    calls = context.mock_mcp.get_calls(tool)
    assert calls, \
        f"MCP tool '{tool}' was not called. All calls: {context.mock_mcp.calls}"


@then('MCP tool "{tool}" was not called')
def step_mcp_not_called(context, tool):
    calls = context.mock_mcp.get_calls(tool)
    assert not calls, \
        f"MCP tool '{tool}' was called but should not have been: {calls}"


@then('MCP tool "{tool}" was called with {key} "{value}"')
def step_mcp_called_with_str(context, tool, key, value):
    calls = context.mock_mcp.get_calls(tool)
    assert calls, \
        f"MCP tool '{tool}' was not called"
    matched = any(c[1].get(key) == value for c in calls)
    assert matched, \
        f"MCP tool '{tool}' was not called with {key}=\"{value}\". Calls: {calls}"


@then('MCP tool "{tool}" was called with {key} {value:d}')
def step_mcp_called_with_int(context, tool, key, value):
    calls = context.mock_mcp.get_calls(tool)
    assert calls, \
        f"MCP tool '{tool}' was not called"
    matched = any(c[1].get(key) == value for c in calls)
    assert matched, \
        f"MCP tool '{tool}' was not called with {key}={value}. Calls: {calls}"


@then('MCP tool "{tool}" was called with {key} {value}')
def step_mcp_called_with_generic(context, tool, key, value):
    calls = context.mock_mcp.get_calls(tool)
    assert calls, \
        f"MCP tool '{tool}' was not called"
    if value.lower() == "true":
        expected = True
    elif value.lower() == "false":
        expected = False
    else:
        try:
            expected = int(value)
        except ValueError:
            expected = value
    matched = any(c[1].get(key) == expected for c in calls)
    assert matched, \
        f"MCP tool '{tool}' was not called with {key}={expected}. Calls: {calls}"


@then('it spoke "{text}"')
def step_spoke(context, text):
    assert context.speaker.messages, \
        f"Nothing was spoken. Expected to hear '{text}'"
    assert any(text.lower() in m.lower() for m in context.speaker.messages), \
        f"Expected speak output containing '{text}', got: {context.speaker.messages}"


@then('nothing was spoken')
def step_nothing_spoken(context):
    assert not context.speaker.messages, \
        f"Expected no speak output, got: {context.speaker.messages}"


# --- Given steps for scenario setup ---

@given('the following windows are open')
def step_set_windows(context):
    windows = []
    for row in context.table:
        windows.append({
            "id": int(row["id"]),
            "title": row["title"],
            "wmClass": row["wmClass"],
            "focused": row.get("focused", "false").lower() == "true",
            "maximized": row.get("maximized", "false").lower() == "true",
            "minimized": row.get("minimized", "false").lower() == "true",
        })
    context.mock_mcp.windows = windows


@given('no windows are open')
def step_no_windows(context):
    context.mock_mcp.windows = []


@given('the user will respond "{response}"')
def step_set_listener(context, response):
    context.listener.set_responses(response)


@given('the user will not respond')
def step_set_listener_silent(context):
    context.listener.set_responses()


@given('a save dialog is open')
def step_set_dialog(context):
    context.mock_dialog.has_dialog = True


@given('the volume is muted')
def step_volume_muted(context):
    context.mock_mcp.responses["get_volume"] = \
        lambda args: json.dumps({"volume": 0, "muted": True})


@given('the volume is at {level:d}')
def step_volume_at(context, level):
    context.mock_mcp.responses["get_volume"] = \
        lambda args: json.dumps({"volume": level, "muted": False})
