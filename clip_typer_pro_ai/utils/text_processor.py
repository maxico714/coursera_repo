"""
Text processing utilities for ClipTyper Pro + AI Assistant.
Provides advanced text manipulation, cleaning, and transformation functions.
"""
import re
import html
from typing import List, Dict, Tuple, Optional, Callable
from collections import Counter
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing characters.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return text
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)
    
    # Remove zero-width characters
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    # Replace various whitespace characters with regular spaces
    text = re.sub(r'[\t\n\r\f\v]+', ' ', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()


def remove_extra_whitespace(text: str) -> str:
    """
    Remove extra whitespace from text.
    
    Args:
        text: Text to process
        
    Returns:
        Text with extra whitespace removed
    """
    # Replace multiple whitespace characters with single space
    return re.sub(r'\s+', ' ', text).strip()


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text (convert all whitespace to regular spaces).
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    # Replace tabs and newlines with spaces
    text = text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    return text.strip()


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text to process
        
    Returns:
        Text with HTML tags removed
    """
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    clean_text = html.unescape(clean_text)
    return clean_text


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text to search for URLs
        
    Returns:
        List of URLs found
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to search for emails
        
    Returns:
        List of email addresses found
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def count_words(text: str) -> int:
    """
    Count the number of words in text.
    
    Args:
        text: Text to count words in
        
    Returns:
        Number of words
    """
    if not text:
        return 0
    # Split on whitespace and count non-empty tokens
    words = [word for word in text.split() if word.strip()]
    return len(words)


def count_sentences(text: str) -> int:
    """
    Count the number of sentences in text.
    
    Args:
        text: Text to count sentences in
        
    Returns:
        Number of sentences
    """
    if not text:
        return 0
    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    # Filter out empty strings
    sentences = [s.strip() for s in sentences if s.strip()]
    return len(sentences)


def count_paragraphs(text: str) -> int:
    """
    Count the number of paragraphs in text.
    
    Args:
        text: Text to count paragraphs in
        
    Returns:
        Number of paragraphs
    """
    if not text:
        return 0
    # Split on double newlines (or single newlines if no double newlines exist)
    paragraphs = text.split('\n\n')
    if len(paragraphs) == 1:
        # If no double newlines, split on single newlines
        paragraphs = [p for p in text.split('\n') if p.strip()]
    else:
        # Filter out empty strings
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return len(paragraphs)


def get_word_frequency(text: str, min_length: int = 2) -> Dict[str, int]:
    """
    Get word frequency in text.
    
    Args:
        text: Text to analyze
        min_length: Minimum word length to include
        
    Returns:
        Dictionary mapping words to their frequencies
    """
    # Convert to lowercase and extract words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter by minimum length and count
    word_counts = Counter(word for word in words if len(word) >= min_length)
    return dict(word_counts)


def find_common_words(text: str, count: int = 10) -> List[str]:
    """
    Find the most common words in text.
    
    Args:
        text: Text to analyze
        count: Number of common words to return
        
    Returns:
        List of most common words
    """
    from utils.helpers import get_common_words as helper_common_words
    return helper_common_words(text, count)


def replace_placeholders(text: str, placeholders: Dict[str, str]) -> str:
    """
    Replace placeholders in text with provided values.
    
    Args:
        text: Text with placeholders
        placeholders: Dictionary mapping placeholder names to values
        
    Returns:
        Text with placeholders replaced
    """
    result = text
    for placeholder, value in placeholders.items():
        # Support both {placeholder} and {{placeholder}} formats
        result = result.replace(f'{{{placeholder}}}', str(value))
        result = result.replace(f'{{{{{placeholder}}}}}', str(value))
    return result


def smart_truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text at word boundary if possible.
    
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
    
    # Try to truncate at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.5:  # Only truncate at word boundary if not too far back
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_text_by_pattern(text: str, pattern: str) -> List[str]:
    """
    Extract text segments matching a pattern.
    
    Args:
        text: Text to search
        pattern: Regular expression pattern
        
    Returns:
        List of text segments matching the pattern
    """
    return re.findall(pattern, text)


def replace_by_pattern(text: str, pattern: str, replacement: str) -> str:
    """
    Replace text segments matching a pattern.
    
    Args:
        text: Text to process
        pattern: Regular expression pattern
        replacement: Replacement string
        
    Returns:
        Processed text
    """
    return re.sub(pattern, replacement, text)


def capitalize_sentences(text: str) -> str:
    """
    Capitalize the first letter of each sentence.
    
    Args:
        text: Text to process
        
    Returns:
        Text with sentences capitalized
    """
    def capitalize_match(match):
        return match.group(0).upper()
    
    # Find sentence endings followed by whitespace and a letter
    result = re.sub(r'([.!?]\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
    # Capitalize the first letter if it's not already capitalized
    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    return result


def add_line_numbers(text: str, start: int = 1) -> str:
    """
    Add line numbers to text.
    
    Args:
        text: Text to process
        start: Starting number
        
    Returns:
        Text with line numbers added
    """
    lines = text.split('\n')
    numbered_lines = [f"{i + start:3d}: {line}" for i, line in enumerate(lines)]
    return '\n'.join(numbered_lines)


def remove_line_numbers(text: str) -> str:
    """
    Remove line numbers from text.
    
    Args:
        text: Text with line numbers
        
    Returns:
        Text with line numbers removed
    """
    # Remove common line number patterns
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Match patterns like "123:", "  123:", etc.
        cleaned_line = re.sub(r'^\s*\d+\s*:\s*', '', line)
        cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines)


def wrap_text(text: str, width: int = 80, indent: str = "") -> str:
    """
    Wrap text to specified width.
    
    Args:
        text: Text to wrap
        width: Maximum line width
        indent: Indentation for each line
        
    Returns:
        Wrapped text
    """
    if width <= 0:
        return text
    
    lines = text.split('\n')
    wrapped_lines = []
    
    for line in lines:
        if len(line) <= width - len(indent):
            wrapped_lines.append(indent + line)
        else:
            # Break line into words and wrap
            words = line.split()
            current_line = indent
            
            for word in words:
                if len(current_line) + len(word) <= width:
                    current_line += word + ' '
                else:
                    wrapped_lines.append(current_line.rstrip())
                    current_line = indent + word + ' '
            
            if current_line.strip():
                wrapped_lines.append(current_line.rstrip())
    
    return '\n'.join(wrapped_lines)


def remove_accents(text: str) -> str:
    """
    Remove accents from text.
    
    Args:
        text: Text with accents
        
    Returns:
        Text with accents removed
    """
    # Normalize to decomposed form
    normalized = unicodedata.normalize('NFD', text)
    # Remove combining characters (accents)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    # Normalize back to composed form
    return unicodedata.normalize('NFC', without_accents)


def is_palindrome(text: str) -> bool:
    """
    Check if text is a palindrome (ignoring spaces, punctuation, and case).
    
    Args:
        text: Text to check
        
    Returns:
        True if text is a palindrome
    """
    # Remove non-alphanumeric characters and convert to lowercase
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    return cleaned == cleaned[::-1]


def levenshtein_distance(str1: str, str2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Levenshtein distance
    """
    if len(str1) < len(str2):
        return levenshtein_distance(str2, str1)

    if len(str2) == 0:
        return len(str1)

    previous_row = list(range(len(str2) + 1))
    for i, c1 in enumerate(str1):
        current_row = [i + 1]
        for j, c2 in enumerate(str2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def similarity_ratio(str1: str, str2: str) -> float:
    """
    Calculate similarity ratio between two strings (0-1 scale).
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    if not str1 and not str2:
        return 1.0
    if not str1 or not str2:
        return 0.0
    
    distance = levenshtein_distance(str1, str2)
    max_len = max(len(str1), len(str2))
    return 1.0 - (distance / max_len)


def find_similar_texts(target: str, texts: List[str], threshold: float = 0.6) -> List[Tuple[str, float]]:
    """
    Find texts similar to the target text.
    
    Args:
        target: Target text to compare against
        texts: List of texts to compare
        threshold: Minimum similarity ratio (0-1)
        
    Returns:
        List of tuples (text, similarity_ratio) for texts above threshold
    """
    similar_texts = []
    for text in texts:
        similarity = similarity_ratio(target, text)
        if similarity >= threshold:
            similar_texts.append((text, similarity))
    
    # Sort by similarity (highest first)
    similar_texts.sort(key=lambda x: x[1], reverse=True)
    return similar_texts


def extract_numbers(text: str) -> List[float]:
    """
    Extract numbers from text.
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of numbers found
    """
    # Pattern to match integers and floats
    number_pattern = r'-?\d+\.?\d*'
    numbers = re.findall(number_pattern, text)
    # Convert to float, filtering out empty strings
    return [float(num) for num in numbers if num and num != '-']


def format_number_list(numbers: List[float], separator: str = ", ") -> str:
    """
    Format a list of numbers as a string.
    
    Args:
        numbers: List of numbers to format
        separator: Separator between numbers
        
    Returns:
        Formatted string
    """
    return separator.join(str(num) for num in numbers)


def count_character_types(text: str) -> Dict[str, int]:
    """
    Count different types of characters in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with character type counts
    """
    counts = {
        'letters': 0,
        'digits': 0,
        'spaces': 0,
        'punctuation': 0,
        'others': 0
    }
    
    for char in text:
        if char.isalpha():
            counts['letters'] += 1
        elif char.isdigit():
            counts['digits'] += 1
        elif char.isspace():
            counts['spaces'] += 1
        elif char in '.,!?;:()[]{}"\'-_':
            counts['punctuation'] += 1
        else:
            counts['others'] += 1
    
    return counts


def apply_text_transformation(text: str, transformations: List[Callable[[str], str]]) -> str:
    """
    Apply a list of text transformations to text.
    
    Args:
        text: Text to transform
        transformations: List of transformation functions
        
    Returns:
        Transformed text
    """
    result = text
    for transform in transformations:
        result = transform(result)
    return result


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Text to split
        
    Returns:
        List of sentences
    """
    # Split on sentence endings, keeping the punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Remove empty strings and strip whitespace
    return [s.strip() for s in sentences if s.strip()]


def extract_quotes(text: str) -> List[str]:
    """
    Extract quoted text from a string.
    
    Args:
        text: Text to extract quotes from
        
    Returns:
        List of quoted text
    """
    # Match both single and double quoted text
    single_quotes = re.findall(r"'([^']*)'", text)
    double_quotes = re.findall(r'"([^"]*)"', text)
    return single_quotes + double_quotes


def remove_quotes(text: str) -> str:
    """
    Remove quoted text from a string, keeping the quotes' content.
    
    Args:
        text: Text to process
        
    Returns:
        Text with quotes removed
    """
    # Remove single and double quotes but keep the content
    text = re.sub(r"'([^']*)'", r'\1', text)
    text = re.sub(r'"([^"]*)"', r'\1', text)
    return text


def text_statistics(text: str) -> Dict[str, any]:
    """
    Get comprehensive statistics about text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with text statistics
    """
    return {
        'character_count': len(text),
        'word_count': count_words(text),
        'sentence_count': count_sentences(text),
        'paragraph_count': count_paragraphs(text),
        'character_types': count_character_types(text),
        'avg_word_length': sum(len(word) for word in text.split()) / count_words(text) if count_words(text) > 0 else 0,
        'avg_sentence_length': count_words(text) / count_sentences(text) if count_sentences(text) > 0 else 0,
        'is_empty': not text.strip(),
        'is_whitespace_only': text.isspace() if text else True,
        'has_digits': bool(re.search(r'\d', text)),
        'has_letters': bool(re.search(r'[a-zA-Z]', text)),
        'has_punctuation': bool(re.search(r'[^\w\s]', text))
    }