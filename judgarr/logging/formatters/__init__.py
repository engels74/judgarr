"""Custom log formatters for Judgarr."""

import logging
from datetime import datetime
from typing import Optional

class JudgarrFormatter(logging.Formatter):
    """Custom formatter for Judgarr logs.
    
    Format example:
    2025-01-12 00:01:47 [INFO] [user.tracking] User X has requested 300GB of data in the last 30 days
    2025-01-12 00:01:48 [DEBUG] [api.overseerr] Fetching user data from Overseerr API
    """
    
    def __init__(self):
        """Initialize the formatter with a custom format."""
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Format the timestamp using UTC."""
        ct = datetime.fromtimestamp(record.created)
        s = ct.strftime(datefmt if datefmt is not None else "%Y-%m-%d %H:%M:%S")
        return s
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record.
        
        Ensures consistent formatting and adds any custom fields if needed.
        """
        # Create a copy of the record to avoid modifying the original
        record_dict = record.__dict__.copy()
        
        # Add user ID if available in extra fields
        msg = str(record_dict.get("msg", ""))
        user_id = record_dict.get("user_id")
        if user_id is not None:
            msg = f"[User {user_id}] {msg}"
            record_dict["msg"] = msg
        
        # Create a new record with our modifications
        modified_record = logging.makeLogRecord(record_dict)
        return super().format(modified_record)
