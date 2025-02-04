"""
MTBP array element implementation according to N210 IGWS2 specification section 3.2.7
"""

from dataclasses import dataclass
from dataclasses import field as field_decorator
from typing import List

from .fields import MTBPField


@dataclass
class MTBPElement:
    """Element within an MTBP array field per N210 spec section 3.2.7

    Element structure:
    - Element Index (1 byte): Zero-based index in array
    - Element Length (2 bytes): Total length of element fields in bytes
    - Element Fields (variable): List of fields in the element
    """

    index: int  # Zero-based index in array
    fields: List[MTBPField] = field_decorator(default_factory=list)  # Element fields
