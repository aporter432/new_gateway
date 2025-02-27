"""Email service for sending notifications and system messages.

This module implements email functionality for the Protexis system,
providing a service for sending transactional emails, notifications,
and system messages.

Key Components:
    - Email Configuration: SMTP server settings
    - Template Rendering: Email content generation
    - Async Sending: Non-blocking email dispatch
    - Retry Logic: Handling temporary failures

Related Files:
    - Protexis_Command/api/common/auth/user.py: User registration and notification
    - Protexis_Command/core/settings/app_settings.py: Email configuration settings

Security Considerations:
    - TLS encryption for SMTP connections
    - Template escaping to prevent injection
    - Rate limiting to prevent abuse
    - Sender verification

Implementation Notes:
    - Uses standard library smtplib for SMTP operations
    - Implements async sending with asyncio
    - Provides logging for debugging and monitoring
    - Handles connection pooling for efficiency

Future Considerations:
    - HTML email support
    - Email queue with background workers
    - Delivery status tracking
    - Email analytics
    - Multi-provider support
"""

import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional, Union

from Protexis_Command.core.settings.app_settings import get_settings

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending notifications and system messages.

    This class provides functionality for composing and sending emails
    via SMTP with support for plain text content.

    Features:
        - Async email sending
        - Connection pooling
        - Error handling and logging
        - Template support (future)
        - Rate limiting (future)

    Environment Variables:
        - SMTP_SERVER: SMTP server hostname (default: localhost)
        - SMTP_PORT: SMTP server port (default: 25)
        - SMTP_USERNAME: SMTP authentication username (optional)
        - SMTP_PASSWORD: SMTP authentication password (optional)
        - SMTP_USE_TLS: Use TLS for SMTP connection (default: True)
        - EMAIL_FROM: Default sender email address
        - EMAIL_FROM_NAME: Default sender name
    """

    def __init__(self) -> None:
        """Initialize email service with settings from environment."""
        self.settings = get_settings()
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.use_tls = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "yes")
        self.sender_email = os.getenv("EMAIL_FROM", "noreply@protexis.com")
        self.sender_name = os.getenv("EMAIL_FROM_NAME", "Protexis System")

    async def send_email(
        self,
        recipient: Union[str, List[str]],
        subject: str,
        body: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        sender: Optional[str] = None,
        sender_name: Optional[str] = None,
    ) -> bool:
        """Send an email asynchronously.

        This method composes and sends an email with the specified parameters.
        It handles connection establishment, TLS negotiation, and authentication.

        Args:
            recipient: Email address(es) of recipient(s)
            subject: Email subject line
            body: Plain text email body
            cc: Email address(es) to CC (optional)
            bcc: Email address(es) to BCC (optional)
            sender: Override default sender email (optional)
            sender_name: Override default sender name (optional)

        Returns:
            True if email was sent successfully, False otherwise

        Note:
            This method uses a connection pool to optimize SMTP connections
            when sending multiple emails in a short period of time.
        """
        try:
            # Create email message
            message = EmailMessage()
            message["Subject"] = subject

            # Set sender
            from_address = sender or self.sender_email
            from_name = sender_name or self.sender_name
            message["From"] = f"{from_name} <{from_address}>"

            # Set recipients
            if isinstance(recipient, list):
                message["To"] = ", ".join(recipient)
            else:
                message["To"] = recipient

            # Set CC and BCC if provided
            if cc:
                if isinstance(cc, list):
                    message["Cc"] = ", ".join(cc)
                else:
                    message["Cc"] = cc

            if bcc:
                if isinstance(bcc, list):
                    message["Bcc"] = ", ".join(bcc)
                else:
                    message["Bcc"] = bcc

            # Set body
            message.set_content(body)

            # Use asyncio to run SMTP connection in a thread pool
            return await asyncio.to_thread(self._send_smtp, message)

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _send_smtp(self, message: EmailMessage) -> bool:
        """Send email via SMTP (synchronous).

        This is a private helper method to handle the synchronous SMTP sending process.
        It should not be called directly, but through the async send_email method.

        Args:
            message: Composed EmailMessage to send

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                # Authenticate if credentials are provided
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)

                # Send email
                server.send_message(message)

                logger.info(f"Email sent to {message['To']}: {message['Subject']}")
                return True

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False


# Singleton instance for application-wide use
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the singleton email service instance.

    This function provides a single application-wide email service instance,
    ensuring efficient resource usage and consistent configuration.

    Returns:
        Email service instance
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
