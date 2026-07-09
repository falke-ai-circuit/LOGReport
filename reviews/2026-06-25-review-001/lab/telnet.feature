Feature: LOGReport telnet protocol tests against mock DNA node

  Background:
    * url 'http://logreport:8080/api/v1'

  # Test that LOGReport's telnet tab can connect to a mock DNA node
  # and execute the FBC/RPC/LIS commands that Valmet DNA engineers use daily

  Scenario: Connect to mock DNA node via telnet
    Given path 'telnet', 'connect'
    And request { host: 'mock-dna-node', port: 23 }
    When method post
    Then status 200

  Scenario: Execute "get fbc" command and receive FBC data
    Given path 'telnet', 'command'
    And request { command: 'get fbc' }
    When method post
    Then status 200
    And match response contains { output: '#notnull' }
    # FBC response should contain TOKEN and AI/DI fields
    * def outputText = response.output
    * if (!outputText.contains('TOKEN') && !outputText.contains('FBC')) karate.fail('FBC response does not contain expected fields')

  Scenario: Execute "get rpc" command and receive RPC data
    Given path 'telnet', 'command'
    And request { command: 'get rpc' }
    When method post
    Then status 200
    And match response contains { output: '#notnull' }

  Scenario: Execute "scan node" command
    Given path 'telnet', 'command'
    And request { command: 'scan node' }
    When method post
    Then status 200
    And match response contains { output: '#notnull' }

  Scenario: Execute "status" command
    Given path 'telnet', 'command'
    And request { command: 'status' }
    When method post
    Then status 200
    And match response contains { output: '#notnull' }

  Scenario: Disconnect from mock DNA node
    Given path 'telnet', 'disconnect'
    When method post
    Then status 200

  # Test that telnet commands are logged (F5 — log writer with decorative headers)
  # This test will fail until log writer is implemented
  Scenario: Telnet command produces log file
    * def logCheck = karate.exec({ line: 'ls /app/test-logs/*.log 2>/dev/null', workingDir: '/app' })
    * if (logCheck.trim() == '') karate.fail('No log file written after telnet commands — gap F5')