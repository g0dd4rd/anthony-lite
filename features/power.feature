Feature: Power commands

  Scenario: Lock screen
    When I say "lock screen"
    Then the response should contain "locked"
    And MCP tool "lock_screen" was called

  Scenario: Shutdown confirmed
    Given the user will respond "yes"
    When I say "shut down"
    Then the response should contain "shutdown"
    And it spoke "Are you sure"
    And MCP tool "power_action" was called with action "shutdown"

  Scenario: Shutdown canceled
    Given the user will respond "no"
    When I say "shut down"
    Then the response should contain "Canceled"
    And it spoke "Are you sure"
    And MCP tool "power_action" was not called

  Scenario: Shutdown no response
    Given the user will not respond
    When I say "shut down"
    Then the response should contain "Canceled"
    And MCP tool "power_action" was not called

  Scenario: Restart confirmed
    Given the user will respond "yes"
    When I say "restart"
    Then the response should contain "restart"
    And MCP tool "power_action" was called with action "restart"

  Scenario: Sleep confirmed
    Given the user will respond "sure"
    When I say "sleep"
    Then the response should contain "suspend"
    And MCP tool "power_action" was called with action "suspend"

  Scenario: Logout confirmed
    Given the user will respond "go ahead"
    When I say "log out"
    Then the response should contain "logout"
    And MCP tool "power_action" was called with action "logout"
