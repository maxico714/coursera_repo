"""
Basic tests for ClipTyper Pro + AI Assistant.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that core modules can be imported."""
    try:
        from main import ClipTyperProAI
        from core.typing_engine import TypingEngine
        from core.clipboard_manager import ClipboardManager
        from core.ai_processor import AIProcessor
        from core.telegram_bridge import TelegramBridge
        from core.hotkey_manager import HotkeyManager
        from core.snippet_manager import SnippetManager
        from core.file_context_manager import FileContextManager
        from core.security_manager import SecurityManager
        from core.event_dispatcher import EventDispatcher
        from config.settings_manager import SettingsManager
        from utils.logger import get_logger
        from utils.security import hash_password, verify_password
        from models.clipboard_item import ClipboardItem
        from models.snippet import Snippet
        from models.ai_context import AIContext
        from models.telegram_message import TelegramMessage
        from api.ai_providers.base_provider import BaseProvider
        from api.ai_providers.deepseek_client import DeepSeekClient
        from api.ai_providers.openai_client import OpenAIClient
        from api.ai_providers.anthropic_client import AnthropicClient
        print("All core modules imported successfully!")
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")

def test_basic_functionality():
    """Test basic functionality without starting the full application."""
    # Test settings manager
    from config.settings_manager import SettingsManager
    settings = SettingsManager()
    assert settings.get("version") is not None
    
    # Test logger
    from utils.logger import get_logger
    logger = get_logger("test")
    assert logger is not None
    
    # Test event dispatcher
    from core.event_dispatcher import EventDispatcher
    dispatcher = EventDispatcher()
    assert dispatcher is not None
    
    # Test basic data models
    from models.clipboard_item import ClipboardItem
    from models.snippet import Snippet
    from models.ai_context import AIContext, FileContext
    from models.telegram_message import TelegramMessage
    
    # Create test instances
    clipboard_item = ClipboardItem("test content")
    assert clipboard_item.content == "test content"
    
    snippet = Snippet("test", "test content", "General")
    assert snippet.name == "test"
    
    print("Basic functionality tests passed!")

if __name__ == "__main__":
    test_imports()
    test_basic_functionality()
    print("All basic tests passed!")