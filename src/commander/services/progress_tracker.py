"""
Progress Tracker - Handles progress tracking and notifications

This module provides a dedicated class for tracking execution progress,
emitting Qt signals, and managing progress state.

Usage:
    from commander.services.progress_tracker import ProgressTracker
    
    tracker = ProgressTracker()
    tracker.progress_updated.connect(update_ui)
    tracker.start(total=100)
    tracker.update(current=25)
"""

import logging
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal

from ..interfaces import IProgressTracker


class ProgressTracker(QObject):
    """
    Tracks and emits progress updates for batch operations.
    
    This class provides a clean interface for progress tracking,
    separating progress concerns from execution logic.
    
    Signals:
        progress_updated: Emitted when progress changes (current, total)
        progress_started: Emitted when tracking starts (total)
        progress_completed: Emitted when tracking completes
        progress_cancelled: Emitted when tracking is cancelled
        message_updated: Emitted when a progress message changes
    
    Example:
        >>> tracker = ProgressTracker()
        >>> tracker.progress_updated.connect(lambda c, t: print(f"{c}/{t}"))
        >>> tracker.start(10)
        >>> tracker.update(5)  # Prints: 5/10
    """
    
    # Signals for UI updates
    progress_updated = pyqtSignal(int, int)  # current, total
    progress_started = pyqtSignal(int)  # total
    progress_completed = pyqtSignal()
    progress_cancelled = pyqtSignal()
    message_updated = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Initialize the progress tracker.
        
        Args:
            parent: Optional Qt parent object
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        self._total: int = 0
        self._current: int = 0
        self._is_tracking: bool = False
        self._message: str = ""
    
    @property
    def total(self) -> int:
        """Get the total number of items to process."""
        return self._total
    
    @property
    def current(self) -> int:
        """Get the current progress count."""
        return self._current
    
    @property
    def percentage(self) -> float:
        """Get progress as a percentage (0-100)."""
        if self._total == 0:
            return 0.0
        return (self._current / self._total) * 100.0
    
    @property
    def is_tracking(self) -> bool:
        """Check if progress tracking is active."""
        return self._is_tracking
    
    @property
    def remaining(self) -> int:
        """Get the number of remaining items."""
        return max(0, self._total - self._current)
    
    @property
    def message(self) -> str:
        """Get the current progress message."""
        return self._message
    
    def start(self, total: int) -> None:
        """
        Start tracking progress for a batch operation.
        
        Args:
            total: Total number of items to process
        
        Raises:
            ValueError: If total is negative
        """
        if total < 0:
            raise ValueError("Total must be non-negative")
        
        self._total = total
        self._current = 0
        self._is_tracking = True
        self._message = ""
        
        self.logger.debug(f"Progress tracking started: 0/{total}")
        self.progress_started.emit(total)
        self.progress_updated.emit(0, total)
    
    def update(self, current: int, message: str = "") -> None:
        """
        Update the current progress.
        
        Args:
            current: Current progress count
            message: Optional progress message
        
        Raises:
            ValueError: If current is negative or exceeds total
        """
        if not self._is_tracking:
            self.logger.warning("Update called but not tracking")
            return
        
        if current < 0:
            raise ValueError("Current must be non-negative")
        
        # Clamp to total
        current = min(current, self._total)
        
        self._current = current
        
        if message:
            self._message = message
            self.message_updated.emit(message)
        
        self.logger.debug(f"Progress updated: {current}/{self._total}")
        self.progress_updated.emit(current, self._total)
    
    def increment(self, amount: int = 1, message: str = "") -> None:
        """
        Increment progress by a specified amount.
        
        Args:
            amount: Amount to increment by
            message: Optional progress message
        """
        new_current = min(self._current + amount, self._total)
        self.update(new_current, message)
    
    def set_message(self, message: str) -> None:
        """
        Set the progress message without changing count.
        
        Args:
            message: New progress message
        """
        self._message = message
        self.message_updated.emit(message)
    
    def complete(self) -> None:
        """
        Mark progress tracking as complete.
        
        Sets current to total and emits completion signal.
        """
        if not self._is_tracking:
            return
        
        self._current = self._total
        self._is_tracking = False
        
        self.logger.debug("Progress tracking completed")
        self.progress_updated.emit(self._total, self._total)
        self.progress_completed.emit()
    
    def cancel(self) -> None:
        """
        Cancel progress tracking.
        
        Stops tracking and emits cancellation signal.
        """
        if not self._is_tracking:
            return
        
        self._is_tracking = False
        
        self.logger.debug("Progress tracking cancelled")
        self.progress_cancelled.emit()
    
    def reset(self) -> None:
        """
        Reset progress tracker to initial state.
        
        Clears all progress data without emitting signals.
        """
        self._total = 0
        self._current = 0
        self._is_tracking = False
        self._message = ""
        self.logger.debug("Progress tracker reset")
    
    def __repr__(self) -> str:
        """String representation of tracker state."""
        return (
            f"ProgressTracker("
            f"current={self._current}, "
            f"total={self._total}, "
            f"tracking={self._is_tracking})"
        )
