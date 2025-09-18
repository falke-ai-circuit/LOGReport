# TODO List

This file contains a list of pending tasks and improvements for the LOGReport project.

[ ]When leftclicking on a node in nodes list corresponding command should appear in command pane automatically ( it appears when command is executed but i want when leftclicked command should appear so i can execute it by pressing execute. EXAMPLE: when leftlicked on AP01m_192_168_0_11-162.fbc file command print from fbc io structure 1620000 should appear in command ), we should do it for telnet tab and for bstool tab with corresponding implementation

[ ]We should add a command to clear all files under selected subgroup ( EXAMPLE: FBC subgroup   shoul had second command clear all .fbc logs or similar so user doesnt have to click on every file separately and then clear every log file)

[ ]We should add posibility to execute all node related commands when rightclicked on node ( example: AP01m when executing all node commands should sequentially execute all FBC and RPC and LOG subcommands hierarchically, so clicking on AP01m and executing all commands would trigger all subcommands one after another )

[ ]We should add colour change on nodes list to files that have been processed ( changes colour to green if command executed and written to file)

[ ]We should add lower timeout for bstool commands ( 10 seconds maybe?) before we read content from temporary file created by it.

[ ]We should add bstool inside pyinstall package and we should set the path automatically to it when started from packaged exe inside bstool tab executiong path ( otherwise we need it separately or we need to know the path ) 