"""
Unit tests for the ProgressTracker and ExecutionStateManager.

Tests progress tracking, state transitions, and signal emissions.
"""

import os
import pytest

# Skip Qt tests if no display available
pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY') and not os.environ.get('QT_QPA_PLATFORM'),
    reason="No display available for Qt tests"
)

from commander.services.progress_tracker import ProgressTracker
from commander.services.execution_state_manager import ExecutionStateManager
from commander.interfaces import ExecutionState


class TestProgressTrackerBasic:
    """Basic tests for ProgressTracker class (no Qt signals)."""
    
    def test_initial_state(self):
        """Test initial tracker state."""
        tracker = ProgressTracker()
        assert tracker.total == 0
        assert tracker.current == 0
        assert tracker.percentage == 0.0
        assert tracker.is_tracking is False
    
    def test_start_tracking(self):
        """Test starting progress tracking."""
        tracker = ProgressTracker()
        tracker.start(100)
        
        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.is_tracking is True
    
    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker()
        tracker.start(100)
        tracker.update(50)
        
        assert tracker.current == 50
        assert tracker.percentage == 50.0
    
    def test_increment_progress(self):
        """Test incrementing progress."""
        tracker = ProgressTracker()
        tracker.start(10)
        
        tracker.increment(3)
        assert tracker.current == 3
        
        tracker.increment()  # Default increment of 1
        assert tracker.current == 4
    
    def test_remaining(self):
        """Test remaining count calculation."""
        tracker = ProgressTracker()
        tracker.start(100)
        tracker.update(30)
        
        assert tracker.remaining == 70
    
    def test_complete(self):
        """Test completing progress."""
        tracker = ProgressTracker()
        tracker.start(100)
        tracker.update(50)
        tracker.complete()
        
        assert tracker.current == tracker.total
        assert tracker.is_tracking is False
    
    def test_cancel(self):
        """Test cancelling progress."""
        tracker = ProgressTracker()
        tracker.start(100)
        tracker.cancel()
        
        assert tracker.is_tracking is False
    
    def test_reset(self):
        """Test resetting tracker."""
        tracker = ProgressTracker()
        tracker.start(100)
        tracker.update(50)
        tracker.reset()
        
        assert tracker.total == 0
        assert tracker.current == 0
        assert tracker.is_tracking is False
    
    def test_message_update(self):
        """Test updating progress message."""
        tracker = ProgressTracker()
        tracker.start(10)
        tracker.set_message("Processing...")
        
        assert tracker.message == "Processing..."
    
    def test_clamp_to_total(self):
        """Test that current is clamped to total."""
        tracker = ProgressTracker()
        tracker.start(10)
        tracker.update(20)  # Exceeds total
        
        assert tracker.current == 10  # Clamped to total
    
    def test_negative_total_raises(self):
        """Test that negative total raises ValueError."""
        tracker = ProgressTracker()
        with pytest.raises(ValueError):
            tracker.start(-1)
    
    def test_negative_current_raises(self):
        """Test that negative current raises ValueError."""
        tracker = ProgressTracker()
        tracker.start(10)
        with pytest.raises(ValueError):
            tracker.update(-1)


