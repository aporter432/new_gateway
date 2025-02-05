"""Message serialization for MTBP protocol.

This module contains the MTBPMessageSerializer class, which handles serializing MTBP messages
to bytes according to N210 spec section 3.2.
"""

import struct
from typing import List, Tuple

from src.protocols.mtbp.constants.field_types import FieldType
from src.protocols.mtbp.constants.message_types import MessageType
from src.protocols.mtbp.models.fields import Field, FieldSize
from src.protocols.mtbp.models.messages import MTBPMessage
from src.protocols.mtbp.validation.exceptions import ParseError


class MTBPMessageSerializer:
    """Handles MTBP message serialization per N210 spec section 3.2"""

    # SIN (1B), MIN (1B), Sequence (2B), MessageType (1B), Flags (1B)
    HEADER_FORMAT = "!BBHBB"  # B=uint8, H=uint16
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @staticmethod
    def to_bytes(message: MTBPMessage, sequence_number: int) -> bytes:
        """Convert message to bytes according to N210 spec section 3.2

        Args:
            message: Message to serialize
            sequence_number: 16-bit sequence number for ordered delivery
        """
        try:
            # Validate message fields
            if not isinstance(message.sin, int) or message.sin < 0 or message.sin > 255:
                raise ParseError(
                    f"Invalid SIN value: {message.sin}",
                    error_code=ParseError.INVALID_SIN,
                )
            if not isinstance(message.min_id, int) or message.min_id < 0 or message.min_id > 255:
                raise ParseError(
                    f"Invalid MIN value: {message.min_id}",
                    error_code=ParseError.INVALID_MIN,
                )
            if not isinstance(message.message_type, MessageType):
                raise ParseError(
                    f"Invalid message type: {message.message_type}",
                    error_code=ParseError.INVALID_FIELD_TYPE,
                )
            if (
                not isinstance(sequence_number, int)
                or sequence_number < 0
                or sequence_number > 65535
            ):
                raise ParseError(
                    f"Invalid sequence number: {sequence_number}",
                    error_code=ParseError.INVALID_SEQUENCE,
                )

            # Pack header using struct
            header = struct.pack(
                MTBPMessageSerializer.HEADER_FORMAT,
                message.sin,
                message.min_id,
                sequence_number,
                message.message_type.value,
                0x01 if message.is_forward else 0x00,
            )

            # Pack fields
            field_bytes = b"".join(field.to_bytes() for field in message.fields)

            return header + field_bytes

        except struct.error as e:
            raise ParseError(
                f"Failed to pack message header: {str(e)}",
                error_code=ParseError.INVALID_FORMAT,
            ) from e
        except Exception as e:
            raise ParseError(
                f"Failed to serialize message: {str(e)}",
                error_code=ParseError.INVALID_FORMAT,
            ) from e

    @staticmethod
    def from_bytes(data: bytes, field_types: List[FieldType]) -> Tuple[MTBPMessage, int, int]:
        """Create message from bytes according to N210 spec section 3.2

        Args:
            data: Raw bytes to parse
            field_types: List of field types in order of appearance

        Returns:
            Tuple of (message, bytes_consumed, sequence_number)
        """
        try:
            if len(data) < MTBPMessageSerializer.HEADER_SIZE:
                raise ParseError(
                    f"Insufficient data for message header (need {MTBPMessageSerializer.HEADER_SIZE} bytes)",
                    error_code=ParseError.INVALID_SIZE,
                )

            # Unpack header using struct
            sin, min_id, sequence, msg_type, flags = struct.unpack(
                MTBPMessageSerializer.HEADER_FORMAT,
                data[: MTBPMessageSerializer.HEADER_SIZE],
            )

            try:
                message_type = MessageType(msg_type)
            except ValueError as e:
                raise ParseError(
                    f"Invalid message type value: {msg_type}",
                    error_code=ParseError.INVALID_FIELD_TYPE,
                ) from e

            # Create message
            message = MTBPMessage(
                sin=sin,
                min_id=min_id,
                message_type=message_type,
                is_forward=bool(flags & 0x01),
            )

            # Parse fields from remaining data
            pos = MTBPMessageSerializer.HEADER_SIZE
            remaining_data = data[pos:]

            for field_type in field_types:
                if not remaining_data:
                    break

                # Parse field based on type using struct directly
                if field_type in (FieldType.UINT, FieldType.INT, FieldType.ENUM):
                    # Fixed 4-byte integers
                    if len(remaining_data) < FieldSize.UINT:
                        raise ParseError(
                            f"Insufficient data for {field_type.name} field",
                            error_code=ParseError.INVALID_SIZE,
                        )
                    if field_type == FieldType.INT:
                        value = struct.unpack("!i", remaining_data[: FieldSize.INT])[0]
                    else:
                        value = struct.unpack("!I", remaining_data[: FieldSize.UINT])[0]
                    field = Field(field_type, value)
                    consumed = FieldSize.UINT

                elif field_type == FieldType.BOOLEAN:
                    # 1-byte boolean
                    if len(remaining_data) < FieldSize.BOOLEAN:
                        raise ParseError(
                            "Insufficient data for boolean field",
                            error_code=ParseError.INVALID_SIZE,
                        )
                    value = bool(struct.unpack("!B", remaining_data[: FieldSize.BOOLEAN])[0])
                    field = Field(field_type, value)
                    consumed = FieldSize.BOOLEAN

                elif field_type in (FieldType.STRING, FieldType.DATA):
                    # Variable length with 2-byte size prefix
                    if len(remaining_data) < 2:
                        raise ParseError(
                            "Insufficient data for string/data length",
                            error_code=ParseError.INVALID_SIZE,
                        )
                    length = struct.unpack("!H", remaining_data[:2])[0]
                    if len(remaining_data) < 2 + length:
                        raise ParseError(
                            f"Insufficient data for {field_type.name} field content",
                            error_code=ParseError.INVALID_SIZE,
                        )
                    if field_type == FieldType.STRING:
                        try:
                            value = remaining_data[2 : 2 + length].decode("utf-8")
                        except UnicodeDecodeError as e:
                            raise ParseError(
                                "Invalid UTF-8 string data",
                                error_code=ParseError.DECODE_FAILED,
                            ) from e
                    else:
                        value = remaining_data[2 : 2 + length]
                    field = Field(field_type, value)
                    consumed = 2 + length

                else:
                    raise ParseError(
                        f"Unsupported field type: {field_type}",
                        error_code=ParseError.INVALID_FIELD_TYPE,
                    )

                message.add_field(field)
                remaining_data = remaining_data[consumed:]
                pos += consumed

            return message, pos, sequence

        except struct.error as e:
            raise ParseError(
                f"Failed to unpack message data: {str(e)}",
                error_code=ParseError.INVALID_FORMAT,
            ) from e
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(
                f"Failed to parse message: {str(e)}",
                error_code=ParseError.INVALID_FORMAT,
            ) from e
