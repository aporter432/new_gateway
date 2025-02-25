"""OGx protocol validation utilities.

This module provides the foundation for all OGx protocol validation,
implementing the core validation logic defined in the Common Message Format
specification.

Constants imported here are used by child validator classes:
- REQUIRED_FIELD_PROPERTIES: Field validation (Table 3)
- REQUIRED_MESSAGE_FIELDS: Message validation (Section 5.1)
- REQUIRED_ELEMENT_PROPERTIES: Element validation (Section 5.1)
"""

from .ogx_base_validator import OGxBaseValidator
from .ogx_element_validator import OGxElementValidator
from .ogx_field_validator import OGxFieldValidator
from .ogx_network_validator import NetworkValidator
from .ogx_size_validator import SizeValidator
from .ogx_structure_validator import OGxStructureValidator
from .ogx_transport_validator import OGxTransportValidator
from .ogx_type_validator import OGxTypeValidator, ValidationContext, ValidationResult

__all__ = [
    "OGxBaseValidator",
    "OGxFieldValidator",
    "OGxElementValidator",
    "NetworkValidator",
    "SizeValidator",
    "OGxStructureValidator",
    "OGxTransportValidator",
    "OGxTypeValidator",
    "ValidationContext",
    "ValidationResult",
]
