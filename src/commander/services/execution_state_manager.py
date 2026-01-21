"""
Execution State Manager - Handles execution state transitions

This module provides a dedicated class for managing execution state,
with proper state transition validation and Qt signal notifications.

Usage:
    from commander.services.execution_state_manager import ExecutionStateManager
    
    manager = ExecutionStateManager()
    manager.state_changed.connect(update_ui)
    manager.transition_to(ExecutionState.RUNNING)
"""

import logging
from typing import Optional, Set, Dict
from PyQt5.QtCore import QObject, pyqtSignal

from ..interfaces import IStateManager, ExecutionState


class ExecutionStateManager(QObject):
    """
    Manages execution state with validated transitions.
    
    This class provides a clean interface for state management,
    ensuring valid state transitions and proper notification.
    
    Valid state transitions:
        IDLE -> RUNNING
        RUNNING -> PAUSED, CANCELLED, COMPLETED, FAILED
        PAUSED -> RUNNING, CANCELLED
        CANCELLED -> IDLE
        COMPLETED -> IDLE
        FAILED -> IDLE
    
    Signals:
        state_changed: Emitted when state changes (old_state, new_state)
        error_occurred: Emitted when invalid transition attempted
    
    Example:
        >>> manager = ExecutionStateManager()
        >>> manager.state_changed.connect(lambda o, n: print(f"{o} -> {n}"))
        >>> manager.transition_to(ExecutionState.RUNNING)  # IDLE -> RUNNING
    """
    
    # Signals for state change notifications
    state_changed = pyqtSignal(object, object)  # old_state, new_state
    error_occurred = pyqtSignal(str)  # error message
    
    # Valid state transitions (from_state -> allowed_to_states)
    VALID_TRANSITIONS: Dict[ExecutionState, Set[ExecutionState]] = {
        ExecutionState.IDLE: {ExecutionState.RUNNING},
        ExecutionState.RUNNING: {
            ExecutionState.PAUSED,
            ExecutionState.CANCELLED,
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
        },
        ExecutionState.PAUSED: {
            ExecutionState.RUNNING,
            ExecutionState.CANCELLED,
        },
        ExecutionState.CANCELLED: {ExecutionState.IDLE},
        ExecutionState.COMPLETED: {ExecutionState.IDLE},
        ExecutionState.FAILED: {ExecutionState.IDLE},
    }
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Initialize the state manager.
        
        Args:
            parent: Optional Qt parent object
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        self._state: ExecutionState = ExecutionState.IDLE
        self._previous_state: Optional[ExecutionState] = None
        self._state_history: list[ExecutionState] = [ExecutionState.IDLE]
    
    @property
    def current_state(self) -> ExecutionState:
        """Get the current execution state."""
        return self._state
    
    @property
    def previous_state(self) -> Optional[ExecutionState]:
        """Get the previous execution state."""
        return self._previous_state
    
    @property
    def is_idle(self) -> bool:
        """Check if currently idle."""
        return self._state == ExecutionState.IDLE
    
    @property
    def is_running(self) -> bool:
        """Check if currently running."""
        return self._state == ExecutionState.RUNNING
    
    @property
    def is_paused(self) -> bool:
        """Check if currently paused."""
        return self._state == ExecutionState.PAUSED
    
    @property
    def is_active(self) -> bool:
        """Check if in an active state (running or paused)."""
        return self._state in {ExecutionState.RUNNING, ExecutionState.PAUSED}
    
    @property
    def is_terminal(self) -> bool:
        """Check if in a terminal state (completed, cancelled, failed)."""
        return self._state in {
            ExecutionState.COMPLETED,
            ExecutionState.CANCELLED,
            ExecutionState.FAILED,
        }
    
    def can_transition_to(self, state: ExecutionState) -> bool:
        """
        Check if transition to the specified state is valid.
        
        Args:
            state: Target state to check
        
        Returns:
            True if transition is valid
        """
        if self._state == state:
            return True  # Already in this state
        
        allowed = self.VALID_TRANSITIONS.get(self._state, set())
        return state in allowed
    
    def transition_to(self, state: ExecutionState) -> bool:
        """
        Attempt to transition to a new state.
        
        Args:
            state: Target state
        
        Returns:
            True if transition was successful
        """
        if self._state == state:
            self.logger.debug(f"Already in state: {state.value}")
            return True
        
        if not self.can_transition_to(state):
            error_msg = (
                f"Invalid state transition: {self._state.value} -> {state.value}"
            )
            self.logger.warning(error_msg)
            self.error_occurred.emit(error_msg)
            return False
        
        old_state = self._state
        self._previous_state = old_state
        self._state = state
        self._state_history.append(state)
        
        self.logger.debug(f"State transition: {old_state.value} -> {state.value}")
        self.state_changed.emit(old_state, state)
        
        return True
    
    def force_state(self, state: ExecutionState) -> None:
        """
        Force state to a specific value (bypasses validation).
        
        Use with caution - only for error recovery scenarios.
        
        Args:
            state: Target state
        """
        old_state = self._state
        self._previous_state = old_state
        self._state = state
        self._state_history.append(state)
        
        self.logger.warning(
            f"Forced state transition: {old_state.value} -> {state.value}"
        )
        self.state_changed.emit(old_state, state)
    
    def reset(self) -> None:
        """
        Reset state manager to initial state.
        
        Forces transition to IDLE regardless of current state.
        """
        old_state = self._state
        self._state = ExecutionState.IDLE
        self._previous_state = old_state
        self._state_history = [ExecutionState.IDLE]
        
        if old_state != ExecutionState.IDLE:
            self.logger.debug("State manager reset to IDLE")
            self.state_changed.emit(old_state, ExecutionState.IDLE)
    
    # Convenience methods for common transitions
    
    def start(self) -> bool:
        """Convenience method to start execution."""
        return self.transition_to(ExecutionState.RUNNING)
    
    def pause(self) -> bool:
        """Convenience method to pause execution."""
        return self.transition_to(ExecutionState.PAUSED)
    
    def resume(self) -> bool:
        """Convenience method to resume from pause."""
        if self._state == ExecutionState.PAUSED:
            return self.transition_to(ExecutionState.RUNNING)
        return False
    
    def cancel(self) -> bool:
        """Convenience method to cancel execution."""
        return self.transition_to(ExecutionState.CANCELLED)
    
    def complete(self) -> bool:
        """Convenience method to mark as completed."""
        return self.transition_to(ExecutionState.COMPLETED)
    
    def fail(self) -> bool:
        """Convenience method to mark as failed."""
        return self.transition_to(ExecutionState.FAILED)
    
    def acknowledge(self) -> bool:
        """
        Acknowledge terminal state and return to IDLE.
        
        Returns:
            True if successfully returned to IDLE
        """
        if self.is_terminal:
            return self.transition_to(ExecutionState.IDLE)
        return False
    
    def get_state_history(self) -> list[ExecutionState]:
        """
        Get the complete state transition history.
        
        Returns:
            List of states in order of transitions
        """
        return list(self._state_history)
    
    def __repr__(self) -> str:
        """String representation of manager state."""
        return (
            f"ExecutionStateManager("
            f"state={self._state.value}, "
            f"previous={self._previous_state.value if self._previous_state else 'None'})"
        )
