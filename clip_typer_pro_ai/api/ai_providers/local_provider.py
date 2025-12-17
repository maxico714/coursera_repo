"""
Local AI Provider for ClipTyper Pro + AI Assistant.
Provides a fallback implementation for local AI models.
"""

from typing import Dict, Any, Optional, Callable
from .base_provider import BaseProvider


class LocalProvider(BaseProvider):
    """
    Concrete implementation of BaseProvider for local AI models.
    Currently provides a mock implementation that echoes back the input
    until a real local model integration is added.
    """
    
    def __init__(self, settings_manager):
        super().__init__(settings_manager)
        self.model_name = settings_manager.get('ai.local_model', 'mock-local-model')
        self.context_size = settings_manager.get('ai.local_context_size', 4096)
        
    def process(self, context: Dict[str, Any], callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Process the given context with the local AI provider.
        
        Args:
            context: Context dictionary containing input, history, etc.
            callback: Optional callback for streaming responses
            
        Returns:
            AI-generated response as string
        """
        input_text = context.get('input', '')
        system_prompt = context.get('system_prompt', '')
        
        # For now, return a mock response indicating this is a local provider
        # In a real implementation, this would connect to a local model
        response = f"[LOCAL MODEL RESPONSE] Input: {input_text[:100]}..."
        
        # If callback is provided, simulate streaming
        if callback:
            chunk_size = 10
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i+chunk_size]
                callback(chunk)
        
        return response
    
    def validate_config(self) -> bool:
        """
        Validate the provider configuration.
        
        Returns:
            True if configuration is valid
        """
        # For local provider, just check if model name is set
        return bool(self.model_name)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the AI model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'provider': 'local',
            'context_size': self.context_size,
            'supports_streaming': True,
            'supports_vision': False,
            'supports_tools': False
        }
    
    def get_context_size(self) -> int:
        """
        Get the maximum context size for this provider.
        
        Returns:
            Maximum context size in tokens
        """
        return self.context_size