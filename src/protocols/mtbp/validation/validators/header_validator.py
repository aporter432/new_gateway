"""MTBP Header Validator

Validates MTBP message headers according to IGWS2 specification.
"""

from ...models.messages import MTBPMessage
from ..exceptions import ParseError


class MTBPHeaderValidator:
    """Validates MTBP message headers"""

    def validate(self, message: MTBPMessage) -> bool:
        """
        Validate MTBP message header.

        Checks:
        - SIN (Service ID) presence and range (0-255)
        - MIN (Message ID) presence and range (0-255)
        """
        if not message.sin or not message.min_id:
            raise ParseError("Missing required header fields (SIN/MIN)", ParseError.MISSING_FIELD)

        if not 0 <= message.sin <= 255 or not 0 <= message.min_id <= 255:
            raise ParseError(
                "SIN/MIN values out of valid range (0-255)", ParseError.INVALID_FIELD_VALUE
            )

        return True
