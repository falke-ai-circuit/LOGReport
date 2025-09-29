# Command Queue Architecture

## Flow Diagram
```mermaid
graph TD
    A[UI Layer] -->|Commands| B(Command Queue)
    B --> C{Queue State}
    C -->|IDLE| D[Create Worker]
    C -->|PROCESSING| E[Reuse Worker]
    C -->|BACKPRESSURE| F[Throttle Input]
    D --> G[Worker Thread]
    E --> G
    G --> H[Log Results]
    H --> I[Update State]
    I --> C
```

## Components
| Component | Details |
|-----------|---------|
| Command Queue | Thread-safe FIFO (deque), atomic Lock, states (idle/processing/backpressure), max 1000 |
| Worker Management | Dynamic pooling; lifecycle: dequeue→execute→signal→cleanup |

## State Transitions
| From | To | Trigger |
|-----|----|---------|
| Idle | Processing | Commands received |
| Processing | Backpressure | Queue >800 |
| Backpressure | Processing | Queue <200 |
| Processing | Idle | Queue empty |

## Performance
| Metric | Value |
|--------|-------|
| Throughput | 1500 cmd/s |
| Latency | <50ms p95 |
| Max Depth | 1000 |
| Memory | <2MB/1000 cmd |

## Failure Handling
| Strategy | Details |
|----------|---------|
| Retries | Transient errors |
| Dead Letter | Failed cmds |
| Circuit Breaker | Node outages |