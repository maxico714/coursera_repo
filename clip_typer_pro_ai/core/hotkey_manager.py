"""
Hotkey Manager for ClipTyper Pro + AI Assistant
Implements global hotkey system using keyboard library to fix original issues.
"""
import keyboard
import threading
import time
from typing import Dict, Callable, List, Optional, Tuple
from utils.logger import get_logger


class HotkeyManager:
    """
    Global hotkey manager using keyboard library for reliable hotkey detection.
    Fixes original issues with pynput hotkey detection.
    """
    
    def __init__(self, settings_manager, event_dispatcher, clipboard_manager, 
                 typing_engine, ai_processor, telegram_bridge):
        self.settings_manager = settings_manager
        self.event_dispatcher = event_dispatcher
        self.clipboard_manager = clipboard_manager
        self.typing_engine = typing_engine
        self.ai_processor = ai_processor
        self.telegram_bridge = telegram_bridge
        self.logger = get_logger('hotkey_manager')
        
        # Registered hotkeys and their callbacks
        self.hotkeys: Dict[str, Callable] = {}
        self.active_hotkeys: List[str] = []
        
        # Default hotkeys
        self.default_hotkeys = {
            'typing_trigger': 'ctrl+alt+insert',  # Changed from Ctrl+Shift+V to fix original issue
            'ai_process_clipboard': 'ctrl+alt+a',
            'paste_clipboard': 'ctrl+alt+v',
            'toggle_monitoring': 'ctrl+alt+m',
            'clear_history': 'ctrl+alt+c',
            'show_history': 'ctrl+alt+h',
            'interrupt_typing': 'backspace, esc'  # Special case for interruption
        }
        
        # Load configured hotkeys
        self.configured_hotkeys = self._load_configured_hotkeys()
        
        # Validate and register hotkeys
        self._validate_and_register_hotkeys()
        
        self.logger.info("Hotkey manager initialized with keyboard library")
    
    def _load_configured_hotkeys(self) -> Dict[str, str]:
        """Load configured hotkeys from settings."""
        configured = {}
        
        for action, default_hotkey in self.default_hotkeys.items():
            if action == 'interrupt_typing':
                # Special case - this is handled by typing engine
                continue
            hotkey = self.settings_manager.get(f'hotkeys.{action}', default_hotkey)
            configured[action] = hotkey
        
        return configured
    
    def _validate_and_register_hotkeys(self):
        """Validate and register all configured hotkeys."""
        for action, hotkey in self.configured_hotkeys.items():
            try:
                # Register the hotkey
                if self._register_single_hotkey(hotkey, action):
                    self.logger.info(f"Registered hotkey '{hotkey}' for action '{action}'")
                else:
                    self.logger.warning(f"Failed to register hotkey '{hotkey}' for action '{action}'")
            except Exception as e:
                self.logger.error(f"Error registering hotkey '{hotkey}' for action '{action}': {str(e)}")
    
    def _register_single_hotkey(self, hotkey: str, action: str) -> bool:
        """Register a single hotkey with its callback."""
        try:
            # Define the callback based on action
            callback = self._get_callback_for_action(action)
            
            if callback:
                # Unregister if already registered
                if hotkey in self.active_hotkeys:
                    keyboard.unregister_hotkey(hotkey)
                
                # Register the hotkey
                keyboard.add_hotkey(hotkey, callback, suppress=True)
                self.hotkeys[hotkey] = callback
                self.active_hotkeys.append(hotkey)
                
                return True
            else:
                self.logger.warning(f"No callback found for action: {action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering hotkey '{hotkey}': {str(e)}")
            return False
    
    def _get_callback_for_action(self, action: str) -> Optional[Callable]:
        """Get the callback function for a specific action."""
        callbacks = {
            'typing_trigger': self._handle_typing_trigger,
            'ai_process_clipboard': self._handle_ai_process_clipboard,
            'paste_clipboard': self._handle_paste_clipboard,
            'toggle_monitoring': self._handle_toggle_monitoring,
            'clear_history': self._handle_clear_history,
            'show_history': self._handle_show_history,
        }
        
        return callbacks.get(action)
    
    def _handle_typing_trigger(self):
        """Handle typing trigger hotkey - types current clipboard content."""
        try:
            current_clipboard = keyboard.paste()  # Using keyboard.paste instead of pyperclip
            if current_clipboard:
                self.typing_engine.type_text(current_clipboard)
                self.logger.info("Triggered typing of clipboard content")
                self.event_dispatcher.dispatch('typing_triggered_by_hotkey', {
                    'content_length': len(current_clipboard)
                })
            else:
                self.logger.warning("Clipboard is empty, nothing to type")
        except Exception as e:
            self.logger.error(f"Error in typing trigger: {str(e)}", exc_info=True)
    
    def _handle_ai_process_clipboard(self):
        """Handle AI processing of clipboard content."""
        try:
            current_clipboard = keyboard.paste()
            if current_clipboard:
                # Process with AI in a separate thread to avoid blocking
                thread = threading.Thread(
                    target=self._process_with_ai_async,
                    args=(current_clipboard,),
                    daemon=True
                )
                thread.start()
                
                self.logger.info("Triggered AI processing of clipboard content")
                self.event_dispatcher.dispatch('ai_processing_triggered_by_hotkey', {
                    'content_length': len(current_clipboard)
                })
            else:
                self.logger.warning("Clipboard is empty, nothing to process with AI")
        except Exception as e:
            self.logger.error(f"Error in AI processing trigger: {str(e)}", exc_info=True)
    
    def _handle_paste_clipboard(self):
        """Handle pasting clipboard content using typing engine."""
        try:
            self.clipboard_manager.paste_from_clipboard()
            self.logger.info("Triggered paste from clipboard")
        except Exception as e:
            self.logger.error(f"Error in paste clipboard: {str(e)}", exc_info=True)
    
    def _handle_toggle_monitoring(self):
        """Handle toggling clipboard monitoring."""
        try:
            if self.clipboard_manager.monitoring:
                self.clipboard_manager.stop_monitoring()
                self.logger.info("Stopped clipboard monitoring")
                self.event_dispatcher.dispatch('clipboard_monitoring_toggled', {
                    'enabled': False
                })
            else:
                self.clipboard_manager.start_monitoring()
                self.logger.info("Started clipboard monitoring")
                self.event_dispatcher.dispatch('clipboard_monitoring_toggled', {
                    'enabled': True
                })
        except Exception as e:
            self.logger.error(f"Error in toggle monitoring: {str(e)}", exc_info=True)
    
    def _handle_clear_history(self):
        """Handle clearing clipboard history."""
        try:
            self.clipboard_manager.clear_history()
            self.logger.info("Cleared clipboard history via hotkey")
        except Exception as e:
            self.logger.error(f"Error in clear history: {str(e)}", exc_info=True)
    
    def _handle_show_history(self):
        """Handle showing clipboard history."""
        try:
            history = self.clipboard_manager.get_history(limit=10)  # Show last 10 items
            self.logger.info(f"Showing clipboard history ({len(history)} items)")
            
            # Dispatch event to potentially show history in UI
            self.event_dispatcher.dispatch('show_clipboard_history_requested', {
                'history_count': len(history)
            })
        except Exception as e:
            self.logger.error(f"Error in show history: {str(e)}", exc_info=True)
    
    def _process_with_ai_async(self, text: str):
        """Process text with AI asynchronously."""
        try:
            response = self.ai_processor.process_with_ai(text)
            if response.success and response.content:
                # Optionally type the response
                should_type_response = self.settings_manager.get('ai.type_response_after_processing', False)
                if should_type_response:
                    self.typing_engine.type_text(response.content)
        except Exception as e:
            self.logger.error(f"Error processing with AI: {str(e)}", exc_info=True)
    
    def register_hotkey(self, hotkey: str, callback: Callable, action_name: str = "") -> bool:
        """
        Register a custom hotkey with callback.
        
        Args:
            hotkey: The hotkey combination (e.g., 'ctrl+shift+t')
            callback: The function to call when hotkey is pressed
            action_name: Name for the action (for internal tracking)
            
        Returns:
            bool: True if registration was successful
        """
        try:
            # Validate the hotkey format
            if not self._is_valid_hotkey_format(hotkey):
                self.logger.error(f"Invalid hotkey format: {hotkey}")
                return False
            
            # Check for conflicts with existing hotkeys
            if self._is_hotkey_conflicting(hotkey):
                self.logger.warning(f"Hotkey '{hotkey}' conflicts with existing hotkey")
                return False
            
            # Register the hotkey
            keyboard.add_hotkey(hotkey, callback, suppress=True)
            self.hotkeys[hotkey] = callback
            self.active_hotkeys.append(hotkey)
            
            self.logger.info(f"Registered custom hotkey: {hotkey}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering custom hotkey '{hotkey}': {str(e)}")
            return False
    
    def unregister_hotkey(self, hotkey: str) -> bool:
        """
        Unregister a hotkey.
        
        Args:
            hotkey: The hotkey to unregister
            
        Returns:
            bool: True if unregistration was successful
        """
        try:
            if hotkey in self.active_hotkeys:
                keyboard.unregister_hotkey(hotkey)
                self.active_hotkeys.remove(hotkey)
                if hotkey in self.hotkeys:
                    del self.hotkeys[hotkey]
                
                self.logger.info(f"Unregistered hotkey: {hotkey}")
                return True
            else:
                self.logger.warning(f"Hotkey not registered: {hotkey}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error unregistering hotkey '{hotkey}': {str(e)}")
            return False
    
    def register_hotkeys(self):
        """Register all configured hotkeys."""
        self._validate_and_register_hotkeys()
        self.logger.info("All configured hotkeys registered")
    
    def unregister_hotkeys(self):
        """Unregister all active hotkeys."""
        for hotkey in self.active_hotkeys[:]:  # Copy the list to iterate safely
            try:
                keyboard.unregister_hotkey(hotkey)
            except Exception:
                pass  # Ignore errors when unregistering
        
        self.hotkeys.clear()
        self.active_hotkeys.clear()
        self.logger.info("All hotkeys unregistered")
    
    def _is_valid_hotkey_format(self, hotkey: str) -> bool:
        """Validate hotkey format."""
        # Basic validation - check if it's not empty and contains allowed modifiers
        if not hotkey.strip():
            return False
        
        # Split by '+' to check individual keys
        parts = hotkey.lower().split('+')
        allowed_modifiers = {'ctrl', 'alt', 'shift', 'win'}
        
        # Check if all parts are valid
        for part in parts:
            part = part.strip()
            if part not in allowed_modifiers and len(part) != 1 and part not in ['backspace', 'tab', 'enter', 'esc', 'space', 'delete', 'insert', 'home', 'end', 'pageup', 'pagedown']:
                # Check if it's a function key (f1-f24)
                if not (part.startswith('f') and part[1:].isdigit() and 1 <= int(part[1:]) <= 24):
                    return False
        
        return True
    
    def _is_hotkey_conflicting(self, hotkey: str) -> bool:
        """Check if hotkey conflicts with existing ones."""
        return hotkey in self.active_hotkeys
    
    def get_registered_hotkeys(self) -> Dict[str, str]:
        """Get all registered hotkeys with their actions."""
        hotkey_actions = {}
        
        # Map hotkeys to actions
        for action, hotkey in self.configured_hotkeys.items():
            hotkey_actions[hotkey] = action
        
        # Add any custom hotkeys
        for hotkey, callback in self.hotkeys.items():
            if hotkey not in hotkey_actions:
                hotkey_actions[hotkey] = "custom"
        
        return hotkey_actions
    
    def update_hotkey(self, action: str, new_hotkey: str) -> bool:
        """
        Update a specific hotkey for an action.
        
        Args:
            action: The action name (e.g., 'typing_trigger')
            new_hotkey: The new hotkey combination
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Validate the new hotkey
            if not self._is_valid_hotkey_format(new_hotkey):
                self.logger.error(f"Invalid hotkey format: {new_hotkey}")
                return False
            
            # Check for conflicts
            if self._is_hotkey_conflicting(new_hotkey):
                self.logger.warning(f"Hotkey '{new_hotkey}' conflicts with existing hotkey")
                return False
            
            # Get the current hotkey for this action
            current_hotkey = self.configured_hotkeys.get(action)
            if current_hotkey:
                # Unregister the old hotkey
                self.unregister_hotkey(current_hotkey)
            
            # Register the new hotkey
            callback = self._get_callback_for_action(action)
            if not callback:
                self.logger.error(f"No callback found for action: {action}")
                return False
            
            if self.register_hotkey(new_hotkey, callback, action):
                # Update configuration
                self.configured_hotkeys[action] = new_hotkey
                self.settings_manager.set(f'hotkeys.{action}', new_hotkey)
                
                self.logger.info(f"Updated hotkey for '{action}' to '{new_hotkey}'")
                return True
            else:
                # If registration failed, restore the old hotkey if it existed
                if current_hotkey:
                    self._register_single_hotkey(current_hotkey, action)
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating hotkey for '{action}': {str(e)}", exc_info=True)
            return False
    
    def reset_to_defaults(self):
        """Reset all hotkeys to default values."""
        self.unregister_hotkeys()
        
        # Reset configured hotkeys to defaults
        self.configured_hotkeys = self._load_configured_hotkeys().copy()
        
        # Restore defaults
        for action, default_hotkey in self.default_hotkeys.items():
            if action != 'interrupt_typing':  # Skip special case
                self.configured_hotkeys[action] = default_hotkey
                self.settings_manager.set(f'hotkeys.{action}', default_hotkey)
        
        # Re-register hotkeys
        self.register_hotkeys()
        
        self.logger.info("Hotkeys reset to defaults")
    
    def test_hotkey(self, hotkey: str) -> bool:
        """
        Test if a hotkey can be registered (useful for validation).
        
        Args:
            hotkey: The hotkey to test
            
        Returns:
            bool: True if hotkey can be registered
        """
        try:
            # Try to register a dummy callback
            def dummy_callback():
                pass
            
            keyboard.add_hotkey(hotkey, dummy_callback, suppress=True)
            
            # Immediately unregister
            keyboard.unregister_hotkey(hotkey)
            
            return True
        except Exception:
            return False
    
    def get_hotkey_for_action(self, action: str) -> Optional[str]:
        """Get the hotkey assigned to a specific action."""
        return self.configured_hotkeys.get(action)