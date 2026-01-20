# Phase 3: Test Organization - Batch Move Script
# Execute this script to reorganize all test files

Write-Host "📦 PHASE 3: Test Organization - Starting batch moves..." -ForegroundColor Cyan

# Counter for tracking
$moved = 0

# NODE MANAGEMENT TESTS
Write-Host "`n🔹 Moving Node Management tests..." -ForegroundColor Yellow
Move-Item "tests/test_node_manager_simple.py" -Destination "tests/unit/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_node_suffix_stripping.py" -Destination "tests/unit/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/unit/test_node_tree_presenter.py" -Destination "tests/unit/node_management/" -Force -ErrorAction SilentlyContinue; $moved++

Move-Item "tests/test_node_config_integration.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_node_config_parser.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_node_config_transformation.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_node_config_validation.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_node_config_sys_file_ui.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++

Move-Item "tests/commander/test_node_color_logic.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_node_color_update_integration.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_node_click_telnet_command_input.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_node_hierarchical_commands.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_node_print_commands.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_node_tree_presenter_signals.py" -Destination "tests/integration/node_management/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved $moved Node Management tests"

# BSTOOL TESTS
Write-Host "`n🔹 Moving BsTool tests..." -ForegroundColor Yellow
Move-Item "tests/test_bstool_append.py" -Destination "tests/integration/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_bstool_bundling.py" -Destination "tests/integration/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_bstool_color_updates.py" -Destination "tests/integration/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_bstool_context_menu_fix.py" -Destination "tests/regression/bstool_issues/" -Force -ErrorAction SilentlyContinue; $moved++

Move-Item "tests/commander/system/test_bstool_path_persistence_e2e.py" -Destination "tests/system/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/system/test_bstool_system_integration.py" -Destination "tests/system/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/system/test_bstool_ui_output.py" -Destination "tests/system/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/system/test_bstool_ui_output_e2e.py" -Destination "tests/system/bstool/" -Force -ErrorAction SilentlyContinue; $moved++

Move-Item "tests/commander/test_bstool_command_service.py" -Destination "tests/integration/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_bstool_copy_to_log_integration.py" -Destination "tests/integration/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_bstool_import.py" -Destination "tests/unit/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_bstool_tab_ui.py" -Destination "tests/integration/bstool/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_fbc_subsection_context_menu.py" -Destination "tests/integration/bstool/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved BsTool tests"

# SYS FILE TESTS
Write-Host "`n🔹 Moving SYS File tests..." -ForegroundColor Yellow
Move-Item "tests/test_sys_file_loader.py" -Destination "tests/unit/sys_file/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_sys_file_parser.py" -Destination "tests/unit/sys_file/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_sys_file_parsing.py" -Destination "tests/system/sys_file/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved SYS File tests"

# RPC COMMAND TESTS
Write-Host "`n🔹 Moving RPC Command tests..." -ForegroundColor Yellow
Move-Item "tests/test_rpc_normalization.py" -Destination "tests/unit/rpc_commands/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_rpc_log_path.py" -Destination "tests/unit/rpc_commands/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_rpc_command_generation.py" -Destination "tests/integration/rpc_commands/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_rpc_token_detection.py" -Destination "tests/integration/rpc_commands/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved RPC Command tests"

# TELNET TESTS
Write-Host "`n🔹 Moving Telnet tests..." -ForegroundColor Yellow
Move-Item "tests/commander/test_telnet_connect.py" -Destination "tests/integration/telnet/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_telnet_connection.py" -Destination "tests/integration/telnet/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_telnet_connect_integration.py" -Destination "tests/integration/telnet/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_telnet_copy_to_log_integration.py" -Destination "tests/integration/telnet/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_telnet_command_output.py" -Destination "tests/integration/telnet/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_telnet_connection_management.py" -Destination "tests/system/telnet/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved Telnet tests"

