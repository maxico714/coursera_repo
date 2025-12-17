"""
OpenAI client for ClipTyper Pro + AI Assistant.
Implements the OpenAI API integration.
"""
import openai
from typing import Dict, Any, Optional, Callable
from .base_provider import BaseProvider
from utils.security import decrypt_data


class OpenAIClient(BaseProvider):
    """
    OpenAI API client implementation.
    Uses the official OpenAI library for API communication.
    """
    
    def __init__(self, settings_manager):
        super().__init__(settings_manager)
        self.api_key = self._get_api_key()
        self.base_url = self.settings_manager.get('ai.openai_base_url', 'https://api.openai.com/v1')
        self.model = self.settings_manager.get('ai.openai_model', 'gpt-4')
        
        # Configure OpenAI client
        openai.api_key = self.api_key
        if self.base_url != 'https://api.openai.com/v1':
            openai.base_url = self.base_url
    
    def _get_api_key(self) -> str:
        """Get the API key from settings, decrypting if necessary."""
        try:
            # Try to get encrypted key first
            encrypted_key = self.settings_manager.get('security.encrypted_api_keys.openai.encrypted_key')
            if encrypted_key:
                salt = self.settings_manager.get('security.encrypted_api_keys.openai.salt')
                if salt:
                    return decrypt_data(f"{salt}:{encrypted_key}")
        except:
            pass
        
        # Fallback to plain text key
        return self.settings_manager.get('ai.openai_api_key', '')
    
    def process(self, context: Dict[str, Any], callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Process the given context with OpenAI API.
        
        Args:
            context: Context dictionary containing input, history, etc.
            callback: Optional callback for streaming responses
            
        Returns:
            AI-generated response as string
        """
        try:
            # Prepare the request
            prepared_context = self.prepare_context(context)
            
            # Build messages array
            messages = []
            
            # Add system prompt if available
            if prepared_context['system_prompt']:
                messages.append({
                    "role": "system",
                    "content": prepared_context['system_prompt']
                })
            
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
            
            # Handle streaming if callback is provided
            if callback:
                return self._process_streaming_request(params, callback)
            else:
                return self._process_non_streaming_request(params)
                
        except Exception as e:
            self.logger.error(f"Error processing with OpenAI: {str(e)}", exc_info=True)
            return f"Error processing request: {str(e)}"
    
    def _process_non_streaming_request(self, params: Dict) -> str:
        """Process a non-streaming request to OpenAI API."""
        try:
            response = openai.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return f"Error: OpenAI API error - {str(e)}"
    
    def _process_streaming_request(self, params: Dict, callback: Callable[[str], None]) -> str:
        """Process a streaming request to OpenAI API."""
        try:
            params['stream'] = True
            response = openai.chat.completions.create(**params)
            
            full_response = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # Call the callback with the content chunk
                    callback(content)
            
            return full_response
        except Exception as e:
            self.logger.error(f"OpenAI streaming API error: {str(e)}")
            return f"Error: OpenAI streaming API error - {str(e)}"
    
    def validate_config(self) -> bool:
        """
        Validate the OpenAI configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.api_key:
            self.logger.warning("No OpenAI API key configured")
            return False
        
        try:
            # Test the API key by making a simple request
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            self.logger.error(f"Error validating OpenAI config: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the OpenAI model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'name': self.model,
            'provider': 'openai',
            'context_size': self._get_context_size_for_model(self.model),
            'max_tokens': 4096,  # Default max tokens
            'capabilities': ['text_generation', 'code_completion', 'analysis', 'reasoning'],
            'pricing': 'paid - check OpenAI pricing'
        }
    
    def _get_context_size_for_model(self, model_name: str) -> int:
        """Get context size for a specific OpenAI model."""
        context_sizes = {
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'gpt-4-128k': 128000,
            'gpt-4-turbo': 128000,
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
        }
        
        # Return specific size or default
        return context_sizes.get(model_name, 4096)
    
    def get_context_size(self) -> int:
        """
        Get the maximum context size for OpenAI model.
        
        Returns:
            Maximum context size in tokens
        """
        return self._get_context_size_for_model(self.model)
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limiting information for OpenAI.
        
        Returns:
            Dictionary with rate limit information
        """
        # Rate limits vary by model and account type
        return {
            'requests_per_minute': 3500,  # Default for GPT-4
            'tokens_per_minute': 100000  # Default for GPT-4
        }
    
    def set_api_key(self, api_key: str, encrypt: bool = True):
        """
        Set the OpenAI API key.
        
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
            if 'openai' not in encrypted_keys:
                encrypted_keys['openai'] = {}
            encrypted_keys['openai']['encrypted_key'] = encrypted_key
            encrypted_keys['openai']['salt'] = salt
            
            self.settings_manager.set('security.encrypted_api_keys', encrypted_keys)
        else:
            self.settings_manager.set('ai.openai_api_key', api_key)
        
        self.api_key = api_key
        openai.api_key = api_key  # Update the OpenAI client
        self.logger.info("OpenAI API key updated")
    
    def set_model(self, model: str):
        """
        Set the OpenAI model to use.
        
        Args:
            model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        """
        self.model = model
        self.settings_manager.set('ai.openai_model', model)
        self.logger.info(f"OpenAI model set to {model}")
    
    def set_base_url(self, base_url: str):
        """
        Set the OpenAI API base URL (for custom endpoints).
        
        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url
        self.settings_manager.set('ai.openai_base_url', base_url)
        openai.base_url = base_url
        self.logger.info(f"OpenAI base URL set to {base_url}")