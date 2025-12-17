"""
Anthropic client for ClipTyper Pro + AI Assistant.
Implements the Anthropic API integration for Claude AI processing.
"""
import anthropic
from typing import Dict, Any, Optional, Callable
from .base_provider import BaseProvider
from utils.security import decrypt_data


class AnthropicClient(BaseProvider):
    """
    Anthropic API client implementation.
    Uses the official Anthropic library for API communication.
    """
    
    def __init__(self, settings_manager):
        super().__init__(settings_manager)
        self.api_key = self._get_api_key()
        self.base_url = self.settings_manager.get('ai.anthropic_base_url', 'https://api.anthropic.com')
        self.model = self.settings_manager.get('ai.anthropic_model', 'claude-3-sonnet-20240229')
        
        # Configure Anthropic client
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def _get_api_key(self) -> str:
        """Get the API key from settings, decrypting if necessary."""
        try:
            # Try to get encrypted key first
            encrypted_key = self.settings_manager.get('security.encrypted_api_keys.anthropic.encrypted_key')
            if encrypted_key:
                salt = self.settings_manager.get('security.encrypted_api_keys.anthropic.salt')
                if salt:
                    return decrypt_data(f"{salt}:{encrypted_key}")
        except:
            pass
        
        # Fallback to plain text key
        return self.settings_manager.get('ai.anthropic_api_key', '')
    
    def process(self, context: Dict[str, Any], callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Process the given context with Anthropic API.
        
        Args:
            context: Context dictionary containing input, history, etc.
            callback: Optional callback for streaming responses
            
        Returns:
            AI-generated response as string
        """
        try:
            # Prepare the request
            prepared_context = self.prepare_context(context)
            
            # Build the prompt - Anthropic uses a different format
            system_prompt = prepared_context['system_prompt']
            
            # Build messages array
            messages = []
            
            # Add conversation history
            for exchange in prepared_context['conversation_history']:
                messages.append({
                    "role": "user",
                    "content": exchange.get('input', '')
                })
                messages.append({
                    "role": "assistant",
                    "content": exchange.get('output', '')
                })
            
            # Add file context if available
            for file_ctx in prepared_context['file_context']:
                messages.append({
                    "role": "user",
                    "content": f"File context ({file_ctx.get('file_name', 'Unknown')}): {file_ctx.get('extracted_text', '')[:1000]}..."  # Limit file content
                })
            
            # Add current input
            messages.append({
                "role": "user",
                "content": prepared_context['input']
            })
            
            # Prepare request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": prepared_context['temperature'],
                "max_tokens": prepared_context['max_tokens'],
            }
            
            # Add system prompt if available
            if system_prompt:
                params["system"] = system_prompt
            
            # Handle streaming if callback is provided
            if callback:
                return self._process_streaming_request(params, callback)
            else:
                return self._process_non_streaming_request(params)
                
        except Exception as e:
            self.logger.error(f"Error processing with Anthropic: {str(e)}", exc_info=True)
            return f"Error processing request: {str(e)}"
    
    def _process_non_streaming_request(self, params: Dict) -> str:
        """Process a non-streaming request to Anthropic API."""
        try:
            response = self.client.messages.create(**params)
            return response.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic API error: {str(e)}")
            return f"Error: Anthropic API error - {str(e)}"
    
    def _process_streaming_request(self, params: Dict, callback: Callable[[str], None]) -> str:
        """Process a streaming request to Anthropic API."""
        try:
            params['stream'] = True
            with self.client.messages.stream(**params) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                    # Call the callback with the content chunk
                    callback(text)
            return full_response
        except Exception as e:
            self.logger.error(f"Anthropic streaming API error: {str(e)}")
            return f"Error: Anthropic streaming API error - {str(e)}"
    
    def validate_config(self) -> bool:
        """
        Validate the Anthropic configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.api_key:
            self.logger.warning("No Anthropic API key configured")
            return False
        
        try:
            # Test the API key by making a simple request
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            self.logger.error(f"Error validating Anthropic config: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Anthropic model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'name': self.model,
            'provider': 'anthropic',
            'context_size': self._get_context_size_for_model(self.model),
            'max_tokens': 4096,  # Default max tokens
            'capabilities': ['text_generation', 'analysis', 'reasoning', 'coding', 'math'],
            'pricing': 'paid - check Anthropic pricing'
        }
    
    def _get_context_size_for_model(self, model_name: str) -> int:
        """Get context size for a specific Anthropic model."""
        context_sizes = {
            'claude-3-sonnet-20240229': 200000,
            'claude-3-opus-20240229': 200000,
            'claude-3-haiku-20240307': 200000,
            'claude-2.1': 200000,
            'claude-instant-1.2': 100000,
        }
        
        # Return specific size or default
        return context_sizes.get(model_name, 100000)
    
    def get_context_size(self) -> int:
        """
        Get the maximum context size for Anthropic model.
        
        Returns:
            Maximum context size in tokens
        """
        return self._get_context_size_for_model(self.model)
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limiting information for Anthropic.
        
        Returns:
            Dictionary with rate limit information
        """
        # Rate limits vary by account type
        return {
            'requests_per_minute': 4000,  # Default rate limit
            'tokens_per_minute': 400000  # Default token rate limit
        }
    
    def set_api_key(self, api_key: str, encrypt: bool = True):
        """
        Set the Anthropic API key.
        
        Args:
            api_key: The API key to set
            encrypt: Whether to encrypt the API key
        """
        if encrypt:
            from utils.security import encrypt_data
            encrypted_data = encrypt_data(api_key)
            salt, encrypted_key = encrypted_data.split(':', 1)
            
            # Store encrypted key
            encrypted_keys = self.settings_manager.get('security.encrypted_api_keys', {})
            if 'anthropic' not in encrypted_keys:
                encrypted_keys['anthropic'] = {}
            encrypted_keys['anthropic']['encrypted_key'] = encrypted_key
            encrypted_keys['anthropic']['salt'] = salt
            
            self.settings_manager.set('security.encrypted_api_keys', encrypted_keys)
        else:
            self.settings_manager.set('ai.anthropic_api_key', api_key)
        
        self.api_key = api_key
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.logger.info("Anthropic API key updated")
    
    def set_model(self, model: str):
        """
        Set the Anthropic model to use.
        
        Args:
            model: Model name (e.g., 'claude-3-sonnet-20240229')
        """
        self.model = model
        self.settings_manager.set('ai.anthropic_model', model)
        self.logger.info(f"Anthropic model set to {model}")
    
    def set_base_url(self, base_url: str):
        """
        Set the Anthropic API base URL (for custom endpoints).
        
        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url
        self.settings_manager.set('ai.anthropic_base_url', base_url)
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=base_url
        )
        self.logger.info(f"Anthropic base URL set to {base_url}")