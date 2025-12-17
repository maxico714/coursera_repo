"""
Event Dispatcher for ClipTyper Pro + AI Assistant
Implements observer pattern for event-driven communication between modules.
"""
import threading
from typing import Dict, List, Callable, Any, Optional
from utils.logger import get_logger


class EventDispatcher:
    """
    Central event bus implementing observer pattern for communication between modules.
    Provides thread-safe event dispatching and listener management.
    """
    
    def __init__(self):
        self.logger = get_logger('event_dispatcher')
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._event_queue = []  # For potential event buffering
        self._max_queue_size = 1000
        
        self.logger.info("Event dispatcher initialized")
    
    def add_listener(self, event_type: str, callback: Callable):
        """
        Add a listener for a specific event type.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            
            if callback not in self._listeners[event_type]:
                self._listeners[event_type].append(callback)
                self.logger.debug(f"Added listener for event '{event_type}'")
    
    def remove_listener(self, event_type: str, callback: Callable) -> bool:
        """
        Remove a listener for a specific event type.
        
        Args:
            event_type: Type of event
            callback: Function to remove from listeners
            
        Returns:
            bool: True if listener was removed
        """
        with self._lock:
            if event_type in self._listeners:
                if callback in self._listeners[event_type]:
                    self._listeners[event_type].remove(callback)
                    self.logger.debug(f"Removed listener for event '{event_type}'")
                    
                    # Clean up empty lists
                    if not self._listeners[event_type]:
                        del self._listeners[event_type]
                    
                    return True
            
            self.logger.warning(f"Attempted to remove non-existent listener for event '{event_type}'")
            return False
    
    def dispatch(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """
        Dispatch an event to all registered listeners.
        
        Args:
            event_type: Type of event to dispatch
            data: Optional data to pass to listeners
        """
        with self._lock:
            # Add to internal queue for potential buffering
            if len(self._event_queue) >= self._max_queue_size:
                self._event_queue.pop(0)  # Remove oldest event
            self._event_queue.append({
                'type': event_type,
                'data': data or {},
                'timestamp': threading.current_thread().ident  # Use thread ID as simple timestamp
            })
        
        # Notify listeners outside the lock to prevent deadlocks
        listeners_to_notify = []
        with self._lock:
            if event_type in self._listeners:
                listeners_to_notify = self._listeners[event_type][:]
        
        # Call all listeners for this event type
        for listener in listeners_to_notify:
            try:
                listener(event_type, data or {})
            except Exception as e:
                self.logger.error(f"Error in event listener for '{event_type}': {str(e)}", exc_info=True)
        
        self.logger.debug(f"Dispatched event '{event_type}' to {len(listeners_to_notify)} listeners")
    
    def dispatch_async(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """
        Dispatch an event asynchronously in a separate thread.
        
        Args:
            event_type: Type of event to dispatch
            data: Optional data to pass to listeners
        """
        thread = threading.Thread(
            target=self.dispatch,
            args=(event_type, data),
            daemon=True
        )
        thread.start()
    
    def get_listeners_for_event(self, event_type: str) -> List[Callable]:
        """
        Get all listeners registered for a specific event type.
        
        Args:
            event_type: Type of event
            
        Returns:
            List of registered listeners
        """
        with self._lock:
            return self._listeners.get(event_type, []).copy()
    
    def get_all_events(self) -> List[str]:
        """
        Get all event types that have registered listeners.
        
        Returns:
            List of event type names
        """
        with self._lock:
            return list(self._listeners.keys())
    
    def get_event_stats(self) -> Dict[str, int]:
        """
        Get statistics about registered events and listeners.
        
        Returns:
            Dictionary with event statistics
        """
        with self._lock:
            return {
                'total_event_types': len(self._listeners),
                'total_listeners': sum(len(listeners) for listeners in self._listeners.values()),
                'event_types': {event_type: len(listeners) for event_type, listeners in self._listeners.items()}
            }
    
    def clear_listeners(self, event_type: Optional[str] = None):
        """
        Clear all listeners, or listeners for a specific event type.
        
        Args:
            event_type: Specific event type to clear, or None to clear all
        """
        with self._lock:
            if event_type:
                if event_type in self._listeners:
                    del self._listeners[event_type]
                    self.logger.info(f"Cleared listeners for event '{event_type}'")
            else:
                self._listeners.clear()
                self.logger.info("Cleared all event listeners")
    
    def has_listeners(self, event_type: str) -> bool:
        """
        Check if there are any listeners for a specific event type.
        
        Args:
            event_type: Type of event to check
            
        Returns:
            bool: True if there are listeners
        """
        with self._lock:
            return event_type in self._listeners and len(self._listeners[event_type]) > 0
    
    def shutdown(self):
        """Shutdown the event dispatcher and clean up resources."""
        with self._lock:
            self._listeners.clear()
            self._event_queue.clear()
        
        self.logger.info("Event dispatcher shut down")
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently dispatched events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        with self._lock:
            return self._event_queue[-limit:]


# Global event dispatcher instance (singleton pattern)
_global_dispatcher: Optional[EventDispatcher] = None
_dispatcher_lock = threading.Lock()


def get_global_dispatcher() -> EventDispatcher:
    """
    Get the global event dispatcher instance.
    
    Returns:
        Global EventDispatcher instance
    """
    global _global_dispatcher
    
    if _global_dispatcher is None:
        with _dispatcher_lock:
            if _global_dispatcher is None:
                _global_dispatcher = EventDispatcher()
    
    return _global_dispatcher