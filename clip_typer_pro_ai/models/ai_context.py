"""
Data model for AI context in ClipTyper Pro + AI Assistant.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class FileContext:
    """Represents a file attached to AI context."""
    id: str
    file_path: str
    file_name: str
    file_type: str
    extracted_text: str
    timestamp: datetime
    size: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'extracted_text': self.extracted_text,
            'timestamp': self.timestamp.isoformat(),
            'size': self.size,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileContext':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            file_path=data['file_path'],
            file_name=data['file_name'],
            file_type=data['file_type'],
            extracted_text=data['extracted_text'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            size=data['size'],
            metadata=data.get('metadata', {})
        )


@dataclass
class AIContext:
    """Represents the complete AI context including conversation history and file attachments."""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    file_contexts: List[FileContext] = field(default_factory=list)
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'conversation_history': self.conversation_history,
            'file_contexts': [fc.to_dict() for fc in self.file_contexts],
            'system_prompt': self.system_prompt,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIContext':
        """Create from dictionary."""
        file_contexts = [FileContext.from_dict(fc_data) for fc_data in data.get('file_contexts', [])]
        
        return cls(
            conversation_history=data.get('conversation_history', []),
            file_contexts=file_contexts,
            system_prompt=data.get('system_prompt', ''),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 2048),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        )
    
    def add_conversation_turn(self, user_input: str, assistant_response: str):
        """Add a conversation turn to the history."""
        self.conversation_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': assistant_response,
            'timestamp': datetime.now().isoformat()
        })
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
    
    def add_file_context(self, file_context: FileContext):
        """Add a file context."""
        self.file_contexts.append(file_context)
    
    def remove_file_context(self, file_id: str) -> bool:
        """Remove a file context by ID."""
        for i, fc in enumerate(self.file_contexts):
            if fc.id == file_id:
                del self.file_contexts[i]
                return True
        return False
    
    def get_total_context_size(self) -> int:
        """Get the total size of the context in characters."""
        history_size = sum(len(turn.get('content', '')) for turn in self.conversation_history)
        files_size = sum(len(fc.extracted_text) for fc in self.file_contexts)
        system_prompt_size = len(self.system_prompt)
        
        return history_size + files_size + system_prompt_size