class TestExecutionStateManagerBasic:
    """Basic tests for ExecutionStateManager class (no Qt signals)."""
    
    def test_initial_state(self):
        """Test initial manager state."""
        manager = ExecutionStateManager()
        assert manager.current_state == ExecutionState.IDLE
        assert manager.is_idle is True
        assert manager.previous_state is None
    
    def test_valid_transition_idle_to_running(self):
        """Test valid transition from IDLE to RUNNING."""
        manager = ExecutionStateManager()
        result = manager.transition_to(ExecutionState.RUNNING)
        
        assert result is True
        assert manager.current_state == ExecutionState.RUNNING
        assert manager.is_running is True
    
    def test_valid_transition_running_to_paused(self):
        """Test valid transition from RUNNING to PAUSED."""
        manager = ExecutionStateManager()
        manager.start()
        
        result = manager.pause()
        
        assert result is True
        assert manager.current_state == ExecutionState.PAUSED
        assert manager.is_paused is True
    
    def test_valid_transition_paused_to_running(self):
        """Test valid transition from PAUSED to RUNNING (resume)."""
        manager = ExecutionStateManager()
        manager.start()
        manager.pause()
        
        result = manager.resume()
        
        assert result is True
        assert manager.current_state == ExecutionState.RUNNING
    
    def test_valid_transition_to_cancelled(self):
        """Test valid transition to CANCELLED."""
        manager = ExecutionStateManager()
        manager.start()
        
        result = manager.cancel()
        
        assert result is True
        assert manager.current_state == ExecutionState.CANCELLED
        assert manager.is_terminal is True
    
    def test_valid_transition_to_completed(self):
        """Test valid transition to COMPLETED."""
        manager = ExecutionStateManager()
        manager.start()
        
        result = manager.complete()
        
        assert result is True
        assert manager.current_state == ExecutionState.COMPLETED
        assert manager.is_terminal is True
    
    def test_valid_transition_to_failed(self):
        """Test valid transition to FAILED."""
        manager = ExecutionStateManager()
        manager.start()
        
        result = manager.fail()
        
        assert result is True
        assert manager.current_state == ExecutionState.FAILED
        assert manager.is_terminal is True
    
    def test_invalid_transition(self):
        """Test invalid transition is rejected."""
        manager = ExecutionStateManager()
        # Can't go from IDLE to PAUSED
        result = manager.transition_to(ExecutionState.PAUSED)
        
        assert result is False
        assert manager.current_state == ExecutionState.IDLE  # Unchanged
    
    def test_same_state_transition(self):
        """Test transition to same state succeeds."""
        manager = ExecutionStateManager()
        result = manager.transition_to(ExecutionState.IDLE)
        
        assert result is True
        assert manager.current_state == ExecutionState.IDLE
    
    def test_can_transition_to(self):
        """Test can_transition_to method."""
        manager = ExecutionStateManager()
        assert manager.can_transition_to(ExecutionState.RUNNING) is True
        assert manager.can_transition_to(ExecutionState.PAUSED) is False
        assert manager.can_transition_to(ExecutionState.IDLE) is True  # Same state
    
    def test_reset(self):
        """Test resetting manager."""
        manager = ExecutionStateManager()
        manager.start()
        manager.pause()
        manager.reset()
        
        assert manager.current_state == ExecutionState.IDLE
        assert manager.is_idle is True
    
    def test_acknowledge_terminal_state(self):
        """Test acknowledging terminal state."""
        manager = ExecutionStateManager()
        manager.start()
        manager.complete()
        
        result = manager.acknowledge()
        
        assert result is True
        assert manager.current_state == ExecutionState.IDLE
    
    def test_acknowledge_non_terminal_fails(self):
        """Test acknowledging non-terminal state fails."""
        manager = ExecutionStateManager()
        manager.start()
        
        result = manager.acknowledge()
        
        assert result is False
        assert manager.current_state == ExecutionState.RUNNING
    
    def test_is_active(self):
        """Test is_active property."""
        manager = ExecutionStateManager()
        assert manager.is_active is False
        
        manager.start()
        assert manager.is_active is True
        
        manager.pause()
        assert manager.is_active is True
        
        manager.cancel()
        assert manager.is_active is False
    
    def test_state_history(self):
        """Test state history tracking."""
        manager = ExecutionStateManager()
        manager.start()
        manager.pause()
        manager.resume()
        manager.complete()
        
        history = manager.get_state_history()
        
        assert history == [
            ExecutionState.IDLE,
            ExecutionState.RUNNING,
            ExecutionState.PAUSED,
            ExecutionState.RUNNING,
            ExecutionState.COMPLETED,
        ]
    
    def test_force_state(self):
        """Test forcing state (bypass validation)."""
        manager = ExecutionStateManager()
        # Force invalid transition
        manager.force_state(ExecutionState.PAUSED)
        
        assert manager.current_state == ExecutionState.PAUSED
    
    def test_previous_state_tracking(self):
        """Test previous state is tracked."""
        manager = ExecutionStateManager()
        manager.start()
        
        assert manager.previous_state == ExecutionState.IDLE
        
        manager.pause()
        
        assert manager.previous_state == ExecutionState.RUNNING
