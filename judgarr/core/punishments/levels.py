"""Punishment level definitions."""

from enum import Enum

class PunishmentLevel(int, Enum):
    """Enumeration of punishment levels."""
    NONE = 0
    WARNING = 1
    MILD = 2
    SEVERE = 3
    MAXIMUM = 4
