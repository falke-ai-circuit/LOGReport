# Validation Script for Token Detection
Write-Host "Starting token detection validation..."

# Create timestamp for report
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportFile = "validation_reports/validation_report_$timestamp.md"

# Start the application with debug logging
$debugLog = "validation_reports/logs/debug_$timestamp.log"
Write-Host "Launching application with debug logging to $debugLog"
Start-Process python -ArgumentList "src/main.py --debug" -RedirectStandardOutput $debugLog -NoNewWindow

Write-Host @"
==================================================
TOKEN DETECTION VALIDATION INSTRUCTIONS

1. Application is now running with debug logging
2. Perform these checks for each node type:
   - AP01m: Verify tokens 162,163,164 in context menu
   - AP01r: Verify tokens 362,363 in context menu
   - AP02m: Verify token 182 in context menu
   - AP02r: Verify token 382 in context menu
   - AP03m: Verify token 2a2 in context menu

3. For each node:
   - Check FBC and RPC subgroups show correct token counts
   - Ensure no duplicate tokens appear
   - Take screenshots of context menus:
        validation_reports/screenshots/AP01m.png
        validation_reports/screenshots/AP01r.png
        ...etc...

4. When finished:
   - Close the application
   - Press Enter here to generate report
==================================================
"@

# Wait for user to complete tests
Read-Host "Press Enter when validation is complete"

# Generate validation report
@"
# Token Detection Validation Report
**Date:** $(Get-Date)
**Validation Performed By:** User

## Test Cases

| Node  | Expected Tokens | Actual Tokens | Status | Screenshot |
|-------|-----------------|--------------|--------|------------|
| AP01m | 162,163,164     |              |        | [AP01m.png](screenshots/AP01m.png) |
| AP01r | 362,363         |              |        | [AP01r.png](screenshots/AP01r.png) |
| AP02m | 182             |              |        | [AP02m.png](screenshots/AP02m.png) |
| AP02r | 382             |              |        | [AP02r.png](screenshots/AP02r.png) |
| AP03m | 2a2             |              |        | [AP03m.png](screenshots/AP03m.png) |

## Debug Logs
[View Debug Logs](logs/debug_$timestamp.log)

## Conclusion
<!-- Add validation conclusion here -->
"@ | Out-File -FilePath $reportFile

Write-Host "Validation report generated: $reportFile"