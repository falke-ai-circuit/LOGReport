# Review 007 — F8 Fix: Context-Aware Telnet Dial for Immediate Cancel

**Date:** 2026-07-01  
**Reviewer:** Coder (automated review)  
**Scope:** F8 fix only — 3 files changed, 93 insertions, 12 deletions  
**Verdict:** ✅ **PASS** — fix is correct, no race conditions, no goroutine leaks, non-queue callers unaffected

---

## Files Reviewed

| File | Change |
|------|--------|
| `internal/telnet/client.go` | Added `DialContext` function (lines 72-89) |
| `internal/telnet/session.go` | Added `ConnectContext` (lines 69-97), `Connect` delegates to it (line 61), added `context` import |
| `internal/api/handlers_commander.go` | Both queue executors use context-aware connect (handleQueueStart ~593, handleQueueResume ~709) |

**Build:** `go build ./internal/telnet/ ./internal/api/` — passes, zero errors.

---

## Verification Checklist

### 1. Context-cancel pattern is correct ✅

The fix introduces a three-layer context propagation:

```
cancelCh (queue) → goroutine → context.Cancel() → DialContext → dialer.DialContext(ctx, ...)
```

- `Queue.Cancel()` and `Queue.Pause()` close `cancelCh` (queue.go:224-236, 198-208)
- A goroutine in the executor bridges `cancelCh` → `cancel()` (handlers_commander.go:602-608, 714-720)
- `DialContext` passes `ctx` to `dialer.DialContext(ctx, "tcp", addr)` (client.go:80)
- When `ctx` is cancelled, `dialer.DialContext` aborts immediately — Go's net package handles this natively

This is the standard Go context-cancel pattern for network operations. Correct.

### 2. `DialContext` properly uses `dialer.DialContext(ctx, ...)` ✅

```go
// client.go:76-89
func DialContext(ctx context.Context, host string, port int, timeout time.Duration) (*Client, error) {
    addr := net.JoinHostPort(host, fmt.Sprintf("%d", port))
    dialer := net.Dialer{Timeout: timeout}
    conn, err := dialer.DialContext(ctx, "tcp", addr)
    if err != nil {
        return nil, fmt.Errorf("telnet dial %s: %w", addr, err)
    }
    return &Client{conn: conn, timeout: timeout}, nil
}
```

- Uses `net.Dialer.DialContext` — the correct stdlib function for context-aware dialing
- `dialer.Timeout` is still set as a fallback: if `ctx` is never cancelled, the dialer's own timeout applies (same behavior as the old `Dial` function)
- Error wrapping preserved (`%w` for `errors.Is` compatibility)
- Returns the same `*Client` struct — no downstream changes needed

### 3. Goroutine does not leak ✅

Both executors use the same goroutine pattern:

```go
// handlers_commander.go:602-608 (handleQueueStart)
cancelCh := s.commandQueue.CancelCh()
ctx, cancel := context.WithCancel(context.Background())
if cancelCh != nil {
    go func() {
        select {
        case <-cancelCh:
            cancel()
        case <-ctx.Done():
        }
    }()
}
```

The goroutine has two exit paths:

