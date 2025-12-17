"""
Settings Manager for ClipTyper Pro + AI Assistant
Manages configuration with versioned settings, migration, and validation.
"""
import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path
from utils.logger import get_logger


class SettingsManager:
    """
    Manages application configuration with versioning, migration, and validation.
    Provides a centralized way to access and modify application settings.
    """
    
    def __init__(self, config_file: str = "config/app_settings.json"):
        self.config_file = config_file
        self.logger = get_logger('settings_manager')
        self._lock = threading.Lock()
        
        # Ensure config directory exists
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Current settings schema version
        self.current_version = "1.0.0"
        
        # Default settings
        self.default_settings = {
            "version": self.current_version,
            "general": {
                "language": "en",
                "theme": "system",
                "auto_start": False,
                "minimize_to_tray": True,
                "check_updates": True
            },
            "clipboard": {
                "max_history": 50,
                "monitor_interval": 0.5,
                "monitor_enabled": True,
                "format_preservation": True
            },
            "typing": {
                "default_speed": "fast_human",  # fast_human, very_fast, machine
                "batch_size": 10,
                "interrupt_keys": ["backspace", "esc"],
                "auto_correct": True
            },
            "ai": {
                "provider": "deepseek",
                "temperature": 0.7,
                "max_tokens": 2048,
                "context_memory": 10,
                "system_prompt": "You are a helpful assistant.",
                "type_response_after_processing": False
            },
            "file_context": {
                "max_file_size_mb": 10,
                "max_total_size_mb": 50,
                "auto_cleanup_enabled": True,
                "auto_cleanup_minutes": 30
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "user_ids": [],
                "auto_copy_from_telegram": False,
                "auto_type_responses": False,
                "connection_method": "polling"
            },
            "hotkeys": {
                "typing_trigger": "ctrl+alt+insert",
                "ai_process_clipboard": "ctrl+alt+a",
                "paste_clipboard": "ctrl+alt+v",
                "toggle_monitoring": "ctrl+alt+m",
                "clear_history": "ctrl+alt+c",
                "show_history": "ctrl+alt+h"
            },
            "security": {
                "password_protected": False,
                "password_hash": "",
                "password_salt": "",
                "level": "moderate",
                "session_timeout_minutes": 30,
                "content_filtering_enabled": True,
                "max_password_attempts": 5,
                "password_attempt_window_seconds": 300,
                "encrypted_api_keys": {}
            },
            "display": {
                "overlay_transparency": 0.8,
                "overlay_position": "bottom_right",
                "font_size": 12,
                "animation_enabled": True,
                "notification_timeout": 5
            },
            "performance": {
                "thread_pool_size": 4,
                "cache_size": 100,
                "log_level": "INFO"
            }
        }
        
        # Load settings from file
        self.settings = self._load_settings()
        
        # Apply migrations if needed
        self._migrate_settings()
        
        # Validate settings
        self._validate_settings()
        
        self.logger.info(f"Settings manager initialized with version {self.current_version}")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults if file doesn't exist."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                self.logger.info(f"Loaded settings from {self.config_file}")
                return loaded_settings
            else:
                self.logger.info("No existing settings file found, using defaults")
                return self.default_settings.copy()
        except Exception as e:
            self.logger.error(f"Error loading settings: {str(e)}, using defaults", exc_info=True)
            return self.default_settings.copy()
    
    def _migrate_settings(self):
        """Apply any necessary migrations to update settings to current version."""
        try:
            # Get current version from settings
            current_file_version = self.settings.get("version", "0.0.0")
            
            if current_file_version != self.current_version:
                self.logger.info(f"Migrating settings from version {current_file_version} to {self.current_version}")
                
                # Perform migrations based on version
                if current_file_version < "1.0.0":
                    # Migration for version 1.0.0
                    self._migrate_to_v1_0_0()
                
                # Update version
                self.settings["version"] = self.current_version
                
                # Save migrated settings
                self._save_settings()
                
                self.logger.info(f"Settings migrated to version {self.current_version}")
        
        except Exception as e:
            self.logger.error(f"Error during settings migration: {str(e)}", exc_info=True)
    
    def _migrate_to_v1_0_0(self):
        """Migration for version 1.0.0."""
        # Example migration logic - add any missing default values
        for section, defaults in self.default_settings.items():
            if section not in self.settings:
                self.settings[section] = defaults
            else:
                # Merge defaults for this section
                for key, default_value in defaults.items():
                    if key not in self.settings[section]:
                        self.settings[section][key] = default_value
    
    def _validate_settings(self):
        """Validate current settings against expected schema."""
        try:
            # Basic validation
            if not isinstance(self.settings, dict):
                raise ValueError("Settings must be a dictionary")
            
            # Validate required sections exist
            required_sections = [
                "general", "clipboard", "typing", "ai", 
                "file_context", "telegram", "hotkeys", 
                "security", "display", "performance"
            ]
            
            for section in required_sections:
                if section not in self.settings:
                    self.logger.warning(f"Missing required section: {section}, adding defaults")
                    self.settings[section] = self.default_settings[section].copy()
            
            # Validate specific values
            self._validate_numeric_settings()
            self._validate_string_settings()
            
            self.logger.info("Settings validation completed")
            
        except Exception as e:
            self.logger.error(f"Error validating settings: {str(e)}", exc_info=True)
    
    def _validate_numeric_settings(self):
        """Validate numeric settings are within acceptable ranges."""
        numeric_validations = {
            ('clipboard', 'max_history'): (1, 10000),
            ('clipboard', 'monitor_interval'): (0.1, 5.0),
            ('typing', 'batch_size'): (1, 100),
            ('ai', 'temperature'): (0.0, 2.0),
            ('ai', 'max_tokens'): (100, 4096),
            ('ai', 'context_memory'): (1, 50),
            ('file_context', 'max_file_size_mb'): (1, 100),
            ('file_context', 'max_total_size_mb'): (1, 500),
            ('file_context', 'auto_cleanup_minutes'): (1, 1440),  # Max 24 hours
            ('security', 'session_timeout_minutes'): (1, 1440),
            ('security', 'max_password_attempts'): (1, 20),
            ('security', 'password_attempt_window_seconds'): (60, 3600),
            ('display', 'overlay_transparency'): (0.1, 1.0),
            ('display', 'font_size'): (8, 72),
            ('display', 'notification_timeout'): (1, 30),
            ('performance', 'thread_pool_size'): (1, 16),
            ('performance', 'cache_size'): (10, 10000)
        }
        
        for (section, key), (min_val, max_val) in numeric_validations.items():
            if section in self.settings and key in self.settings[section]:
                value = self.settings[section][key]
                if not isinstance(value, (int, float)) or value < min_val or value > max_val:
                    self.logger.warning(f"Invalid value for {section}.{key}: {value}, resetting to default")
                    self.settings[section][key] = self.default_settings[section][key]
    
    def _validate_string_settings(self):
        """Validate string settings are within acceptable values."""
        # Validate AI provider
        valid_ai_providers = {"deepseek", "openai", "anthropic", "local"}
        current_provider = self.settings.get("ai", {}).get("provider", "deepseek")
        if current_provider not in valid_ai_providers:
            self.logger.warning(f"Invalid AI provider: {current_provider}, resetting to default")
            self.settings["ai"]["provider"] = "deepseek"
        
        # Validate security level
        valid_security_levels = {"safe", "moderate", "unrestricted"}
        current_level = self.settings.get("security", {}).get("level", "moderate")
        if current_level not in valid_security_levels:
            self.logger.warning(f"Invalid security level: {current_level}, resetting to default")
            self.settings["security"]["level"] = "moderate"
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation (e.g., 'ai.provider').
        
        Args:
            key: Setting key in dot notation
            default: Default value if key doesn't exist
            
        Returns:
            Setting value or default
        """
        try:
            keys = key.split('.')
            value = self.settings
            
            for k in keys:
                value = value[k]
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a setting value using dot notation (e.g., 'ai.provider').
        
        Args:
            key: Setting key in dot notation
            value: Value to set
            
        Returns:
            bool: True if successful
        """
        try:
            with self._lock:
                keys = key.split('.')
                current = self.settings
                
                # Navigate to the parent of the target key
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                # Set the final value
                current[keys[-1]] = value
                
                # Save settings to file
                self._save_settings()
                
                self.logger.debug(f"Setting updated: {key} = {value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting {key} to {value}: {str(e)}", exc_info=True)
            return False
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            # Create a backup of the current settings
            backup_path = f"{self.config_file}.backup"
            if os.path.exists(self.config_file):
                import shutil
                shutil.copy2(self.config_file, backup_path)
            
            # Write settings to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Settings saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {str(e)}", exc_info=True)
            # Try to restore from backup if save failed
            backup_path = f"{self.config_file}.backup"
            if os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, self.config_file)
    
    def reset_to_defaults(self, section: Optional[str] = None):
        """
        Reset settings to defaults.
        
        Args:
            section: Specific section to reset, or None to reset all
        """
        with self._lock:
            if section:
                if section in self.default_settings:
                    self.settings[section] = self.default_settings[section].copy()
                    self.logger.info(f"Reset settings section: {section}")
                else:
                    self.logger.warning(f"Unknown section to reset: {section}")
            else:
                self.settings = self.default_settings.copy()
                self.logger.info("Reset all settings to defaults")
            
            # Save the reset settings
            self._save_settings()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get a copy of all settings.
        
        Returns:
            Dictionary containing all settings
        """
        return self.settings.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a specific section of settings.
        
        Args:
            section: Section name to retrieve
            
        Returns:
            Dictionary containing the section settings
        """
        return self.settings.get(section, {}).copy()
    
    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        Update a specific section with new values.
        
        Args:
            section: Section name to update
            values: New values to set
            
        Returns:
            bool: True if successful
        """
        try:
            with self._lock:
                if section not in self.settings:
                    self.settings[section] = {}
                
                # Update values in the section
                for key, value in values.items():
                    self.settings[section][key] = value
                
                # Save settings
                self._save_settings()
                
                self.logger.debug(f"Updated section {section} with {len(values)} values")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating section {section}: {str(e)}", exc_info=True)
            return False
    
    def backup_settings(self, backup_path: str = None) -> bool:
        """
        Create a backup of current settings.
        
        Args:
            backup_path: Path for backup file, or None to use timestamped name
            
        Returns:
            bool: True if backup was successful
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"config/settings_backup_{timestamp}.json"
            
            # Ensure backup directory exists
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Settings backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error backing up settings: {str(e)}", exc_info=True)
            return False
    
    def restore_settings(self, backup_path: str) -> bool:
        """
        Restore settings from a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if restore was successful
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_settings = json.load(f)
            
            # Validate the backup settings
            if not isinstance(backup_settings, dict):
                raise ValueError("Backup file does not contain valid settings")
            
            # Apply the backup settings
            with self._lock:
                self.settings = backup_settings
                self._save_settings()
            
            self.logger.info(f"Settings restored from {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring settings from {backup_path}: {str(e)}", exc_info=True)
            return False
    
    def export_settings(self, export_path: str) -> bool:
        """
        Export settings to a file (without sensitive data).
        
        Args:
            export_path: Path to export file
            
        Returns:
            bool: True if export was successful
        """
        try:
            # Create a copy of settings without sensitive data
            export_settings = self.settings.copy()
            
            # Remove sensitive information
            if 'security' in export_settings:
                export_settings['security'] = export_settings['security'].copy()
                export_settings['security']['password_hash'] = ''
                export_settings['security']['password_salt'] = ''
                export_settings['security']['encrypted_api_keys'] = {}
            
            # Ensure export directory exists
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Settings exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting settings: {str(e)}", exc_info=True)
            return False
    
    def import_settings(self, import_path: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            bool: True if import was successful
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_settings = json.load(f)
            
            # Validate the import settings
            if not isinstance(import_settings, dict):
                raise ValueError("Import file does not contain valid settings")
            
            # Merge with current settings (preserve sensitive data)
            with self._lock:
                # Preserve sensitive information from current settings
                preserved_security = self.settings.get('security', {}).copy()
                
                # Update settings with imported values
                for section, values in import_settings.items():
                    if section == 'security':
                        # Merge security settings, preserving sensitive data
                        if 'security' not in self.settings:
                            self.settings['security'] = {}
                        
                        for key, value in values.items():
                            # Don't overwrite sensitive fields
                            if key not in ['password_hash', 'password_salt', 'encrypted_api_keys']:
                                self.settings['security'][key] = value
                        
                        # Restore sensitive fields
                        for key in ['password_hash', 'password_salt', 'encrypted_api_keys']:
                            if key in preserved_security:
                                self.settings['security'][key] = preserved_security[key]
                    else:
                        self.settings[section] = values
                
                self._save_settings()
            
            self.logger.info(f"Settings imported from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing settings from {import_path}: {str(e)}", exc_info=True)
            return False
    
    def get_settings_schema(self) -> Dict[str, Any]:
        """
        Get the schema for settings (for UI configuration).
        
        Returns:
            Dictionary describing the settings schema
        """
        return {
            "version": self.current_version,
            "schema": {
                "general": {
                    "type": "object",
                    "properties": {
                        "language": {"type": "string", "enum": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]},
                        "theme": {"type": "string", "enum": ["system", "light", "dark"]},
                        "auto_start": {"type": "boolean"},
                        "minimize_to_tray": {"type": "boolean"},
                        "check_updates": {"type": "boolean"}
                    }
                },
                "clipboard": {
                    "type": "object",
                    "properties": {
                        "max_history": {"type": "integer", "minimum": 1, "maximum": 10000},
                        "monitor_interval": {"type": "number", "minimum": 0.1, "maximum": 5.0},
                        "monitor_enabled": {"type": "boolean"},
                        "format_preservation": {"type": "boolean"}
                    }
                },
                "typing": {
                    "type": "object",
                    "properties": {
                        "default_speed": {"type": "string", "enum": ["fast_human", "very_fast", "machine"]},
                        "batch_size": {"type": "integer", "minimum": 1, "maximum": 100},
                        "interrupt_keys": {"type": "array", "items": {"type": "string"}},
                        "auto_correct": {"type": "boolean"}
                    }
                },
                "ai": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string", "enum": ["deepseek", "openai", "anthropic", "local"]},
                        "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
                        "max_tokens": {"type": "integer", "minimum": 100, "maximum": 4096},
                        "context_memory": {"type": "integer", "minimum": 1, "maximum": 50},
                        "system_prompt": {"type": "string"},
                        "type_response_after_processing": {"type": "boolean"}
                    }
                },
                "file_context": {
                    "type": "object",
                    "properties": {
                        "max_file_size_mb": {"type": "integer", "minimum": 1, "maximum": 100},
                        "max_total_size_mb": {"type": "integer", "minimum": 1, "maximum": 500},
                        "auto_cleanup_enabled": {"type": "boolean"},
                        "auto_cleanup_minutes": {"type": "integer", "minimum": 1, "maximum": 1440}
                    }
                },
                "telegram": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "bot_token": {"type": "string"},
                        "user_ids": {"type": "array", "items": {"type": "string"}},
                        "auto_copy_from_telegram": {"type": "boolean"},
                        "auto_type_responses": {"type": "boolean"},
                        "connection_method": {"type": "string", "enum": ["polling", "webhook"]}
                    }
                },
                "hotkeys": {
                    "type": "object",
                    "properties": {
                        "typing_trigger": {"type": "string"},
                        "ai_process_clipboard": {"type": "string"},
                        "paste_clipboard": {"type": "string"},
                        "toggle_monitoring": {"type": "string"},
                        "clear_history": {"type": "string"},
                        "show_history": {"type": "string"}
                    }
                },
                "security": {
                    "type": "object",
                    "properties": {
                        "password_protected": {"type": "boolean"},
                        "level": {"type": "string", "enum": ["safe", "moderate", "unrestricted"]},
                        "session_timeout_minutes": {"type": "integer", "minimum": 1, "maximum": 1440},
                        "content_filtering_enabled": {"type": "boolean"},
                        "max_password_attempts": {"type": "integer", "minimum": 1, "maximum": 20},
                        "password_attempt_window_seconds": {"type": "integer", "minimum": 60, "maximum": 3600}
                    }
                },
                "display": {
                    "type": "object",
                    "properties": {
                        "overlay_transparency": {"type": "number", "minimum": 0.1, "maximum": 1.0},
                        "overlay_position": {"type": "string", "enum": ["top_left", "top_right", "bottom_left", "bottom_right", "center"]},
                        "font_size": {"type": "integer", "minimum": 8, "maximum": 72},
                        "animation_enabled": {"type": "boolean"},
                        "notification_timeout": {"type": "integer", "minimum": 1, "maximum": 30}
                    }
                },
                "performance": {
                    "type": "object",
                    "properties": {
                        "thread_pool_size": {"type": "integer", "minimum": 1, "maximum": 16},
                        "cache_size": {"type": "integer", "minimum": 10, "maximum": 10000},
                        "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]}
                    }
                }
            }
        }
    
    def get_settings_status(self) -> Dict[str, Any]:
        """
        Get the status of settings management.
        
        Returns:
            Dictionary with settings status information
        """
        return {
            "version": self.settings.get("version", "unknown"),
            "config_file": self.config_file,
            "file_exists": os.path.exists(self.config_file),
            "sections_count": len(self.settings),
            "last_modified": os.path.getmtime(self.config_file) if os.path.exists(self.config_file) else None
        }