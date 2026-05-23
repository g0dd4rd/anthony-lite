Feature: Help commands

  Scenario: General help
    When I say "help"
    Then the response should contain "I can help with"
    And the response should contain "audio"
    And the response should contain "window"

  Scenario: Help with specific category
    When I say "help with audio"
    Then the response should contain "Mute"

  Scenario: Help with category alias
    When I say "help with windows"
    Then the response should contain "window"

  Scenario: Help with sound alias
    When I say "help with sound"
    Then the response should contain "audio"

  Scenario: Help with unknown category
    When I say "help with foobar"
    Then the response should contain "No category"

  Scenario: What can you do
    When I say "what can you do"
    Then the response should contain "I can help with"
