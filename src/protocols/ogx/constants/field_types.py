"""Field types as defined in OGWS-1.txt section 5.1 Table 3."""

from enum import Enum


class FieldType(str, Enum):
    """Basic field types from OGWS-1.txt Table 3.

    Note: According to OGWS-1.txt, Dynamic and Property fields use these
    types in their Type Attribute rather than being types themselves.
    """

    ENUM = "enum"
    BOOLEAN = "boolean"
    UNSIGNED_INT = "unsignedint"
    SIGNED_INT = "signedint"
    STRING = "string"
    DATA = "data"
    ARRAY = "array"  # Can only use Elements, not Value
    MESSAGE = "message"  # Can only use Message, not Value
