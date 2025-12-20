"""
System Tray UI for ClipTyper Pro + AI Assistant.
Implements the system tray icon with dynamic menu and status indicators.
"""
import threading
import os
import sys
from pathlib import Path
from utils.logger import get_logger
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

class SystemTrayApp:
    """
    System tray application using pystray.
    Provides a system tray icon and menu for controlling the application.
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
        self.is_running = False
        self.icon = None

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

    def _on_typing_completed(self, event_type, data):
        """Handle typing completed event."""
        self.typing_active = False

    def _on_monitoring_started(self, event_type, data):
        """Handle clipboard monitoring started event."""
        self.monitoring_active = True

    def _on_monitoring_stopped(self, event_type, data):
        """Handle clipboard monitoring stopped event."""
        self.monitoring_active = False

    def _on_security_locked(self, event_type, data):
        """Handle security locked event."""
        self.security_locked = True

    def _on_security_unlocked(self, event_type, data):
        """Handle security unlocked event."""
        self.security_locked = False

    def create_image(self):
        """Create the icon image. Loads from file or generates default."""
        # Try to load from assets
        try:
            # Assuming this file is in ui/, assets is in parent/assets/
            icon_path = Path(__file__).parent.parent / 'assets' / 'icon.png'
            if icon_path.exists():
                return Image.open(icon_path)

            # Try .ico
            icon_path_ico = Path(__file__).parent.parent / 'assets' / 'icon.ico'
            if icon_path_ico.exists():
                return Image.open(icon_path_ico)
        except Exception as e:
            self.logger.warning(f"Failed to load icon from file: {e}")

        # Generate default icon (blue square with white circle)
        width = 64
        height = 64
        color_bg = (0, 120, 215) # Windows blue
        color_fg = (255, 255, 255)

        image = Image.new('RGB', (width, height), color_bg)
        dc = ImageDraw.Draw(image)
        # Draw a 'C' or something simple
        dc.ellipse((16, 16, 48, 48), fill=color_fg)

        return image

    def setup_tray(self):
        """Setup the system tray icon and menu."""
        image = self.create_image()

        menu = pystray.Menu(
            item('Status', self._show_status),
            item('Toggle Monitoring', self._toggle_monitoring),
            item('Clear History', self._clear_history),
            pystray.Menu.SEPARATOR,
            item('Test AI Connection', self._test_ai_connection),
            item('Settings', self._open_settings),
            pystray.Menu.SEPARATOR,
            item('Exit', self._exit_app)
        )

        self.icon = pystray.Icon("clip_typer", image, "ClipTyper Pro", menu)

    def run(self):
        """Start the system tray application."""
        if self.is_running:
            self.logger.warning("System tray app already running")
            return

        self.is_running = True
        self.logger.info("System tray app started")

        self.setup_tray()
        # This blocks until the icon is stopped
        self.icon.run()

        # When icon stops
        self.is_running = False
        self.logger.info("System tray app stopped")

    def stop(self):
        """Stop the system tray application."""
        self.logger.info("Stopping system tray app")
        if self.icon:
            self.icon.stop()
        self.is_running = False

    def _show_main_window(self, icon=None, item=None):
        """Show the main application window."""
        self.logger.info("Main window requested")
        # If there was a GUI window, we would show it here.

    def _type_clipboard_content(self, icon=None, item=None):
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

    def _ai_process_clipboard(self, icon=None, item=None):
        """Process clipboard content with AI."""
        try:
            current_content = self.clipboard_manager.clipboard_manager.paste()
            if current_content:
                # Process in a separate thread to avoid blocking
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

    def _toggle_monitoring(self, icon=None, item=None):
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

    def _clear_history(self, icon=None, item=None):
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

    def _show_all_history(self, icon=None, item=None):
        """Show all clipboard history."""
        self.logger.info("Show all history requested")

    def _send_clipboard_to_telegram(self, icon=None, item=None):
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

    def _attach_file_context(self, icon=None, item=None):
        """Attach a file to AI context."""
        self.logger.info("Attach file context requested")

    def _clear_file_context(self, icon=None, item=None):
        """Clear file context."""
        try:
            self.file_context_manager.clear_all_files()
            self.logger.info("Cleared file context")
        except Exception as e:
            self.logger.error(f"Error clearing file context: {str(e)}")

    def _test_ai_connection(self, icon=None, item=None):
        """Test AI provider connection."""
        try:
            success = self.ai_processor.test_provider_connection()
            if success:
                self.logger.info("AI connection test passed")
            else:
                self.logger.warning("AI connection test failed")
        except Exception as e:
            self.logger.error(f"Error testing AI connection: {str(e)}")

    def _open_settings(self, icon=None, item=None):
        """Open settings dialog."""
        self.logger.info("Settings dialog requested")

    def _show_status(self, icon=None, item=None):
        """Show application status."""
        try:
            status_info = {
                'Typing Active': self.typing_active,
                'Monitoring Active': self.monitoring_active,
                'Security Locked': self.security_locked,
                'Clipboard Items': len(self.clipboard_manager.get_history()),
                'AI Provider': self.ai_processor.current_provider.value if hasattr(self.ai_processor, 'current_provider') else 'Unknown',
                'Telegram Enabled': self.telegram_bridge.enabled,
                'Telegram Running': self.telegram_bridge.running
            }

            status_str = "\n".join([f"{key}: {value}" for key, value in status_info.items()])
            self.logger.info(f"Application status:\n{status_str}")

        except Exception as e:
            self.logger.error(f"Error getting status: {str(e)}")

    def _exit_app(self, icon=None, item=None):
        """Exit the application."""
        self.logger.info("Exit requested from system tray")
        self.stop()
