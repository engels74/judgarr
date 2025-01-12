"""SMTP email notification provider."""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from ..types import NotificationType
import aiosmtplib

class EmailNotifier:
    """SMTP email notifier."""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True
    ) -> None:
        """Initialize the email notifier.
        
        Args:
            host: SMTP server hostname
            port: SMTP server port
            username: SMTP authentication username
            password: SMTP authentication password
            from_email: Sender email address
            use_tls: Whether to use TLS (default: True)
        """
        self.smtp_host = host
        self.smtp_port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        notification_type: Optional[NotificationType] = None
    ) -> None:
        """Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            notification_type: Type of notification (default: None)
        """
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = str(self.from_email)
        msg['To'] = str(to_email)
        
        # Create HTML version of the message
        html_template = f"""
        <html>
            <body>
                <h2>{subject}</h2>
                <p>{body}</p>
                <hr>
                <small>Sent by Judgarr Notification System</small>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html_template, 'html'))
        
        try:
            smtp = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port, use_tls=self.use_tls)
            await smtp.connect()
            await smtp.login(self.username, self.password)
            await smtp.send_message(msg)
            await smtp.quit()
        except Exception as e:
            print(f"Error sending email: {e}")

    async def send(self, message: str, username: str, **kwargs) -> None:
        """Send a notification email.
        
        Args:
            message: Message content
            username: Username to notify
            **kwargs: Additional arguments
        """
        subject = kwargs.get('subject', 'Judgarr Notification')
        to_email = kwargs.get('email')
        
        if not to_email:
            raise ValueError("Email address required for email notifications")
            
        await self.send_email(
            to_email=to_email,
            subject=subject,
            body=message,
            notification_type=kwargs.get('notification_type')
        )
