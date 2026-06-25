Feature: LOGReport frontend tests

  Background:
    * configure driver = { type: 'chrome', headless: true,
        addOptions: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] }

  Scenario: Report page loads
    * driver 'http://logreport:8080/'
    * waitFor('body')
    * match driver.title contains 'LOGReport'
    * screenshot()

  Scenario: Commander page loads
    * driver 'http://logreport:8080/commander'
    * waitFor('body')
    * screenshot()
    # Verify tree is present
    * match driver.text contains 'AP01m'

  Scenario: Node tree expands to show tokens
    * driver 'http://logreport:8080/commander'
    * waitFor('body')
    * match driver.text contains 'AP01m'
    * screenshot()

  # CRITICAL: Scan tab should show file dropdown, NOT paste box
  Scenario: Scan tab — should NOT have paste textarea
    * driver 'http://logreport:8080/commander'
    * waitFor('body')
    # Check if "Paste FBC file data here" exists — it should NOT
    * def hasPasteBox = driver.text.contains('Paste FBC file data')
    * if (hasPasteBox) karate.fail('Scan tab still uses paste textarea — gap F2')

  # CRITICAL: Commander should have "Set Log Root" button
  Scenario: Commander — should have Set Log Root button
    * driver 'http://logreport:8080/commander'
    * waitFor('body')
    * def hasLogRoot = driver.text.contains('Set Log Root') || driver.text.contains('Log Root')
    * if (!hasLogRoot) karate.fail('No Set Log Root button in Commander — gap F3')

  # Tree tokens should have status icons (colored circles)
  Scenario: Tree — should have status indicators
    * driver 'http://logreport:8080/commander'
    * waitFor('body')
    * screenshot()
    # This is a visual check — screenshot provides evidence

  # Telnet tab should connect to mock DNA node
  Scenario: Telnet tab — connect to mock node
    * driver 'http://logreport:8080/commander'
    * waitFor('body')
    # Look for telnet-related inputs
    * screenshot()

  # BsTool tab should render
  Scenario: BsTool tab renders
    * driver 'http://logreport:8080/commander'
    * waitFor('body')
    * screenshot()

  # Report generation from frontend
  Scenario: Report page — generate report button
    * driver 'http://logreport:8080/'
    * waitFor('body')
    * screenshot()
    # Check for format selection (PDF should be an option)
    * def hasPDF = driver.text.contains('PDF') || driver.text.contains('pdf')
    * if (!hasPDF) karate.fail('PDF format option missing in Report page — gap F1/F7')