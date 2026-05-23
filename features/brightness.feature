Feature: Brightness commands

  Scenario: Increase brightness
    When I say "increase brightness"
    Then the response should contain "Brightness"
    And MCP tool "set_brightness" was called with level "up"

  Scenario: Decrease brightness
    When I say "decrease brightness"
    Then the response should contain "Brightness"
    And MCP tool "set_brightness" was called with level "down"

  Scenario: Max brightness
    When I say "max brightness"
    Then the response should contain "Brightness"
    And MCP tool "set_brightness" was called with level "max"

  Scenario: Min brightness
    When I say "min brightness"
    Then the response should contain "Brightness"
    And MCP tool "set_brightness" was called with level "min"

  Scenario: Set brightness to percentage
    When I say "set brightness to 70"
    Then the response should contain "Brightness"
    And MCP tool "set_brightness" was called with level "70%"

  Scenario: Keyboard backlight up
    When I say "keyboard brightness up"
    Then MCP tool "set_brightness" was called with target "keyboard"

  Scenario: Keyboard backlight off
    When I say "keyboard backlight off"
    Then MCP tool "set_brightness" was called with target "keyboard"

  Scenario: Check power profile
    When I say "what power mode"
    Then the response should contain "balanced"
    And MCP tool "get_power_profile" was called

  Scenario: Set power profile
    When I say "set power mode to performance"
    Then MCP tool "set_power_profile" was called with profile "performance"
