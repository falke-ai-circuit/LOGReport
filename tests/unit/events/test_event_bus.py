"""
Tests for EventBus.
"""

import pytest
from src.commander.events import EventBus, EventType, Event, get_event_bus


class TestEventBus:
    """Test suite for EventBus."""
    
    @pytest.fixture
    def event_bus(self):
        """Create a fresh EventBus instance for each test."""
        EventBus.reset()
        return EventBus()
    
    def test_subscribe_and_publish(self, event_bus):
        """Should call handler when event is published."""
        received_events = []
        
        def handler(event: Event):
            received_events.append(event)
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler)
        event_bus.publish(EventType.COMMAND_COMPLETED, {"result": "success"})
        
        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.COMMAND_COMPLETED
        assert received_events[0].data["result"] == "success"
    
    def test_multiple_subscribers(self, event_bus):
        """Should call all subscribers for an event."""
        count = {"value": 0}
        
        def handler1(event: Event):
            count["value"] += 1
        
        def handler2(event: Event):
            count["value"] += 10
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler1)
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler2)
        event_bus.publish(EventType.COMMAND_COMPLETED)
        
        assert count["value"] == 11
    
    def test_unsubscribe(self, event_bus):
        """Should not call handler after unsubscribe."""
        count = {"value": 0}
        
        def handler(event: Event):
            count["value"] += 1
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler)
        event_bus.publish(EventType.COMMAND_COMPLETED)
        assert count["value"] == 1
        
        event_bus.unsubscribe(EventType.COMMAND_COMPLETED, handler)
        event_bus.publish(EventType.COMMAND_COMPLETED)
        assert count["value"] == 1  # Not incremented
    
    def test_publish_without_subscribers(self, event_bus):
        """Should not raise error when publishing to no subscribers."""
        event_bus.publish(EventType.COMMAND_COMPLETED, {"data": "test"})
        # No error raised
    
    def test_handler_error_isolation(self, event_bus):
        """Should continue calling handlers even if one raises."""
        count = {"value": 0}
        
        def bad_handler(event: Event):
            raise ValueError("Handler error")
        
        def good_handler(event: Event):
            count["value"] += 1
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, bad_handler)
        event_bus.subscribe(EventType.COMMAND_COMPLETED, good_handler)
        
        event_bus.publish(EventType.COMMAND_COMPLETED)
        
        assert count["value"] == 1  # good_handler was called
    
    def test_publish_event_object(self, event_bus):
        """Should accept pre-constructed Event objects."""
        received_events = []
        
        def handler(event: Event):
            received_events.append(event)
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler)
        
        event = Event(
            event_type=EventType.COMMAND_COMPLETED,
            data={"custom": "data"},
            source="test_source"
        )
        event_bus.publish_event(event)
        
        assert len(received_events) == 1
        assert received_events[0].source == "test_source"
    
    def test_clear_subscriptions(self, event_bus):
        """Should remove all subscriptions when cleared."""
        count = {"value": 0}
        
        def handler(event: Event):
            count["value"] += 1
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler)
        event_bus.subscribe(EventType.PROGRESS_UPDATED, handler)
        
        event_bus.clear()
        
        event_bus.publish(EventType.COMMAND_COMPLETED)
        event_bus.publish(EventType.PROGRESS_UPDATED)
        
        assert count["value"] == 0
    
    def test_get_subscriber_count(self, event_bus):
        """Should return correct subscriber count."""
        assert event_bus.get_subscriber_count(EventType.COMMAND_COMPLETED) == 0
        
        def handler(event: Event):
            pass
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler)
        assert event_bus.get_subscriber_count(EventType.COMMAND_COMPLETED) == 1
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, lambda e: None)
        assert event_bus.get_subscriber_count(EventType.COMMAND_COMPLETED) == 2
    
    def test_singleton_pattern(self):
        """EventBus should be a singleton."""
        EventBus.reset()
        bus1 = EventBus()
        bus2 = EventBus()
        
        assert bus1 is bus2
    
    def test_prevent_duplicate_subscription(self, event_bus):
        """Should not add duplicate handlers."""
        count = {"value": 0}
        
        def handler(event: Event):
            count["value"] += 1
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler)
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler)  # Duplicate
        
        event_bus.publish(EventType.COMMAND_COMPLETED)
        
        assert count["value"] == 1  # Handler called only once
    
    def test_event_timestamp(self, event_bus):
        """Event should have a timestamp."""
        received_events = []
        
        def handler(event: Event):
            received_events.append(event)
        
        event_bus.subscribe(EventType.COMMAND_COMPLETED, handler)
        event_bus.publish(EventType.COMMAND_COMPLETED)
        
        assert received_events[0].timestamp is not None


class TestEventTypes:
    """Test EventType enum."""
    
    def test_command_events_exist(self):
        """Command-related event types should exist."""
        assert EventType.COMMAND_STARTED
        assert EventType.COMMAND_COMPLETED
        assert EventType.COMMAND_FAILED
        assert EventType.COMMAND_QUEUED
    
    def test_progress_events_exist(self):
        """Progress-related event types should exist."""
        assert EventType.PROGRESS_UPDATED
        assert EventType.PROGRESS_STARTED
        assert EventType.PROGRESS_COMPLETED
    
    def test_node_events_exist(self):
        """Node-related event types should exist."""
        assert EventType.NODE_SELECTED
        assert EventType.NODE_UPDATED
        assert EventType.NODE_ADDED
        assert EventType.NODE_REMOVED


class TestEvent:
    """Test Event dataclass."""
    
    def test_event_creation(self):
        """Should create event with all attributes."""
        event = Event(
            event_type=EventType.COMMAND_COMPLETED,
            data={"key": "value"},
            source="test"
        )
        
        assert event.event_type == EventType.COMMAND_COMPLETED
        assert event.data["key"] == "value"
        assert event.source == "test"
        assert event.timestamp is not None
    
    def test_event_str(self):
        """Should have readable string representation."""
        event = Event(
            event_type=EventType.COMMAND_COMPLETED,
            source="test"
        )
        
        str_repr = str(event)
        assert "command_completed" in str_repr
        assert "test" in str_repr


class TestGetEventBus:
    """Test get_event_bus function."""
    
    def test_returns_singleton(self):
        """get_event_bus should return singleton instance."""
        EventBus.reset()
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        assert bus1 is bus2
