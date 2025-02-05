"""
MTBP field validation according to N210 IGWS2 specification section 3.2
"""

from typing import Any

from ...constants.field_types import FieldType
from ...models.fields import Field
from ..exceptions import ParseError


class MTBPFieldValidator:
    """Validates MTBP fields according to N210 section 3.2"""

    MAX_FIELD_LENGTH = 0xFFFF  # 2 bytes max

    def validate(self, field: Field) -> None:
        """
        Validate complete field structure and content.

        Args:
            field: The field to validate

        Raises:
            ParseError: If field is invalid according to N210 spec
        """
        # Validate field type (1 byte)
        self._validate_field_type(field.field_type)

        # Validate field length (2 bytes)
        self._validate_field_length(field.value)

        # Validate field value matches type
        self._validate_field_value(field.field_type, field.value)

    def _validate_field_type(self, field_type: FieldType) -> None:
        """
        Validate field type according to N210 section 3.2.

        Args:
            field_type: The field type to validate

        Raises:
            ParseError: If field type is invalid
        """
        if not isinstance(field_type, FieldType):
            raise ParseError(f"Invalid field type: {field_type}", ParseError.INVALID_FIELD_TYPE)

    def _validate_field_length(self, value: Any) -> None:
        """
        Validate field length according to N210 section 3.2.

        Args:
            value: The field value to check length of

        Raises:
            ParseError: If field length is invalid
        """
        # Convert value to bytes for length check
        if isinstance(value, str):
            value_bytes = value.encode("utf-8")
        elif isinstance(value, bytes):
            value_bytes = value
        elif isinstance(value, bool):
            value_bytes = bytes([1]) if value else bytes([0])
        elif isinstance(value, int):
            value_bytes = value.to_bytes((value.bit_length() + 7) // 8, byteorder="big")
        else:
            value_bytes = str(value).encode("utf-8")

        if len(value_bytes) > self.MAX_FIELD_LENGTH:
            raise ParseError(
                f"Field length {len(value_bytes)} exceeds maximum {self.MAX_FIELD_LENGTH}",
                ParseError.INVALID_SIZE,
            )

    def _validate_field_value(self, field_type: FieldType, value: Any) -> None:
        """
        Validate field value matches its type according to N210 section 3.2.

        Args:
            field_type: The field's type
            value: The value to validate

        Raises:
            ParseError: If value is invalid for the field type
        """
        if value is None:
            raise ParseError("Field value cannot be None", ParseError.MISSING_FIELD)

        try:
            if field_type == FieldType.STRING:
                if not isinstance(value, str):
                    raise ParseError(
                        "String field must have str value", ParseError.INVALID_FIELD_VALUE
                    )

            elif field_type == FieldType.BOOLEAN:
                if not isinstance(value, bool):
                    raise ParseError(
                        "Boolean field must have bool value", ParseError.INVALID_FIELD_VALUE
                    )

            elif field_type in (FieldType.UINT, FieldType.INT, FieldType.ENUM):
                if not isinstance(value, int):
                    raise ParseError(
                        f"{field_type.name} field must have int value",
                        ParseError.INVALID_FIELD_VALUE,
                    )
                if field_type == FieldType.UINT and value < 0:
                    raise ParseError(
                        "UINT field cannot be negative", ParseError.INVALID_FIELD_VALUE
                    )

            elif field_type == FieldType.DATA:
                if not isinstance(value, bytes):
                    raise ParseError(
                        "Data field must have bytes value", ParseError.INVALID_FIELD_VALUE
                    )

            elif field_type == FieldType.ARRAY:
                if not isinstance(value, list):
                    raise ParseError(
                        "Array field must have list value", ParseError.INVALID_FIELD_VALUE
                    )

            elif field_type == FieldType.MESSAGE:
                if not isinstance(value, dict):
                    raise ParseError(
                        "Message field must have dict value", ParseError.INVALID_FIELD_VALUE
                    )

        except ParseError:
            raise
        except Exception as e:
            raise ParseError(
                f"Field validation failed: {str(e)}", ParseError.VALIDATION_FAILED
            ) from e
