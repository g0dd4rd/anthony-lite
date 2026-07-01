Feature: Vision commands

  Scenario: Take a screenshot
    When I say "take a screenshot"
    Then the response should contain "Screenshot"
    And MCP tool "screenshot" was called

  Scenario: Pick color at coordinates
    When I say "pick color at 500 300"
    Then the response should contain "red"
    And the response should contain "255"
    And MCP tool "pick_color" was called

  Scenario: Monitor info
    When I say "monitor info"
    Then the response should contain "1920"
    And the response should contain "1080"
    And MCP tool "get_monitors" was called
