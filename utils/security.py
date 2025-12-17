"""
Security utilities for ClipTyper Pro + AI Assistant.
Provides encryption, decryption, and security-related functions.
"""

import hashlib
import secrets
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


class SecurityUtils:
    """Security utilities for encryption, hashing, and secure operations."""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """
        Hash a password with salt using SHA-256.
        
        Args:
            password: The password to hash
            salt: Optional salt, generated if not provided
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        pwdhash = hashlib.pbkdf2_hmac('sha256',
                                      password.encode('utf-8'),
                                      salt,
                                      100000)
        return pwdhash, salt
    
    @staticmethod
    def verify_password(stored_password: bytes, provided_password: str, salt: bytes) -> bool:
        """
        Verify a password against stored hash.
        
        Args:
            stored_password: The stored password hash
            provided_password: The password to verify
            salt: The salt used for hashing
            
        Returns:
            True if password matches, False otherwise
        """
        pwdhash, _ = SecurityUtils.hash_password(provided_password, salt)
        return pwdhash == stored_password
    
    @staticmethod
    def encrypt_data(data: str, key: bytes) -> bytes:
        """
        Encrypt data using AES encryption.
        
        Args:
            data: String data to encrypt
            key: Encryption key (must be 16, 24, or 32 bytes long)
            
        Returns:
            Encrypted data as bytes
        """
        cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
        iv = cipher.iv
        return iv + ct_bytes
    
    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
        """
        Decrypt data using AES decryption.
        
        Args:
            encrypted_data: Encrypted data as bytes
            key: Decryption key (same as used for encryption)
            
        Returns:
            Decrypted string data
        """
        iv = encrypted_data[:AES.block_size]
        ct = encrypted_data[AES.block_size:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')
    
    @staticmethod
    def generate_secure_key(length: int = 32) -> bytes:
        """
        Generate a cryptographically secure random key.
        
        Args:
            length: Length of key in bytes (default 32 for AES-256)
            
        Returns:
            Random bytes of specified length
        """
        return get_random_bytes(length)
    
    @staticmethod
    def sanitize_content(content: str) -> str:
        """
        Sanitize content to remove potentially dangerous elements.
        
        Args:
            content: Content to sanitize
            
        Returns:
            Sanitized content
        """
        # Remove potentially dangerous sequences
        sanitized = content.replace('\x00', '')  # Null bytes
        # Additional sanitization could be added here
        return sanitized