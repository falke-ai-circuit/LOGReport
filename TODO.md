# TODO List

This file contains a list of pending tasks and improvements for the LOGReport project.

[X]We should show content that we copy to selected files when commands are executed in telnet tab window
So its clear and visible whats being received and written to .lis .fbc .log .rpc files

[X]When leftclicking on a node in nodes list corresponding command should appear in command pane automatically ( it appears when command is executed but i want when leftclicked command should appear so i can execute it by pressing execute. EXAMPLE: when leftlicked on AP01m_192_168_0_11-162.fbc file command print from fbc io structure 1620000 should appear in command ), we should do it for telnet tab and for bstool tab with corresponding implementation

[X]We should add colour change on nodes list to files that have been processed, .rpc .fbc .log and .lis files ( changes colour to green if command executed and if there is content in selected file for example more than 5 lines change to green, if command is executed and content is below 5 lines in file writing should be in red colour, and if no command is executed and its below 5 lines of content for example writing should become yellow)

[X]We should add lower timeout for bstool commands ( 10 seconds maybe?) before we read content from temporary file created by it.

[X]We should add colour persistence on .fbc .rpc .log and .lis files, also we should apply same colouring system to FBC RPC LIS and LOG subgroup and to nodes also, so we hierarchically colour the .fbc .rpc .log .lis and if all is green then subgroups become green, ifa ll subgroups are green then node becomes green 

[ ]We should add bstool inside pyinstall package and we should set the path automatically to it when started from packaged exe inside bstool tab executiong path ( otherwise we need it separately or we need to know the path ) 

[X]We should add a command to clear all files under selected subgroup, and also possibility to trigger all subgroups commands for clearing from node rightclick ( EXAMPLE: FBC subgroup   shoul had second command clear all .fbc logs or similar so user doesnt have to click on every file separately and then clear every log file, if command is under node then it should trigger subgroup commands and sequentially clear all files)

[X]we need to change colour of nodes in node configurator to green for nodes that have all information and to red ones that miss information, also we need to detect automatically when we load AB01_sys and search if tokenid.sys file exists in same directory and load ip adress from it, and if we already have a list we should be able to click on load sys file and if we load only tokenid.sys it should automatically understand and export ip adress for node with that tokenid

[X]We need to adjust main generate report window since in report not all files content are visible ( we need to scan for .log .lis and .fbc and .rpc files in subfolders selected by select log folder, also when generating report we should use those files contents, i belive old way was to scan only for .log files but we should scan for all and include content in our report )

[X]We need to implement in node tree list to show colours based on file content ( if we have sucesfully executed a operation and written to file and it became green when we reopen program we should check if content is there and should make it green again ), also during execution node tree should autp expand and show processed file and highlight it when its processed - COMPLETED 2025-10-10: Implemented startup color persistence checking file content (red=0 lines, yellow<10 lines, green>=10 lines). Auto-expansion implemented: entire tree expands when "Print All Nodes" clicked, making all files visible. Files highlight and scroll into view as they're processed during command execution.

[X]We should show content that we copy to selected files when commands are executed in telnet tab window - COMPLETED 2025-01-10: Actual file content now displays in Telnet tab with headers showing destination file and statistics. Users can compare displayed content with saved files for verification.

[ ]We need to fix ASCII table column alignment in Telnet tab when displaying FBC command output. Currently the vertical columns (like the 'sum' column with zeros) are not properly aligned with their headers despite using monospace font and tab-to-space conversion. The table displays correctly in the log files but not in the Telnet tab widget. Need to investigate alternative approaches: different fonts (Liberation Mono, DejaVu Sans Mono), pre-processing the content to normalize spacing, or using a different widget type (QPlainTextEdit, custom table widget).

[]We need to include a stopping of execution actions if telnet debugger is disconnected so that way we dont send commands if there is no connection, also in telnet tab when we connect using connect we are connecting to debugger session of our remote system and if someone else is connected it will ask if we want to connect and we should write yes and press enter. when we are in debugger remote session we should be in system mode ( wich is indicated by %s ) and we can change mode by typing toggle and pressing enter ( wich will show either system or appl mode, we need to be in system mode to be able to send commands )

[]We need to debug pause resume and cancel of Print All Nodes command in commander window since it is not doing anything at the moment and it should pause resume and cancel main workflow

[X]VNC tab and all related functionality completely removed as per user request on 2025-01-10. Deleted vnc_tab.py (272 lines), test_vnc_connection.py (193 lines). Modified 8 files removing VNC imports, classes, methods, signal connections. Application maintains Telnet and BsTool functionality. Verified with pytest: 488/489 tests collected (1 VNC test properly excluded), 26 tests passed.

[]we need to change rectangle colour on log file we currently processed in commander window ( logfile naming colour changes based on content but rectangle should change based on executed command )it can become green upon command execution, and even subgroup rectangle can become green if all file commands are executed and green and node circle can become green if all its subgroup rectangles are green 