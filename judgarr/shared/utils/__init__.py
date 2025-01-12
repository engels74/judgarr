"""
Shared utility functions.
"""
from datetime import datetime, timedelta

from ..types import PunishmentLevel


def calculate_rolling_window(days: int) -> tuple[datetime, datetime]:
    """Calculate start and end dates for a rolling window."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def format_size(size: int) -> str:
    """Format byte size to human readable format."""
    size_float = float(size)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_float < 1024 or unit == 'TB':
            return f"{size_float:.2f} {unit}"
        size_float /= 1024
    return f"{size_float:.2f} TB"  # Fallback return for extremely large sizes


def get_punishment_severity(current_level: PunishmentLevel) -> PunishmentLevel:
    """Get next punishment level based on current level."""
    levels = list(PunishmentLevel)
    current_index = levels.index(current_level)
    next_index = min(current_index + 1, len(levels) - 1)
    return levels[next_index]
