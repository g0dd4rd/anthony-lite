Feature: System commands

  Scenario: What time is it
    When I say "what time is it"
    Then the response should contain "It is"

  Scenario: What date is it
    When I say "what date is it"
    Then the response should contain "It is"

  Scenario: Battery status
    When I say "battery status"
    Then the response should contain "Battery"
    And MCP tool "get_battery_status" was called

  Scenario: Set a reminder
    When I say "remind me in 5 minutes to check the oven"
    Then the response should contain "check the oven"
    And MCP tool "send_notification" was called

  Scenario: Send a notification
    When I say "send notification hello"
    Then the response should contain "hello"
    And MCP tool "send_notification" was called

  Scenario: Cleanup screenshots
    When I say "clean up screenshots"
    Then the response should contain "screenshots"
    And MCP tool "cleanup_screenshots" was called

  Scenario: List installed apps
    When I say "list installed applications"
    Then the response should contain "installed applications"
