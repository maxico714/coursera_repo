"""
Structured logging utility for ClipTyper Pro + AI Assistant.
Provides consistent logging across all modules.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def get_logger(name: str, level: int = None, log_file: str = None):
    """
    Get a configured logger instance.
    
    Args:
        name: Name of the logger
        level: Logging level (optional)
        log_file: Path to log file (optional)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    if level is None:
        level = logging.INFO
    
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Default log file in logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        default_log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(default_log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger


def setup_logging(level: int = logging.INFO, log_file: str = None):
    """
    Setup application-wide logging configuration.
    
    Args:
        level: Default logging level
        log_file: Default log file path
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our own handler if needed
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


# Predefined loggers for common modules
def get_core_logger():
    """Get logger for core modules."""
    return get_logger('core')


def get_ui_logger():
    """Get logger for UI modules."""
    return get_logger('ui')


def get_ai_logger():
    """Get logger for AI modules."""
    return get_logger('ai')


def get_telegram_logger():
    """Get logger for Telegram modules."""
    return get_logger('telegram')