Feature: Audio commands

  Scenario: Mute
    When I say "mute"
    Then the response should contain "Muted"
    And MCP tool "mute_volume" was called with mute true

  Scenario: Unmute
    When I say "unmute"
    Then the response should contain "Unmuted"
    And MCP tool "mute_volume" was called with mute false

  Scenario: Set volume to specific level
    When I say "set volume to 75"
    Then the response should contain "50%"
    And MCP tool "set_volume" was called with volume 75

  Scenario: Volume up
    When I say "volume up"
    Then the response should contain "Volume"
    And MCP tool "set_volume" was called

  Scenario: Volume down
    When I say "volume down"
    Then the response should contain "Volume"
    And MCP tool "set_volume" was called

  Scenario: Play music
    When I say "play"
    Then the response should contain "Playing"
    And MCP tool "media_control" was called with action "play"

  Scenario: Pause music
    When I say "pause"
    Then the response should contain "Paused"
    And MCP tool "media_control" was called with action "pause"

  Scenario: Stop music
    When I say "stop"
    Then the response should contain "Stopped"
    And MCP tool "media_control" was called with action "stop"

  Scenario: Next track
    When I say "next track"
    Then the response should contain "Test Song"
    And MCP tool "media_control" was called with action "next"

  Scenario: Previous track
    When I say "previous track"
    Then the response should contain "Test Song"
    And MCP tool "media_control" was called with action "previous"

  Scenario: Mute tab
    When I say "mute tab"
    Then the response should contain "Muted tab"
    And MCP tool "key_combo" was called with keys "ctrl+m"

  Scenario: Unmute tab
    When I say "unmute tab"
    Then the response should contain "Unmuted tab"
    And MCP tool "key_combo" was called with keys "ctrl+m"

  Scenario: Increase volume says louder
    When I say "louder"
    Then the response should contain "Volume"

  Scenario: Decrease volume says quieter
    When I say "quieter"
    Then the response should contain "Volume"
