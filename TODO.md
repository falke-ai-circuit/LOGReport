# TODO List

This file contains a list of pending tasks and improvements for the LOGReport project.

[ ]When leftclicking on a node in nodes list corresponding command should appear in command pane automatically ( it appears when command is executed but i want when leftclicked command should appear so i can execute it by pressing execute. EXAMPLE: when leftlicked on AP01m_192_168_0_11-162.fbc file command print from fbc io structure 1620000 should appear in command )

[ ]We should add a command to clear all files under selected subgroup ( EXAMPLE: FBC subgroup   shoul had second command clear all .fbc logs or similar so user doesnt have to click on every file separately and then clear every log file)

[ ]We should add posibility to execute all node related commands when rightclicked on node ( example: AP01m when executing all node commands should sequentially execute all FBC and RPC and LOG subcommands hierarchically, so clicking on AP01m and executing all commands would trigger all subcommands one after another )

[ ]We should add Bstool tab wich will use external tool called bstool.exe ( wich is exe file found in project root, so we should move where necessary appropriately ) and integrate it so we can use it in same way we use telnet to get information in automated way, please make a blueprint with mockup for the tab and integrate bstool.exe in our program so when we use build.exe we also have the bstool with use to use. create also roadmap that we can use to integrate this tab ask user to approve and then start implementing