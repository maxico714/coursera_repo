"""
File utilities for ClipTyper Pro + AI Assistant.
Provides file operations, path management, and file type detection.
"""
import os
import shutil
import tempfile
import mimetypes
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime


def get_file_info(filepath: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Dictionary with file information
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {filepath}")
    
    stat = path.stat()
    
    return {
        'name': path.name,
        'path': str(path.absolute()),
        'size': stat.st_size,
        'size_formatted': format_bytes(stat.st_size),
        'extension': path.suffix.lower(),
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'accessed': datetime.fromtimestamp(stat.st_atime),
        'is_file': path.is_file(),
        'is_directory': path.is_directory(),
        'mime_type': mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
    }


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human readable format.
    (This is a duplicate of the one in helpers, but we'll keep it here for file_utils independence)
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Human readable string (e.g., '1.2 KB', '3.4 MB')
    """
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 ** 2:
        return f"{bytes_value / 1024:.1f} KB"
    elif bytes_value < 1024 ** 3:
        return f"{bytes_value / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_value / (1024 ** 3):.1f} GB"


def safe_copy_file(src: str, dst: str, overwrite: bool = False) -> bool:
    """
    Safely copy a file with error handling.
    
    Args:
        src: Source file path
        dst: Destination file path
        overwrite: Whether to overwrite if destination exists
        
    Returns:
        True if copy was successful
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {src}")
        
        if dst_path.exists() and not overwrite:
            raise FileExistsError(f"Destination file exists and overwrite is False: {dst}")
        
        # Create destination directory if it doesn't exist
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(src_path, dst_path)
        
        return True
        
    except Exception as e:
        print(f"Error copying file from {src} to {dst}: {str(e)}")
        return False


def safe_move_file(src: str, dst: str, overwrite: bool = False) -> bool:
    """
    Safely move a file with error handling.
    
    Args:
        src: Source file path
        dst: Destination file path
        overwrite: Whether to overwrite if destination exists
        
    Returns:
        True if move was successful
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {src}")
        
        if dst_path.exists() and not overwrite:
            raise FileExistsError(f"Destination file exists and overwrite is False: {dst}")
        
        # Create destination directory if it doesn't exist
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        shutil.move(str(src_path), str(dst_path))
        
        return True
        
    except Exception as e:
        print(f"Error moving file from {src} to {dst}: {str(e)}")
        return False


def safe_delete_file(filepath: str) -> bool:
    """
    Safely delete a file with error handling.
    
    Args:
        filepath: Path to file to delete
        
    Returns:
        True if deletion was successful
    """
    try:
        path = Path(filepath)
        
        if not path.exists():
            print(f"File does not exist: {filepath}")
            return True  # File doesn't exist, so it's effectively deleted
        
        if path.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {filepath}")
        
        path.unlink()
        return True
        
    except Exception as e:
        print(f"Error deleting file {filepath}: {str(e)}")
        return False


def get_files_by_extension(directory: str, extensions: List[str]) -> List[str]:
    """
    Get all files in a directory with specified extensions.
    
    Args:
        directory: Directory to search
        extensions: List of extensions to look for (e.g., ['.txt', '.pdf'])
        
    Returns:
        List of file paths matching the extensions
    """
    directory_path = Path(directory)
    
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Directory does not exist or is not a directory: {directory}")
    
    # Normalize extensions to lowercase with dots
    normalized_extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions}
    
    files = []
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in normalized_extensions:
            files.append(str(file_path.absolute()))
    
    return files


def create_temp_file(suffix: str = "", prefix: str = "clip_typer_", directory: Optional[str] = None) -> str:
    """
    Create a temporary file.
    
    Args:
        suffix: File suffix (e.g., '.txt')
        prefix: File prefix
        directory: Directory for temp file (None for system default)
        
    Returns:
        Path to the created temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix, dir=directory)
    temp_file.close()
    return temp_file.name


def create_temp_directory(suffix: str = "", prefix: str = "clip_typer_", directory: Optional[str] = None) -> str:
    """
    Create a temporary directory.
    
    Args:
        suffix: Directory suffix
        prefix: Directory prefix
        directory: Directory for temp dir (None for system default)
        
    Returns:
        Path to the created temporary directory
    """
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=directory)


