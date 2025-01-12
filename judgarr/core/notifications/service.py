"""Notification service for managing multiple notification providers."""

import asyncio
from typing import Dict, List, Any
from . import NotificationProvider, NotificationType, BaseNotificationService

class NotificationService(BaseNotificationService):
    """Service for managing and sending notifications through multiple providers."""
    
    def __init__(self):
        """Initialize the notification service."""
        self._providers: List[NotificationProvider] = []
        
    def add_provider(self, provider: NotificationProvider) -> None:
        """Add a notification provider to the service.
        
        Args:
            provider: The notification provider to add
        """
        self._providers.append(provider)
        
    def remove_provider(self, provider: NotificationProvider) -> None:
        """Remove a notification provider from the service.
        
        Args:
            provider: The notification provider to remove
        """
        if provider in self._providers:
            self._providers.remove(provider)
            
    async def notify(self, notification_type: NotificationType, message: str, **kwargs: Dict[str, Any]) -> bool:
        """Send a notification through all registered providers.
        
        Args:
            notification_type: The type of notification
            message: The message to send
            **kwargs: Additional arguments for the notification providers
            
        Returns:
            bool: True if at least one provider successfully sent the notification
        """
        if not self._providers:
            return False
            
        # Add notification type to kwargs
        notification_kwargs = {**kwargs, 'notification_type': notification_type}
        
        # Try to send through all providers
        results = await asyncio.gather(
            *[provider.send(message, **notification_kwargs) for provider in self._providers],
            return_exceptions=True
        )
        
        # Return True if at least one provider succeeded
        return any(isinstance(result, bool) and result for result in results)
