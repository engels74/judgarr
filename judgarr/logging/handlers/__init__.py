"""Custom log handlers for Judgarr."""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

class ConsoleHandler(logging.StreamHandler):
    """Handler for console output with color support."""
    
    COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    
    def emit(self, record):
        """Emit a colored record to the console."""
        try:
            msg = self.format(record)
            color = self.COLORS.get(record.levelno, self.RESET)
            stream = self.stream
            stream.write(f"{color}{msg}{self.RESET}\n")
            self.flush()
        except Exception:
            self.handleError(record)

class FileHandler(RotatingFileHandler):
    """Rotating file handler with size limits."""
    
    def __init__(self, filename: Path, max_bytes: int = 10_485_760, backup_count: int = 5):
        """Initialize the rotating file handler.
        
        Args:
            filename: Path to log file
            max_bytes: Maximum size of each log file (default: 10MB)
            backup_count: Number of backup files to keep (default: 5)
        """
        # Ensure parent directory exists
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(
            filename=str(filename),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
