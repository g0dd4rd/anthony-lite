Feature: Search and open commands

  Scenario: Open an app that is already running
    When I say "open firefox"
    Then the response should contain "already running"
    And MCP tool "focus_window" was called

  Scenario: Open a URL
    When I say "open google.com"
    Then the response should contain "Opening"
    Then the response should contain "google.com"

  Scenario: Go to a website
    When I say "go to github.com"
    Then the response should contain "Opening"
    Then the response should contain "github.com"

  Scenario: Search for files
    When I say "search for screenshots"
    Then the response should contain "No files found"
    And MCP tool "search_files" was called