| Trigger | Exit path | Goroutine exits? |
|---------|-----------|-----------------|
| `cancelCh` closes (Cancel/Pause called) | `case <-cancelCh` fires → calls `cancel()` → returns | ✅ Yes |
| `ConnectContext` completes (success or error) | Executor calls `cancel()` at line 630/742 → `ctx.Done()` fires → `case <-ctx.Done()` | ✅ Yes |
| `cancelCh` is nil (shouldn't happen during Start, but defensive) | Goroutine not started (`if cancelCh != nil` guard) | ✅ N/A |

No leak in any scenario. The `case <-ctx.Done()` branch is the key — it ensures the goroutine exits even when the dial completes normally without cancellation.

### 4. Non-queue callers unaffected ✅

`Connect` delegates to `ConnectContext` with `context.Background()`:

```go
// session.go:60-62
func (sm *SessionManager) Connect(sessionID, host string, port int, timeout time.Duration) (*Session, error) {
    return sm.ConnectContext(context.Background(), sessionID, host, port, timeout)
}
```

`context.Background()` is never cancelled, so `dialer.DialContext` uses only the `dialer.Timeout` — identical behavior to the old `dialer.Dial`. Four non-queue call sites confirmed:

| Caller | File:Line | Uses `Connect` (not `ConnectContext`) |
|--------|-----------|--------------------------------------|
| `handleTelnetConnect` | handlers_commander.go:281 | ✅ |
| `handleExecuteSingleCommand` | handlers_commander.go:462 | ✅ |
| WebSocket telnet handler | handlers_websocket.go:126 | ✅ |
| Batch node executor | handlers_commander.go:1578 | ✅ |

No behavior change for any non-queue caller.

### 5. Race condition analysis ✅

**Race 1: Concurrent `cancel()` calls**  
The goroutine may call `cancel()` (when cancelCh closes) and the executor also calls `cancel()` at line 630/742 after ConnectContext returns. `context.CancelFunc` is documented as safe to call concurrently and multiple times. No issue.

**Race 2: `cancelCh` closes simultaneously with `ctx.Done()`**  
The `select` is non-deterministic — either case may fire. Both lead to goroutine exit. If `cancelCh` fires, it calls `cancel()` (redundant with executor's call, but safe). If `ctx.Done()` fires first, the goroutine exits without calling `cancel()` — but the executor already called it. No issue.

**Race 3: Each executor invocation has its own context**  
Each call to the executor creates a fresh `context.WithCancel` and a fresh goroutine. Contexts are not shared across executor invocations. No issue.

**Race 4: `CancelCh()` returns a stale channel**  
`CancelCh()` is called inside the executor body (not captured in the closure), so it returns the current `cancelCh` from the running queue. `Start()` creates `cancelCh` at line 125 before entering the loop. The executor is called from within the loop (line 163). The channel is always valid during execution. No issue.

**Race 5: `cancelCh` is nil**  
Guarded by `if cancelCh != nil`. If nil, the goroutine is not started, and `ConnectContext` runs with a context that's only cancelled by the executor's `cancel()` call at line 630/742. No issue.

### 6. Error handling after cancelled dial ✅

```go
// handlers_commander.go:629-637
sess, err := s.telnetSM.ConnectContext(ctx, "", host, port, 10*time.Second)
cancel() // release context resources after connect completes
if err != nil {
    if ctx.Err() != nil {
        return "", fmt.Errorf("cancelled during connect")
    }
    return "", fmt.Errorf("reconnect failed: %w", err)
}
```

- `cancel()` is called immediately after ConnectContext returns — releases context resources and signals the goroutine to exit
- `ctx.Err()` distinguishes cancellation from a genuine connection error
- On cancellation, returns a clear `"cancelled during connect"` error
- The queue loop then sees `q.cancelled` on the next iteration (line 130), marks remaining commands as cancelled, and sets state to `QueueIdle`

Correct flow.

---

## Observations (non-blocking)

### O1: `verifySystemMode` is not context-aware

After `DialContext` succeeds, `ConnectContext` calls `verifySystemMode(sess)` (session.go:90) which uses `time.Sleep` and `SetReadDeadline` — not context-aware. If the host is reachable but Cancel is called during `verifySystemMode` (which takes ~5-6s worst case), the cancellation won't be immediate.

This is a pre-existing limitation and outside the F8 fix scope. The F8 fix specifically addresses the unreachable-host case where `Dial` blocks for the full 10s timeout. If the host is reachable, `verifySystemMode` completes in ~3-5s normally, and the `waitForOutput` call after the command (line 656/760) already checks `cancelCh`. The window for delay is narrow and acceptable.

### O2: Code duplication between handleQueueStart and handleQueueResume

The executor closure is duplicated verbatim between `handleQueueStart` (lines 577-670) and `handleQueueResume` (lines 696-772). This is pre-existing (not introduced by the F8 fix) but worth noting for future cleanup. A shared `makeExecutor()` method would eliminate the duplication.

---

## Test Results (from VM, per task description)

- DIA host set to 192.168.99.99 (unreachable)
- 11 commands queued, queue started
- Cancel called after 2s
- Cancel + status check completed in **1005ms** (was ~8-10s before fix)
- Queue state: idle, current=1, total=11

The ~1s residual is expected: the cancel API call itself + the goroutine wakeup + DialContext abort + queue loop iteration to set state. This is a 8-10x improvement over the pre-fix behavior.

---

## Verdict

**✅ PASS.** The F8 fix is correct, well-structured, and follows standard Go context-cancel patterns. No race conditions, no goroutine leaks, no impact on non-queue callers. Build passes. VM test confirms the fix works (1005ms vs 8-10s). The fix is ready to ship.