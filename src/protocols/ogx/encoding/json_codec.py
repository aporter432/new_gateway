"""
OGx JSON codec according to N214 specification section 5.
Implements encoding/decoding of the Common Message Format.
"""

import json
from typing import Any, Dict, Union

from ..exceptions import EncodingError
from ..models import OGxMessage


class OGxJsonCodec:
    """Encodes/decodes OGx messages to/from JSON format according to N214 section 5"""

    @staticmethod
    def encode(message: OGxMessage) -> str:
        """
        Encode OGx message to JSON string.

        Args:
            message: OGxMessage instance to encode

        Returns:
            JSON string representation of the message

        Raises:
            EncodingError: If message cannot be encoded
        """
        try:
            return json.dumps(message.to_dict())
        except Exception as exc:
            raise EncodingError("Failed to encode message to JSON") from exc

    @staticmethod
    def decode(data: Union[str, Dict[str, Any]]) -> OGxMessage:
        """
        Decode JSON string to OGx message.

        Args:
            data: JSON string or dictionary to decode

        Returns:
            Decoded OGxMessage instance

        Raises:
            EncodingError: If data cannot be decoded
        """
        try:
            if isinstance(data, str):
                dict_data: Dict[str, Any] = json.loads(data)
            else:
                dict_data = data
            return OGxMessage.from_dict(dict_data)
        except Exception as exc:
            raise EncodingError("Failed to decode JSON to message") from exc
