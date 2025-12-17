"""
Data model for clipboard items in ClipTyper Pro + AI Assistant.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class ClipboardItem:
    """
    Represents a single clipboard item with content, timestamp, and metadata.
    """
    
    def __init__(self, content: str, timestamp: Optional[datetime] = None, item_type: str = "text"):
        """
        Initialize a clipboard item.
        
        Args:
            content: The clipboard content
            timestamp: When the item was created (defaults to now)
            item_type: Type of content ('text', 'image', 'file', etc.)
        """
        self.id = str(uuid.uuid4())
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.item_type = item_type
        self.length = len(content)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the clipboard item to a dictionary for serialization."""
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'item_type': self.item_type,
            'length': self.length
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClipboardItem':
        """Create a clipboard item from a dictionary."""
        item = cls.__new__(cls)
        item.id = data['id']
        item.content = data['content']
        item.timestamp = datetime.fromisoformat(data['timestamp'])
        item.item_type = data.get('item_type', 'text')
        item.length = data.get('length', len(item.content))
        return item
    
    def __repr__(self) -> str:
        """String representation of the clipboard item."""
        return f"ClipboardItem(id={self.id[:8]}, type={self.item_type}, length={self.length})"
    
    def __eq__(self, other) -> bool:
        """Check equality based on content and timestamp."""
        if not isinstance(other, ClipboardItem):
            return False
        return self.content == other.content and self.timestamp == other.timestamp
    
    def preview(self, max_length: int = 50) -> str:
        """Get a preview of the content."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."