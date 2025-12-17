"""
System Tray UI for ClipTyper Pro + AI Assistant.
Implements the system tray icon with dynamic menu and status indicators.
"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import os
import sys
from pathlib import Path
from utils.logger import get_logger


class SystemTrayApp:
    """
    System tray application with dynamic menu and status indicators.
    Provides quick access to common functions and status information.
    """
    
    def __init__(self, settings_manager, event_dispatcher, clipboard_manager,
                 typing_engine, ai_processor, telegram_bridge, hotkey_manager,
                 snippet_manager, file_context_manager, security_manager):
        self.settings_manager = settings_manager
        self.event_dispatcher = event_dispatcher
        self.clipboard_manager = clipboard_manager
        self.typing_engine = typing_engine
        self.ai_processor = ai_processor
        self.telegram_bridge = telegram_bridge
        self.hotkey_manager = hotkey_manager
        self.snippet_manager = snippet_manager
        self.file_context_manager = file_context_manager
        self.security_manager = security_manager
        self.logger = get_logger('system_tray')
        
        # Application state
        self.icon = None
        self.menu = None
        self.is_running = False
        self.root = None  # For any UI dialogs
        
        # Status indicators
        self.typing_active = False
        self.monitoring_active = clipboard_manager.monitoring
        self.security_locked = not security_manager.is_session_active()
        
        # Register for events
        self._register_event_listeners()
        
        self.logger.info("System tray app initialized")
    
    def _register_event_listeners(self):
        """Register event listeners for status updates."""
        self.event_dispatcher.add_listener('typing_started', self._on_typing_started)
        self.event_dispatcher.add_listener('typing_completed', self._on_typing_completed)
        self.event_dispatcher.add_listener('clipboard_monitoring_started', self._on_monitoring_started)
        self.event_dispatcher.add_listener('clipboard_monitoring_stopped', self._on_monitoring_stopped)
        self.event_dispatcher.add_listener('security_locked', self._on_security_locked)
        self.event_dispatcher.add_listener('security_unlocked', self._on_security_unlocked)
    
    def _on_typing_started(self, event_type, data):
        """Handle typing started event."""
        self.typing_active = True
        self._update_menu()
    
    def _on_typing_completed(self, event_type, data):
        """Handle typing completed event."""
        self.typing_active = False
        self._update_menu()
    
    def _on_monitoring_started(self, event_type, data):
        """Handle clipboard monitoring started event."""
        self.monitoring_active = True
        self._update_menu()
    
    def _on_monitoring_stopped(self, event_type, data):
        """Handle clipboard monitoring stopped event."""
        self.monitoring_active = False
        self._update_menu()
    
    def _on_security_locked(self, event_type, data):
        """Handle security locked event."""
        self.security_locked = True
        self._update_menu()
    
    def _on_security_unlocked(self, event_type, data):
        """Handle security unlocked event."""
        self.security_locked = False
        self._update_menu()
    
    def _update_menu(self):
        """Update the system tray menu to reflect current state."""
        if self.icon and self.is_running:
            try:
                self.icon.menu = self._create_menu()
            except Exception as e:
                self.logger.error(f"Error updating menu: {str(e)}")
    
    def _create_menu(self):
        """Create the system tray menu."""
        # Determine status indicators
        typing_status = " [TYPING]" if self.typing_active else ""
        monitoring_status = " [MONITORING]" if self.monitoring_active else ""
        security_status = " [LOCKED]" if self.security_locked else ""
        
        # Create menu items
        menu_items = [
            item(f'ClipTyper Pro + AI Assistant{typing_status}{monitoring_status}{security_status}', 
                 self._show_main_window, default=True),
            item('Quick Actions', self._create_quick_actions_menu()),
            item('History', self._create_history_menu()),
            item('AI Functions', self._create_ai_menu()),
            item('Settings', self._open_settings),
            item('Status', self._show_status),
            item('Exit', self._exit_app)
        ]
        
        return pystray.Menu(*menu_items)
    
    def _create_quick_actions_menu(self):
        """Create submenu for quick actions."""
        return pystray.Menu(
            item('Type Clipboard Content', self._type_clipboard_content),
            item('Process Clipboard with AI', self._ai_process_clipboard),
            item('Toggle Monitoring', self._toggle_monitoring),
            item('Clear History', self._clear_history),
            item('Send Clipboard to Telegram', self._send_clipboard_to_telegram)
        )
    
    def _create_history_menu(self):
        """Create submenu for clipboard history."""
        history_items = []
        
        # Get recent clipboard items
        recent_items = self.clipboard_manager.get_history(limit=10)
        
        for i, clipboard_item in enumerate(recent_items):
            # Create a lambda with default parameter to capture the current value
            item_func = lambda idx=i: self._copy_history_item(idx)
            preview = clipboard_item.preview(30)
            history_items.append(item(f"{i+1}. {preview}", item_func))
        
        if not history_items:
            history_items.append(item("No history available", lambda: None))
        
        history_items.append(item('Show All History', self._show_all_history))
        history_items.append(item('Clear History', self._clear_history))
        
        return pystray.Menu(*history_items)
    
    def _create_ai_menu(self):
        """Create submenu for AI functions."""
        return pystray.Menu(
            item('Process with AI', self._ai_process_clipboard),
            item('Attach File Context', self._attach_file_context),
            item('Clear File Context', self._clear_file_context),
            item('Test AI Connection', self._test_ai_connection)
        )
    
    def _create_status_submenu(self):
        """Create submenu for status information."""
        stats = {
            'Clipboard': self.clipboard_manager.get_stats(),
            'AI': self.ai_processor.get_conversation_stats(),
            'Security': self.security_manager.get_security_status()
        }
        
        status_items = []
        for category, stat_dict in stats.items():
            status_items.append(item(f'{category} Stats', lambda: self._show_category_stats(category, stat_dict)))
        
        return pystray.Menu(*status_items)
    
    def _show_category_stats(self, category, stats):
        """Show statistics for a specific category."""
        # This would typically open a dialog or notification
        self.logger.info(f"{category} stats: {stats}")
    
    def _show_main_window(self, icon, item):
        """Show the main application window."""
        # For now, just log the action
        self.logger.info("Main window requested")
        # In a full implementation, this would show the main UI
    
    def _type_clipboard_content(self, icon, item):
        """Type the current clipboard content."""
        try:
            current_content = self.clipboard_manager.clipboard_manager.paste()
            if current_content:
                self.typing_engine.type_text(current_content)
                self.logger.info("Triggered typing of clipboard content")
            else:
                self.logger.warning("Clipboard is empty")
        except Exception as e:
            self.logger.error(f"Error typing clipboard content: {str(e)}")
    
    def _ai_process_clipboard(self, icon, item):
        """Process clipboard content with AI."""
        try:
            current_content = self.clipboard_manager.clipboard_manager.paste()
            if current_content:
                # Process in a separate thread to avoid blocking UI
                thread = threading.Thread(
                    target=self._process_with_ai_thread,
                    args=(current_content,),
                    daemon=True
                )
                thread.start()
                self.logger.info("Triggered AI processing of clipboard content")
            else:
                self.logger.warning("Clipboard is empty")
        except Exception as e:
            self.logger.error(f"Error processing clipboard with AI: {str(e)}")
    
    def _process_with_ai_thread(self, content):
        """Process content with AI in a separate thread."""
        try:
            response = self.ai_processor.process_with_ai(content)
            if response.success and response.content:
                # Optionally copy response to clipboard or type it
                should_copy_response = self.settings_manager.get('ai.copy_response_after_processing', False)
                if should_copy_response:
                    import pyperclip
                    pyperclip.copy(response.content)
        except Exception as e:
            self.logger.error(f"Error in AI processing thread: {str(e)}")
    
    def _toggle_monitoring(self, icon, item):
        """Toggle clipboard monitoring."""
        try:
            if self.clipboard_manager.monitoring:
                self.clipboard_manager.stop_monitoring()
                self.logger.info("Stopped clipboard monitoring")
            else:
                self.clipboard_manager.start_monitoring()
                self.logger.info("Started clipboard monitoring")
        except Exception as e:
            self.logger.error(f"Error toggling monitoring: {str(e)}")
    
    def _clear_history(self, icon, item):
        """Clear clipboard history."""
        try:
            self.clipboard_manager.clear_history()
            self.logger.info("Cleared clipboard history")
        except Exception as e:
            self.logger.error(f"Error clearing history: {str(e)}")
    
    def _copy_history_item(self, index):
        """Copy a specific history item to clipboard."""
        try:
            success = self.clipboard_manager.copy_from_history(index)
            if success:
                self.logger.info(f"Copied history item {index} to clipboard")
            else:
                self.logger.warning(f"Failed to copy history item {index}")
        except Exception as e:
            self.logger.error(f"Error copying history item {index}: {str(e)}")
    
    def _show_all_history(self, icon, item):
        """Show all clipboard history."""
        # This would typically open a history viewer window
        self.logger.info("Show all history requested")
        # In a full implementation, this would show the history UI
    
    def _send_clipboard_to_telegram(self, icon, item):
        """Send clipboard content to Telegram."""
        try:
            if self.telegram_bridge.enabled:
                success = self.telegram_bridge.send_clipboard_content_to_telegram()
                if success:
                    self.logger.info("Sent clipboard content to Telegram")
                else:
                    self.logger.warning("Failed to send clipboard content to Telegram")
            else:
                self.logger.warning("Telegram bridge not enabled")
        except Exception as e:
            self.logger.error(f"Error sending clipboard to Telegram: {str(e)}")
    
    def _attach_file_context(self, icon, item):
        """Attach a file to AI context."""
        # In a GUI implementation, this would open a file dialog
        self.logger.info("Attach file context requested")
        # For now, we'll just log it - in a full implementation, 
        # this would open a file selection dialog
    
    def _clear_file_context(self, icon, item):
        """Clear file context."""
        try:
            self.file_context_manager.clear_all_files()
            self.logger.info("Cleared file context")
        except Exception as e:
            self.logger.error(f"Error clearing file context: {str(e)}")
    
    def _test_ai_connection(self, icon, item):
        """Test AI provider connection."""
        try:
            success = self.ai_processor.test_provider_connection()
            if success:
                self.logger.info("AI connection test passed")
                # Show notification to user
            else:
                self.logger.warning("AI connection test failed")
        except Exception as e:
            self.logger.error(f"Error testing AI connection: {str(e)}")
    
    def _open_settings(self, icon, item):
        """Open settings dialog."""
        # This would typically open the configuration dialog
        self.logger.info("Settings dialog requested")
        # In a full implementation, this would show the settings UI
    
    def _show_status(self, icon, item):
        """Show application status."""
        try:
            status_info = {
                'Typing Active': self.typing_active,
                'Monitoring Active': self.monitoring_active,
                'Security Locked': self.security_locked,
                'Clipboard Items': len(self.clipboard_manager.get_history()),
                'AI Provider': self.ai_processor.current_provider.value,
                'Telegram Enabled': self.telegram_bridge.enabled,
                'Telegram Running': self.telegram_bridge.running
            }
            
            status_str = "\n".join([f"{key}: {value}" for key, value in status_info.items()])
            self.logger.info(f"Application status:\n{status_str}")
            
            # In a full implementation, this might show a notification or dialog
        except Exception as e:
            self.logger.error(f"Error getting status: {str(e)}")
    
    def _exit_app(self, icon, item):
        """Exit the application."""
        self.logger.info("Exit requested from system tray")
        self.is_running = False
        if self.icon:
            self.icon.stop()
        # The main application should handle the actual shutdown
    
    def _create_icon_image(self):
        """Create the system tray icon image."""
        # Create a simple icon with PIL
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), (70, 130, 180))  # Steel blue
        
        # Draw a simple representation of the app
        draw = ImageDraw.Draw(image)
        
        # Draw a clipboard-like rectangle
        draw.rectangle([15, 15, 49, 35], fill=(255, 255, 255))
        
        # Draw text "AI" in the icon
        try:
            # Try to draw text if we have font support
            draw.text((25, 38), "AI", fill=(255, 255, 255))
        except:
            # If text drawing fails, just draw a simple shape
            draw.ellipse([25, 38, 39, 52], fill=(255, 255, 255))
        
        return image
    
    def run(self):
        """Start the system tray application."""
        if self.is_running:
            self.logger.warning("System tray app already running")
            return
        
        try:
            # Create the icon
            self.icon = pystray.Icon(
                "ClipTyper Pro + AI Assistant",
                self._create_icon_image(),
                menu=self._create_menu()
            )
            
            self.is_running = True
            self.logger.info("System tray app started")
            
            # Run the icon
            self.icon.run()
            
        except Exception as e:
            self.logger.error(f"Error running system tray app: {str(e)}", exc_info=True)
            raise
    
    def stop(self):
        """Stop the system tray application."""
        if self.is_running and self.icon:
            try:
                self.icon.stop()
                self.is_running = False
                self.logger.info("System tray app stopped")
            except Exception as e:
                self.logger.error(f"Error stopping system tray app: {str(e)}")
    
    def show_notification(self, title: str, message: str, duration: int = 5):
        """
        Show a notification balloon.
        
        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds (not supported by all systems)
        """
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception as e:
                self.logger.error(f"Error showing notification: {str(e)}")