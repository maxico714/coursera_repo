"""
Clipboard Manager for ClipTyper Pro + AI Assistant
Manages clipboard history, monitoring, and provides quick access to recent items.
"""
import time
import threading
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import pyperclip
from models.clipboard_item import ClipboardItem
from utils.logger import get_logger


class ClipboardManager:
    """
    Manages clipboard history, monitoring, and provides quick access to recent items.
    Includes persistent storage and smart deduplication.
    """
    
    def __init__(self, settings_manager, event_dispatcher, typing_engine):
        self.settings_manager = settings_manager
        self.event_dispatcher = event_dispatcher
        self.typing_engine = typing_engine
        self.logger = get_logger('clipboard_manager')
        
        # Clipboard history
        self.history: List[ClipboardItem] = []
        self.max_history_items = settings_manager.get('clipboard.max_history', 50)
        self.monitor_interval = settings_manager.get('clipboard.monitor_interval', 0.5)
        
        # Monitoring state
        self.monitoring = False
        self.monitoring_thread = None
        self.last_clipboard_content = ""
        
        # File paths
        self.history_file = "data/clipboard_history.json"
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        
        # Load existing history
        self.load_history()
        
        self.logger.info(f"Clipboard manager initialized with max {self.max_history_items} items")
    
    def start_monitoring(self):
        """Start monitoring clipboard changes."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Clipboard monitoring started")
        self.event_dispatcher.dispatch('clipboard_monitoring_started', {})
    
    def stop_monitoring(self):
        """Stop monitoring clipboard changes."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        
        self.logger.info("Clipboard monitoring stopped")
        self.event_dispatcher.dispatch('clipboard_monitoring_stopped', {})
    
    def _monitor_clipboard(self):
        """Monitor clipboard for changes."""
        while self.monitoring:
            try:
                current_content = pyperclip.paste()
                
                # Check if content has changed
                if current_content != self.last_clipboard_content:
                    # Only add if it's not a duplicate of the last item
                    if not self.history or self.history[0].content != current_content:
                        self.add_to_history(current_content)
                    
                    self.last_clipboard_content = current_content
                
                # Sleep for monitoring interval
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring clipboard: {str(e)}", exc_info=True)
                time.sleep(1.0)  # Longer sleep on error
    
    def add_to_history(self, content: str) -> ClipboardItem:
        """Add content to clipboard history."""
        if not content.strip():
            return None
        
        # Create clipboard item
        item = ClipboardItem(content=content, timestamp=datetime.now())
        
        # Add to beginning of history
        self.history.insert(0, item)
        
        # Trim history to max size
        if len(self.history) > self.max_history_items:
            removed_items = self.history[self.max_history_items:]
            self.history = self.history[:self.max_history_items]
            
            # Optionally notify about removal
            for removed_item in removed_items:
                self.event_dispatcher.dispatch('clipboard_item_removed', {
                    'item_id': removed_item.id,
                    'reason': 'history_limit'
                })
        
        # Save to file
        self.save_history()
        
        # Notify listeners
        self.event_dispatcher.dispatch('clipboard_item_added', {
            'item_id': item.id,
            'content_length': len(content)
        })
        
        return item
    
    def get_history(self, limit: Optional[int] = None) -> List[ClipboardItem]:
        """Get clipboard history."""
        if limit is None:
            return self.history.copy()
        else:
            return self.history[:limit]
    
    def clear_history(self):
        """Clear clipboard history."""
        old_count = len(self.history)
        self.history.clear()
        self.save_history()
        
        self.logger.info(f"Cleared clipboard history ({old_count} items removed)")
        self.event_dispatcher.dispatch('clipboard_history_cleared', {
            'removed_count': old_count
        })
    
    def copy_from_history(self, index: int) -> bool:
        """Copy item from history back to clipboard."""
        if 0 <= index < len(self.history):
            item = self.history[index]
            pyperclip.copy(item.content)
            
            self.logger.info(f"Copied item {index} from history to clipboard")
            self.event_dispatcher.dispatch('clipboard_item_restored', {
                'item_id': item.id,
                'index': index
            })
            return True
        else:
            self.logger.warning(f"Invalid history index: {index}")
            return False
    
    def search_history(self, query: str) -> List[ClipboardItem]:
        """Search clipboard history for items containing query."""
        query_lower = query.lower()
        results = []
        
        for item in self.history:
            if query_lower in item.content.lower():
                results.append(item)
        
        return results
    
    def save_history(self):
        """Save clipboard history to file."""
        try:
            history_data = [item.to_dict() for item in self.history]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving clipboard history: {str(e)}", exc_info=True)
    
    def load_history(self):
        """Load clipboard history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                self.history = []
                for item_data in history_data:
                    item = ClipboardItem.from_dict(item_data)
                    self.history.append(item)
                
                self.logger.info(f"Loaded {len(self.history)} items from history file")
            else:
                self.logger.info("No history file found, starting with empty history")
        except Exception as e:
            self.logger.error(f"Error loading clipboard history: {str(e)}", exc_info=True)
            self.history = []  # Start with empty history on error
    
    def export_history(self, filepath: str):
        """Export clipboard history to a file."""
        try:
            history_data = [item.to_dict() for item in self.history]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported {len(self.history)} items to {filepath}")
            self.event_dispatcher.dispatch('clipboard_history_exported', {
                'filepath': filepath,
                'exported_count': len(self.history)
            })
        except Exception as e:
            self.logger.error(f"Error exporting clipboard history: {str(e)}", exc_info=True)
            raise
    
    def import_history(self, filepath: str):
        """Import clipboard history from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            imported_items = []
            for item_data in history_data:
                item = ClipboardItem.from_dict(item_data)
                imported_items.append(item)
            
            # Add imported items to history
            for item in imported_items:
                if not self.history or self.history[0].content != item.content:  # Avoid immediate duplicates
                    self.history.insert(0, item)
            
            # Trim to max size
            if len(self.history) > self.max_history_items:
                self.history = self.history[:self.max_history_items]
            
            self.save_history()
            
            self.logger.info(f"Imported {len(imported_items)} items from {filepath}")
            self.event_dispatcher.dispatch('clipboard_history_imported', {
                'filepath': filepath,
                'imported_count': len(imported_items)
            })
        except Exception as e:
            self.logger.error(f"Error importing clipboard history: {str(e)}", exc_info=True)
            raise
    
    def get_stats(self) -> Dict:
        """Get clipboard statistics."""
        total_chars = sum(len(item.content) for item in self.history)
        avg_length = total_chars / len(self.history) if self.history else 0
        
        return {
            'total_items': len(self.history),
            'total_characters': total_chars,
            'average_length': avg_length,
            'max_history_size': self.max_history_items,
            'monitoring_active': self.monitoring
        }
    
    def set_max_history_items(self, count: int):
        """Set the maximum number of items in history."""
        self.max_history_items = max(1, count)
        self.settings_manager.set('clipboard.max_history', count)
        
        # Trim history if needed
        if len(self.history) > self.max_history_items:
            removed_items = self.history[self.max_history_items:]
            self.history = self.history[:self.max_history_items]
            
            for removed_item in removed_items:
                self.event_dispatcher.dispatch('clipboard_item_removed', {
                    'item_id': removed_item.id,
                    'reason': 'history_limit_changed'
                })
        
        self.logger.info(f"Max history items set to {count}")
    
    def set_monitor_interval(self, interval: float):
        """Set the clipboard monitoring interval."""
        self.monitor_interval = max(0.1, interval)  # Minimum 0.1 seconds
        self.settings_manager.set('clipboard.monitor_interval', interval)
        self.logger.info(f"Clipboard monitor interval set to {interval}s")
    
    def paste_from_clipboard(self):
        """Paste current clipboard content using typing engine."""
        current_content = pyperclip.paste()
        if current_content:
            self.typing_engine.type_text(current_content)
            self.logger.info("Pasted clipboard content using typing engine")
        else:
            self.logger.warning("Clipboard is empty, nothing to paste")