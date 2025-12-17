"""
Security Manager for ClipTyper Pro + AI Assistant
Manages password protection, content filtering, and secure credential storage.
"""
import hashlib
import secrets
import os
import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from utils.security import encrypt_data, decrypt_data, hash_password
from utils.logger import get_logger


class SecurityLevel(Enum):
    """Enumeration for security levels."""
    SAFE = "safe"          # Most restrictive
    MODERATE = "moderate"  # Balanced
    UNRESTRICTED = "unrestricted"  # Least restrictive


class SecurityManager:
    """
    Manages password protection, content filtering, and secure credential storage.
    Implements various security features to protect user data and privacy.
    """
    
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.logger = get_logger('security_manager')
        
        # Password protection
        self.password_protected = settings_manager.get('security.password_protected', False)
        self.password_hash = settings_manager.get('security.password_hash', '')
        self.password_salt = settings_manager.get('security.password_salt', '')
        self.session_timeout = settings_manager.get('security.session_timeout_minutes', 30)
        self.last_activity = time.time()
        
        # Content filtering
        self.security_level = SecurityLevel(settings_manager.get('security.level', 'moderate'))
        
        # API key encryption
        self.encrypted_api_keys = settings_manager.get('security.encrypted_api_keys', {})
        
        # Audit logging
        self.audit_log = []
        self.max_audit_entries = 1000
        
        # Session management
        self.session_active = not self.password_protected  # If not password protected, session is always active
        self.session_start_time = time.time() if self.session_active else None
        
        # Security policies
        self.content_filtering_enabled = settings_manager.get('security.content_filtering_enabled', True)
        self.max_password_attempts = settings_manager.get('security.max_password_attempts', 5)
        self.password_attempt_window = settings_manager.get('security.password_attempt_window_seconds', 300)  # 5 minutes
        self.failed_attempts = []
        
        self.logger.info(f"Security manager initialized with level: {self.security_level.value}")
    
    def set_password(self, new_password: str) -> bool:
        """
        Set or update the application password.
        
        Args:
            new_password: The new password to set
            
        Returns:
            bool: True if password was set successfully
        """
        try:
            # Generate salt
            salt = secrets.token_hex(32)
            
            # Hash the password with salt
            password_hash = hash_password(new_password, salt)
            
            # Update settings
            self.password_protected = True
            self.password_hash = password_hash
            self.password_salt = salt
            
            self.settings_manager.set('security.password_protected', True)
            self.settings_manager.set('security.password_hash', password_hash)
            self.settings_manager.set('security.password_salt', salt)
            
            self.logger.info("Password set successfully")
            self._log_security_event('password_set', 'Password was set or updated')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting password: {str(e)}", exc_info=True)
            return False
    
    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
        Args:
            password: The password to verify
            
        Returns:
            bool: True if password is correct
        """
        try:
            # Check if password protection is enabled
            if not self.password_protected:
                self.logger.info("Password protection not enabled, access granted")
                self.session_active = True
                self.last_activity = time.time()
                return True
            
            # Check rate limiting for password attempts
            current_time = time.time()
            self.failed_attempts = [attempt_time for attempt_time in self.failed_attempts 
                                    if current_time - attempt_time < self.password_attempt_window]
            
            if len(self.failed_attempts) >= self.max_password_attempts:
                self.logger.warning("Too many failed password attempts, access denied")
                self._log_security_event('max_attempts_exceeded', 'Too many failed password attempts')
                return False
            
            # Hash the provided password with stored salt
            provided_hash = hash_password(password, self.password_salt)
            
            # Compare hashes
            if provided_hash == self.password_hash:
                self.session_active = True
                self.last_activity = time.time()
                self.failed_attempts.clear()  # Clear failed attempts on success
                
                self.logger.info("Password verified successfully")
                self._log_security_event('password_verified', 'Password verification successful')
                
                return True
            else:
                # Record failed attempt
                self.failed_attempts.append(current_time)
                
                self.logger.warning("Incorrect password provided")
                self._log_security_event('password_failed', 'Password verification failed')
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying password: {str(e)}", exc_info=True)
            return False
    
    def is_session_active(self) -> bool:
        """
        Check if the current session is active (not locked).
        
        Returns:
            bool: True if session is active
        """
        # If password protection is not enabled, always return True
        if not self.password_protected:
            return True
        
        # Check if session has timed out
        if self.session_active and self.session_start_time:
            elapsed = time.time() - self.last_activity
            if elapsed > (self.session_timeout * 60):  # Convert minutes to seconds
                self.session_active = False
                self.logger.info("Session timed out due to inactivity")
                self._log_security_event('session_timeout', f'Session timed out after {self.session_timeout} minutes')
        
        return self.session_active
    
    def lock_session(self):
        """Lock the current session."""
        self.session_active = False
        self.logger.info("Session locked")
        self._log_security_event('session_locked', 'Session was manually locked')
    
    def unlock_session(self, password: str) -> bool:
        """
        Unlock the session with a password.
        
        Args:
            password: The password to unlock the session
            
        Returns:
            bool: True if session was unlocked
        """
        if self.verify_password(password):
            self.session_active = True
            self.session_start_time = time.time()
            self.last_activity = time.time()
            
            self.logger.info("Session unlocked")
            self._log_security_event('session_unlocked', 'Session was unlocked')
            
            return True
        else:
            return False
    
    def set_security_level(self, level: SecurityLevel):
        """
        Set the security level.
        
        Args:
            level: The security level to set
        """
        self.security_level = level
        self.settings_manager.set('security.level', level.value)
        
        self.logger.info(f"Security level set to {level.value}")
        self._log_security_event('security_level_changed', f'Security level changed to {level.value}')
    
    def filter_content(self, content: str) -> tuple[bool, str]:
        """
        Filter content based on security level.
        
        Args:
            content: Content to filter
            
        Returns:
            tuple[bool, str]: (is_allowed, reason) 
        """
        if not self.content_filtering_enabled:
            return True, "Content filtering disabled"
        
        # Check for potentially dangerous content based on security level
        dangerous_patterns = []
        
        if self.security_level in [SecurityLevel.SAFE, SecurityLevel.MODERATE]:
            # Look for command execution patterns
            dangerous_patterns.extend([
                r'exec\(',
                r'eval\(',
                r'os\.',
                r'subprocess\.',
                r'import os',
                r'import subprocess',
                r'import sys',
                r'rm\s+-rf',
                r'del\s+/f\s+/s',
                r'format\(',
            ])
        
        if self.security_level == SecurityLevel.SAFE:
            # Additional restrictions for SAFE level
            dangerous_patterns.extend([
                r'<script',
                r'javascript:',
                r'vbscript:',
                r'on\w+\s*=',
                r'\\x[0-9a-fA-F]{2}',
                r'%[0-9a-fA-F]{2}',
            ])
        
        # Check for dangerous patterns
        content_lower = content.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in content_lower:
                reason = f"Content blocked due to security policy (level: {self.security_level.value}). Pattern found: {pattern}"
                self.logger.warning(f"Content filtered: {reason}")
                self._log_security_event('content_filtered', f'Content filtered: {reason}')
                return False, reason
        
        return True, "Content passed security check"
    
    def encrypt_api_key(self, provider: str, api_key: str) -> bool:
        """
        Encrypt and store an API key.
        
        Args:
            provider: The AI provider name
            api_key: The API key to encrypt
            
        Returns:
            bool: True if successful
        """
        try:
            # Generate a unique salt for this key
            salt = secrets.token_hex(32)
            
            # Encrypt the API key
            encrypted_key = encrypt_data(api_key, salt)
            
            # Store in settings
            if provider not in self.encrypted_api_keys:
                self.encrypted_api_keys[provider] = {}
            
            self.encrypted_api_keys[provider] = {
                'encrypted_key': encrypted_key,
                'salt': salt,
                'timestamp': datetime.now().isoformat()
            }
            
            self.settings_manager.set('security.encrypted_api_keys', self.encrypted_api_keys)
            
            self.logger.info(f"API key for {provider} encrypted and stored")
            self._log_security_event('api_key_encrypted', f'API key for {provider} was encrypted and stored')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error encrypting API key for {provider}: {str(e)}", exc_info=True)
            return False
    
    def decrypt_api_key(self, provider: str) -> Optional[str]:
        """
        Decrypt and retrieve an API key.
        
        Args:
            provider: The AI provider name
            
        Returns:
            str: The decrypted API key, or None if not found/decryption failed
        """
        try:
            if provider not in self.encrypted_api_keys:
                self.logger.warning(f"No encrypted API key found for provider: {provider}")
                return None
            
            encrypted_data = self.encrypted_api_keys[provider]
            encrypted_key = encrypted_data['encrypted_key']
            salt = encrypted_data['salt']
            
            # Decrypt the API key
            decrypted_key = decrypt_data(encrypted_key, salt)
            
            self.logger.info(f"API key for {provider} decrypted successfully")
            
            return decrypted_key
            
        except Exception as e:
            self.logger.error(f"Error decrypting API key for {provider}: {str(e)}", exc_info=True)
            return None
    
    def sanitize_clipboard_content(self, content: str) -> str:
        """
        Sanitize clipboard content based on security settings.
        
        Args:
            content: The clipboard content to sanitize
            
        Returns:
            str: Sanitized content
        """
        try:
            # First, check if content is allowed based on filtering
            is_allowed, reason = self.filter_content(content)
            if not is_allowed:
                self.logger.warning(f"Clipboard content blocked: {reason}")
                return ""  # Return empty string for blocked content
            
            # Apply sanitization based on security level
            sanitized = content
            
            if self.security_level in [SecurityLevel.SAFE, SecurityLevel.MODERATE]:
                # Remove potential command injection characters
                sanitized = sanitized.replace('\0', '')  # Remove null bytes
                sanitized = sanitized.replace('\x00', '')  # Another way null bytes might appear
            
            if self.security_level == SecurityLevel.SAFE:
                # More aggressive sanitization
                import re
                # Remove potential script tags
                sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
                # Remove potential event handlers
                sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Error sanitizing clipboard content: {str(e)}", exc_info=True)
            return content  # Return original content if sanitization fails
    
    def _log_security_event(self, event_type: str, description: str):
        """
        Log a security event to the audit trail.
        
        Args:
            event_type: Type of security event
            description: Description of the event
        """
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'description': description,
                'session_active': self.session_active
            }
            
            self.audit_log.append(event)
            
            # Trim audit log if too large
            if len(self.audit_log) > self.max_audit_entries:
                self.audit_log = self.audit_log[-self.max_audit_entries:]
                
        except Exception as e:
            self.logger.error(f"Error logging security event: {str(e)}", exc_info=True)
    
    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the security audit log.
        
        Args:
            limit: Maximum number of entries to return (None for all)
            
        Returns:
            List of audit log entries
        """
        if limit is None:
            return self.audit_log.copy()
        else:
            return self.audit_log[-limit:]
    
    def clear_audit_log(self):
        """Clear the security audit log."""
        old_count = len(self.audit_log)
        self.audit_log.clear()
        
        self.logger.info(f"Cleared audit log ({old_count} entries removed)")
        self._log_security_event('audit_log_cleared', f'Audit log cleared ({old_count} entries removed)')
    
    def set_content_filtering_enabled(self, enabled: bool):
        """
        Enable or disable content filtering.
        
        Args:
            enabled: Whether to enable content filtering
        """
        self.content_filtering_enabled = enabled
        self.settings_manager.set('security.content_filtering_enabled', enabled)
        
        self.logger.info(f"Content filtering {'enabled' if enabled else 'disabled'}")
        self._log_security_event('content_filtering_toggled', f'Content filtering {"enabled" if enabled else "disabled"}')
    
    def set_session_timeout(self, minutes: int):
        """
        Set the session timeout.
        
        Args:
            minutes: Number of minutes before session times out
        """
        self.session_timeout = max(1, minutes)  # Minimum 1 minute
        self.settings_manager.set('security.session_timeout_minutes', self.session_timeout)
        
        self.logger.info(f"Session timeout set to {self.session_timeout} minutes")
        self._log_security_event('session_timeout_changed', f'Session timeout set to {self.session_timeout} minutes')
    
    def set_max_password_attempts(self, attempts: int):
        """
        Set the maximum number of password attempts before lockout.
        
        Args:
            attempts: Maximum number of attempts
        """
        self.max_password_attempts = max(1, attempts)
        self.settings_manager.set('security.max_password_attempts', self.max_password_attempts)
        
        self.logger.info(f"Max password attempts set to {self.max_password_attempts}")
        self._log_security_event('max_password_attempts_changed', f'Max password attempts set to {self.max_password_attempts}')
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get the current security status.
        
        Returns:
            Dictionary with security status information
        """
        return {
            'password_protected': self.password_protected,
            'session_active': self.session_active,
            'security_level': self.security_level.value,
            'content_filtering_enabled': self.content_filtering_enabled,
            'session_timeout_minutes': self.session_timeout,
            'failed_attempts_count': len(self.failed_attempts),
            'max_password_attempts': self.max_password_attempts,
            'audit_log_entries': len(self.audit_log),
            'encrypted_api_keys_count': len(self.encrypted_api_keys)
        }
    
    def check_permissions(self, feature: str) -> bool:
        """
        Check if a feature is allowed based on security settings.
        
        Args:
            feature: The feature to check permissions for
            
        Returns:
            bool: True if feature is allowed
        """
        # Define feature permissions based on security level
        permissions = {
            SecurityLevel.UNRESTRICTED: {
                'ai_processing': True,
                'telegram_integration': True,
                'file_attachments': True,
                'clipboard_monitoring': True,
                'typing_automation': True,
                'api_key_management': True
            },
            SecurityLevel.MODERATE: {
                'ai_processing': True,
                'telegram_integration': True,
                'file_attachments': True,
                'clipboard_monitoring': True,
                'typing_automation': True,
                'api_key_management': True
            },
            SecurityLevel.SAFE: {
                'ai_processing': True,
                'telegram_integration': False,  # Disable by default for SAFE level
                'file_attachments': False,      # Disable by default for SAFE level
                'clipboard_monitoring': True,
                'typing_automation': True,
                'api_key_management': True
            }
        }
        
        allowed_features = permissions.get(self.security_level, permissions[SecurityLevel.MODERATE])
        return allowed_features.get(feature, False)
    
    def reset_failed_attempts(self):
        """Reset the failed password attempt counter."""
        self.failed_attempts.clear()
        self.logger.info("Failed password attempts reset")
        self._log_security_event('failed_attempts_reset', 'Failed password attempts counter reset')