"""Tests for MTBP message parser.

This module contains tests that verify the XML-based message parsing functionality
of the MTBP protocol implementation.
"""

import os
import tempfile
from pathlib import Path
import pytest
from typing import Dict, Any, Generator
import xml.etree.ElementTree as ET

from src.protocols.mtbp.encoding.message_parser import MessageParser
from src.protocols.mtbp.validation.exceptions import ParseError
from src.protocols.mtbp.encoding.field_parser import FieldParser
from src.protocols.mtbp.encoding.header_parser import HeaderParser
from src.protocols.utils import compute_crc16_ccitt


class TestMessageParser:
    """Test suite for MTBP message parser."""

    @pytest.fixture
    def sample_xml(self) -> str:
        """Sample XML message definitions for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <messages>
            <message SIN="1" MIN="1" name="TestMessage1" direction="both">
                <fields>
                    <field name="field1" type="UINT8" description="Test field 1"/>
                    <field name="field2" type="STRING" description="Test field 2"/>
                    <field name="field3" type="BOOLEAN" optional="true" description="Optional field"/>
                </fields>
            </message>
            <message SIN="2" MIN="1" name="TestMessage2" direction="forward">
                <fields>
                    <field name="data" type="DATA" description="Binary data field"/>
                    <field name="value" type="INT16" description="Signed integer field"/>
                </fields>
            </message>
        </messages>
        """

    @pytest.fixture
    def xml_file(self, sample_xml: str, monkeypatch) -> Generator[Path, None, None]:
        """Create a temporary XML file with sample message definitions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(sample_xml)
            temp_path = Path(f.name)

        # Monkeypatch the CONFIG_PATH to use our temporary file
        monkeypatch.setattr(MessageParser, "CONFIG_PATH", temp_path)

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    def test_load_message_definitions(self, xml_file: Path):
        """Test loading message definitions from XML file."""
        definitions = MessageParser.load_message_definitions()

        # Test basic structure
        assert isinstance(definitions, dict)
        assert "1:1" in definitions
        assert "2:1" in definitions

        # Test first message definition
        msg1 = definitions["1:1"]
        assert msg1["name"] == "TestMessage1"
        assert msg1["direction"] == "both"
        assert len(msg1["fields"]) == 3

        # Test field definitions
        field1 = msg1["fields"]["field1"]
        assert field1["type"] == "UINT8"
        assert not field1["optional"]

        field3 = msg1["fields"]["field3"]
        assert field3["type"] == "BOOLEAN"
        assert field3["optional"]

    def test_parse_message_basic(self, xml_file: Path):
        """Test parsing a basic message with fixed-size fields."""
        # Create a test message with UINT8=5, STRING="test", and BOOLEAN=True
        message_data = (
            bytes([5]) + bytes([4]) + b"test" + bytes([1])
        )  # field1=5, field2="test", field3=True
        total_length = len(message_data)

        header = bytes(
            [
                1,  # SIN
                1,  # MIN
                total_length,  # Length (payload only)
            ]
        )

        # Calculate CRC for header + payload
        data_for_crc = header + message_data
        crc = compute_crc16_ccitt(data_for_crc)
        crc_bytes = crc.to_bytes(2, byteorder="big")

        data = header + crc_bytes + message_data

        result = MessageParser.parse_message(data)

        assert result["header"]["SIN"] == 1
        assert result["header"]["MIN"] == 1
        assert result["name"] == "TestMessage1"
        assert result["fields"]["field1"] == 5
        assert result["fields"]["field2"] == "test"
        assert result["fields"]["field3"] is True

    def test_parse_message_variable_length(self, xml_file: Path):
        """Test parsing a message with variable-length fields."""
        # Create a test message with DATA field and INT16 field
        test_data = b"Hello"
        data_length = len(test_data)
        length_bytes = data_length.to_bytes(2, byteorder="big")
        value_bytes = (42).to_bytes(2, byteorder="big", signed=True)  # INT16 value of 42

        message_data = length_bytes + test_data + value_bytes
        total_length = len(message_data)

        header = bytes(
            [
                2,  # SIN
                1,  # MIN
                total_length,  # Length (payload only)
            ]
        )

        # Calculate CRC for header + payload
        data_for_crc = header + message_data
        crc = compute_crc16_ccitt(data_for_crc)
        crc_bytes = crc.to_bytes(2, byteorder="big")

        data = header + crc_bytes + message_data

        result = MessageParser.parse_message(data)

        assert result["header"]["SIN"] == 2
        assert result["header"]["MIN"] == 1
        assert result["name"] == "TestMessage2"
        assert result["fields"]["data"] == test_data
        assert result["fields"]["value"] == 42

    def test_parse_message_invalid_sin_min(self, xml_file: Path):
        """Test parsing a message with unknown SIN/MIN combination."""
        header = bytes(
            [
                99,  # Invalid SIN
                99,  # Invalid MIN
                0,  # Length (no payload)
            ]
        )

        # Calculate CRC for header only
        crc = compute_crc16_ccitt(header)
        crc_bytes = crc.to_bytes(2, byteorder="big")

        data = header + crc_bytes

        with pytest.raises(ParseError) as exc_info:
            MessageParser.parse_message(data)

        assert exc_info.value.error_code == ParseError.INVALID_SIN
        assert "Unknown message type" in str(exc_info.value)

    def test_parse_message_invalid_field(self, xml_file: Path):
        """Test parsing a message with invalid field data."""
        # Create message with insufficient data for field
        message_data = bytes([5])  # Incomplete field data
        total_length = len(message_data)

        header = bytes(
            [
                1,  # SIN
                1,  # MIN
                total_length,  # Length (payload only)
            ]
        )

        # Calculate CRC for header + payload
        data_for_crc = header + message_data
        crc = compute_crc16_ccitt(data_for_crc)
        crc_bytes = crc.to_bytes(2, byteorder="big")

        data = header + crc_bytes + message_data

        with pytest.raises(ParseError) as exc_info:
            MessageParser.parse_message(data)

        assert exc_info.value.error_code == ParseError.INVALID_FIELD_VALUE

    def test_parse_message_with_optional_fields(self, xml_file: Path):
        """Test parsing a message with missing optional fields."""
        # Create message with required fields but without the optional boolean field
        message_data = bytes([5]) + bytes([4]) + b"test"  # field1=5, field2="test"
        total_length = len(message_data)

        header = bytes(
            [
                1,  # SIN
                1,  # MIN
                total_length,  # Length (payload only)
            ]
        )

        # Calculate CRC for header + payload
        data_for_crc = header + message_data
        crc = compute_crc16_ccitt(data_for_crc)
        crc_bytes = crc.to_bytes(2, byteorder="big")

        data = header + crc_bytes + message_data

        result = MessageParser.parse_message(data)

        assert result["header"]["SIN"] == 1
        assert result["fields"]["field1"] == 5
        assert result["fields"]["field2"] == "test"
        assert "field3" not in result["fields"]  # Optional field omitted

    def test_message_definition_caching(self, xml_file: Path):
        """Test that message definitions are properly cached."""
        # First call should load from file
        definitions1 = MessageParser.load_message_definitions()

        # Modify the file
        with open(xml_file, "w") as f:
            f.write("<messages></messages>")

        # Second call should use cached version
        definitions2 = MessageParser.load_message_definitions()

        assert definitions1 == definitions2
        assert "1:1" in definitions2  # Should still have original definitions

    def test_invalid_xml_file(self, monkeypatch):
        """Test handling of invalid XML file."""
        # Create temporary file with invalid XML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("Invalid XML content")
            temp_path = Path(f.name)

        monkeypatch.setattr(MessageParser, "CONFIG_PATH", temp_path)

        # Clear the cache to force loading from file
        MessageParser._message_definitions = None

        with pytest.raises(ET.ParseError) as exc_info:
            MessageParser.load_message_definitions()

        assert "syntax error" in str(exc_info.value)

        # Cleanup
        os.unlink(temp_path)

    def test_exception_chaining(self, xml_file: Path):
        """Test that exceptions are properly chained."""
        # Create message with invalid data that will cause IndexError
        data = bytes([1, 1])  # Too short, will cause IndexError

        with pytest.raises(ParseError) as exc_info:
            MessageParser.parse_message(data)

        assert exc_info.value.error_code == ParseError.INVALID_SIZE
        assert exc_info.value.__cause__ is not None  # Should have chained exception
