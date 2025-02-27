"""Common clients for the API."""

from Protexis_Command.api.common.clients.email_service import EmailService, get_email_service

from .base import BaseAPIClient
from .factory import get_OGx_client

__all__ = ["BaseAPIClient", "get_OGx_client", "EmailService", "get_email_service"]
