"""
Helper utilities for ClipTyper Pro + AI Assistant.
Provides common utility functions used throughout the application.
"""
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import os
import sys


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human readable format.
    
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


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human readable string (e.g., '1h 23m 45s', '2m 30s')
    """
    if seconds < 0:
        return "0s"
    
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.now().isoformat()


def get_unique_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters for Windows/Linux/Mac
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
    
    # Limit length to 255 characters (most filesystems limit)
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized


def is_valid_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add to truncated text
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    if max_length <= len(suffix):
        return text[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def normalize_text(text: str) -> str:
    """
    Normalize text by removing extra whitespace.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    # Replace multiple whitespace with single space
    normalized = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    return normalized.strip()


def get_common_words(text: str, count: int = 10) -> List[str]:
    """
    Get most common words in text.
    
    Args:
        text: Input text
        count: Number of common words to return
        
    Returns:
        List of common words
    """
    from collections import Counter
    
    # Convert to lowercase and extract words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'about', 'as', 'into', 'through', 'during', 'before', 
        'after', 'above', 'below', 'from', 'up', 'down', 'out', 'off', 'over', 
        'under', 'again', 'further', 'then', 'once', 'i', 'me', 'my', 'myself', 
        'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 
        'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 
        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 
        'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 
        'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 
        'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'would', 'should', 
        'could', 'ought', 'i\'m', 'you\'re', 'he\'s', 'she\'s', 'it\'s', 'we\'re', 
        'they\'re', 'i\'ve', 'you\'ve', 'we\'ve', 'they\'ve', 'i\'d', 'you\'d', 
        'he\'d', 'she\'d', 'we\'d', 'they\'d', 'i\'ll', 'you\'ll', 'he\'ll', 
        'she\'ll', 'we\'ll', 'they\'ll', 'isn\'t', 'aren\'t', 'wasn\'t', 'weren\'t', 
        'hasn\'t', 'haven\'t', 'hadn\'t', 'doesn\'t', 'don\'t', 'didn\'t', 'won\'t', 
        'wouldn\'t', 'shan\'t', 'shouldn\'t', 'can\'t', 'cannot', 'couldn\'t', 
        'mustn\'t', 'let\'s', 'that\'s', 'who\'s', 'what\'s', 'here\'s', 'there\'s', 
        'when\'s', 'where\'s', 'why\'s', 'how\'s', 'a', 'an', 'the', 'and', 'but', 
        'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 
        'with', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 
        'among', 'into', 'throughout', 'despite', 'towards', 'upon', 'concerning', 
        'without', 'following', 'across', 'beyond', 'plus', 'except', 'within', 
        'around', 'among', 'beneath', 'beside', 'besides', 'up', 'down', 'out', 
        'around', 'above', 'below', 'in', 'on', 'off', 'over', 'under', 'again', 
        'further', 'then', 'once'
    }
    
    # Filter out stop words and count occurrences
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    word_counts = Counter(filtered_words)
    
    # Return most common words
    return [word for word, count in word_counts.most_common(count)]


def find_in_dict(data: Dict, key: str) -> Any:
    """
    Find a key in a nested dictionary.
    
    Args:
        data: Dictionary to search
        key: Key to find
        
    Returns:
        Value of the key or None if not found
    """
    if key in data:
        return data[key]
    
    for k, v in data.items():
        if isinstance(v, dict):
            result = find_in_dict(v, key)
            if result is not None:
                return result
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    result = find_in_dict(item, key)
                    if result is not None:
                        return result
    
    return None


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary to merge into first
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def get_system_info() -> Dict[str, Any]:
    """
    Get system information.
    
    Returns:
        Dictionary with system information
    """
    import platform
    
    return {
        'platform': platform.platform(),
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'python_implementation': platform.python_implementation(),
        'architecture': platform.architecture(),
        'node': platform.node(),
    }


def is_running_in_venv() -> bool:
    """
    Check if the application is running in a virtual environment.
    
    Returns:
        True if running in virtual environment
    """
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )


def get_app_directory() -> Path:
    """
    Get the application directory.
    
    Returns:
        Path to application directory
    """
    return Path(__file__).parent.parent


def get_data_directory() -> Path:
    """
    Get the data directory for the application.
    
    Returns:
        Path to data directory
    """
    app_dir = get_app_directory()
    data_dir = app_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_config_directory() -> Path:
    """
    Get the configuration directory for the application.
    
    Returns:
        Path to configuration directory
    """
    app_dir = get_app_directory()
    config_dir = app_dir / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_cache_directory() -> Path:
    """
    Get the cache directory for the application.
    
    Returns:
        Path to cache directory
    """
    app_dir = get_app_directory()
    cache_dir = app_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function on failure.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                    else:
                        break
            
            # If all retries failed, raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


def batch_process(items: List, batch_size: int, process_func):
    """
    Process items in batches.
    
    Args:
        items: List of items to process
        batch_size: Size of each batch
        process_func: Function to process each batch
        
    Returns:
        List of results from processing each batch
    """
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        result = process_func(batch)
        results.append(result)
    
    return results


def validate_json(json_str: str) -> bool:
    """
    Validate if a string is valid JSON.
    
    Args:
        json_str: String to validate
        
    Returns:
        True if valid JSON
    """
    try:
        import json
        json.loads(json_str)
        return True
    except ValueError:
        return False


def escape_html(text: str) -> str:
    """
    Escape HTML special characters in text.
    
    Args:
        text: Text to escape
        
    Returns:
        HTML-escaped text
    """
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    
    return "".join(html_escape_table.get(c, c) for c in text)


def unescape_html(text: str) -> str:
    """
    Unescape HTML special characters in text.
    
    Args:
        text: Text to unescape
        
    Returns:
        HTML-unescaped text
    """
    html_unescape_table = {
        "&amp;": "&",
        "&quot;": '"',
        "&#x27;": "'",
        "&gt;": ">",
        "&lt;": "<",
    }
    
    import re
    # Create a regular expression from the dictionary keys
    regex = re.compile("|".join(re.escape(key) for key in html_unescape_table.keys()))
    # For each match, look up the corresponding value in the dictionary
    return regex.sub(lambda match: html_unescape_table[match.group(0)], text)