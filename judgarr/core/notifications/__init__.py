"""
Core notification system for Judgarr.

This module provides the base notification interfaces and types used across
different notification providers.
"""

from typing import Protocol, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

class NotificationType(Enum):
    """Types of notifications that can be sent."""
    PUNISHMENT = "punishment"
    WARNING = "warning"
    RESET = "reset"
    SYSTEM = "system"

class NotificationProvider(Protocol):
    """Protocol defining the interface for notification providers."""
    
    async def send(self, message: str, **kwargs: Dict[str, Any]) -> bool:
        """Send a notification using this provider."""
        ...

class BaseNotificationService(ABC):
    """Base class for notification services."""
    
    @abstractmethod
    async def notify(self, notification_type: NotificationType, message: str, **kwargs: Dict[str, Any]) -> bool:
        """Send a notification."""
        pass
