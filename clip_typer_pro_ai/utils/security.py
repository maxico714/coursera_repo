"""
Security utilities for ClipTyper Pro + AI Assistant.
Provides encryption, hashing, and other security-related functions.
"""
import hashlib
import secrets
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    Hash a password with salt using SHA-256.
    
    Args:
        password: Password to hash
        salt: Salt to use (if None, generates a new one)
        
    Returns:
        Hashed password with salt (format: salt:hash)
    """
    if salt is None:
        salt = secrets.token_hex(32)
    
    # Combine password and salt
    salted_password = password + salt
    
    # Create hash
    hash_obj = hashlib.sha256(salted_password.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    
    return f"{salt}:{password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash.
    
    Args:
        password: Password to verify
        stored_hash: Stored hash in format 'salt:hash'
        
    Returns:
        True if password matches the hash
    """
    try:
        salt, stored_password_hash = stored_hash.split(':', 1)
        computed_hash = hash_password(password, salt).split(':', 1)[1]
        return computed_hash == stored_password_hash
    except ValueError:
        # If stored_hash doesn't have the expected format
        return False


def encrypt_data(data: str, salt: Optional[str] = None) -> str:
    """
    Encrypt data using AES encryption.
    
    Args:
        data: Data to encrypt
        salt: Salt for encryption (if None, generates a new one)
        
    Returns:
        Encrypted data as base64 string with salt prepended
    """
    if salt is None:
        salt = secrets.token_hex(16)  # 16 bytes = 128 bits
    
    # Create a key from the salt
    key = hashlib.pbkdf2_hmac('sha256', salt.encode('utf-8'), b'salt_', 100000)
    key = key[:32]  # AES-256 requires 32 bytes key
    
    # Create cipher
    cipher = AES.new(key, AES.MODE_CBC)
    
    # Pad and encrypt the data
    padded_data = pad(data.encode('utf-8'), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    
    # Combine IV and encrypted data, then encode as base64
    encrypted_result = cipher.iv + encrypted_data
    encoded_result = base64.b64encode(encrypted_result).decode('utf-8')
    
    # Return salt + encoded result
    return f"{salt}:{encoded_result}"


def decrypt_data(encrypted_data_with_salt: str) -> str:
    """
    Decrypt data using AES encryption.
    
    Args:
        encrypted_data_with_salt: Encrypted data with salt (format: salt:encrypted_data)
        
    Returns:
        Decrypted data as string
    """
    try:
        salt, encrypted_data_b64 = encrypted_data_with_salt.split(':', 1)
        
        # Decode the base64 encrypted data
        encrypted_data = base64.b64decode(encrypted_data_b64.encode('utf-8'))
        
        # Extract IV (first 16 bytes) and the rest is the encrypted content
        iv = encrypted_data[:16]
        encrypted_content = encrypted_data[16:]
        
        # Create key from salt
        key = hashlib.pbkdf2_hmac('sha256', salt.encode('utf-8'), b'salt_', 100000)
        key = key[:32]  # AES-256 requires 32 bytes key
        
        # Create cipher and decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(encrypted_content)
        
        # Remove padding
        decrypted_data = unpad(decrypted_padded, AES.block_size)
        
        return decrypted_data.decode('utf-8')
    
    except Exception as e:
        raise ValueError(f"Failed to decrypt data: {str(e)}")


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        Generated API key
    """
    return secrets.token_urlsafe(32)


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate the format of an API key.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if format is valid
    """
    # Basic validation: should be non-empty and contain only URL-safe characters
    if not api_key or len(api_key) < 20:
        return False
    
    # Check if it's a valid URL-safe base64 string
    try:
        # Add padding if needed
        padded_key = api_key
        missing_padding = len(api_key) % 4
        if missing_padding:
            padded_key += '=' * (4 - missing_padding)
        
        # Try to decode it
        base64.b64decode(padded_key, validate=True)
        return True
    except Exception:
        return False


def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_str: Input string to sanitize
        
    Returns:
        Sanitized string
    """
    if not input_str:
        return input_str
    
    # Remove null bytes
    sanitized = input_str.replace('\0', '').replace('\x00', '')
    
    # Remove potential command injection characters
    # Note: This is a basic implementation - more sophisticated sanitization
    # might be needed depending on the use case
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized


def is_safe_filename(filename: str) -> bool:
    """
    Check if a filename is safe to use.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if filename is safe
    """
    # Check for dangerous patterns
    dangerous_patterns = [
        '..',      # Directory traversal
        '/etc/',   # System directory access
        '/root/',  # Root directory access
        '/home/',  # Home directory access (unless intended)
        'C:\\Windows\\',  # Windows system directory
        'C:\\Program Files\\',  # Windows program files
    ]
    
    filename_lower = filename.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in filename_lower:
            return False
    
    # Check for valid characters (alphanumeric, dots, underscores, hyphens)
    import re
    valid_pattern = r'^[a-zA-Z0-9._-]+$'
    if not re.match(valid_pattern, os.path.basename(filename)):
        return False
    
    return True


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes (default 32)
        
    Returns:
        Generated secure token
    """
    return secrets.token_urlsafe(length)


def hash_file(filepath: str) -> str:
    """
    Generate a SHA-256 hash of a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        SHA-256 hash of the file
    """
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


# Import os here since we need it for the is_safe_filename function
import os