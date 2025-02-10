"""Common validation types as defined in OGWS-1.txt Section 5.1.

This module defines the core validation types and structures used across
the validation system, based on the Common Message Format specification.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Union

from ...constants.field_types import FieldType
from ...constants.message_types import MessageType


class ValidationType(Enum):
    """Types of validation to perform based on OGWS-1.txt Section 5."""

    FIELD = auto()  # Field-level validation
    MESSAGE = auto()  # Message structure validation
    PAYLOAD = auto()  # Raw payload validation
    PROTOCOL = auto()  # Protocol-level validation
    SIZE = auto()  # Message size validation


@dataclass
class ValidationContext:
    """Context for validation operations from OGWS-1.txt Section 5.1."""

    network_type: str
    direction: MessageType
    transport_type: Optional[int] = None
    field_types: Optional[Dict[str, FieldType]] = None
    size_limit: Optional[int] = None
    is_array: bool = False


@dataclass
class ValidationResult:
    """Result of validation operations."""

    is_valid: bool
    errors: List[str]
    context: Optional[ValidationContext] = None
    details: Optional[Dict[str, Union[str, int]]] = None
