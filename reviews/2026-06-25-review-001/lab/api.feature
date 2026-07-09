Feature: LOGReport API tests

  Background:
    * url 'http://logreport:8080/api/v1'

  Scenario: Health endpoint returns ok status
    Given path 'health'
    When method get
    Then status 200
    And match response == { status: 'ok', version: '#notnull', db_status: 'connected' }

  Scenario: Get all nodes
    Given path 'nodes'
    When method get
    Then status 200
    And match response contains { nodes: '#notnull' }

  Scenario: Get nodes tree
    Given path 'nodes', 'tree'
    When method get
    Then status 200
    And match response contains { tree: '#notnull' }

  Scenario: Generate DOCX report
    Given path 'reports', 'generate'
    And request { format: 'docx' }
    When method post
    Then status 200
    And match responseHeaders['Content-Type'][0] contains 'application'

  Scenario: Generate JSON report
    Given path 'reports', 'generate'
    And request { format: 'json' }
    When method post
    Then status 200

  # CRITICAL: PDF format should be supported but currently returns error
  Scenario: Generate PDF report — should work but currently fails
    Given path 'reports', 'generate'
    And request { format: 'pdf' }
    When method post
    Then assert responseStatus == 400 || responseStatus == 200
    * if (responseStatus == 400) karate.fail('PDF format not supported — CRITICAL gap F1')

  # CRITICAL: Log folder selection should exist — test if endpoint accepts log_root
  Scenario: Generate report with log_root parameter
    Given path 'reports', 'generate'
    And request { format: 'docx', log_root: '/app/test-logs' }
    When method post
    Then status 200
    # This test documents whether log_root is accepted — currently it's ignored

  Scenario: Scan endpoint — should accept file path not paste data
    Given path 'scan'
    When method get
    Then status 200
    And match response contains { nodes: '#notnull' }

  Scenario: Telnet connect to mock DNA node
    Given path 'telnet', 'connect'
    And request { host: 'mock-dna-node', port: 23 }
    When method post
    Then status 200

  Scenario: Telnet send command to mock DNA node
    Given path 'telnet', 'command'
    And request { command: 'get fbc' }
    When method post
    Then status 200
    And match response contains { output: '#notnull' }

  Scenario: SysFile upload
    Given path 'sysfile', 'upload'
    And multipart file file { read: '../fixtures/logs/AP01m.log', filename: 'AP01m.log', contentType: 'text/plain' }
    When method post
    Then status 200

  Scenario: BsTool status
    Given path 'bstool', 'status'
    When method get
    Then status 200