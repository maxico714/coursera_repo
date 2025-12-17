"""
Advanced Typing Engine for ClipTyper Pro + AI Assistant
Implements human-like typing with interruption support, multiple speeds, and smart features.
"""
import time
import threading
import queue
import keyboard
from enum import Enum
from typing import Optional, Callable
import pyperclip
from utils.logger import get_logger


class TypingSpeed(Enum):
    """Enumeration for different typing speeds."""
    FAST_HUMAN = 0.05  # 50ms delay between keystrokes
    VERY_FAST = 0.02   # 20ms delay between keystrokes  
    MACHINE = 0.001    # 1ms delay between keystrokes (fastest practical)


class TypingEngine:
    """
    Advanced typing engine with interruption support, batch processing, and smart features.
    Uses keyboard library for global hotkey detection to fix original issues.
    """
    
    def __init__(self, settings_manager, event_dispatcher):
        self.settings_manager = settings_manager
        self.event_dispatcher = event_dispatcher
        self.logger = get_logger('typing_engine')
        
        # Typing state
        self.is_typing = False
        self.typing_thread = None
        self.interrupt_event = threading.Event()
        self.current_text = ""
        
        # Typing configuration
        self.default_speed = TypingSpeed.FAST_HUMAN.value
        self.batch_size = 10  # Characters processed in each batch
        
        # Interrupt keys (Backspace and Esc to stop typing)
        self.interrupt_keys = {'backspace', 'esc'}
        
        # Initialize keyboard listener for interruption
        self.setup_interrupt_listener()
        
        self.logger.info("Typing engine initialized")
    
    def setup_interrupt_listener(self):
        """Set up keyboard listener for interruption keys."""
        def on_key_release(key):
            try:
                if self.is_typing:
                    # Check for interruption keys
                    key_name = str(key).lower().replace("'", "")
                    if key_name in self.interrupt_keys:
                        self.interrupt_typing()
            except Exception as e:
                self.logger.error(f"Error in interrupt listener: {str(e)}")
        
        # Start the keyboard listener
        keyboard.on_release(on_key_release)
    
    def type_text(self, text: str, speed: Optional[float] = None) -> bool:
        """
        Type the given text with specified speed.
        
        Args:
            text: Text to type
            speed: Typing speed in seconds between keystrokes
            
        Returns:
            bool: True if typing completed successfully, False if interrupted
        """
        if not text:
            return True
        
        if self.is_typing:
            self.logger.warning("Typing already in progress, skipping request")
            return False
        
        # Set typing speed
        typing_speed = speed if speed is not None else self.default_speed
        
        # Prepare typing state
        self.current_text = text
        self.is_typing = True
        self.interrupt_event.clear()
        
        # Create typing thread
        self.typing_thread = threading.Thread(
            target=self._perform_typing,
            args=(text, typing_speed),
            daemon=True
        )
        self.typing_thread.start()
        
        self.logger.info(f"Started typing {len(text)} characters")
        self.event_dispatcher.dispatch('typing_started', {
            'text_length': len(text),
            'speed': typing_speed
        })
        
        return True
    
    def _perform_typing(self, text: str, speed: float):
        """Internal method to perform the actual typing."""
        try:
            # Process text in batches for better responsiveness
            for i in range(0, len(text), self.batch_size):
                if self.interrupt_event.is_set():
                    break
                
                batch = text[i:i + self.batch_size]
                
                # Type each character in the batch
                for char in batch:
                    if self.interrupt_event.is_set():
                        break
                    
                    # Handle special characters and modifiers
                    self._type_character(char)
                    
                    # Sleep between characters based on speed
                    if speed > 0:
                        time.sleep(speed)
                
                # Small pause between batches to allow interruption
                time.sleep(0.01)
            
            # Notify completion
            if not self.interrupt_event.is_set():
                self.logger.info("Typing completed successfully")
                self.event_dispatcher.dispatch('typing_completed', {
                    'text_length': len(text),
                    'interrupted': False
                })
            else:
                self.logger.info("Typing was interrupted")
                self.event_dispatcher.dispatch('typing_completed', {
                    'text_length': len(text),
                    'interrupted': True
                })
        
        except Exception as e:
            self.logger.error(f"Error during typing: {str(e)}", exc_info=True)
            self.event_dispatcher.dispatch('typing_error', {
                'error': str(e)
            })
        finally:
            self.is_typing = False
            self.current_text = ""
    
    def _type_character(self, char: str):
        """Type a single character using keyboard library."""
        try:
            # Handle special characters
            if char == '\n':
                keyboard.press_and_release('enter')
            elif char == '\t':
                keyboard.press_and_release('tab')
            elif char == '\r':
                keyboard.press_and_release('enter')
            else:
                # For regular characters, just type them
                keyboard.write(char)
        except Exception as e:
            self.logger.error(f"Error typing character '{char}': {str(e)}")
    
    def interrupt_typing(self):
        """Interrupt ongoing typing operation."""
        if self.is_typing:
            self.interrupt_event.set()
            self.logger.info("Typing interrupted by user")
            self.event_dispatcher.dispatch('typing_interrupted', {})
    
    def get_current_status(self) -> dict:
        """Get current typing status."""
        return {
            'is_typing': self.is_typing,
            'current_text_length': len(self.current_text),
            'interrupted': self.interrupt_event.is_set() if self.is_typing else False
        }
    
    def set_default_speed(self, speed: TypingSpeed):
        """Set the default typing speed."""
        self.default_speed = speed.value
        self.logger.info(f"Default typing speed set to {speed.name}")
    
    def set_batch_size(self, size: int):
        """Set the batch size for processing characters."""
        if size > 0:
            self.batch_size = size
            self.logger.info(f"Batch size set to {size}")
    
    def stop_all_typing(self):
        """Stop all ongoing typing operations."""
        if self.is_typing:
            self.interrupt_typing()
            if self.typing_thread and self.typing_thread.is_alive():
                self.typing_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish