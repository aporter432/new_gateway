"""MTWS Protocol Constants.

This module defines protocol-level constants as specified in N206.
Single Responsibility: Maintain protocol constants in a single source of truth.
"""

import re

# HTTP Methods (N206 section 2.1)
HTTP_POST = "POST"
HTTP_GET = "GET"

# URL Patterns (N206 section 2.1)
SUBMIT_RETURN_URL_PATTERN = "/SubmitReturn/{mobile_id}"
GET_FORWARD_URL_PATTERN = "/GetForward/{mobile_id}"

# Protocol Limits (N206 section 2.4.3)
MAX_MESSAGE_SIZE = 1024  # 1KB total message size limit
MAX_HTTP_HEADER_SIZE = 256  # Maximum HTTP header size
BASE_HTTP_HEADER_SIZE = 97  # Base POST header size
TCP_IP_OVERHEAD = 40  # TCP/IP overhead per direction

# Message Structure (N206 section 2.4.1)
MESSAGE_ENVELOPE_SIZE = 2  # {} bytes
MESSAGE_NAME_BASE_SIZE = 9  # Base bytes for message name
SIN_BASE_SIZE = 7  # Base bytes for SIN
MIN_BASE_SIZE = 7  # Base bytes for MIN
FIELDS_ENVELOPE_SIZE = 12  # Fields envelope bytes
FIELD_ENVELOPE_SIZE = 2  # Field envelope bytes
FIELD_NAME_BASE_SIZE = 10  # Base bytes for field name
FIELD_VALUE_BASE_SIZE = 10  # Base bytes for field value
ELEMENTS_ENVELOPE_SIZE = 16  # Elements envelope bytes
INDEX_BASE_SIZE = 10  # Base bytes for element index

# GPRS Session (N206 section 2.4.3.4)
SESSION_INIT_PACKETS = 3  # SYN, SYN/ACK, ACK
SESSION_TERM_PACKETS = 4  # FIN, ACK, FIN, ACK
SESSION_PACKET_SIZE = 40  # Bytes per session packet
GPRS_ROUNDING_SIZE = 1024  # 1KB rounding for GPRS billing

# Add to existing constants
MAX_NAME_LENGTH = 32
MAX_TYPE_LENGTH = 32
MAX_VALUE_LENGTH = 1024
PROTOCOL_VERSION = "2.0.6"
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")
TYPE_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")