def get_file_encoding(filepath: str) -> str:
    """
    Detect the encoding of a text file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Detected encoding (e.g., 'utf-8', 'latin-1')
    """
    import chardet
    
    with open(filepath, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'


def read_text_file(filepath: str, encoding: Optional[str] = None) -> str:
    """
    Read a text file with proper encoding detection.
    
    Args:
        filepath: Path to the file
        encoding: Specific encoding to use (None to auto-detect)
        
    Returns:
        Content of the file as string
    """
    if encoding is None:
        encoding = get_file_encoding(filepath)
    
    with open(filepath, 'r', encoding=encoding) as file:
        return file.read()


def write_text_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Write text to a file.
    
    Args:
        filepath: Path to the file
        content: Content to write
        encoding: Encoding to use
        
    Returns:
        True if write was successful
    """
    try:
        # Create directory if it doesn't exist
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding=encoding) as file:
            file.write(content)
        
        return True
        
    except Exception as e:
        print(f"Error writing to file {filepath}: {str(e)}")
        return False


def is_text_file(filepath: str) -> bool:
    """
    Check if a file is likely a text file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file is likely a text file
    """
    # First, check the file extension
    text_extensions = {
        '.txt', '.py', '.js', '.html', '.htm', '.css', '.json', '.xml', '.csv',
        '.md', '.rst', '.log', '.cfg', '.conf', '.ini', '.yaml', '.yml', '.sql',
        '.sh', '.bat', '.cmd', '.ps1', '.rb', '.php', '.java', '.cpp', '.c', '.h'
    }
    
    path = Path(filepath)
    if path.suffix.lower() in text_extensions:
        return True
    
    # If not a known text extension, check if it's binary by reading first few bytes
    try:
        with open(filepath, 'rb') as file:
            chunk = file.read(1024)  # Read first 1KB
            
            # Check for null bytes (common in binary files)
            if b'\x00' in chunk:
                return False
            
            # Check if most characters are printable ASCII
            printable_chars = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in {9, 10, 13})
            printable_ratio = printable_chars / len(chunk) if chunk else 0
            
            return printable_ratio > 0.7  # If more than 70% are printable, consider it text
            
    except Exception:
        return False


def get_directory_size(directory: str) -> int:
    """
    Calculate the total size of a directory.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    directory_path = Path(directory)
    
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            try:
                total_size += filepath.stat().st_size
            except OSError:
                # Skip files that can't be accessed
                continue
    
    return total_size


def get_directory_info(directory: str) -> Dict[str, Any]:
    """
    Get information about a directory.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Dictionary with directory information
    """
    directory_path = Path(directory)
    
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Directory does not exist or is not a directory: {directory}")
    
    # Count files and subdirectories
    file_count = 0
    dir_count = 0
    total_size = 0
    
    for item in directory_path.rglob('*'):
        if item.is_file():
            file_count += 1
            try:
                total_size += item.stat().st_size
            except OSError:
                continue
        elif item.is_dir():
            dir_count += 1
    
    return {
        'path': str(directory_path.absolute()),
        'name': directory_path.name,
        'size': total_size,
        'size_formatted': format_bytes(total_size),
        'file_count': file_count,
        'directory_count': dir_count,
        'created': datetime.fromtimestamp(directory_path.stat().st_ctime),
        'modified': datetime.fromtimestamp(directory_path.stat().st_mtime)
    }


def find_duplicate_files(directory: str) -> Dict[str, List[str]]:
    """
    Find duplicate files in a directory based on content hash.
    
    Args:
        directory: Directory to search for duplicates
        
    Returns:
        Dictionary mapping hash to list of duplicate file paths
    """
    import hashlib
    
    directory_path = Path(directory)
    file_hashes = {}
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file():
            try:
                # Calculate file hash
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                if file_hash not in file_hashes:
                    file_hashes[file_hash] = []
                file_hashes[file_hash].append(str(file_path.absolute()))
                
            except Exception:
                # Skip files that can't be read
                continue
    
    # Return only hashes that have multiple files (duplicates)
    return {hash_val: paths for hash_val, paths in file_hashes.items() if len(paths) > 1}


def backup_file(filepath: str, backup_dir: Optional[str] = None, suffix: str = None) -> Optional[str]:
    """
    Create a backup of a file.
    
    Args:
        filepath: Path to the file to backup
        backup_dir: Directory for backup (None for same directory as original)
        suffix: Suffix for backup file (None for timestamp)
        
    Returns:
        Path to backup file or None if backup failed
    """
    import time
    
    path = Path(filepath)
    
    if not path.exists():
        print(f"File does not exist: {filepath}")
        return None
    
    if suffix is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f".backup_{timestamp}"
    
    if backup_dir is None:
        backup_path = path.parent / f"{path.stem}{suffix}{path.suffix}"
    else:
        backup_path = Path(backup_dir) / f"{path.stem}{suffix}{path.suffix}"
    
    try:
        # Create backup directory if needed
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file to backup location
        shutil.copy2(filepath, str(backup_path))
        
        return str(backup_path)
        
    except Exception as e:
        print(f"Error creating backup of {filepath}: {str(e)}")
        return None


def restore_file_from_backup(backup_path: str, original_path: str) -> bool:
    """
    Restore a file from backup.
    
    Args:
        backup_path: Path to the backup file
        original_path: Path where to restore the file
        
    Returns:
        True if restore was successful
    """
    return safe_copy_file(backup_path, original_path, overwrite=True)


def clean_directory(directory: str, keep_patterns: List[str] = None, 
                   remove_patterns: List[str] = None, dry_run: bool = False) -> Dict[str, List[str]]:
    """
    Clean a directory by removing files based on patterns.
    
    Args:
        directory: Directory to clean
        keep_patterns: List of patterns to keep (files matching these won't be removed)
        remove_patterns: List of patterns to remove (files matching these will be removed)
        dry_run: If True, only report what would be deleted without actually deleting
        
    Returns:
        Dictionary with 'deleted' and 'kept' lists
    """
    import fnmatch
    
    directory_path = Path(directory)
    deleted_files = []
    kept_files = []
    
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Directory does not exist or is not a directory: {directory}")
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file():
            file_str = str(file_path.relative_to(directory_path))
            
            should_delete = False
            
            # Check remove patterns first
            if remove_patterns:
                for pattern in remove_patterns:
                    if fnmatch.fnmatch(file_str, pattern):
                        should_delete = True
                        break
            
            # Check keep patterns (these override remove patterns)
            if keep_patterns:
                for pattern in keep_patterns:
                    if fnmatch.fnmatch(file_str, pattern):
                        should_delete = False
                        break
            
            if should_delete:
                if not dry_run:
                    try:
                        file_path.unlink()
                        deleted_files.append(file_str)
                    except Exception as e:
                        print(f"Error deleting {file_path}: {str(e)}")
                        kept_files.append(file_str)
                else:
                    deleted_files.append(file_str)
            else:
                kept_files.append(file_str)
    
    return {
        'deleted': deleted_files,
        'kept': kept_files
    }


def validate_file_path(filepath: str, allowed_extensions: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate a file path for safety and allowed extensions.
    
    Args:
        filepath: File path to validate
        allowed_extensions: List of allowed extensions (None to allow any)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    from utils.security import is_safe_filename
    
    # Check if path is safe
    if not is_safe_filename(filepath):
        return False, "Unsafe file path detected"
    
    path = Path(filepath)
    
    # Check extension if specified
    if allowed_extensions:
        allowed_exts = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in allowed_extensions}
        if path.suffix.lower() not in allowed_exts:
            return False, f"File extension {path.suffix} not allowed. Allowed: {allowed_extensions}"
    
    return True, "File path is valid"