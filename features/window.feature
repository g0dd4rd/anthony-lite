Feature: Window commands

  Scenario: Focus an app by name
    When I say "focus firefox"
    Then the response should contain "Focused"
    And MCP tool "focus_window" was called

  Scenario: Focus nonexistent app
    When I say "focus calculator"
    Then the response should contain "No window found"

  Scenario: Close focused window
    When I say "close"
    Then the response should contain "closed"
    And MCP tool "close_window" was called

  Scenario: Close window by name
    When I say "close firefox"
    Then the response should contain "closed"
    And MCP tool "close_window" was called

  Scenario: Close window with save dialog
    Given a save dialog is open
    And the user will respond "discard"
    When I say "close"
    Then the response should contain "closed"
    And it spoke "unsaved changes"

  Scenario: Close window with save dialog but no response
    Given a save dialog is open
    And the user will not respond
    When I say "close"
    Then the response should contain "canceled"
    And it spoke "No response heard"

  Scenario: Minimize focused window
    When I say "minimize"
    Then the response should contain "Minimized"
    And MCP tool "minimize_window" was called

  Scenario: Minimize app by name
    When I say "minimize firefox"
    Then the response should contain "Minimized"
    And MCP tool "minimize_window" was called

  Scenario: Maximize focused window
    When I say "maximize"
    Then the response should contain "Maximized"
    And MCP tool "maximize_window" was called

  Scenario: Maximize already maximized window restores it
    Given the following windows are open
      | id   | title          | wmClass              | focused | maximized |
      | 1001 | Text Editor    | org.gnome.TextEditor | true    | true      |
    When I say "maximize"
    Then the response should contain "Restored"
    And MCP tool "unmaximize_window" was called

  Scenario: Restore focused window
    When I say "restore"
    Then the response should contain "Restored"
    And MCP tool "unminimize_window" was called
    And MCP tool "focus_window" was called

  Scenario: List windows
    When I say "list windows"
    Then the response should contain "3 open windows"

  Scenario: List windows when none are open
    Given no windows are open
    When I say "list windows"
    Then the response should contain "No windows"

  Scenario: Tile window left
    When I say "tile left"
    Then the response should contain "left"
    And MCP tool "move_resize_window" was called

  Scenario: Tile window right
    When I say "tile right"
    Then the response should contain "right"
    And MCP tool "move_resize_window" was called

  Scenario: Tile window to center
    When I say "tile center"
    Then the response should contain "center"
    And MCP tool "move_resize_window" was called

  Scenario: Screenshot of a window
    When I say "screenshot firefox"
    Then the response should contain "Screenshot"
    And MCP tool "screenshot_window" was called

  Scenario: Focus already focused window
    When I say "focus"
    Then the response should contain "already focused"
