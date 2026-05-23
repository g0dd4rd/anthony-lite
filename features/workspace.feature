Feature: Workspace commands

  Scenario: List workspaces
    When I say "list workspaces"
    Then the response should contain "2 workspaces"
    And the response should contain "workspace 1"

  Scenario: Switch to workspace
    When I say "switch to workspace 2"
    Then the response should contain "workspace 2"
    And MCP tool "activate_workspace" was called with index 1
