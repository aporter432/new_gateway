"""Integration tests for return message endpoints.

This module tests the return message API endpoints according to OGx-1.txt specifications.

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

    Return Message Context:
    - Return messages must specify network type in ValidationContext
    - Network type determines available transport options
    - Network type affects message size limits
"""

# Test cases will be implemented here
