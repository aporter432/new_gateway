"""Integration tests for message chain validation.

Tests validation of message chains according to OGx-1.txt specifications.
"""

from Protexis_Command.protocol.ogx.constants import FieldType
from Protexis_Command.protocol.ogx.models.fields import Element, Field, Message


def test_complex_nested_structure():
    """Test handling of complex nested message structures"""
    # Create a message with multiple levels of nesting
    nested_fields = [
        Field(
            Name="level1",
            Type=FieldType.ARRAY,
            Elements=[
                Element(
                    Index=0,
                    Fields=[
                        Field(Name="field1", Type=FieldType.STRING, Value="test"),
                        Field(
                            Name="level2",
                            Type=FieldType.ARRAY,
                            Elements=[
                                Element(
                                    Index=0,
                                    Fields=[
                                        Field(Name="field2", Type=FieldType.BOOLEAN, Value=True),
                                        Field(
                                            Name="level3",
                                            Type=FieldType.ARRAY,
                                            Elements=[
                                                Element(
                                                    Index=0,
                                                    Fields=[
                                                        Field(
                                                            Name="field3",
                                                            Type=FieldType.UNSIGNED_INT,
                                                            Value=42,
                                                        )
                                                    ],
                                                )
                                            ],
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                )
            ],
        )
    ]

    message = Message(Name="nested_test", SIN=16, MIN=1, Fields=nested_fields)

    # Verify structure is preserved
    assert len(message.Fields) == 1
    assert message.Fields[0].Type == FieldType.ARRAY
    assert message.Fields[0].Elements is not None, "Array field should have elements"
    assert len(message.Fields[0].Elements) == 1
    assert message.Fields[0].Elements[0].Fields is not None, "Element should have fields"
    assert len(message.Fields[0].Elements[0].Fields) == 2
