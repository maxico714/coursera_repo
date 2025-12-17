"""
Structured logging utilities for ClipTyper Pro + AI Assistant.
Provides centralized logging with rotation and different output formats.
"""
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logger(name: str, log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Name of the logger
        log_file: Path to log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler (10MB max, keep 5 files)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance. If it doesn't exist, create one with default settings.
    
    Args:
        name: Name of the logger
        
    Returns:
        Logger instance
    """
    if not logging.getLogger(name).handlers:
        return setup_logger(name, f"logs/{name.lower()}.log")
    return logging.getLogger(name)


# Global application logger
app_logger = setup_logger('clip_typer_pro', 'logs/app.log', 'INFO')


def log_exception(logger: logging.Logger, msg: str = "An exception occurred"):
    """
    Log an exception with traceback.
    
    Args:
        logger: Logger instance to use
        msg: Message to log with the exception
    """
    logger.exception(msg)


def set_global_log_level(level: str):
    """
    Set the global log level for the application.
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    app_logger.setLevel(getattr(logging, level.upper()))
    
    # Also update all existing loggers
    for name in logging.Logger.manager.loggerDict:
        logging.getLogger(name).setLevel(getattr(logging, level.upper()))


def get_log_level() -> str:
    """
    Get the current global log level.
    
    Returns:
        Current log level as string
    """
    return logging.getLevelName(app_logger.level)


# Initialize logs directory
os.makedirs('logs', exist_ok=True)