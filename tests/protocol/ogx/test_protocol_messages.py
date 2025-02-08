"""Tests for OGx protocol-specific message types and performance"""

import time

import pytest

from protocols.ogx.constants import FieldType
from protocols.ogx.encoding.json.decoder import decode_message
from protocols.ogx.encoding.json.encoder import encode_message
from protocols.ogx.exceptions import EncodingError, ValidationError
from protocols.ogx.models.messages import OGxMessage
from protocols.ogx.validation.json.message_validator import OGxMessageValidator


class TestProtocolMessages:
    """Test suite for OGx protocol-specific message types and performance.

    Tests various message types defined in the N214 specification,
    including position messages, status messages, and command messages.
    Also includes performance testing for large and complex messages.
    """

    @pytest.fixture
    def validator(self):
        """Create a message validator instance for testing.

        Returns:
            OGxMessageValidator: A fresh validator instance for each test.
        """
        return OGxMessageValidator()

    @pytest.fixture
    def codec(self):
        """Create a JSON codec instance for testing.

        Returns:
            OGxJsonCodec: A fresh codec instance for each test.
        """
        return OGxJsonCodec()

    def test_position_message(self, validator):
        """Test validation of a position message"""
        message = {
            "Name": "position",
            "SIN": 20,
            "MIN": 1,
            "Fields": [
                {"Name": "fixValid", "Type": "boolean", "Value": True},
                {"Name": "fixType", "Type": "enum", "Value": "3D"},
                {"Name": "latitude", "Type": "signedint", "Value": 2717897},
                {"Name": "longitude", "Type": "signedint", "Value": -4555212},
                {"Name": "altitude", "Type": "signedint", "Value": 760},
                {"Name": "speed", "Type": "unsignedint", "Value": 0},
                {"Name": "heading", "Type": "unsignedint", "Value": 0},
                {"Name": "timestamp", "Type": "signedint", "Value": 1695145141},
            ],
        }
        validator.validate_message(message)  # Should not raise

    def test_status_message(self, validator):
        """Test validation of a status message"""
        message = {
            "Name": "terminalStatus",
            "SIN": 16,
            "MIN": 2,
            "Fields": [
                {"Name": "batteryLevel", "Type": "unsignedint", "Value": 95},
                {"Name": "signalStrength", "Type": "signedint", "Value": -65},
                {"Name": "temperature", "Type": "signedint", "Value": 25},
                {"Name": "lastError", "Type": "string", "Value": "none"},
            ],
        }
        validator.validate_message(message)  # Should not raise

    def test_command_message(self, validator):
        """Test validation of a command message"""
        message = {
            "Name": "command",
            "SIN": 32,
            "MIN": 3,
            "Fields": [
                {"Name": "commandId", "Type": "unsignedint", "Value": 1234},
                {"Name": "commandType", "Type": "enum", "Value": "RESTART"},
                {
                    "Name": "parameters",
                    "Type": "array",
                    "Elements": [
                        {
                            "Index": 0,
                            "Fields": [
                                {"Name": "name", "Type": "string", "Value": "delay"},
                                {"Name": "value", "Type": "unsignedint", "Value": 5},
                            ],
                        }
                    ],
                },
            ],
        }
        validator.validate_message(message)  # Should not raise

    def test_large_message_performance(self, validator, codec):
        """Test performance with large messages"""
        # Create a large message with many fields
        fields = []
        for i in range(1000):  # 1000 fields
            fields.append(
                {
                    "Name": f"field_{i}",
                    "Type": "string",
                    "Value": f"value_{i}" * 10,  # Make each value relatively large
                }
            )

        large_message = {"Name": "large_message", "SIN": 99, "MIN": 1, "Fields": fields}

        # Test validation performance
        start_time = time.time()
        validator.validate_message(large_message)
        validation_time = time.time() - start_time
        assert validation_time < 1.0  # Should validate in under 1 second

        # Test encoding performance
        message_obj = OGxMessage.from_dict(large_message)
        start_time = time.time()
        json_str = codec.encode(message_obj)
        encoding_time = time.time() - start_time
        assert encoding_time < 1.0  # Should encode in under 1 second

        # Test decoding performance
        start_time = time.time()
        decoded = codec.decode(json_str)
        decoding_time = time.time() - start_time
        assert decoding_time < 1.0  # Should decode in under 1 second
        assert len(decoded.fields) == 1000  # Verify all fields were preserved

    def test_deeply_nested_message_performance(self, validator, codec):
        """Test performance with deeply nested message structures"""

        def create_nested_element(depth, width):
            """Create a nested element structure for testing.

            Args:
                depth: Current depth level
                width: Number of elements at each level

            Returns:
                list: List of nested field definitions
            """
            if depth == 0:
                return [{"Name": "leaf", "Type": "string", "Value": "test"}]

            fields = []
            for i in range(width):
                fields.append(
                    {
                        "Name": f"array_{depth}_{i}",
                        "Type": "array",
                        "Elements": [
                            {"Index": j, "Fields": create_nested_element(depth - 1, width)}
                            for j in range(width)
                        ],
                    }
                )
            return fields

        nested_message = {
            "Name": "nested_message",
            "SIN": 99,
            "MIN": 1,
            "Fields": create_nested_element(5, 3),  # Depth 5, Width 3
        }

        # Test validation performance
        start_time = time.time()
        validator.validate_message(nested_message)
        validation_time = time.time() - start_time
        assert validation_time < 1.0  # Should validate in under 1 second

        # Test encoding/decoding performance
        message_obj = OGxMessage.from_dict(nested_message)
        start_time = time.time()
        json_str = codec.encode(message_obj)
        decoded = codec.decode(json_str)
        total_time = time.time() - start_time
        assert total_time < 2.0  # Should complete full cycle in under 2 seconds
        assert len(decoded.fields) > 0  # Verify structure was preserved

    def test_message_with_all_field_types(self, validator):
        """Test message containing all possible field types"""
        message = {
            "Name": "all_types",
            "SIN": 50,
            "MIN": 1,
            "Fields": [
                {"Name": "string_field", "Type": "string", "Value": "test"},
                {"Name": "uint_field", "Type": "unsignedint", "Value": 42},
                {"Name": "int_field", "Type": "signedint", "Value": -42},
                {"Name": "bool_field", "Type": "boolean", "Value": True},
                {"Name": "enum_field", "Type": "enum", "Value": "OPTION_A"},
                {"Name": "data_field", "Type": "data", "Value": "dGVzdA=="},  # "test" in base64
                {
                    "Name": "array_field",
                    "Type": "array",
                    "Elements": [
                        {
                            "Index": 0,
                            "Fields": [{"Name": "sub_field", "Type": "string", "Value": "test"}],
                        }
                    ],
                },
                {
                    "Name": "dynamic_field",
                    "Type": "dynamic",
                    "TypeAttribute": "string",
                    "Value": "test",
                },
                {
                    "Name": "property_field",
                    "Type": "property",
                    "TypeAttribute": "unsignedint",
                    "Value": 42,
                },
            ],
        }
        validator.validate_message(message)  # Should not raise
