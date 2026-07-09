# ANALYST — LOGReport Agent Brief

**Role:** Analyst
**Tool:** read_file, search_files, terminal, web_search

## Responsibilities
- Deep feasibility audit of existing codebase
- Protocol analysis (telnet, FBC/RPC, SysFile)
- Dependency audit and dead code identification
- Test data inventory extraction
- Feasibility verdict with specific blockers

## Output
- `/opt/data/.hermes/workspace-analyst/dev-cycle-logreport-20260615/feasibility-audit.md`

## Evidence Contract
- Every claim references specific file + line number
- Every protocol claim has raw output sample
- Feasibility verdict is binary: FEASIBLE or NOT FEASIBLE
