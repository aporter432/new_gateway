"""Integration tests for OGx message models.

This module tests the OGx message models according to OGWS-1.txt specifications.

Important:
    NetworkType Usage:
    - ALWAYS use NetworkType enum from protocols.ogx.constants
    - NEVER use string representations of network types
    - NEVER convert NetworkType to/from strings unless required by external API
    - Example:
        CORRECT:   network_type=NetworkType.OGX
        INCORRECT: network_type="OGX" or network_type="1"

    This ensures type safety and consistency across the codebase.
    The NetworkType enum is the single source of truth for network types.

    Model Serialization:
    - When serializing models, network_type must remain as NetworkType enum
    - Only convert to string/int at API boundaries if required
    - Validation must use NetworkType enum for type checking
    - Model dumps should preserve NetworkType enum values
"""

from protocols.ogx.constants import NetworkType  # Always import NetworkType enum

# Test cases will be implemented here
