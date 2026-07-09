Feature: LOGReport file processing tests

  Background:
    * url 'http://logreport:8080/api/v1'

  # Test that LOGReport can process log files from a directory
  # This tests the CRITICAL gap F1 — log file → report pipeline

  Scenario: List log files from log root directory
    Given path 'logs'
    And request { log_root: '/app/test-logs' }
    When method get
    Then status 200
    # If this endpoint doesn't exist, it's evidence of gap F1
    # Response should list .fbc, .rpc, .log, .lis files

  Scenario: Process FBC file and generate report
    Given path 'reports', 'generate'
    And request { format: 'docx', log_root: '/app/test-logs', file_filter: '.fbc' }
    When method post
    Then status 200
    # Currently the API ignores log_root — this test documents that

  Scenario: Process all log files from log root
    Given path 'reports', 'generate'
    And request { format: 'json', log_root: '/app/test-logs' }
    When method post
    Then status 200
    # Response should contain data from the log files, not just SQLite scan data

  # FBC file comparison (F2 — Scan tab should do cell-by-cell comparison)
  Scenario: Compare two FBC files
    Given path 'scan', 'compare'
    And request { file1: '/app/test-logs/AP01m.fbc', file2: '/app/test-logs/AP01m.fbc' }
    When method post
    Then status 200
    # If endpoint doesn't exist, it's evidence of gap F2

  # Verify test fixtures are accessible
  Scenario: Test fixtures exist in container
    * def fbcExists = karate.exec({ line: 'test -f /app/test-logs/AP01m.fbc && echo EXISTS || echo MISSING', workingDir: '/app' })
    * match fbcExists contains 'EXISTS'
    * def rpcExists = karate.exec({ line: 'test -f /app/test-logs/AP01m.rpc && echo EXISTS || echo MISSING', workingDir: '/app' })
    * match rpcExists contains 'EXISTS'
    * def lisExists = karate.exec({ line: 'test -f /app/test-logs/AP01m.lis && echo EXISTS || echo MISSING', workingDir: '/app' })
    * match lisExists contains 'EXISTS'
    * def logExists = karate.exec({ line: 'test -f /app/test-logs/AP01m.log && echo EXISTS || echo MISSING', workingDir: '/app' })
    * match logExists contains 'EXISTS'