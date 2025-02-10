"""Message validation module for OGWS-1.txt Section 5.

This module implements validation for the Common Message Format
as defined in Section 5 and Figure 10 of the OGWS specification.

Components:
- MessageValidator: Validates overall message structure
- FieldValidator: Validates field types per Table 3
- ElementValidator: Validates array element structures

Example:
    from protocols.ogx.validation.message import OGxMessageValidator

    validator = OGxMessageValidator()
    result = validator.validate(message_dict, context)
    if not result.is_valid:
        print(f"Validation errors: {result.errors}")
"""

from .element_validator import OGxElementValidator
from .field_validator import OGxFieldValidator
from .message_validator import OGxMessageValidator

__all__ = ["OGxMessageValidator", "OGxFieldValidator", "OGxElementValidator"]
