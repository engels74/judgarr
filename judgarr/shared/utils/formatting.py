"""Utility functions for formatting data."""

from ..constants import GB, TB

def format_size(size_bytes: int) -> str:
    """Format a size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string (e.g., '1.5 GB', '2.3 TB')
    """
    if size_bytes >= TB:
        return f"{size_bytes / TB:.1f} TB"
    elif size_bytes >= GB:
        return f"{size_bytes / GB:.1f} GB"
    else:
        return f"{size_bytes} B"
