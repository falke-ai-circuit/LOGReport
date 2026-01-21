"""
Event Bus - Centralized event communication system.

This module provides a simple event bus pattern for decoupled
communication between application components.

Usage:
    from commander.events import EventBus, EventType, Event
    
    bus = EventBus()
    bus.subscribe(EventType.COMMAND_COMPLETED, handler)
    bus.publish(EventType.COMMAND_COMPLETED, {"result": "success"})
"""

import logging
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class EventType(Enum):
    """Types of events that can be published on the event bus."""
    # Command events
    COMMAND_STARTED = "command_started"
    COMMAND_COMPLETED = "command_completed"
    COMMAND_FAILED = "command_failed"
    COMMAND_QUEUED = "command_queued"
    
    # Progress events
    PROGRESS_UPDATED = "progress_updated"
    PROGRESS_STARTED = "progress_started"
    PROGRESS_COMPLETED = "progress_completed"
    
    # State events
    STATE_CHANGED = "state_changed"
    
    # Token events
    TOKEN_PROCESSING_STARTED = "token_processing_started"
    TOKEN_PROCESSING_COMPLETED = "token_processing_completed"
    TOKEN_PROCESSING_FAILED = "token_processing_failed"
    
    # Node events
    NODE_SELECTED = "node_selected"
    NODE_UPDATED = "node_updated"
    NODE_ADDED = "node_added"
    NODE_REMOVED = "node_removed"
    
    # Connection events
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_CLOSED = "connection_closed"
    CONNECTION_FAILED = "connection_failed"
    
    # UI events
    STATUS_MESSAGE = "status_message"
    ERROR_MESSAGE = "error_message"
    LOG_ENTRY = "log_entry"


@dataclass
class Event:
    """
    Represents an event published on the event bus.
    
    Attributes:
        event_type: Type of the event
        data: Event payload data
        timestamp: When the event occurred
        source: Optional source identifier
    """
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Event({self.event_type.value}, source={self.source})"


EventHandler = Callable[[Event], None]


class EventBus:
    """
    Centralized event bus for application-wide event communication.
    
    Provides a publish-subscribe pattern for decoupled communication
    between application components.
    
    Thread Safety:
        This implementation is not thread-safe. For Qt applications,
        use QtEventBus which integrates with Qt's signal/slot mechanism.
    
    Example:
        >>> bus = EventBus()
        >>> def on_command_completed(event: Event):
        ...     print(f"Command completed: {event.data}")
        >>> bus.subscribe(EventType.COMMAND_COMPLETED, on_command_completed)
        >>> bus.publish(EventType.COMMAND_COMPLETED, {"result": "success"})
    """
    
    _instance: Optional['EventBus'] = None
    
    def __new__(cls) -> 'EventBus':
        """Singleton pattern - returns the same instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the event bus."""
        if self._initialized:
            return
        
        self._subscribers: Dict[EventType, List[EventHandler]] = {}
        self._logger = logging.getLogger(__name__)
        self._initialized = True
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            self._logger.debug(f"Subscribed handler to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                self._logger.debug(f"Unsubscribed handler from {event_type.value}")
            except ValueError:
                pass  # Handler not found
    
    def publish(self, event_type: EventType, data: Optional[Dict[str, Any]] = None,
               source: Optional[str] = None) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event to publish
            data: Event payload data
            source: Optional source identifier
        """
        event = Event(
            event_type=event_type,
            data=data or {},
            source=source
        )
        
        self._logger.debug(f"Publishing event: {event}")
        
        if event_type not in self._subscribers:
            return
        
        for handler in self._subscribers[event_type]:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"Error in event handler for {event_type.value}: {e}")
    
    def publish_event(self, event: Event) -> None:
        """
        Publish a pre-constructed event.
        
        Args:
            event: Event object to publish
        """
        self._logger.debug(f"Publishing event: {event}")
        
        if event.event_type not in self._subscribers:
            return
        
        for handler in self._subscribers[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"Error in event handler for {event.event_type.value}: {e}")
    
    def clear(self) -> None:
        """Clear all subscriptions."""
        self._subscribers.clear()
        self._logger.debug("Cleared all event subscriptions")
    
    def get_subscriber_count(self, event_type: EventType) -> int:
        """
        Get the number of subscribers for an event type.
        
        Args:
            event_type: Type of event to check
            
        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns:
        The singleton EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
