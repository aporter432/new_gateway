"""OGx protocol message and field models according to OGx-1.txt Section 5."""

from ...protocol.ogx.models.ogx_messages import OGxMessage
from .ogx_fields import Element, Field, Message

__all__ = [
    "Element",
    "Field",
    "Message",
    "OGxMessage",  # The single message type defined in OGx-1.txt Section 5
]
