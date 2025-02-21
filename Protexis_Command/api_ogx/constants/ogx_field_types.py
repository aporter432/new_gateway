"""Field types as defined in OGx-1.txt section 5.1 Table 3.

Field Types from Table 3:
Basic field types:
- enum: Enumeration values
- boolean: True/False values
- unsignedint: Non-negative decimal numbers
- signedint: Signed decimal numbers
- string: String values
- data: Base64 encoded data
- array: Array of elements (no Value attribute)
- message: Embedded message (no Value attribute)
- dynamic: Uses another basic type's attributes
- property: Uses another basic type's attributes

Note: DYNAMIC and PROPERTY fields must specify their Type Attribute
as one of the basic field types above. Their Value Attribute
will match whatever type they reference.
"""

from enum import Enum


class FieldType(str, Enum):
    """Field types from OGx-1.txt Table 3."""

    # Basic field types
    ENUM = "enum"
    BOOLEAN = "boolean"
    UNSIGNED_INT = "unsignedint"
    SIGNED_INT = "signedint"
    STRING = "string"
    DATA = "data"
    ARRAY = "array"
    MESSAGE = "message"
    DYNAMIC = "dynamic"
    PROPERTY = "property"


# Valid type attributes (excludes dynamic and property since they can't be used as attributes)
BASIC_TYPE_ATTRIBUTES = {
    FieldType.ENUM.value,
    FieldType.BOOLEAN.value,
    FieldType.UNSIGNED_INT.value,
    FieldType.SIGNED_INT.value,
    FieldType.STRING.value,
    FieldType.DATA.value,
    FieldType.ARRAY.value,
    FieldType.MESSAGE.value,
}
