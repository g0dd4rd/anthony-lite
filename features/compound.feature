Feature: Compound commands

  Scenario: Two commands joined by and
    When I say "minimize firefox and maximize terminal"
    Then the response should contain "Minimized"
    And the response should contain "Maximized"
    And MCP tool "minimize_window" was called
    And MCP tool "maximize_window" was called

  Scenario: Commands joined by and then
    When I say "mute and then take a screenshot"
    Then MCP tool "mute_volume" was called
    And MCP tool "screenshot" was called

  Scenario: Verb carry-forward
    Given the following windows are open
      | id   | title          | wmClass              | focused | maximized |
      | 1001 | Firefox        | firefox              | true    | false     |
      | 1002 | Terminal       | org.gnome.Ptyxis     | false   | false     |
    When I say "minimize firefox and terminal"
    Then MCP tool "minimize_window" was called
