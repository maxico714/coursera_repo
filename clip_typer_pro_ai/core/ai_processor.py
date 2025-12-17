"""
AI Processor for ClipTyper Pro + AI Assistant
Manages multiple AI providers, context management, and file context attachment system.
"""
import asyncio
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
import json
import os
from models.ai_context import AIContext
from core.file_context_manager import FileContextManager
from utils.logger import get_logger


class AIProvider(Enum):
    """Enumeration for supported AI providers."""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class AIResponse:
    """Data class for AI responses."""
    content: str
    provider: AIProvider
    tokens_used: int
    processing_time: float
    success: bool
    error: Optional[str] = None


class AIProcessor:
    """
    AI processing engine with multi-model support, context management, and file context attachment.
    """
    
    def __init__(self, settings_manager, event_dispatcher, file_context_manager: FileContextManager):
        self.settings_manager = settings_manager
        self.event_dispatcher = event_dispatcher
        self.file_context_manager = file_context_manager
        self.logger = get_logger('ai_processor')
        
        # AI configuration
        self.current_provider = AIProvider(settings_manager.get('ai.provider', 'deepseek'))
        self.api_keys = {}
        self.temperature = settings_manager.get('ai.temperature', 0.7)
        self.max_tokens = settings_manager.get('ai.max_tokens', 2048)
        
        # Context management
        self.conversation_memory = []
        self.max_context_messages = settings_manager.get('ai.context_memory', 10)
        
        # File context
        self.attached_files = []
        self.auto_cleanup_timer = None
        
        # Rate limiting
        self.request_times = []
        self.rate_limit_requests = 60  # Max requests per minute
        self.rate_limit_window = 60  # 60 seconds window
        
        # Initialize API clients
        self._initialize_clients()
        
        self.logger.info(f"AI processor initialized with {self.current_provider.value} provider")
    
    def _initialize_clients(self):
        """Initialize AI provider clients."""
        try:
            # Import clients dynamically to avoid requiring all dependencies upfront
            from api.ai_providers.deepseek_client import DeepSeekClient
            from api.ai_providers.openai_client import OpenAIClient
            from api.ai_providers.anthropic_client import AnthropicClient
            from api.ai_providers.base_provider import BaseProvider
            
            self.clients = {
                AIProvider.DEEPSEEK: DeepSeekClient(self.settings_manager),
                AIProvider.OPENAI: OpenAIClient(self.settings_manager),
                AIProvider.ANTHROPIC: AnthropicClient(self.settings_manager),
                AIProvider.LOCAL: BaseProvider(self.settings_manager)  # Placeholder for local models
            }
            
            self.logger.info("AI clients initialized successfully")
        except ImportError as e:
            self.logger.warning(f"Could not import all AI clients: {str(e)}. Some providers may not be available.")
            # Initialize with minimal clients
            self.clients = {}
    
    def process_with_ai(self, 
                       text: str, 
                       context: Optional[Dict] = None, 
                       callback: Optional[Callable[[str], None]] = None) -> AIResponse:
        """
        Process text with AI using current provider and context.
        
        Args:
            text: Input text to process
            context: Additional context information
            callback: Optional callback for streaming responses
            
        Returns:
            AIResponse object with result
        """
        start_time = time.time()
        
        try:
            # Check rate limiting
            if not self._check_rate_limit():
                raise Exception("Rate limit exceeded. Please wait before making another request.")
            
            # Get current provider client
            client = self.clients.get(self.current_provider)
            if not client:
                raise Exception(f"No client available for provider: {self.current_provider.value}")
            
            # Build context including file context
            full_context = self._build_context(text, context)
            
            # Process with AI
            response = client.process(full_context, callback=callback)
            
            processing_time = time.time() - start_time
            
            # Update conversation memory
            self._update_conversation_memory(text, response)
            
            # Dispatch event
            self.event_dispatcher.dispatch('ai_response_generated', {
                'provider': self.current_provider.value,
                'processing_time': processing_time,
                'tokens_used': len(response.split()) if response else 0
            })
            
            return AIResponse(
                content=response,
                provider=self.current_provider,
                tokens_used=len(response.split()) if response else 0,
                processing_time=processing_time,
                success=True
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing with AI: {str(e)}", exc_info=True)
            
            return AIResponse(
                content="",
                provider=self.current_provider,
                tokens_used=0,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    async def process_with_ai_async(self, text: str, context: Optional[Dict] = None) -> AIResponse:
        """Asynchronous version of AI processing."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process_with_ai, text, context)
    
    def _build_context(self, text: str, additional_context: Optional[Dict] = None) -> Dict:
        """Build full context including conversation history and file context."""
        context = {
            'input': text,
            'conversation_history': self.conversation_memory[-self.max_context_messages:],
            'file_context': self.file_context_manager.get_attached_files_context(),
            'system_prompt': self.settings_manager.get('ai.system_prompt', ''),
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
        
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _update_conversation_memory(self, input_text: str, output_text: str):
        """Update conversation memory with new exchange."""
        # Add new exchange to memory
        exchange = {
            'input': input_text,
            'output': output_text,
            'timestamp': time.time()
        }
        
        self.conversation_memory.append(exchange)
        
        # Trim memory if too large
        if len(self.conversation_memory) > self.max_context_messages:
            self.conversation_memory = self.conversation_memory[-self.max_context_messages:]
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        current_time = time.time()
        
        # Remove requests older than the window
        self.request_times = [req_time for req_time in self.request_times 
                              if current_time - req_time < self.rate_limit_window]
        
        # Check if we've exceeded the limit
        if len(self.request_times) >= self.rate_limit_requests:
            return False
        
        # Add current request
        self.request_times.append(current_time)
        return True
    
    def set_provider(self, provider: AIProvider):
        """Set the current AI provider."""
        self.current_provider = provider
        self.settings_manager.set('ai.provider', provider.value)
        self.logger.info(f"AI provider set to {provider.value}")
    
    def set_temperature(self, temperature: float):
        """Set the temperature for AI responses."""
        self.temperature = max(0.0, min(2.0, temperature))  # Clamp between 0 and 2
        self.settings_manager.set('ai.temperature', self.temperature)
        self.logger.info(f"AI temperature set to {self.temperature}")
    
    def set_max_tokens(self, max_tokens: int):
        """Set the maximum tokens for AI responses."""
        self.max_tokens = max(100, max_tokens)  # Minimum 100 tokens
        self.settings_manager.set('ai.max_tokens', self.max_tokens)
        self.logger.info(f"AI max tokens set to {self.max_tokens}")
    
    def clear_conversation_memory(self):
        """Clear the conversation memory."""
        old_count = len(self.conversation_memory)
        self.conversation_memory.clear()
        self.logger.info(f"Cleared conversation memory ({old_count} exchanges removed)")
        self.event_dispatcher.dispatch('ai_conversation_memory_cleared', {
            'cleared_count': old_count
        })
    
    def get_conversation_stats(self) -> Dict:
        """Get statistics about the conversation memory."""
        return {
            'memory_size': len(self.conversation_memory),
            'max_memory_size': self.max_context_messages,
            'total_exchanges': len(self.conversation_memory),
            'current_provider': self.current_provider.value
        }
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt for AI behavior."""
        self.settings_manager.set('ai.system_prompt', prompt)
        self.logger.info("System prompt updated")
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available AI providers."""
        return [provider for provider in AIProvider if provider in self.clients]
    
    def test_provider_connection(self, provider: Optional[AIProvider] = None) -> bool:
        """Test connection to an AI provider."""
        test_provider = provider or self.current_provider
        client = self.clients.get(test_provider)
        
        if not client:
            return False
        
        try:
            # Send a simple test request
            test_response = client.process({'input': 'Hello, are you working?', 'max_tokens': 10})
            return bool(test_response and len(test_response.strip()) > 0)
        except Exception as e:
            self.logger.error(f"Connection test failed for {test_provider.value}: {str(e)}")
            return False
    
    def attach_file_context(self, file_path: str) -> bool:
        """Attach a file to the AI context."""
        return self.file_context_manager.attach_file(file_path)
    
    def remove_file_context(self, file_id: str) -> bool:
        """Remove a file from the AI context."""
        return self.file_context_manager.remove_file(file_id)
    
    def get_attached_files(self) -> List[Dict]:
        """Get list of attached files."""
        return self.file_context_manager.get_attached_files()
    
    def clear_file_context(self):
        """Clear all attached file contexts."""
        self.file_context_manager.clear_all_files()
        self.logger.info("Cleared all attached file contexts")