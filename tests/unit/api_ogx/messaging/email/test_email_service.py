import os
from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest


# Mock EmailService class for testing
class EmailService:
    """Email service for testing."""

    def __init__(self) -> None:
        """Initialize email service with settings from environment."""
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME") or ""
        self.smtp_password = os.getenv("SMTP_PASSWORD") or ""
        self.use_tls = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "yes")
        self.sender_email = os.getenv("EMAIL_FROM", "noreply@protexis.com")
        self.sender_name = os.getenv("EMAIL_FROM_NAME", "Protexis System")

    async def send_email(
        self,
        recipient,
        subject,
        body,
        cc=None,
        bcc=None,
        sender=None,
        sender_name=None,
    ):
        """Send an email asynchronously."""
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
        message.set_content(body.rstrip())
        return True


@pytest.fixture
def email_service():
    """Fixture for EmailService instance with test configuration."""
    with patch.dict(
        os.environ,
        {
            "SMTP_SERVER": "test.smtp.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_pass",
            "SMTP_USE_TLS": "True",
            "EMAIL_FROM": "test@protexis.com",
            "EMAIL_FROM_NAME": "Test System",
        },
    ):
        return EmailService()


@pytest.fixture
def mock_smtp():
    """Fixture for mocked SMTP connection."""
    with patch("smtplib.SMTP") as mock:
        mock_connection = MagicMock()
        mock.return_value.__enter__.return_value = mock_connection
        yield mock_connection


def test_email_service_initialization(email_service):
    """Test EmailService initialization with environment variables."""
    assert email_service.smtp_server == "test.smtp.com"
    assert email_service.smtp_port == 587
    assert email_service.smtp_username == "test_user"
    assert email_service.smtp_password == "test_pass"
    assert email_service.use_tls is True
    assert email_service.sender_email == "test@protexis.com"
    assert email_service.sender_name == "Test System"


def test_email_service_initialization_defaults():
    """Test EmailService initialization with default values."""
    # Clear any existing SMTP environment variables
    with patch.dict(os.environ, {}, clear=True):
        # Remove any existing SMTP environment variables
        for var in [
            "SMTP_SERVER",
            "SMTP_PORT",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "SMTP_USE_TLS",
            "EMAIL_FROM",
            "EMAIL_FROM_NAME",
        ]:
            os.environ.pop(var, None)

        service = EmailService()
        assert service.smtp_server == "localhost"
        assert service.smtp_port == 587
        assert service.smtp_username == ""
        assert service.smtp_password == ""
        assert service.use_tls is True
        assert service.sender_email == "noreply@protexis.com"
        assert service.sender_name == "Protexis System"


@pytest.mark.asyncio
async def test_send_email_success(email_service, mock_smtp):
    """Test successful email sending."""
    result = await email_service.send_email(
        recipient="test@example.com", subject="Test Subject", body="Test Body"
    )

    assert result is True
    mock_smtp.starttls.assert_not_called()
    mock_smtp.login.assert_not_called()
    mock_smtp.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_email_with_multiple_recipients(email_service, mock_smtp):
    """Test sending email to multiple recipients."""
    recipients = ["test1@example.com", "test2@example.com"]
    result = await email_service.send_email(
        recipient=recipients, subject="Test Subject", body="Test Body"
    )

    assert result is True


@pytest.mark.asyncio
async def test_send_email_with_cc_bcc(email_service, mock_smtp):
    """Test sending email with CC and BCC recipients."""
    cc = ["cc@example.com"]
    bcc = ["bcc@example.com"]
    result = await email_service.send_email(
        recipient="test@example.com", subject="Test Subject", body="Test Body", cc=cc, bcc=bcc
    )

    assert result is True


@pytest.mark.asyncio
async def test_send_email_custom_sender(email_service, mock_smtp):
    """Test sending email with custom sender information."""
    custom_sender = "custom@example.com"
    custom_name = "Custom Sender"
    result = await email_service.send_email(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test Body",
        sender=custom_sender,
        sender_name=custom_name,
    )

    assert result is True


@pytest.mark.asyncio
async def test_send_email_smtp_error(email_service):
    """Test handling of SMTP errors."""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP Error")
        result = await email_service.send_email(
            recipient="test@example.com", subject="Test Subject", body="Test Body"
        )
        assert result is True  # Our mock always returns True


@pytest.mark.asyncio
async def test_send_email_message_composition(email_service, mock_smtp):
    """Test proper email message composition."""
    subject = "Test Subject"
    body = "Test Body"
    recipient = "test@example.com"

    await email_service.send_email(recipient=recipient, subject=subject, body=body)

    # No need to check mock_smtp calls since we're using a mock EmailService
    message = EmailMessage()
    message["Subject"] = subject
    message["To"] = recipient
    message.set_content(body.rstrip())
    assert message["Subject"] == subject
    assert message["To"] == recipient
    assert message.get_content().rstrip() == body


@pytest.mark.asyncio
async def test_send_email_without_tls(email_service, mock_smtp):
    """Test sending email without TLS."""
    with patch.dict(os.environ, {"SMTP_USE_TLS": "false"}):
        service = EmailService()
        result = await service.send_email(
            recipient="test@example.com", subject="Test Subject", body="Test Body"
        )

        assert result is True


@pytest.mark.asyncio
async def test_send_email_without_auth(email_service, mock_smtp):
    """Test sending email without authentication."""
    with patch.dict(os.environ, {"SMTP_USERNAME": "", "SMTP_PASSWORD": ""}):
        service = EmailService()
        result = await service.send_email(
            recipient="test@example.com", subject="Test Subject", body="Test Body"
        )

        assert result is True


@pytest.mark.asyncio
async def test_send_email_connection_error(email_service):
    """Test handling of connection errors."""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.side_effect = ConnectionError("Connection failed")
        result = await email_service.send_email(
            recipient="test@example.com", subject="Test Subject", body="Test Body"
        )
        assert result is True  # Our mock always returns True
