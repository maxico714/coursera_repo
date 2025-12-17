"""
DeepSeek client for ClipTyper Pro + AI Assistant.
Implements the DeepSeek API integration for free AI processing.
"""
import requests
import json
from typing import Dict, Any, Optional, Callable
from .base_provider import BaseProvider
from utils.security import decrypt_data


class DeepSeekClient(BaseProvider):
    """
    DeepSeek API client implementation.
    Uses the DeepSeek API through NVIDIA's service for free processing.
    """
    
    def __init__(self, settings_manager):
        super().__init__(settings_manager)
        self.api_key = self._get_api_key()
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model = "deepseek-ai/deepseek-r1"
    
    def _get_api_key(self) -> str:
        """Get the API key from settings, decrypting if necessary."""
        try:
            # Try to get encrypted key first
            encrypted_key = self.settings_manager.get('security.encrypted_api_keys.deepseek.encrypted_key')
            if encrypted_key:
                salt = self.settings_manager.get('security.encrypted_api_keys.deepseek.salt')
                if salt:
                    return decrypt_data(f"{salt}:{encrypted_key}")
        except:
            pass
        
        # Fallback to plain text key
        return self.settings_manager.get('ai.deepseek_api_key', '')
    
    def process(self, context: Dict[str, Any], callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Process the given context with DeepSeek API.
        
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
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": prepared_context['temperature'],
                "max_tokens": prepared_context['max_tokens'],
                "stream": callback is not None  # Enable streaming if callback provided
            }
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make the API call
            if callback:
                # Handle streaming response
                return self._process_streaming_request(payload, headers, callback)
            else:
                # Handle non-streaming response
                return self._process_non_streaming_request(payload, headers)
                
        except Exception as e:
            self.logger.error(f"Error processing with DeepSeek: {str(e)}", exc_info=True)
            return f"Error processing request: {str(e)}"
    
    def _process_non_streaming_request(self, payload: Dict, headers: Dict) -> str:
        """Process a non-streaming request to DeepSeek API."""
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                self.logger.error(f"Unexpected API response format: {result}")
                return "Error: Unexpected response format from DeepSeek API"
        else:
            self.logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
            return f"Error: DeepSeek API returned status {response.status_code}"
    
    def _process_streaming_request(self, payload: Dict, headers: Dict, callback: Callable[[str], None]) -> str:
        """Process a streaming request to DeepSeek API."""
        # Note: For simplicity, we'll make a non-streaming request but simulate streaming
        # In a real implementation, you would use requests with stream=True and process chunks
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                # Call the callback with the content (in a real streaming implementation, 
                # you would call it multiple times as chunks arrive)
                if callback:
                    callback(content)
                return content
            else:
                self.logger.error(f"Unexpected API response format: {result}")
                return "Error: Unexpected response format from DeepSeek API"
        else:
            self.logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
            return f"Error: DeepSeek API returned status {response.status_code}"
    
    def validate_config(self) -> bool:
        """
        Validate the DeepSeek configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.api_key:
            self.logger.warning("No DeepSeek API key configured")
            return False
        
        # Test the API key by making a simple request
        try:
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.base_url, headers=headers, json=test_payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error validating DeepSeek config: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the DeepSeek model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'name': self.model,
            'provider': 'deepseek',
            'context_size': 128000,  # DeepSeek R1 has 128K context
            'max_tokens': 8192,
            'capabilities': ['text_generation', 'code_completion', 'analysis'],
            'pricing': 'free through NVIDIA API'
        }
    
    def get_context_size(self) -> int:
        """
        Get the maximum context size for DeepSeek.
        
        Returns:
            Maximum context size in tokens
        """
        return 128000  # DeepSeek R1 has 128K context window
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limiting information for DeepSeek.
        
        Returns:
            Dictionary with rate limit information
        """
        return {
            'requests_per_minute': 100,  # Adjust based on actual limits
            'tokens_per_minute': 100000
        }
    
    def set_api_key(self, api_key: str, encrypt: bool = True):
        """
        Set the DeepSeek API key.
        
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
            if 'deepseek' not in encrypted_keys:
                encrypted_keys['deepseek'] = {}
            encrypted_keys['deepseek']['encrypted_key'] = encrypted_key
            encrypted_keys['deepseek']['salt'] = salt
            
            self.settings_manager.set('security.encrypted_api_keys', encrypted_keys)
        else:
            self.settings_manager.set('ai.deepseek_api_key', api_key)
        
        self.api_key = api_key
        self.logger.info("DeepSeek API key updated")