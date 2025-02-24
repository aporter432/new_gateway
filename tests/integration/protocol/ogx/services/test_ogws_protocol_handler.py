"""Integration tests for OGx protocol handler.

This module tests the OGx protocol handler service.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from Protexis_Command.protocol.ogx.constants.ogx_message_types import MessageType
from Protexis_Command.protocol.ogx.constants.ogx_network_types import NetworkType
from Protexis_Command.protocol.ogx.constants.ogx_transport_types import TransportType
from Protexis_Command.protocol.ogx.ogx_protocol_handler import OGxProtocolHandler
from Protexis_Command.protocol.ogx.validation.common.validation_exceptions import (
    AuthenticationError,
    ProtocolError,
    RateLimitError,
    ValidationError,
)
from Protexis_Command.protocol.ogx.validation.validators.ogx_network_validator import (
    NetworkValidator,
)
from Protexis_Command.protocol.ogx.validation.validators.ogx_size_validator import SizeValidator
from Protexis_Command.protocol.ogx.validation.validators.ogx_transport_validator import (
    OGxTransportValidator,
)
from Protexis_Command.protocol.ogx.validation.validators.ogx_type_validator import (
    ValidationContext,
    ValidationResult,
)

# Mock core dependencies to avoid circular imports
with patch.dict(
    "sys.modules",
    {
        "core.app_settings": MagicMock(),
        "core.logging.loggers": MagicMock(),
        "infrastructure.redis": MagicMock(),
        "Protexis_Command.protocol.ogx.validation.validators.ogx_field_validator": MagicMock(),
        "Protexis_Command.protocol.ogx.validation.message.message_validator": MagicMock(),
    },
):
    # Class must be indented inside the with block
    class MockOGxHandler(OGxProtocolHandler):
        """Mock implementation of OGxProtocolHandler for testing.

        This class provides a concrete implementation of the abstract base class
        with configurable behavior for testing different scenarios.

        Attributes:
            mock_token (str): Token to return from authenticate
           mock_messages (List[Dict]): Messages to return from get_messages
           should_fail (bool): Whether operations should raise exceptions
            rate_limited (bool): Whether to simulate rate limiting
        """

        def __init__(
            self,
            mock_token: str = "test_token",
            mock_messages: Optional[List[Dict[str, Any]]] = None,
            should_fail: bool = False,
            rate_limited: bool = False,
        ):
            """Initialize mock handler with test configuration."""
            super().__init__()
            self.mock_token = mock_token
            self.mock_messages = mock_messages or []
            self.should_fail = should_fail
            self.rate_limited = rate_limited
            # Initialize validators
            self.size_validator = SizeValidator()
            self.network_validator = NetworkValidator()
            self.transport_validator = OGxTransportValidator()
            self.message_validator = MagicMock()

            # Check for required payload
            def validate_mock(message, context):
                if "RawPayload" not in message and "Payload" not in message:
                    raise ValidationError("Message must contain either RawPayload or Payload")
                return ValidationResult(True, [])

            self.message_validator.validate.side_effect = validate_mock

        def set_auth_state(
            self, is_authenticated: bool = True, token: Optional[str] = None
        ) -> None:
            """Set authentication state for testing.

            This method is only for testing purposes to avoid accessing protected members.
            """
            self._authenticated = is_authenticated
            self._bearer_token = token or self.mock_token if is_authenticated else None

        def update_metrics(self) -> None:
            """Update request metrics for testing.

            This method is only for testing purposes to avoid accessing protected members.
            """
            self._update_request_metrics()

        def validate_message(
            self, message: Dict[str, Any], context: ValidationContext
        ) -> ValidationResult:
            """Validate message for testing.

            This method is only for testing purposes to avoid accessing protected members.
            """
            return self._validate_message(message, context)

        @property
        def is_authenticated(self) -> bool:
            """Get authentication status."""
            return self._authenticated

        @property
        def bearer_token(self) -> Optional[str]:
            """Get bearer token."""
            return self._bearer_token

        @property
        def request_count(self) -> int:
            """Get request count."""
            return self._request_count

        @property
        def last_request_time(self) -> Optional[datetime]:
            """Get last request time."""
            return self._last_request_time

        async def authenticate(self, credentials: Dict[str, Any]) -> str:
            """Mock authentication implementation."""
            if self.should_fail:
                raise AuthenticationError("Mock auth failure")
            if self.rate_limited:
                raise RateLimitError("Mock rate limit")
            self.set_auth_state(True, self.mock_token)
            self.update_metrics()
            return self.mock_token

        async def submit_message(
            self,
            message: Dict[str, Any],
            destination_id: str,
            transport_type: Optional[TransportType] = None,
        ) -> tuple[str, ValidationResult]:
            """Mock message submission implementation."""
            if not self.is_authenticated:
                raise ProtocolError("Not authenticated")
            if self.should_fail:
                raise ProtocolError("Mock submission failure")
            if self.rate_limited:
                raise RateLimitError("Mock rate limit")
            self.update_metrics()
            return "mock_message_id", ValidationResult(True, [], None)

        async def get_messages(
            self, from_utc: datetime, message_type: MessageType
        ) -> List[Dict[str, Any]]:
            """Mock message retrieval implementation."""
            if not self.is_authenticated:
                raise ProtocolError("Not authenticated")
            if self.should_fail:
                raise ProtocolError("Mock retrieval failure")
            if self.rate_limited:
                raise RateLimitError("Mock rate limit")
            self.update_metrics()
            return self.mock_messages

        async def get_message_status(self, message_id: str) -> Dict[str, Any]:
            """Mock status check implementation."""
            if not self.is_authenticated:
                raise ProtocolError("Not authenticated")
            if self.should_fail:
                raise ProtocolError("Mock status check failure")
            if self.rate_limited:
                raise RateLimitError("Mock rate limit")
            self.update_metrics()
            return {"State": 1, "StatusUTC": datetime.utcnow().isoformat()}

        async def close(self) -> None:
            """Implement required close method."""
            # Empty implementation is fine, no pass needed


@pytest.mark.asyncio
class TestOGxProtocolHandlerAuthenticate:
    """Test suite for OGxProtocolHandler.authenticate method.

    Tests the authentication flow according to OGx-1.txt Section 3.1.
    """

    @pytest.fixture
    def handler(self) -> MockOGxHandler:
        """Create MockOGxHandler instance."""
        return MockOGxHandler()

    @pytest.fixture
    def authenticated_handler(self) -> MockOGxHandler:
        """Create authenticated MockOGxHandler instance."""
        handler = MockOGxHandler()
        handler.set_auth_state(True)
        return handler

    @pytest.fixture
    def mock_credentials(self) -> Dict[str, Any]:
        """Create valid test credentials."""
        return {
            "client_id": "7000001",
            "client_secret": "test_password",
            "expires_in": 3600,
        }

    async def test_successful_authentication(
        self, handler: MockOGxHandler, mock_credentials: Dict[str, Any]
    ):
        """Test successful authentication flow."""
        token = await handler.authenticate(mock_credentials)
        assert token == handler.mock_token
        assert handler.is_authenticated
        assert handler.bearer_token == token

    async def test_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        handler = MockOGxHandler(should_fail=True)
        with pytest.raises(AuthenticationError):
            await handler.authenticate({"client_id": "invalid"})
        assert not handler.is_authenticated
        assert handler.bearer_token is None

    async def test_rate_limited_authentication(self, mock_credentials: Dict[str, Any]):
        """Test authentication under rate limiting."""
        handler = MockOGxHandler(rate_limited=True)
        with pytest.raises(RateLimitError) as exc:
            await handler.authenticate(mock_credentials)
        assert "Mock rate limit" in str(exc.value)


@pytest.mark.asyncio
class TestOGxProtocolHandlerSubmitMessage:
    """Test suite for OGxProtocolHandler.submit_message method.

    Tests message submission according to OGx-1.txt Section 4.3.
    """

    @pytest.fixture
    def handler(self) -> MockOGxHandler:
        """Create authenticated MockOGxHandler instance."""
        handler = MockOGxHandler()
        handler.set_auth_state(True)
        return handler

    @pytest.fixture
    def valid_message(self) -> Dict[str, Any]:
        """Create valid test message."""
        return {
            "Payload": {
                "Name": "test_message",
                "SIN": 16,
                "MIN": 1,
                "Fields": [{"Name": "test_field", "Value": "test_value", "Type": "string"}],
            }
        }

    async def test_successful_submission(
        self,
        handler: MockOGxHandler,
        valid_message: Dict[str, Any],
    ):
        """Test successful message submission."""
        message_id, result = await handler.submit_message(valid_message, "test_destination")
        assert message_id == "mock_message_id"
        assert result.is_valid
        assert handler.request_count == 1

    async def test_unauthenticated_submission(self, valid_message: Dict[str, Any]):
        """Test submission without authentication."""
        handler = MockOGxHandler()
        with pytest.raises(ProtocolError):
            await handler.submit_message(valid_message, "test_destination")

    async def test_rate_limited_submission(
        self, handler: MockOGxHandler, valid_message: Dict[str, Any]
    ):
        """Test submission under rate limiting."""
        handler.rate_limited = True
        with pytest.raises(RateLimitError):
            await handler.submit_message(valid_message, "test_destination")


@pytest.mark.asyncio
class TestOGxProtocolHandlerGetMessages:
    """Test suite for OGxProtocolHandler.get_messages method.

    Tests message retrieval according to OGx-1.txt Section 4.4.
    """

    @pytest.fixture
    def handler(self) -> MockOGxHandler:
        """Create authenticated MockOGxHandler instance."""
        handler = MockOGxHandler()
        handler.set_auth_state(True)
        return handler

    async def test_successful_retrieval(self, handler: MockOGxHandler):
        """Test successful message retrieval."""
        from_time = datetime.utcnow() - timedelta(hours=1)
        messages = await handler.get_messages(from_time, MessageType.RETURN)
        assert isinstance(messages, list)
        assert handler.request_count == 1

    async def test_unauthenticated_retrieval(self):
        """Test retrieval without authentication."""
        handler = MockOGxHandler()
        from_time = datetime.utcnow() - timedelta(hours=1)
        with pytest.raises(ProtocolError):
            await handler.get_messages(from_time, MessageType.RETURN)

    async def test_rate_limited_retrieval(self, handler: MockOGxHandler):
        """Test retrieval under rate limiting."""
        handler.rate_limited = True
        from_time = datetime.utcnow() - timedelta(hours=1)
        with pytest.raises(RateLimitError):
            await handler.get_messages(from_time, MessageType.RETURN)


@pytest.mark.asyncio
class TestOGxProtocolHandlerGetMessageStatus:
    """Test suite for OGxProtocolHandler.get_message_status method.

    Tests message status checking according to OGx-1.txt Section 4.4.2.
    """

    @pytest.fixture
    def handler(self) -> MockOGxHandler:
        """Create authenticated MockOGxHandler instance."""
        handler = MockOGxHandler()
        handler.set_auth_state(True)
        return handler

    async def test_successful_status_check(self, handler: MockOGxHandler):
        """Test successful status check."""
        status = await handler.get_message_status("test_message_id")
        assert status["State"] == 1
        assert "StatusUTC" in status
        assert handler.request_count == 1

    async def test_unauthenticated_status_check(self):
        """Test status check without authentication."""
        handler = MockOGxHandler()
        with pytest.raises(ProtocolError):
            await handler.get_message_status("test_message_id")

    async def test_rate_limited_status_check(self, handler: MockOGxHandler):
        """Test status check under rate limiting."""
        handler.rate_limited = True
        with pytest.raises(RateLimitError):
            await handler.get_message_status("test_message_id")


class TestOGxProtocolHandlerValidateMessage:
    """Test suite for OGxProtocolHandler._validate_message method.

    Tests message validation according to OGx-1.txt Section 5.
    """

    @pytest.fixture
    def handler(self) -> MockOGxHandler:
        """Create MockOGxHandler instance."""
        return MockOGxHandler()

    @pytest.fixture
    def valid_message(self) -> Dict[str, Any]:
        """Create valid test message."""
        return {
            "Payload": {
                "Name": "test_message",
                "SIN": 16,
                "MIN": 1,
                "Fields": [{"Name": "test_field", "Value": "test_value", "Type": "string"}],
            }
        }

    @pytest.fixture
    def mock_context(self) -> ValidationContext:
        """Create ValidationContext for testing."""
        return ValidationContext(
            direction=MessageType.FORWARD,
            network_type=NetworkType.OGX,  # Use NetworkType enum instead of string
        )

    def test_validation_pipeline(
        self,
        handler: MockOGxHandler,
        valid_message: Dict[str, Any],
        mock_context: ValidationContext,
    ):
        """Test complete validation pipeline."""
        result = handler.validate_message(valid_message, mock_context)
        assert isinstance(result, ValidationResult)
        assert hasattr(result, "is_valid")
        assert hasattr(result, "errors")

    def test_size_validation(self, handler: MockOGxHandler, mock_context: ValidationContext):
        """Test message size validation.

        Tests that messages exceeding the raw binary payload limit (1023 bytes)
        are rejected, regardless of their Base64-encoded size.
        """
        # Create a raw binary payload that exceeds 1023 bytes
        raw_payload = "x" * 1024  # 1024 bytes of raw data
        large_message = {
            "RawPayload": raw_payload,  # This will be larger when Base64-encoded
            "DestinationID": "test_destination",
            "Network": "OGX",  # Use correct key name
        }
        result = handler.validate_message(large_message, mock_context)
        assert not result.is_valid
        assert "Raw payload size 1024 bytes exceeds maximum of 1023 bytes" in result.errors[0]
        assert result.current_size == 1024
        assert result.max_size == 1023

    def test_base64_size_validation(self, handler: MockOGxHandler, mock_context: ValidationContext):
        """Test that Base64 encoding overhead doesn't affect size validation.

        A payload of exactly 1023 bytes should pass validation, even though
        its Base64-encoded form will be larger.
        """
        # Create a raw binary payload at the size limit
        raw_payload = "x" * 1023  # Exactly 1023 bytes
        valid_message = {
            "RawPayload": raw_payload,
            "DestinationID": "test_destination",
            "Network": NetworkType.OGX,  # Use enum instead of string
        }
        result = handler.validate_message(valid_message, mock_context)
        assert result.is_valid, "Message at size limit should be valid"

    def test_invalid_payload_type(self, handler: MockOGxHandler, mock_context: ValidationContext):
        """Test validation with invalid payload type."""
        invalid_message = {
            "RawPayload": 123,  # Should be string
            "Network": "OGX",
        }
        result = handler.validate_message(invalid_message, mock_context)
        assert not result.is_valid
        assert "RawPayload must be a string" in result.errors[0]

    def test_missing_payload(self, handler: MockOGxHandler, mock_context: ValidationContext):
        """Test validation with missing payload."""
        # The message is missing both RawPayload and Payload
        invalid_message = {
            "Network": NetworkType.OGX,
            "DestinationID": "test_destination",
        }
        # Should return invalid result with specific message
        result = handler.validate_message(invalid_message, mock_context)
        assert not result.is_valid
        assert "Message must contain either RawPayload or Payload" in result.errors[0]

    def test_invalid_json_payload(self, handler: MockOGxHandler, mock_context: ValidationContext):
        """Test validation with invalid JSON payload."""
        invalid_message = {
            "Payload": "not a dict",  # Should be a dictionary
            "Network": "OGX",
        }
        result = handler.validate_message(invalid_message, mock_context)
        assert not result.is_valid
        assert "Payload must be a JSON object" in result.errors[0]

    def test_transport_validation(self, handler: MockOGxHandler, mock_context: ValidationContext):
        """Test transport validation."""
        # Test valid transport
        valid_message = {
            "RawPayload": "test",
            "Network": NetworkType.OGX,  # Use enum
            "Transport": "satellite",
        }
        result = handler.validate_message(valid_message, mock_context)
        assert result.is_valid

        # Test invalid transport
        invalid_message = {
            "RawPayload": "test",
            "Network": NetworkType.OGX,  # Use enum
            "Transport": ["invalid_transport"],  # Invalid transport type
        }
        result = handler.validate_message(invalid_message, mock_context)
        assert not result.is_valid
        assert any("Invalid transport type" in error for error in result.errors)

    def test_network_validation(self, handler: MockOGxHandler, mock_context: ValidationContext):
        """Test network validation."""
        # Test valid network
        valid_message = {
            "RawPayload": "test",
            "Network": NetworkType.OGX,  # Use enum for valid case
        }
        result = handler.validate_message(valid_message, mock_context)
        assert result.is_valid

        # Test invalid network
        invalid_message = {
            "RawPayload": "test",
            "Network": "OGX",  # Use string to test invalid case
        }
        result = handler.validate_message(invalid_message, mock_context)
        assert not result.is_valid
        assert any("Invalid network type" in error for error in result.errors)

    def test_validation_with_none_context(self, handler: MockOGxHandler):
        """Test validation with None context."""
        message = {
            "RawPayload": "test",
            "Network": "OGX",
        }
        result = handler.validate_message(message, None)  # type: ignore
        assert not result.is_valid
        assert any("Missing message direction" in error for error in result.errors)

    def test_size_validation_result(self, handler: MockOGxHandler, mock_context: ValidationContext):
        """Test that size validation failures are properly propagated.

        This test ensures that when size validation fails, the result is returned
        directly without proceeding to network validation.
        """
        # Mock both validators
        handler.size_validator = MagicMock()
        handler.network_validator = MagicMock()

        # Configure size validator to return invalid result
        size_result = ValidationResult(
            is_valid=False, errors=["Mock size validation error"], context=mock_context
        )
        handler.size_validator.validate.return_value = size_result

        # Test message doesn't matter since we're mocking the validator
        message = {
            "RawPayload": "test",
            "Network": "OGX",
        }

        # Validate message
        result = handler.validate_message(message, mock_context)

        # Verify result matches size validator result
        assert result == size_result
        assert not result.is_valid
        assert "Mock size validation error" in result.errors[0]

        # Verify network validation was not called
        handler.network_validator.validate.assert_not_called()


class TestOGxProtocolHandlerRateLimit:
    """Test suite for OGxProtocolHandler rate limiting methods.

    Tests rate limiting according to OGx-1.txt Section 3.4.
    """

    @pytest.fixture
    def handler(self) -> MockOGxHandler:
        """Create MockOGxHandler instance."""
        return MockOGxHandler()

    def test_request_metrics_update(self, handler: MockOGxHandler):
        """Test request metrics tracking."""
        initial_count = handler.request_count
        handler.update_metrics()
        assert handler.request_count == initial_count + 1
        assert handler.last_request_time is not None

    def test_concurrent_request_tracking(self, handler: MockOGxHandler):
        """Test concurrent request tracking."""
        for _ in range(5):
            handler.update_metrics()
        assert handler.request_count == 5
        assert handler.last_request_time is not None
