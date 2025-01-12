"""Notification type definitions."""

from enum import Enum, auto

class NotificationType(Enum):
    """Types of notifications that can be sent."""
    
    PUNISHMENT = auto()
    USER_PUNISHED = PUNISHMENT  # Alias for consistency
    RESET = auto()
    USER_RESTORED = RESET  # Alias for consistency
    WARNING = auto()
    USER_WARNED = WARNING  # Alias for consistency
    SYSTEM = auto()
