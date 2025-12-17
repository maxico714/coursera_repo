"""
Data model for Telegram messages in ClipTyper Pro + AI Assistant.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TelegramMessage:
    """
    Represents a Telegram message with metadata.
    """
    message_id: int
    user_id: str
    username: Optional[str]
    text: str
    timestamp: datetime
    chat_id: Optional[int] = None
    message_type: str = "text"  # 'text', 'photo', 'document', etc.
    reply_to_message_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert the message to a dictionary for serialization."""
        return {
            'message_id': self.message_id,
            'user_id': self.user_id,
            'username': self.username,
            'text': self.text,
            'timestamp': self.timestamp.isoformat(),
            'chat_id': self.chat_id,
            'message_type': self.message_type,
            'reply_to_message_id': self.reply_to_message_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TelegramMessage':
        """Create a TelegramMessage from a dictionary."""
        return cls(
            message_id=data['message_id'],
            user_id=data['user_id'],
            username=data.get('username'),
            text=data['text'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            chat_id=data.get('chat_id'),
            message_type=data.get('message_type', 'text'),
            reply_to_message_id=data.get('reply_to_message_id')
        )
    
    def preview(self, max_length: int = 100) -> str:
        """Get a preview of the message text."""
        if len(self.text) <= max_length:
            return self.text
        return self.text[:max_length] + "..."
    
    def __str__(self) -> str:
        """String representation of the message."""
        username_str = f"@{self.username}" if self.username else f"User {self.user_id}"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {username_str}: {self.preview()}"