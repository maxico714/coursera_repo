"""
Snippet Manager for ClipTyper Pro + AI Assistant
Manages text templates/snippets with variable expansion and AI-enhanced features.
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from models.snippet import Snippet
from utils.logger import get_logger


class SnippetManager:
    """
    Manages text templates/snippets with variable expansion and AI-enhanced features.
    Supports categories, variable expansion, and integration with AI.
    """
    
    def __init__(self, settings_manager, event_dispatcher):
        self.settings_manager = settings_manager
        self.event_dispatcher = event_dispatcher
        self.logger = get_logger('snippet_manager')
        
        # Snippet storage
        self.snippets: Dict[str, Snippet] = {}
        self.categories: Dict[str, List[str]] = {}  # category -> list of snippet IDs
        
        # File paths
        self.snippets_file = "data/snippets.json"
        os.makedirs(os.path.dirname(self.snippets_file), exist_ok=True)
        
        # Load existing snippets
        self.load_snippets()
        
        self.logger.info(f"Snippet manager initialized with {len(self.snippets)} snippets")
    
    def add_snippet(self, name: str, content: str, category: str = "General", 
                   description: str = "", tags: List[str] = None) -> bool:
        """
        Add a new snippet.
        
        Args:
            name: Name of the snippet
            content: Content of the snippet
            category: Category for the snippet
            description: Description of the snippet
            tags: List of tags for the snippet
            
        Returns:
            bool: True if successful
        """
        try:
            # Check if snippet with this name already exists
            if name in self.snippets:
                self.logger.warning(f"Snippet '{name}' already exists, updating")
            
            # Create snippet
            snippet = Snippet(
                name=name,
                content=content,
                category=category,
                description=description,
                tags=tags or [],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Add to storage
            old_category = self.snippets.get(name, None)
            if old_category and old_category.category != category:
                # Remove from old category
                if old_category.category in self.categories:
                    if name in self.categories[old_category.category]:
                        self.categories[old_category.category].remove(name)
            
            self.snippets[name] = snippet
            
            # Add to category
            if category not in self.categories:
                self.categories[category] = []
            if name not in self.categories[category]:
                self.categories[category].append(name)
            
            # Save to file
            self.save_snippets()
            
            self.logger.info(f"Added/updated snippet: {name}")
            self.event_dispatcher.dispatch('snippet_added', {
                'name': name,
                'category': category,
                'content_length': len(content)
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding snippet '{name}': {str(e)}", exc_info=True)
            return False
    
    def get_snippet(self, name: str) -> Optional[Snippet]:
        """Get a snippet by name."""
        return self.snippets.get(name)
    
    def remove_snippet(self, name: str) -> bool:
        """Remove a snippet by name."""
        if name not in self.snippets:
            self.logger.warning(f"Snippet '{name}' not found")
            return False
        
        try:
            snippet = self.snippets[name]
            
            # Remove from category list
            if snippet.category in self.categories:
                if name in self.categories[snippet.category]:
                    self.categories[snippet.category].remove(name)
            
            # Remove from snippets
            del self.snippets[name]
            
            # Save to file
            self.save_snippets()
            
            self.logger.info(f"Removed snippet: {name}")
            self.event_dispatcher.dispatch('snippet_removed', {
                'name': name,
                'category': snippet.category
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing snippet '{name}': {str(e)}", exc_info=True)
            return False
    
    def expand_snippet(self, name: str) -> Optional[str]:
        """
        Expand a snippet by name, replacing variables with current values.
        
        Args:
            name: Name of the snippet to expand
            
        Returns:
            Expanded content or None if snippet not found
        """
        snippet = self.get_snippet(name)
        if not snippet:
            self.logger.warning(f"Snippet '{name}' not found for expansion")
            return None
        
        try:
            expanded_content = self._expand_variables(snippet.content)
            
            self.logger.info(f"Expanded snippet: {name}")
            self.event_dispatcher.dispatch('snippet_expanded', {
                'name': name,
                'original_length': len(snippet.content),
                'expanded_length': len(expanded_content)
            })
            
            return expanded_content
            
        except Exception as e:
            self.logger.error(f"Error expanding snippet '{name}': {str(e)}", exc_info=True)
            return None
    
    def _expand_variables(self, content: str) -> str:
        """Expand variables in content."""
        # Current date/time variables
        now = datetime.now()
        replacements = {
            r'\{date\}': now.strftime('%Y-%m-%d'),
            r'\{time\}': now.strftime('%H:%M:%S'),
            r'\{datetime\}': now.strftime('%Y-%m-%d %H:%M:%S'),
            r'\{year\}': str(now.year),
            r'\{month\}': str(now.month).zfill(2),
            r'\{day\}': str(now.day).zfill(2),
            r'\{hour\}': str(now.hour).zfill(2),
            r'\{minute\}': str(now.minute).zfill(2),
            r'\{second\}': str(now.second).zfill(2),
        }
        
        # Clipboard content
        try:
            import pyperclip
            clipboard_content = pyperclip.paste()
            replacements[r'\{clipboard\}'] = clipboard_content
        except ImportError:
            self.logger.warning("pyperclip not available, {clipboard} variable will be empty")
            replacements[r'\{clipboard\}'] = ""
        
        # Apply replacements
        result = content
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def get_snippets_by_category(self, category: str) -> List[Snippet]:
        """Get all snippets in a category."""
        if category not in self.categories:
            return []
        
        return [self.snippets[snippet_id] for snippet_id in self.categories[category] 
                if snippet_id in self.snippets]
    
    def get_all_categories(self) -> List[str]:
        """Get all category names."""
        return list(self.categories.keys())
    
    def get_all_snippets(self) -> List[Snippet]:
        """Get all snippets."""
        return list(self.snippets.values())
    
    def search_snippets(self, query: str) -> List[Snippet]:
        """Search snippets by name, content, or tags."""
        query_lower = query.lower()
        results = []
        
        for snippet in self.snippets.values():
            if (query_lower in snippet.name.lower() or 
                query_lower in snippet.content.lower() or 
                query_lower in snippet.description.lower() or 
                any(query_lower in tag.lower() for tag in snippet.tags)):
                results.append(snippet)
        
        return results
    
    def save_snippets(self):
        """Save snippets to file."""
        try:
            # Convert snippets to serializable format
            snippets_data = {name: snippet.to_dict() for name, snippet in self.snippets.items()}
            
            with open(self.snippets_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'snippets': snippets_data,
                    'categories': self.categories
                }, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error saving snippets: {str(e)}", exc_info=True)
    
    def load_snippets(self):
        """Load snippets from file."""
        try:
            if not os.path.exists(self.snippets_file):
                self.logger.info("No snippets file found, starting with empty snippets")
                return
            
            with open(self.snippets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load snippets
            self.snippets = {}
            for name, snippet_data in data.get('snippets', {}).items():
                self.snippets[name] = Snippet.from_dict(snippet_data)
            
            # Load categories
            self.categories = data.get('categories', {})
            
            self.logger.info(f"Loaded {len(self.snippets)} snippets from file")
            
        except Exception as e:
            self.logger.error(f"Error loading snippets: {str(e)}", exc_info=True)
            self.snippets = {}
            self.categories = {}
    
    def import_snippets_from_file(self, filepath: str) -> bool:
        """
        Import snippets from a JSON file.
        
        Args:
            filepath: Path to the JSON file containing snippets
            
        Returns:
            bool: True if import was successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            for name, snippet_data in data.get('snippets', {}).items():
                # Add or update snippet
                snippet = Snippet.from_dict(snippet_data)
                self.snippets[name] = snippet
                
                # Add to category
                if snippet.category not in self.categories:
                    self.categories[snippet.category] = []
                if name not in self.categories[snippet.category]:
                    self.categories[snippet.category].append(name)
                
                imported_count += 1
            
            # Save to main file
            self.save_snippets()
            
            self.logger.info(f"Imported {imported_count} snippets from {filepath}")
            self.event_dispatcher.dispatch('snippets_imported', {
                'filepath': filepath,
                'imported_count': imported_count
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing snippets from {filepath}: {str(e)}", exc_info=True)
            return False
    
    def export_snippets_to_file(self, filepath: str) -> bool:
        """
        Export snippets to a JSON file.
        
        Args:
            filepath: Path to save the JSON file
            
        Returns:
            bool: True if export was successful
        """
        try:
            # Convert snippets to serializable format
            snippets_data = {name: snippet.to_dict() for name, snippet in self.snippets.items()}
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'snippets': snippets_data,
                    'categories': self.categories
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported {len(self.snippets)} snippets to {filepath}")
            self.event_dispatcher.dispatch('snippets_exported', {
                'filepath': filepath,
                'exported_count': len(self.snippets)
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting snippets to {filepath}: {str(e)}", exc_info=True)
            return False
    
    def get_snippet_stats(self) -> Dict[str, Any]:
        """Get statistics about snippets."""
        total_snippets = len(self.snippets)
        total_categories = len(self.categories)
        total_tags = len(set(tag for snippet in self.snippets.values() for tag in snippet.tags))
        total_content_chars = sum(len(snippet.content) for snippet in self.snippets.values())
        
        return {
            'total_snippets': total_snippets,
            'total_categories': total_categories,
            'total_tags': total_tags,
            'total_content_chars': total_content_chars,
            'average_content_length': total_content_chars / total_snippets if total_snippets > 0 else 0,
            'categories': {cat: len(ids) for cat, ids in self.categories.items()}
        }
    
    def update_snippet(self, name: str, **kwargs) -> bool:
        """
        Update an existing snippet.
        
        Args:
            name: Name of the snippet to update
            **kwargs: Fields to update (content, category, description, tags)
            
        Returns:
            bool: True if update was successful
        """
        if name not in self.snippets:
            self.logger.warning(f"Cannot update snippet '{name}': not found")
            return False
        
        try:
            snippet = self.snippets[name]
            
            # Update fields that were provided
            if 'content' in kwargs:
                snippet.content = kwargs['content']
            if 'category' in kwargs:
                # Remove from old category
                if snippet.category in self.categories:
                    if name in self.categories[snippet.category]:
                        self.categories[snippet.category].remove(name)
                
                # Update category
                snippet.category = kwargs['category']
                
                # Add to new category
                if snippet.category not in self.categories:
                    self.categories[snippet.category] = []
                if name not in self.categories[snippet.category]:
                    self.categories[snippet.category].append(name)
            
            if 'description' in kwargs:
                snippet.description = kwargs['description']
            if 'tags' in kwargs:
                snippet.tags = kwargs['tags'] or []
            
            snippet.updated_at = datetime.now()
            
            # Save to file
            self.save_snippets()
            
            self.logger.info(f"Updated snippet: {name}")
            self.event_dispatcher.dispatch('snippet_updated', {
                'name': name,
                'updated_fields': list(kwargs.keys())
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating snippet '{name}': {str(e)}", exc_info=True)
            return False
    
    def create_ai_enhanced_snippet(self, name: str, ai_query: str, ai_processor) -> bool:
        """
        Create a snippet using AI to generate the content.
        
        Args:
            name: Name for the new snippet
            ai_query: Query to send to AI to generate content
            ai_processor: AIProcessor instance to use for generation
            
        Returns:
            bool: True if successful
        """
        try:
            # Process the query with AI
            response = ai_processor.process_with_ai(ai_query)
            
            if not response.success or not response.content:
                self.logger.error(f"AI processing failed for snippet '{name}'")
                return False
            
            # Add the AI-generated content as a new snippet
            success = self.add_snippet(
                name=name,
                content=response.content,
                description=f"AI-generated snippet: {ai_query[:50]}...",
                tags=['ai-generated']
            )
            
            if success:
                self.logger.info(f"Created AI-enhanced snippet: {name}")
                self.event_dispatcher.dispatch('ai_enhanced_snippet_created', {
                    'name': name,
                    'query': ai_query,
                    'content_length': len(response.content)
                })
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating AI-enhanced snippet '{name}': {str(e)}", exc_info=True)
            return False
    
    def clear_all_snippets(self):
        """Clear all snippets."""
        old_count = len(self.snippets)
        self.snippets.clear()
        self.categories.clear()
        
        # Save empty data
        self.save_snippets()
        
        self.logger.info(f"Cleared all {old_count} snippets")
        self.event_dispatcher.dispatch('all_snippets_cleared', {
            'cleared_count': old_count
        })