---
metadata:
  created_date: "2025-09-01_000000"
  last_modified: "2025-10-01T06:00:00Z"
  last_accessed: "2025-10-01T06:00:00Z"
  word_count: 20
  reference_count: 2
  document_hash: "sha256:computed_hash_cli"
  similarity_index: 0.95
  obsolete_check_date: "2025-10-01"
---

# 🏗️ CLI Main

Param | Type | Desc |
|-------|------|------|
input_path | str | Logs dir |
output_file | str | Report path |

Flow: Init→Scan/Parse→Gen/Save→Complete ✅Orch (Cmd Red 15%)

Deps: [Proc](src/processor.py) [Gen](src/generator.py)