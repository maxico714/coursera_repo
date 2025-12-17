"""
ClipTyper Pro + AI Assistant - Main Entry Point
Unified entry point with error handling for the production-grade application.
"""
import sys
import os
import threading
import signal
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.event_dispatcher import EventDispatcher
from core.clipboard_manager import ClipboardManager
from core.typing_engine import TypingEngine
from core.ai_processor import AIProcessor
from core.telegram_bridge import TelegramBridge
from core.hotkey_manager import HotkeyManager
from core.snippet_manager import SnippetManager
from core.file_context_manager import FileContextManager
from core.security_manager import SecurityManager
from ui.system_tray import SystemTrayApp
from config.settings_manager import SettingsManager
from utils.logger import setup_logger


class ClipTyperProAI:
    """
    Main application class that orchestrates all components of ClipTyper Pro + AI Assistant.
    Implements singleton pattern and manages the lifecycle of all subsystems.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implement singleton pattern with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the main application with all required components."""
        if hasattr(self, '_initialized'):
            return
        
        # Set up logging first
        self.logger = setup_logger('ClipTyperProAI', 'logs/app.log')
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        
        # Initialize event dispatcher
        self.event_dispatcher = EventDispatcher()
        
        # Initialize all core components
        self.clipboard_manager = None
        self.typing_engine = None
        self.ai_processor = None
        self.telegram_bridge = None
        self.hotkey_manager = None
        self.snippet_manager = None
        self.file_context_manager = None
        self.security_manager = None
        self.system_tray_app = None
        
        # Application state
        self.is_running = False
        self.initialized = False
        
        self._initialized = True
        self.logger.info("ClipTyper Pro + AI Assistant initialized")
    
    def initialize_components(self):
        """Initialize all application components."""
        try:
            # Initialize security manager first (for authentication)
            self.security_manager = SecurityManager(self.settings_manager)
            
            # Initialize file context manager
            self.file_context_manager = FileContextManager(
                self.settings_manager, 
                self.event_dispatcher
            )
            
            # Initialize snippet manager
            self.snippet_manager = SnippetManager(
                self.settings_manager, 
                self.event_dispatcher
            )
            
            # Initialize AI processor
            self.ai_processor = AIProcessor(
                self.settings_manager, 
                self.event_dispatcher,
                self.file_context_manager
            )
            
            # Initialize typing engine
            self.typing_engine = TypingEngine(
                self.settings_manager, 
                self.event_dispatcher
            )
            
            # Initialize clipboard manager
            self.clipboard_manager = ClipboardManager(
                self.settings_manager, 
                self.event_dispatcher,
                self.typing_engine
            )
            
            # Initialize Telegram bridge
            self.telegram_bridge = TelegramBridge(
                self.settings_manager, 
                self.event_dispatcher,
                self.clipboard_manager
            )
            
            # Initialize hotkey manager
            self.hotkey_manager = HotkeyManager(
                self.settings_manager, 
                self.event_dispatcher,
                self.clipboard_manager,
                self.typing_engine,
                self.ai_processor,
                self.telegram_bridge
            )
            
            # Initialize system tray UI
            self.system_tray_app = SystemTrayApp(
                self.settings_manager,
                self.event_dispatcher,
                self.clipboard_manager,
                self.typing_engine,
                self.ai_processor,
                self.telegram_bridge,
                self.hotkey_manager,
                self.snippet_manager,
                self.file_context_manager,
                self.security_manager
            )
            
            self.initialized = True
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {str(e)}", exc_info=True)
            raise
    
    def start(self):
        """Start the application and all its components."""
        if self.is_running:
            self.logger.warning("Application is already running")
            return
        
        try:
            # Initialize components if not already done
            if not self.initialized:
                self.initialize_components()
            
            # Start all services
            self.start_services()
            
            # Start the system tray UI
            self.system_tray_app.run()
            
            self.is_running = True
            self.logger.info("Application started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start application: {str(e)}", exc_info=True)
            self.shutdown()
            raise
    
    def start_services(self):
        """Start background services."""
        # Start clipboard monitoring
        self.clipboard_manager.start_monitoring()
        
        # Start Telegram bridge if enabled
        if self.settings_manager.get('telegram.enabled', False):
            self.telegram_bridge.start()
        
        # Register hotkeys
        self.hotkey_manager.register_hotkeys()
        
        self.logger.info("Background services started")
    
    def stop(self):
        """Stop the application and all its components."""
        if not self.is_running:
            return
        
        try:
            # Stop all services
            self.stop_services()
            
            # Shutdown system tray
            if self.system_tray_app:
                self.system_tray_app.stop()
            
            self.is_running = False
            self.logger.info("Application stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping application: {str(e)}", exc_info=True)
    
    def stop_services(self):
        """Stop background services."""
        # Stop clipboard monitoring
        if self.clipboard_manager:
            self.clipboard_manager.stop_monitoring()
        
        # Stop Telegram bridge
        if self.telegram_bridge:
            self.telegram_bridge.stop()
        
        # Unregister hotkeys
        if self.hotkey_manager:
            self.hotkey_manager.unregister_hotkeys()
    
    def shutdown(self):
        """Perform complete shutdown of the application."""
        self.logger.info("Shutting down application...")
        
        # Stop the application
        self.stop()
        
        # Close all resources
        if self.event_dispatcher:
            self.event_dispatcher.shutdown()
        
        self.logger.info("Application shutdown complete")


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    app = ClipTyperProAI()
    app.shutdown()
    sys.exit(0)


def main():
    """Main entry point of the application."""
    try:
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and start the application
        app = ClipTyperProAI()
        app.start()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Fatal error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()