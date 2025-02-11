"""Integration tests for OGx message validation chain"""

from protocols.ogx.constants import FieldType
from src.protocols.ogx.models.fields import ArrayField, Element, Field
from src.protocols.ogx.models.messages import OGxMessage


def test_complex_nested_structure():
    """Test handling of complex nested message structures"""
    # Create a message with multiple levels of nesting
    nested_fields = [
        ArrayField(
            name="level1",
            type=FieldType.ARRAY,
            elements=[
                Element(
                    index=0,
                    fields=[
                        Field(name="field1", type=FieldType.STRING, value="test"),
                        ArrayField(
                            name="level2",
                            type=FieldType.ARRAY,
                            elements=[
                                Element(
                                    index=0,
                                    fields=[
                                        Field(name="field2", type=FieldType.BOOLEAN, value=True),
                                        ArrayField(
                                            name="level3",
                                            type=FieldType.ARRAY,
                                            elements=[
                                                Element(
                                                    index=0,
                                                    fields=[
                                                        Field(
                                                            name="field3",
                                                            type=FieldType.UNSIGNED_INT,
                                                            value=42,
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

    message = OGxMessage(name="nested_test", sin=16, min=1, fields=nested_fields)

    # Verify structure is preserved
    assert len(message.fields) == 1
    assert isinstance(message.fields[0], ArrayField)
    assert len(message.fields[0].elements) == 1
    assert len(message.fields[0].elements[0].fields) == 2
