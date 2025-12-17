"""
Data model for snippets in ClipTyper Pro + AI Assistant.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List
import json


@dataclass
class Snippet:
    """
    Represents a text snippet/template with metadata.
    """
    name: str
    content: str
    category: str
    description: str = ""
    tags: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        """Initialize default values after dataclass initialization."""
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert the snippet to a dictionary for serialization."""
        return {
            'name': self.name,
            'content': self.content,
            'category': self.category,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Snippet':
        """Create a Snippet from a dictionary."""
        return cls(
            name=data['name'],
            content=data['content'],
            category=data['category'],
            description=data.get('description', ''),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        )
    
    def preview(self, max_length: int = 100) -> str:
        """Get a preview of the snippet content."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
    
    def __str__(self) -> str:
        """String representation of the snippet."""
        return f"Snippet(name='{self.name}', category='{self.category}', length={len(self.content)})"