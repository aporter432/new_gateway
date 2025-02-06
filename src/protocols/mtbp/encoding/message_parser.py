"""
MTBP message parser.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional

from src.protocols.mtbp.validation.exceptions import ParseError
from src.protocols.mtbp.encoding.header_parser import HeaderParser
from src.protocols.mtbp.encoding.field_parser import FieldParser


class MessageParser:
    """Handles full MTBP message parsing using XML-based message definitions."""

    CONFIG_PATH = Path("src/protocols/mtbp/constants/message_definitions.xml")
    _message_definitions: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def load_message_definitions(cls) -> Dict[str, Dict[str, Any]]:
        """
        Loads message definitions from an XML file and returns them as a dictionary.
        Caches the definitions for subsequent calls.
        """
        if cls._message_definitions is not None:
            return cls._message_definitions

        if not cls.CONFIG_PATH.exists():
            raise FileNotFoundError(f"Message definitions file not found: {cls.CONFIG_PATH}")

        tree = ET.parse(cls.CONFIG_PATH)
        root = tree.getroot()

        definitions = {}
        for msg in root.findall("message"):
            sin = msg.get("SIN")
            min_id = msg.get("MIN")
            if not sin or not min_id:
                continue  # Skip invalid message definitions

            key = f"{sin}:{min_id}"
            fields_elem = msg.find("fields")
            if fields_elem is None:
                continue  # Skip messages without field definitions

            fields = {}
            for field in fields_elem.findall("field"):
                field_name = field.get("name")
                field_type = field.get("type")
                if field_name and field_type:
                    fields[field_name] = {
                        "type": field_type,
                        "optional": field.get("optional", "false").lower() == "true",
                        "description": field.get("description", ""),
                        "default": field.get("default"),
                    }

            definitions[key] = {
                "name": msg.get("name", f"Message_{sin}_{min_id}"),
                "direction": msg.get("direction", "both"),
                "description": msg.get("description", ""),
                "fields": fields,
            }

        cls._message_definitions = definitions
        return definitions

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
        # Extract header using HeaderParser
        header = HeaderParser.parse_header(data)
        sin, min_id = header["SIN"], header["MIN"]

        # Get message definition
        message_key = f"{sin}:{min_id}"
        definitions = cls.load_message_definitions()
        message_def = definitions.get(message_key)

        if not message_def:
            raise ParseError(
                f"Unknown message type SIN={sin}, MIN={min_id}",
                error_code=ParseError.INVALID_SIN,
            )

        # Parse fields
        position = HeaderParser.HEADER_SIZE
        fields = {}

        for field_name, field_info in message_def["fields"].items():
            field_type = field_info["type"].upper()

            try:
                # Handle variable-length fields
                if field_type in ["STRING", "DATA"]:
                    field_value = FieldParser.parse_field(data, position, field_type)
                    position += len(field_value) + (
                        2 if field_type == "DATA" else 1
                    )  # Account for length byte(s)
                else:
                    field_size = FieldParser.get_field_size(field_type)
                    if field_size is None:
                        raise ParseError(
                            f"Unknown field type: {field_type}",
                            error_code=ParseError.INVALID_FIELD_TYPE,
                        )

                    field_value = FieldParser.parse_field(data, position, field_type)
                    position += field_size

                fields[field_name] = field_value

            except (IndexError, ParseError) as e:
                if not field_info["optional"]:
                    raise ParseError(
                        f"Failed to parse required field '{field_name}': {str(e)}",
                        error_code=ParseError.INVALID_FIELD_VALUE,
                    ) from e
                # Skip optional fields that can't be parsed
                continue

        return {
            "header": header,
            "name": message_def["name"],
            "direction": message_def["direction"],
            "fields": fields,
        }

    @staticmethod
    def get_field_definitions(sin: int, min_id: int) -> dict:
        """Retrieves field definitions dynamically from XML."""
        definitions = MessageParser.load_message_definitions()
        return definitions.get(f"{sin}:{min_id}", {}).get("fields", {})
