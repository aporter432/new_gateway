"""Field types as defined in OGWS-1.txt.

This module defines the supported field types for messages:
- Basic types (string, boolean, integers)
- Complex types (enum, array, message)
- Special types (data, dynamic, property)

Each field type has specific:
- Encoding/decoding rules
- Validation requirements
- Value constraints
- Usage patterns

Usage:
    from protocols.ogx.constants import FieldType

    # Validate field value based on type
    def validate_field_value(field_type: FieldType, value: Any) -> None:
        if field_type == FieldType.STRING:
            if not isinstance(value, str):
                raise ValidationError("String value required")
        elif field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool) and value not in ("0", "1", "True", "False"):
                raise ValidationError("Boolean value required")
        elif field_type == FieldType.UNSIGNED_INT:
            try:
                val = int(value)
                if val < 0:
                    raise ValidationError("Non-negative integer required")
            except (ValueError, TypeError):
                raise ValidationError("Integer value required")

    # Create field with type-specific validation
    def create_field(name: str, type: FieldType, value: Any) -> dict:
        validate_field_value(type, value)
        return {
            "Name": name,
            "Type": type,
            "Value": value
        }

    # Check if type supports arrays
    def supports_array(field_type: FieldType) -> bool:
        return field_type in (
            FieldType.STRING,
            FieldType.UNSIGNED_INT,
            FieldType.SIGNED_INT,
            FieldType.ENUM
        )

Implementation Notes:
    - All values must match their declared type
    - String values are UTF-8 encoded
    - Integer ranges are enforced
    - Enum values must be predefined
    - Arrays have element-level validation
    - Dynamic types resolved at runtime
    - Property fields require type attribute
    - Binary data must be base64 encoded
    - Message types support nesting
"""

from enum import Enum


class FieldType(str, Enum):
    """Field types for message fields.

    Defines the allowed data types and their validation rules:
    - STRING: Text data, UTF-8 encoded
    - BOOLEAN: True/False values ("True"/"False" or "1"/"0")
    - UNSIGNED_INT: Non-negative integers (0 to 2^32-1)
    - SIGNED_INT: Integers including negatives (-2^31 to 2^31-1)
    - ENUM: Enumerated values from a predefined set
    - DATA: Binary/raw data (Base64 encoded)
    - ARRAY: Sequence of elements
    - MESSAGE: Nested message structure
    - DYNAMIC: Type determined at runtime
    - PROPERTY: Configuration property field

    Usage:
        # Validate field value
        def validate_value(field_type: FieldType, value: Any) -> None:
            validators = {
                FieldType.STRING: validate_string,
                FieldType.BOOLEAN: validate_boolean,
                FieldType.UNSIGNED_INT: validate_unsigned,
                FieldType.SIGNED_INT: validate_signed,
                FieldType.ENUM: validate_enum,
                FieldType.DATA: validate_data,
                FieldType.ARRAY: validate_array,
                FieldType.MESSAGE: validate_message,
                FieldType.DYNAMIC: validate_dynamic,
                FieldType.PROPERTY: validate_property
            }
            validator = validators.get(field_type)
            if validator:
                validator(value)

        # Get type constraints
        def get_type_constraints(field_type: FieldType) -> dict:
            constraints = {
                FieldType.STRING: {"encoding": "UTF-8"},
                FieldType.UNSIGNED_INT: {"min": 0, "max": 2**32-1},
                FieldType.SIGNED_INT: {"min": -2**31, "max": 2**31-1},
                FieldType.DATA: {"encoding": "base64"},
                FieldType.ARRAY: {"max_elements": 100}
            }
            return constraints.get(field_type, {})

        # Check if type needs special handling
        def needs_special_handling(field_type: FieldType) -> bool:
            return field_type in (
                FieldType.DYNAMIC,
                FieldType.PROPERTY,
                FieldType.MESSAGE
            )

    Implementation Notes:
        - STRING: Must be valid UTF-8 text
        - BOOLEAN: Accepts "True"/"False" or "1"/"0"
        - UNSIGNED_INT: 0 to 4,294,967,295
        - SIGNED_INT: -2,147,483,648 to 2,147,483,647
        - ENUM: Must match predefined values
        - DATA: Must be valid base64 string
        - ARRAY: Contains sequence of elements
        - MESSAGE: Contains nested message structure
        - DYNAMIC: Runtime type resolution
        - PROPERTY: Requires type attribute
        - Type validation is strict
        - No implicit type conversion
        - Case sensitivity varies by type
        - Some types have size limits
        - Array types support indexing
        - Message types support nesting
    """

    STRING = "string"  # Text data
    BOOLEAN = "boolean"  # True/False values
    UNSIGNED_INT = "unsignedint"  # Non-negative integers
    SIGNED_INT = "signedint"  # Integers including negatives
    ENUM = "enum"  # Enumerated values
    DATA = "data"  # Binary/raw data
    ARRAY = "array"  # Sequence of elements
    MESSAGE = "message"  # Nested message
    DYNAMIC = "dynamic"  # Runtime type
    PROPERTY = "property"  # Configuration property
