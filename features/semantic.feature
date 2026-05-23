@semantic
Feature: Semantic fallback matching

  Scenario: Paraphrase for volume up
    When I say "make it louder"
    Then the response should contain "Volume"

  Scenario: Paraphrase for muting
    When I say "silence the speakers"
    Then the response should contain "Muted"

  Scenario: Gibberish does not match
    When I say "the quick brown fox jumped over the lazy dog"
    Then there is no match