# LOG MANAGEMENT TESTS
Write-Host "`n🔹 Moving Log Management tests..." -ForegroundColor Yellow
Move-Item "tests/commander/test_clear_log.py" -Destination "tests/unit/log_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_log_filename_parser.py" -Destination "tests/unit/log_management/" -Force -ErrorAction SilentlyContinue; $moved++

Move-Item "tests/commander/test_clear_subgroup_log_files.py" -Destination "tests/integration/log_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_copy_to_log_functionality.py" -Destination "tests/integration/log_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_log_writer.py" -Destination "tests/integration/log_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_log_writer_additional.py" -Destination "tests/integration/log_management/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_log_write_notification_display.py" -Destination "tests/integration/log_management/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved Log Management tests"

# COMMAND QUEUE TESTS
Write-Host "`n🔹 Moving Command Queue tests..." -ForegroundColor Yellow
Move-Item "tests/test_command_queue_sequential.py" -Destination "tests/integration/command_queue/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_sequential_integration.py" -Destination "tests/integration/command_queue/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_hierarchical_manual.py" -Destination "tests/integration/command_queue/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_command_execution.py" -Destination "tests/integration/command_queue/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_hierarchical_command_execution.py" -Destination "tests/integration/command_queue/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_sequential_output_display.py" -Destination "tests/system/command_queue/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved Command Queue tests"

# UI BEHAVIOR TESTS
Write-Host "`n🔹 Moving UI Behavior tests..." -ForegroundColor Yellow
Move-Item "tests/test_auto_connect_initialization.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_debugger_connection_management.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_pause_resume_cancel.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_pause_resume_cancel_buttons.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_print_all_nodes_auto_connect.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_smart_tab_switching.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_startup_color_logic.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_tree_expansion.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_qt_append_behavior.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/test_qt_behavior.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++

Move-Item "tests/commander/test_button_actions.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_button_styling.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_clipboard_monitor.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_commander_window.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_print_all_nodes_button.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_session_player.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/test_session_recorder.py" -Destination "tests/integration/ui_behavior/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved UI Behavior tests"

# REGRESSION TESTS
Write-Host "`n🔹 Moving Regression tests..." -ForegroundColor Yellow
Move-Item "tests/test_auto_expansion_fix.py" -Destination "tests/regression/ui_issues/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/regression_test_load_nodes_explorer.py" -Destination "tests/regression/node_issues/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/regression_test_select_root_button.py" -Destination "tests/regression/ui_issues/" -Force -ErrorAction SilentlyContinue; $moved++
Move-Item "tests/commander/regression_test_telnet_tab_visibility.py" -Destination "tests/regression/ui_issues/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "✅ Moved Regression tests"

# MISC TESTS
Write-Host "`n🔹 Moving remaining tests..." -ForegroundColor Yellow
Move-Item "tests/test_multi_file_report_generation.py" -Destination "tests/integration/" -Force -ErrorAction SilentlyContinue; $moved++

Write-Host "`n✅ COMPLETE: Moved $moved test files"
Write-Host "`n📊 Verifying organization..." -ForegroundColor Cyan

# Count files in new locations
$unitCount = (Get-ChildItem "tests/unit" -Recurse -File | Measure-Object).Count
$integrationCount = (Get-ChildItem "tests/integration" -Recurse -File | Measure-Object).Count
$systemCount = (Get-ChildItem "tests/system" -Recurse -File | Measure-Object).Count
$regressionCount = (Get-ChildItem "tests/regression" -Recurse -File | Measure-Object).Count

Write-Host "📁 Unit tests: $unitCount files" -ForegroundColor Green
Write-Host "📁 Integration tests: $integrationCount files" -ForegroundColor Green
Write-Host "📁 System tests: $systemCount files" -ForegroundColor Green
Write-Host "📁 Regression tests: $regressionCount files" -ForegroundColor Green

Write-Host "`n🎉 Phase 3: Test Organization COMPLETE!" -ForegroundColor Cyan
