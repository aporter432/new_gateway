"""
MTBP array element implementation according to N210 IGWS2 specification section 3.2.7
"""

import struct
from dataclasses import dataclass
from dataclasses import field as field_decorator
from typing import List, Tuple

from src.protocols.mtbp.validation.exceptions import ParseError

from .fields import Field


@dataclass
class MTBPElement:
    """Element within an MTBP array field per N210 spec section 3.2.7

    Element structure:
    - Element Index (1 byte): Zero-based index in array
    - Element Length (2 bytes): Total length of element fields in bytes
    - Element Fields (variable): List of fields in the element

    Attributes:
        index: Zero-based index in array (0-255)
        fields: List of fields contained in this element
    """

    # Format strings for struct packing/unpacking
    HEADER_FORMAT = "!BH"  # B=uint8 (index), H=uint16 (length)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    index: int  # Zero-based index in array
    fields: List[Field] = field_decorator(default_factory=list)  # Element fields

    def __post_init__(self):
        """Validate element attributes after initialization"""
        if not isinstance(self.index, int):
            raise ParseError(
                f"Element index must be an integer, got {type(self.index)}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        if self.index < 0 or self.index > 255:
            raise ParseError(
                f"Element index must be between 0 and 255, got {self.index}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        if not isinstance(self.fields, list):
            raise ParseError(
                f"Element fields must be a list, got {type(self.fields)}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        for field in self.fields:
            if not isinstance(field, Field):
                raise ParseError(
                    f"Element fields must be Field objects, got {type(field)}",
                    error_code=ParseError.INVALID_FIELD_VALUE,
                )

    def to_bytes(self) -> bytes:
        """Convert element to bytes according to N210 spec section 3.2.7"""
        try:
            # Convert fields to bytes first to get total length
            fields_bytes = b"".join(field.to_bytes() for field in self.fields)

            # Pack index and length using struct format
            header = struct.pack(self.HEADER_FORMAT, self.index, len(fields_bytes))

            return header + fields_bytes

        except struct.error as e:
            raise ParseError(
                f"Failed to pack element header: {str(e)}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            ) from e
        except Exception as e:
            raise ParseError(
                f"Failed to convert element to bytes: {str(e)}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            ) from e

    @classmethod
    def from_bytes(cls, data: bytes, field_type_getter) -> Tuple["MTBPElement", int]:
        """Create element from bytes according to N210 spec section 3.2.7

        Args:
            data: Raw bytes to parse
            field_type_getter: Function that returns the FieldType for the next field to parse

        Returns:
            Tuple of (element, bytes_consumed)
        """
        try:
            if len(data) < cls.HEADER_SIZE:
                raise ParseError(
                    f"Insufficient data for element header (need {cls.HEADER_SIZE} bytes)",
                    error_code=ParseError.INVALID_SIZE,
                )

            # Unpack index and length using struct format
            index, length = struct.unpack(cls.HEADER_FORMAT, data[: cls.HEADER_SIZE])

            if len(data) < cls.HEADER_SIZE + length:
                raise ParseError(
                    f"Insufficient data for element fields (need {cls.HEADER_SIZE + length} bytes)",
                    error_code=ParseError.INVALID_SIZE,
                )

            # Create element with empty fields list
            element = cls(index=index)

            # Parse fields from remaining bytes
            pos = cls.HEADER_SIZE
            field_data = data[cls.HEADER_SIZE : cls.HEADER_SIZE + length]
            field_pos = 0

            while field_pos < length:
                # Get field type for next field
                field_type = field_type_getter()

                # Parse field using Field class
                field = Field.from_bytes(field_type, field_data[field_pos:])
                element.fields.append(field)

                # Calculate consumed bytes based on field type and data
                field_bytes = field.to_bytes()
                field_pos += len(field_bytes)
                pos += len(field_bytes)

            return element, pos

        except struct.error as e:
            raise ParseError(
                f"Failed to unpack element header: {str(e)}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            ) from e
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(
                f"Failed to parse element from bytes: {str(e)}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            ) from e
