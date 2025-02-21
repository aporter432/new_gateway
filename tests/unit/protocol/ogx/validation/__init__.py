"""Unit tests for OGx protocol validation components.

This package contains comprehensive test suites for validating OGx protocol messages
according to OGx-1.txt specifications. The tests are organized into focused modules:

- test_field_validation_basic.py: Basic field type validation
- test_field_validation_array.py: Array field validation
- test_field_validation_message.py: Message field validation
- test_field_validation_dynamic.py: Dynamic field validation
- test_field_validation_edge.py: Edge cases and error handling

Each module uses common fixtures and utilities defined in this package.
"""

import pytest
from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.message.field_validator import OGxFieldValidator


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
