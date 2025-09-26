# TODO List

This file contains a list of pending tasks and improvements for the LOGReport project.

[X]When leftclicking on a node in nodes list corresponding command should appear in command pane automatically ( it appears when command is executed but i want when leftclicked command should appear so i can execute it by pressing execute. EXAMPLE: when leftlicked on AP01m_192_168_0_11-162.fbc file command print from fbc io structure 1620000 should appear in command ), we should do it for telnet tab and for bstool tab with corresponding implementation

[X]We should add colour change on nodes list to files that have been processed, .rpc .fbc .log and .lis files ( changes colour to green if command executed and if there is content in selected file for example more than 5 lines change to green, if command is executed and content is below 5 lines in file writing should be in red colour, and if no command is executed and its below 5 lines of content for example writing should become yellow)

[X]We should add lower timeout for bstool commands ( 10 seconds maybe?) before we read content from temporary file created by it.

[X]We should add colour persistence on .fbc .rpc .log and .lis files, also we should apply same colouring system to FBC RPC LIS and LOG subgroup and to nodes also, so we hierarchically colour the .fbc .rpc .log .lis and if all is green then subgroups become green, ifa ll subgroups are green then node becomes green 

[ ]We should add bstool inside pyinstall package and we should set the path automatically to it when started from packaged exe inside bstool tab executiong path ( otherwise we need it separately or we need to know the path ) 

[X]We should add a command to clear all files under selected subgroup, and also possibility to trigger all subgroups commands for clearing from node rightclick ( EXAMPLE: FBC subgroup   shoul had second command clear all .fbc logs or similar so user doesnt have to click on every file separately and then clear every log file, if command is under node then it should trigger subgroup commands and sequentially clear all files)

[ ]We should add posibility to execute all node related commands when rightclicked on node ( example: AP01m when executing all node commands should sequentially execute all FBC and RPC and LOG subcommands hierarchically, so clicking on AP01m and executing all commands would trigger all subcommands one after another )
