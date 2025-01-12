"""
Common type definitions used across the Judgarr project.
"""
from enum import Enum
from typing import NewType

UserId = NewType('UserId', str)
DataSize = NewType('DataSize', int)  # Size in bytes

class PunishmentLevel(Enum):
    """Punishment severity levels"""
    WARNING = "warning"
    FIRST_OFFENSE = "first_offense"
    SECOND_OFFENSE = "second_offense"
    THIRD_OFFENSE = "third_offense"
