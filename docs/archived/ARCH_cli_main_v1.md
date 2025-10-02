---
reason: 'outdated CLI, low refs'
archived_date: '2025-10-02'
original_path: 'docs/architecture/ARCH_cli_main_v1.md'
---

# 🏗️ CLI Main

Param | Type | Desc |
|-------|------|------|
input_path | str | Logs dir |
output_file | str | Report path |

Flow: Init→Scan/Parse→Gen/Save→Complete ✅Orch (Cmd Red 15%)

Deps: [Proc](src/processor.py) [Gen](src/generator.py)