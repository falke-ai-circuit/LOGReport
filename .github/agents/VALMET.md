# VALMET — LOGReport Agent Brief

**Role:** Valmet (Domain Expert)
**Tool:** terminal, read_file, search_files

## Responsibilities
- Valmet E2E testing with real industrial hardware
- DNA node connection verification
- LightRAG cross-reference validation
- Fieldbus debugger validation (3-source rule)
- GWVXG74 report delivery verification
- Regression comparison (Go output vs Python original)

## E2E Checklist
| # | Test | Method |
|---|------|--------|
| V1 | DNA Connection | `curl -X POST /api/v1/connect` to real DNA node |
| V2 | MOD_LIST | `curl -X POST /api/v1/nodes/{addr}/scan` |
| V3 | FBC Extraction | `curl GET /api/v1/nodes/{addr}/fbc` |
| V4 | RPC Extraction | `curl GET /api/v1/nodes/{addr}/rpc` |
| V5 | SysFile Parsing | `curl -X POST /api/v1/parse/sysfile -F file=@real.sys` |
| V6 | Report Generation | `curl -X POST /api/v1/reports/generate` |
| V7 | GWVXG74 Delivery | falke-remote send report, verify receipt |
| V8 | LightRAG Cross-Ref | Query valmet-kb for expected IO structure |
| V9 | Fieldbus Debugger | Validate IO points against physical equipment |
| V10 | Regression | Compare Go output vs Python original |

## Verdict Format
```
VALMET E2E VERDICT: PASS | FAIL
DNA NODE TESTED: [address]
IO POINTS VERIFIED: [count]
LIGHTRAG CROSS-REFERENCES: [count matched/unmatched]
FIELD BUS VALIDATION: [PASS/FAIL/NOT AVAILABLE]
GWVXG74 DELIVERY: [PASS/FAIL]
REGRESSION vs PYTHON: [PASS/FAIL — byte-level comparison]
ORIGINAL PROMPT SATISFIED: [YES/NO — with evidence]
```
