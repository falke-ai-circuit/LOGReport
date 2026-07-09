# LOGReport Review Lab — 2026-06-25-review-001

## What This Lab Tests

This Containerlab + Karate lab tests the LOGReport Go+React app against a mock Valmet DNA telnet node. It provides automated evidence for the review findings.

## Testing Surface

| Dimension | Tested? | Feature File | Mock |
|-----------|---------|-------------|------|
| HTTP API (11 endpoints) | Yes | `api.feature` | N/A |
| Web frontend (React SPA) | Yes | `frontend.feature` | N/A |
| Telnet protocol (FBC/RPC/LIS) | Yes | `telnet.feature` | `mocks/dna_telnet_mock.py` |
| File processing (.fbc/.rpc/.log/.lis) | Yes | `file-processing.feature` | `fixtures/logs/` |
| Cross-platform (BsTool.exe) | No | — | Windows-only, needs Wine node |
| Real DNA hardware | No | — | Mock only, document as untested |

## Topology

```
┌──────────────┐       ┌──────────────────┐
│  logreport   │───────│  mock-dna-node   │
│  (Go app)    │ eth1  │  (Python mock)   │
│  :8080       │       │  :23 (telnet)    │
└──────────────┘       └──────────────────┘
       │ eth1
       │
┌──────┴───────┐
│   karate     │
│  (test run)  │
└──────────────┘
```

## Fixtures

- `fixtures/logs/AP01m.fbc` — sample FBC data (12 tokens, AI/DI fields)
- `fixtures/logs/AP01m.rpc` — sample RPC data
- `fixtures/logs/AP01m.lis` — sample LIS data
- `fixtures/logs/AP01m.log` — sample log file with timestamps

## How to Run

### Prerequisites
- Containerlab installed on host (SSH to 100.78.148.26)
- LOGReport binary built: `cd /opt/data/LOGReport && /opt/data/go/bin/go build -o logreport-bin ./cmd/logreport/`

### Deploy + Run

```bash
# SSH to hostinger host
ssh -i /opt/data/.ssh/hermes_desktop root@100.78.148.26

# Copy lab files to host (if running from container)
# scp -r this folder to host

# Deploy topology
cd /opt/data/LOGReport/reviews/2026-06-25-review-001/lab
containerlab deploy -t topology.yml

# Wait for nodes to initialize
sleep 10

# Run all tests
docker exec clab-logreport-test-lab-karate \
  java -jar /karate.jar -o /target/karate-reports /tests/

# Or run individual test suites
docker exec clab-logreport-test-lab-karate \
  java -jar /karate.jar -o /target/karate-reports /tests/api.feature

# Collect results
ls -la /opt/data/LOGReport/reviews/2026-06-25-review-001/results/
cat /opt/data/LOGReport/reviews/2026-06-25-review-001/results/*.xml

# Destroy topology when done
containerlab destroy -t topology.yml
```

## Test Results Interpretation

Tests are designed to PASS when features work and FAIL with descriptive messages when gaps exist:

- `karate.fail('PDF format not supported — CRITICAL gap F1')` → gap F1 confirmed
- `karate.fail('Scan tab still uses paste textarea — gap F2')` → gap F2 confirmed
- `karate.fail('No Set Log Root button in Commander — gap F3')` → gap F3 confirmed
- `karate.fail('No log file written after telnet commands — gap F5')` → gap F5 confirmed
- `karate.fail('PDF format option missing in Report page — gap F1/F7')` → gap F7 confirmed

After coder fixes, re-running the lab should show all tests passing — that's the evidence the gaps are closed.

## Adding Wine Node for BsTool Cross-Platform Testing

To test BsTool.exe (currently untested, Windows-only), add this node to `topology.yml`:

```yaml
    app-windows:
      kind: linux
      image: scottyhardy/docker-wine:latest
      binds:
        - ../../../../BsTool.exe:/app/BsTool.exe
      cmd: "sleep infinity"
```

Then add a `cross-platform.feature` file. See `automated-test-infrastructure` skill for reference.