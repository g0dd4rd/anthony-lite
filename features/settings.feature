Feature: Settings commands

  Scenario: Turn on dark mode
    When I say "turn on dark mode"
    Then the response should contain "dark_style"
    And MCP tool "quick_settings" was called with enabled true

  Scenario: Turn off dark mode
    When I say "turn off dark mode"
    Then the response should contain "dark_style"
    And MCP tool "quick_settings" was called with enabled false

  Scenario: Enable wifi
    When I say "turn on wifi"
    Then MCP tool "quick_settings" was called with setting "wifi"

  Scenario: Disable bluetooth
    When I say "turn off bluetooth"
    Then MCP tool "quick_settings" was called with setting "bluetooth"

  Scenario: Enable night light
    When I say "turn on night light"
    Then MCP tool "quick_settings" was called with setting "night_light"

  Scenario: Enable do not disturb
    When I say "enable do not disturb"
    Then MCP tool "quick_settings" was called with setting "do_not_disturb"

  Scenario: Unknown setting
    When I say "turn on foobar"
    Then the response should contain "Unknown setting"
