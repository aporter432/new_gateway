"""
MTBP message parser.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, cast

from src.protocols.mtbp.validation.exceptions import ParseError
from src.protocols.mtbp.encoding.header_parser import HeaderParser
from src.protocols.mtbp.encoding.field_parser import FieldParser


class MessageParser:
    """Handles full MTBP message parsing using XML-based message definitions."""

    CONFIG_PATH: Path = Path("config/message_definitions.xml")
    _message_definitions: Optional[Dict[str, Any]] = None

    @classmethod
    def load_message_definitions(cls) -> Dict[str, Any]:
        """
        Loads message definitions from an XML file and returns them as a dictionary.
        Caches the definitions for subsequent calls.

        Returns:
            Dict containing message definitions indexed by 'SIN:MIN'.

        Raises:
            ET.ParseError: If XML file is invalid.
            FileNotFoundError: If config file doesn't exist.
        """
        if cls._message_definitions is not None:
            return cls._message_definitions

        try:
            tree = ET.parse(cls.CONFIG_PATH)
            root = tree.getroot()

            definitions = {}
            for message in root.findall("message"):
                sin_str = cast(str, message.get("SIN"))
                min_str = cast(str, message.get("MIN"))
                if not sin_str or not min_str:
                    continue

                try:
                    sin = int(sin_str)
                    min_val = int(min_str)
                except ValueError as e:
                    raise ET.ParseError(f"Invalid SIN/MIN values: {str(e)}") from e

                key = f"{sin}:{min_val}"

                fields = {}
                for field in message.findall(".//field"):
                    field_def = {
                        "name": field.get("name"),
                        "type": field.get("type"),
                        "description": field.get("description"),
                        "optional": field.get("optional", "false").lower() == "true",
                    }
                    fields[field_def["name"]] = field_def

                definitions[key] = {
                    "name": message.get("name"),
                    "direction": message.get("direction"),
                    "fields": fields,
                }

            cls._message_definitions = definitions
            return definitions

        except ET.ParseError:
            # Re-raise the ET.ParseError directly
            raise
        except FileNotFoundError as e:
            # Re-raise FileNotFoundError with our custom message but preserve the original cause
            raise FileNotFoundError(f"Message definitions file not found: {cls.CONFIG_PATH}") from e
        except Exception as e:
            # Convert unexpected errors to ET.ParseError but preserve the original cause
            raise ET.ParseError(f"Error parsing message definitions: {str(e)}") from e

    @classmethod
    def parse_message(cls, data: bytes) -> Dict[str, Any]:
        """
        Parses a complete MTBP message, extracting the header and fields.

        Args:
            data (bytes): The raw binary message.

        Returns:
            dict: Parsed message containing header and field data.

        Raises:
            ParseError: If message is malformed or has CRC issues.
        """
        try:
            # Parse header first to validate message integrity
            header = HeaderParser.parse_header(data)

            # Load message definitions (may raise ET.ParseError)
            try:
                definitions = cls.load_message_definitions()
            except ET.ParseError as e:
                raise ParseError(f"XML parsing error: {str(e)}", ParseError.INVALID_FORMAT) from e

            key = f"{header['SIN']}:{header['MIN']}"

            if key not in definitions:
                raise ParseError(
                    f"Unknown message type SIN={header['SIN']}, MIN={header['MIN']}",
                    ParseError.INVALID_SIN,
                ) from None

            message_def = definitions[key]
            payload = data[HeaderParser.HEADER_SIZE + HeaderParser.CRC_SIZE :]

            # Parse fields
            fields = {}
            offset = 0

            for field_name, field_def in message_def["fields"].items():
                # Skip optional fields if we've reached the end of the payload
                if offset >= len(payload):
                    if not field_def["optional"]:
                        raise ParseError(
                            f"Missing required field {field_name}",
                            ParseError.INVALID_FIELD_VALUE,
                        ) from None  # Explicit None cause for missing field
                    continue

                try:
                    field_type = cast(str, field_def["type"])
                    value, bytes_consumed = FieldParser.parse_field(
                        data=payload[offset:], position=0, field_type=field_type
                    )
                    fields[field_name] = value
                    offset += bytes_consumed
                except ParseError as e:
                    raise ParseError(
                        f"Failed to parse field {field_name}: {str(e)}", e.error_code
                    ) from e
                except Exception as e:
                    raise ParseError(
                        f"Unexpected error parsing field {field_name}: {str(e)}",
                        ParseError.INVALID_FIELD_VALUE,
                    ) from e

            # Verify we consumed exactly the expected number of bytes
            if offset != header["length"]:
                raise ParseError(
                    f"Message length mismatch: expected {header['length']}, got {offset}",
                    ParseError.INVALID_SIZE,
                ) from None  # Explicit None cause for length mismatch

            return {"header": header, "name": message_def["name"], "fields": fields}

        except ParseError as e:
            # Re-raise ParseError with cause preserved
            raise ParseError(str(e), e.error_code) from e.__cause__
        except ET.ParseError as e:
            # Convert ET.ParseError to ParseError but preserve the original cause
            raise ParseError(f"XML parsing error: {str(e)}", ParseError.INVALID_FORMAT) from e
        except Exception as e:
            # Convert unexpected errors to ParseError but preserve the original cause
            raise ParseError(f"Failed to parse message: {str(e)}", ParseError.INVALID_SIZE) from e

    @staticmethod
    def get_field_definitions(sin: int, min_id: int) -> dict:
        """Retrieves field definitions dynamically from XML."""
        definitions = MessageParser.load_message_definitions()
        return definitions.get(f"{sin}:{min_id}", {}).get("fields", {})
