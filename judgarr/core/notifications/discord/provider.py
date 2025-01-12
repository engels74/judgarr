"""Discord notification provider."""

from ..types import NotificationType

class DiscordNotifier:
    """Discord webhook notifier."""
    
    def __init__(self, webhook_url: str) -> None:
        """Initialize the Discord notifier.
        
        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url
    
    async def send_message(
        self,
        message: str,
        username: str,
        notification_type: NotificationType
    ) -> None:
        """Send a message to Discord.
        
        Args:
            message: Message to send
            username: User the message is about
            notification_type: Type of notification
        """
        # TODO: Implement Discord webhook sending
        pass
