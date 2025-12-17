"""
Base provider for AI integrations in ClipTyper Pro + AI Assistant.
Defines the interface for all AI providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from utils.logger import get_logger


class BaseProvider(ABC):
    """
    Abstract base class for AI providers.
    All AI providers should inherit from this class.
    """
    
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.logger = get_logger(f'ai_provider_{self.__class__.__name__}')
    
    @abstractmethod
    def process(self, context: Dict[str, Any], callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Process the given context with the AI provider.
        
        Args:
            context: Context dictionary containing input, history, etc.
            callback: Optional callback for streaming responses
            
        Returns:
            AI-generated response as string
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate the provider configuration.
        
        Returns:
            True if configuration is valid
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the AI model.
        
        Returns:
            Dictionary with model information
        """
        pass
    
    def get_context_size(self) -> int:
        """
        Get the maximum context size for this provider.
        
        Returns:
            Maximum context size in tokens
        """
        return 4096  # Default value
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limiting information for this provider.
        
        Returns:
            Dictionary with rate limit information
        """
        return {
            'requests_per_minute': 60,
            'tokens_per_minute': 10000
        }
    
    def prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and sanitize context before sending to AI provider.
        
        Args:
            context: Raw context dictionary
            
        Returns:
            Prepared context
        """
        # Ensure required fields exist
        prepared_context = {
            'input': context.get('input', ''),
            'system_prompt': context.get('system_prompt', ''),
            'temperature': context.get('temperature', 0.7),
            'max_tokens': context.get('max_tokens', 2048),
            'conversation_history': context.get('conversation_history', []),
            'file_context': context.get('file_context', [])
        }
        
        # Sanitize and validate values
        prepared_context['temperature'] = max(0.0, min(2.0, prepared_context['temperature']))
        prepared_context['max_tokens'] = max(1, min(4096, prepared_context['max_tokens']))
        
        return prepared_context