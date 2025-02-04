"""OGx protocol constants as defined in N214 specification"""

from enum import Enum
from typing import Final


class MessageDirection(str, Enum):
    """Message direction as defined in N214 section 5"""

    TO_MOBILE = "to-mobile"
    FROM_MOBILE = "from-mobile"


class FieldType(str, Enum):
    """Field types as defined in N214 section 5 Common Message Format"""

    STRING = "string"
    BOOLEAN = "boolean"
    UNSIGNED_INT = "unsignedint"
    SIGNED_INT = "signedint"
    ENUM = "enum"
    DATA = "data"
    ARRAY = "array"
    MESSAGE = "message"
    DYNAMIC = "dynamic"
    PROPERTY = "property"


# Message Format Constants
REQUIRED_MESSAGE_FIELDS: Final[set[str]] = {
    "MIN",  # Message identification number
    "SIN",  # Service identification number
    "Name",  # Message name
    "Fields",  # Array of Field instances
}

# Field Format Constants
REQUIRED_FIELD_PROPERTIES: Final[set[str]] = {
    "Name",  # Field name
    "Type",  # Type of the field
    "Value",  # Value of the field
}

# Element Format Constants
REQUIRED_ELEMENT_PROPERTIES: Final[set[str]] = {
    "Index",  # Element's index
    "Fields",  # Element's fields
}
