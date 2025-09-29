# Memory Consolidation Architecture

## Dual Memory System
```mermaid
flowchart TD
    A[Project Memory] -->|Promotion| B(Global Memory)
    B -->|Pattern Reuse| C[New Projects]
    A --> D[Current Project]
    D -->|Context-Specific| E[Implementation Details]
    B -->|Best Practices| D
```

## UAL Resolution Sequence
```mermaid
sequenceDiagram
    participant C as Commander
    participant P as Project Memory
    participant G as Global Memory
    C->>P: Resolve Project UAL
    alt Project UAL Found
        P-->>C: Return Entity
    else
        C->>G: Resolve Global UAL
        G-->>C: Return Pattern
        C->>P: Store Local Instance
    end
```

## Cryptographic Verification
```python
def verify_memory_integrity(entity):
    content = json.dumps(entity, sort_keys=True)
    computed_hash = hashlib.sha256(content.encode()).hexdigest()
    return computed_hash == entity['integrity_hash']
```

## ⬆️ Promotion Workflow

| Step | Description |
|---|---|
| **Validation** | Verify pattern meets reuse criteria |
| **Normalization** | Standardize pattern structure |
| **Versioning** | Apply global version scheme |
| **Chaining** | Link to source project version |
| **Verification** | Generate integrity hash |
| **Promotion** | Add to global memory |

## Performance Metrics
| Operation | Avg Time | 95th %ile |
|-----------|----------|-----------|
| Local Lookup | 12ms | 25ms |
| Global Lookup | 45ms | 85ms |
| Pattern Promotion | 320ms | 520ms |
| Integrity Check | 8ms | 15ms |

## ✨ Recent Enhancements

| Enhancement | Description |
|---|---|
| **SHA-256 Verification** | Cryptographic integrity check |
| **Version Chaining** | Links patterns across memory systems |
| **Batch Promotion** | Efficient bulk pattern promotion |
| **Auto Dependency Resolution** | Streamlined dependency management |