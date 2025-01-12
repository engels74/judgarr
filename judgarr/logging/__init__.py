"""Logging configuration for Judgarr."""

import logging
from pathlib import Path
from typing import Optional

from .formatters import JudgarrFormatter
from .handlers import FileHandler, ConsoleHandler

def setup_logging(log_path: Optional[Path] = None) -> None:
    """Set up logging configuration.
    
    Args:
        log_path: Optional path to log file. If not provided, logs will only go to console.
    """
    logger = logging.getLogger("judgarr")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    formatter = JudgarrFormatter()
    
    # Console handler (INFO and above)
    console_handler = ConsoleHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # File handler (DEBUG and above) if log path provided
    if log_path:
        file_handler = FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
