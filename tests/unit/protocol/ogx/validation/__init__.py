"""Test initialization for OGx validation."""

from Protexis_Command.protocols.ogx.constants.ogx_message_types import MessageType
from Protexis_Command.protocols.ogx.validation.validators.ogx_field_validator import (
    OGxFieldValidator,
)
from Protexis_Command.protocols.ogx.validation.validators.ogx_type_validator import (
    ValidationContext,
)

__all__ = ["MessageType", "ValidationContext", "OGxFieldValidator"]

import pytest


@pytest.fixture
def field_validator():
    """Provides an instance of OGxFieldValidator for testing."""
    return OGxFieldValidator()


@pytest.fixture
def validation_context():
    """Provides a ValidationContext instance with standard settings.

    Returns:
        ValidationContext: Context configured with OGx network type and FORWARD direction
    """
    return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)
