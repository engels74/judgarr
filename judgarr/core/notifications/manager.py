"""Notification manager for handling all notification types."""

from typing import Optional
from ...config import Config, load_config
from .discord.provider import DiscordNotifier
from .smtp.provider import EmailNotifier
from .types import NotificationType

class NotificationManager:
    """Manages sending notifications through configured providers."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize the notification manager.
        
        Args:
            config: Configuration object, loads from file if not provided
        """
        self.config = config or load_config()
        self.discord_notifier: Optional[DiscordNotifier] = None
        self.email_notifier: Optional[EmailNotifier] = None

        # Initialize enabled providers
        if self.config.notifications.discord:
            self.discord_notifier = DiscordNotifier(
                webhook_url=self.config.notifications.discord.webhook_url
            )
        if self.config.notifications.email:
            email_config = self.config.notifications.email.smtp
            if email_config:
                self.email_notifier = EmailNotifier(
                    host=email_config.host,
                    port=email_config.port,
                    username=email_config.username,
                    password=email_config.password,
                    from_email=email_config.from_address,
                    use_tls=email_config.use_tls
                )

    async def send(
        self,
        notification_type: NotificationType,
        message: str,
        recipient: str,
        **kwargs
    ) -> None:
        """Send a notification through configured providers.
        
        Args:
            notification_type: Type of notification
            message: Notification message
            recipient: User to notify
            **kwargs: Additional provider-specific arguments
        """
        if self.discord_notifier and notification_type in (
            NotificationType.USER_PUNISHED,
            NotificationType.USER_WARNED,
            NotificationType.USER_RESTORED
        ):
            await self.discord_notifier.send_message(
                message=message,
                username=recipient,
                notification_type=notification_type
            )
            
        if self.email_notifier:
            await self.email_notifier.send(message, recipient, **kwargs)

    async def notify_punishment(
        self,
        recipient: str,
        cooldown_days: Optional[int] = None,
        request_limit: Optional[int] = None,
        reason: Optional[str] = None,
        **kwargs
    ) -> None:
        """Send a punishment notification.
        
        Args:
            recipient: User being punished
            cooldown_days: Days until punishment expires
            request_limit: New request limit
            reason: Reason for punishment
        """
        message = self._format_punishment_message(
            recipient=recipient,
            cooldown_days=cooldown_days,
            request_limit=request_limit,
            reason=reason
        )
        await self.send(
            notification_type=NotificationType.PUNISHMENT,
            message=message,
            recipient=recipient,
            **kwargs
        )

    async def notify_reset(self, recipient: str, reason: Optional[str] = None) -> None:
        """Send a notification about a punishment reset.
        
        Args:
            recipient: User who had punishment reset
            reason: Optional reason for the reset
        """
        message = f"Your punishment has been reset{f' - {reason}' if reason else ''}"
        await self.send(
            notification_type=NotificationType.RESET,
            message=message,
            recipient=recipient
        )

    def _format_punishment_message(self, recipient: str, cooldown_days: Optional[int],
                                 request_limit: Optional[int], reason: Optional[str]) -> str:
        """Format punishment notification message.
        
        Args:
            recipient: User who was punished
            cooldown_days: New cooldown days
            request_limit: New request limit
            reason: Reason for punishment
            
        Returns:
            str: Formatted message
        """
        message = []
        message.append(f"Punishment applied to {recipient}")
        
        if cooldown_days is not None:
            message.append(f"• Cooldown period: {cooldown_days} days")
        if request_limit is not None:
            message.append(f"• Request limit: {request_limit}")
        if reason:
            message.append(f"\nReason: {reason}")

        return "\n".join(message)

    def _format_reset_message(self, recipient: str, reason: Optional[str]) -> str:
        """Format reset notification message.
        
        Args:
            recipient: User whose punishment was reset
            reason: Reason for reset
            
        Returns:
            str: Formatted message
        """
        message = [f"Punishment reset for {recipient}"]
        if reason:
            message.append(f"\nReason: {reason}")
        return "\n".join(message)
