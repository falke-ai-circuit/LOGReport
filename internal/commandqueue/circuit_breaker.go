// Package commandqueue provides a circuit breaker for the command queue.
// It trips after 3 consecutive failures, blocks execution for 60s,
// then allows a single retry (HALF_OPEN). On success → CLOSED (reset).
// On failure → OPEN (reset timer).
package commandqueue

import (
	"sync"
	"time"
)

// CircuitBreakerState represents the state of the circuit breaker.
type CircuitBreakerState string

const (
	CBClosed   CircuitBreakerState = "closed"
	CBOpen     CircuitBreakerState = "open"
	CBHalfOpen CircuitBreakerState = "half_open"
)

// failureThreshold is the number of consecutive failures before tripping.
const failureThreshold = 3

// openTimeout is how long the breaker stays OPEN before transitioning to HALF_OPEN.
const openTimeout = 60 * time.Second

// CircuitBreaker prevents cascading failures by blocking command execution
// after repeated errors. Thread-safe.
type CircuitBreaker struct {
	mu           sync.Mutex
	state        CircuitBreakerState
	failureCount int
	openTime     time.Time
}

// NewCircuitBreaker creates a circuit breaker in CLOSED state.
func NewCircuitBreaker() *CircuitBreaker {
	return &CircuitBreaker{
		state: CBClosed,
	}
}

// AllowExecution returns true if commands may be attempted (CLOSED or HALF_OPEN).
// If OPEN and the timeout has elapsed, transitions to HALF_OPEN before returning true.
func (cb *CircuitBreaker) AllowExecution() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch cb.state {
	case CBClosed:
		return true
	case CBOpen:
		if time.Since(cb.openTime) > openTimeout {
			cb.state = CBHalfOpen
			return true
		}
		return false
	case CBHalfOpen:
		return true
	default:
		return true
	}
}

// RecordSuccess resets the failure count and transitions to CLOSED.
func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	cb.failureCount = 0
	cb.state = CBClosed
}

// RecordFailure increments the failure count. If CLOSED and threshold reached,
// trips to OPEN. If HALF_OPEN, immediately trips back to OPEN.
func (cb *CircuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.failureCount++

	if cb.state == CBHalfOpen {
		// Half-open retry failed — go back to OPEN
		cb.state = CBOpen
		cb.openTime = time.Now()
		return
	}

	if cb.state == CBClosed && cb.failureCount >= failureThreshold {
		cb.state = CBOpen
		cb.openTime = time.Now()
	}
}

// State returns the current circuit breaker state.
func (cb *CircuitBreaker) State() string {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return string(cb.state)
}

// Reset forces the breaker back to CLOSED with zero failures.
func (cb *CircuitBreaker) Reset() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	cb.failureCount = 0
	cb.state = CBClosed
}