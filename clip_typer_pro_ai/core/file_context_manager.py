"""
File Context Manager for ClipTyper Pro + AI Assistant
Manages file context attachment system with auto-cleanup and text extraction.
"""
import os
import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib

# Import file processing libraries conditionally
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from models.ai_context import FileContext
from utils.logger import get_logger


class FileContextManager:
    """
    Manages file context attachment system with auto-cleanup and text extraction.
    Supports PDF, TXT, DOC, DOCX, RTF, and HTML formats.
    """
    
    SUPPORTED_FORMATS = {'.pdf', '.txt', '.doc', '.docx', '.rtf', '.html', '.htm'}
    
    def __init__(self, settings_manager, event_dispatcher):
        self.settings_manager = settings_manager
        self.event_dispatcher = event_dispatcher
        self.logger = get_logger('file_context_manager')
        
        # File context storage
        self.attached_files: List[FileContext] = []
        self.max_file_size = settings_manager.get('file_context.max_file_size_mb', 10) * 1024 * 1024  # Convert to bytes
        self.max_total_size = settings_manager.get('file_context.max_total_size_mb', 50) * 1024 * 1024  # Convert to bytes
        self.auto_cleanup_enabled = settings_manager.get('file_context.auto_cleanup_enabled', True)
        self.auto_cleanup_minutes = settings_manager.get('file_context.auto_cleanup_minutes', 30)
        
        # Auto-cleanup timer
        self.cleanup_timer = None
        self.start_auto_cleanup_timer()
        
        self.logger.info(f"File context manager initialized with support for: {', '.join(self.SUPPORTED_FORMATS)}")
    
    def attach_file(self, file_path: str) -> bool:
        """
        Attach a file to the context.
        
        Args:
            file_path: Path to the file to attach
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            
            # Validate file
            if not file_path.exists():
                self.logger.error(f"File does not exist: {file_path}")
                return False
            
            if not self._is_supported_format(file_path):
                self.logger.error(f"Unsupported file format: {file_path.suffix}")
                return False
            
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                self.logger.error(f"File too large ({file_size} bytes > {self.max_file_size} bytes): {file_path}")
                return False
            
            # Calculate total size with new file
            current_total_size = sum(fc.size for fc in self.attached_files)
            if current_total_size + file_size > self.max_total_size:
                self.logger.error(f"Total file size limit exceeded: {current_total_size + file_size} > {self.max_total_size}")
                return False
            
            # Extract text from file
            extracted_text = self._extract_text_from_file(file_path)
            if not extracted_text.strip():
                self.logger.warning(f"No text extracted from file: {file_path}")
                return False
            
            # Create file context
            file_context = FileContext(
                id=str(uuid.uuid4()),
                file_path=str(file_path.absolute()),
                file_name=file_path.name,
                file_type=file_path.suffix.lower(),
                extracted_text=extracted_text,
                timestamp=datetime.now(),
                size=file_size
            )
            
            # Add to attached files
            self.attached_files.append(file_context)
            
            self.logger.info(f"Attached file to context: {file_path.name} ({file_size} bytes)")
            self.event_dispatcher.dispatch('file_attached_to_context', {
                'file_id': file_context.id,
                'file_name': file_context.file_name,
                'size': file_size
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error attaching file {file_path}: {str(e)}", exc_info=True)
            return False
    
    def remove_file(self, file_id: str) -> bool:
        """
        Remove a file from the context.
        
        Args:
            file_id: ID of the file to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        for i, file_context in enumerate(self.attached_files):
            if file_context.id == file_id:
                removed_file = self.attached_files.pop(i)
                
                self.logger.info(f"Removed file from context: {removed_file.file_name}")
                self.event_dispatcher.dispatch('file_removed_from_context', {
                    'file_id': file_id,
                    'file_name': removed_file.file_name
                })
                
                return True
        
        self.logger.warning(f"File not found in context: {file_id}")
        return False
    
    def clear_all_files(self):
        """Clear all attached files from context."""
        old_count = len(self.attached_files)
        self.attached_files.clear()
        
        self.logger.info(f"Cleared all {old_count} attached files from context")
        self.event_dispatcher.dispatch('all_files_cleared_from_context', {
            'cleared_count': old_count
        })
    
    def get_attached_files(self) -> List[Dict]:
        """Get list of attached files."""
        return [
            {
                'id': fc.id,
                'file_name': fc.file_name,
                'file_type': fc.file_type,
                'size': fc.size,
                'timestamp': fc.timestamp.isoformat(),
                'preview': fc.extracted_text[:100] + "..." if len(fc.extracted_text) > 100 else fc.extracted_text
            }
            for fc in self.attached_files
        ]
    
    def get_attached_files_context(self) -> List[Dict]:
        """Get the context data for all attached files."""
        return [
            {
                'id': fc.id,
                'file_name': fc.file_name,
                'file_type': fc.file_type,
                'extracted_text': fc.extracted_text,
                'timestamp': fc.timestamp.isoformat()
            }
            for fc in self.attached_files
        ]
    
    def get_file_by_id(self, file_id: str) -> Optional[FileContext]:
        """Get a file context by ID."""
        for file_context in self.attached_files:
            if file_context.id == file_id:
                return file_context
        return None
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Check if the file format is supported."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def _extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from a file based on its format."""
        try:
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.txt':
                return self._extract_text_from_txt(file_path)
            elif file_ext == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self._extract_text_from_doc(file_path)
            elif file_ext in ['.html', '.htm']:
                return self._extract_text_from_html(file_path)
            elif file_ext == '.rtf':
                return self._extract_text_from_rtf(file_path)
            else:
                self.logger.warning(f"Unsupported file format for text extraction: {file_ext}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {str(e)}", exc_info=True)
            return ""
    
    def _extract_text_from_txt(self, file_path: Path) -> str:
        """Extract text from a text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from a PDF file."""
        if pdfplumber is None:
            self.logger.error("pdfplumber not installed, cannot extract text from PDF")
            return ""
        
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n".join(text_parts)
        except Exception as e:
            self.logger.error(f"Error reading PDF file {file_path}: {str(e)}", exc_info=True)
            return ""
    
    def _extract_text_from_doc(self, file_path: Path) -> str:
        """Extract text from a DOC/DOCX file."""
        if Document is None:
            self.logger.error("python-docx not installed, cannot extract text from DOC/DOCX")
            return ""
        
        try:
            doc = Document(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs]
            return "\n".join(paragraphs)
        except Exception as e:
            self.logger.error(f"Error reading DOC/DOCX file {file_path}: {str(e)}", exc_info=True)
            return ""
    
    def _extract_text_from_html(self, file_path: Path) -> str:
        """Extract text from an HTML file."""
        if BeautifulSoup is None:
            self.logger.error("beautifulsoup4 not installed, cannot extract text from HTML")
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                return soup.get_text(separator='\n', strip=True)
        except Exception as e:
            self.logger.error(f"Error reading HTML file {file_path}: {str(e)}", exc_info=True)
            return ""
    
    def _extract_text_from_rtf(self, file_path: Path) -> str:
        """Extract text from an RTF file."""
        # For RTF, we'll read it as text and try to remove basic RTF formatting
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Simple RTF tag removal - this is a basic approach
                # For a more robust solution, consider using python-docx or rtfparse
                import re
                # Remove basic RTF formatting tags
                clean_content = re.sub(r'{\\[^}]*}', '', content)
                clean_content = re.sub(r'\\[a-z]+', '', clean_content)
                return clean_content
        except Exception as e:
            self.logger.error(f"Error reading RTF file {file_path}: {str(e)}", exc_info=True)
            return ""
    
    def start_auto_cleanup_timer(self):
        """Start the auto-cleanup timer."""
        if self.auto_cleanup_enabled and self.auto_cleanup_minutes > 0:
            # Cancel existing timer if present
            if self.cleanup_timer:
                self.cleanup_timer.cancel()
            
            # Create new timer
            self.cleanup_timer = threading.Timer(
                self.auto_cleanup_minutes * 60,  # Convert minutes to seconds
                self._auto_cleanup_expired_files
            )
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()
    
    def _auto_cleanup_expired_files(self):
        """Clean up expired files from context."""
        try:
            # Files expire after auto_cleanup_minutes
            expiration_time = datetime.now() - timedelta(minutes=self.auto_cleanup_minutes)
            
            expired_files = []
            remaining_files = []
            
            for file_context in self.attached_files:
                if file_context.timestamp < expiration_time:
                    expired_files.append(file_context)
                else:
                    remaining_files.append(file_context)
            
            # Update the list
            self.attached_files = remaining_files
            
            if expired_files:
                self.logger.info(f"Auto-cleaned {len(expired_files)} expired files from context")
                for file_ctx in expired_files:
                    self.event_dispatcher.dispatch('file_auto_cleaned_from_context', {
                        'file_id': file_ctx.id,
                        'file_name': file_ctx.file_name
                    })
            
            # Restart the timer
            self.start_auto_cleanup_timer()
            
        except Exception as e:
            self.logger.error(f"Error during auto-cleanup: {str(e)}", exc_info=True)
            # Restart the timer anyway to maintain the schedule
            self.start_auto_cleanup_timer()
    
    def set_max_file_size(self, size_mb: int):
        """Set the maximum file size allowed."""
        self.max_file_size = size_mb * 1024 * 1024
        self.settings_manager.set('file_context.max_file_size_mb', size_mb)
        self.logger.info(f"Maximum file size set to {size_mb} MB")
    
    def set_max_total_size(self, size_mb: int):
        """Set the maximum total size for all files."""
        self.max_total_size = size_mb * 1024 * 1024
        self.settings_manager.set('file_context.max_total_size_mb', size_mb)
        self.logger.info(f"Maximum total size set to {size_mb} MB")
    
    def enable_auto_cleanup(self, enabled: bool, minutes: Optional[int] = None):
        """Enable or disable auto-cleanup."""
        self.auto_cleanup_enabled = enabled
        self.settings_manager.set('file_context.auto_cleanup_enabled', enabled)
        
        if minutes is not None:
            self.auto_cleanup_minutes = minutes
            self.settings_manager.set('file_context.auto_cleanup_minutes', minutes)
        
        if enabled:
            self.start_auto_cleanup_timer()
            self.logger.info(f"Auto-cleanup enabled (every {self.auto_cleanup_minutes} minutes)")
        else:
            if self.cleanup_timer:
                self.cleanup_timer.cancel()
            self.logger.info("Auto-cleanup disabled")
    
    def get_stats(self) -> Dict:
        """Get statistics about attached files."""
        total_size = sum(fc.size for fc in self.attached_files)
        return {
            'attached_files_count': len(self.attached_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'max_file_size_bytes': self.max_file_size,
            'max_total_size_bytes': self.max_total_size,
            'auto_cleanup_enabled': self.auto_cleanup_enabled,
            'auto_cleanup_minutes': self.auto_cleanup_minutes
        }
    
    def validate_file_for_attachment(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if a file can be attached based on size and format.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False, "File does not exist"
            
            if not self._is_supported_format(file_path):
                return False, f"Unsupported file format: {file_path.suffix}"
            
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                return False, f"File too large ({file_size} bytes > {self.max_file_size} bytes)"
            
            current_total_size = sum(fc.size for fc in self.attached_files)
            if current_total_size + file_size > self.max_total_size:
                return False, f"Total file size limit would be exceeded"
            
            return True, "File is valid for attachment"
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"
    
    def shutdown(self):
        """Shutdown the file context manager."""
        if self.cleanup_timer:
            self.cleanup_timer.cancel()
        self.logger.info("File context manager shut down")