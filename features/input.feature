Feature: Input commands

  Scenario: Type text
    When I say "type hello world"
    Then the response should contain "Typed"
    And MCP tool "type_text" was called with text "hello world"

  Scenario: Press a single key
    When I say "press enter"
    Then the response should contain "Pressed"
    And MCP tool "key_press" was called

  Scenario: Press a key combo
    When I say "press ctrl c"
    Then the response should contain "Pressed"
    And MCP tool "key_combo" was called

  Scenario: Click at coordinates
    When I say "click at 100 200"
    Then the response should contain "Clicked at (100, 200)"
    And MCP tool "mouse_click" was called with x 100

  Scenario: Double click at coordinates
    When I say "double click at 300 400"
    Then the response should contain "Double-clicked at (300, 400)"
    And MCP tool "mouse_double_click" was called

  Scenario: Right click at coordinates
    When I say "right click at 500 600"
    Then the response should contain "Right-clicked at (500, 600)"
    And MCP tool "mouse_click" was called with button 3

  Scenario: Scroll down
    When I say "scroll down"
    Then the response should contain "Scrolled down"
    And MCP tool "mouse_scroll" was called

  Scenario: Scroll up
    When I say "scroll up"
    Then the response should contain "Scrolled up"
    And MCP tool "mouse_scroll" was called

  Scenario: Drag from one position to another
    When I say "drag from 10 20 to 300 400"
    Then the response should contain "Dragged"
    And MCP tool "mouse_drag" was called
