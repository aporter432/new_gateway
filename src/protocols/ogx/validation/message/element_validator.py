"""Element validation according to OGWS-1.txt Section 5.1.

This validator implements the array element validation rules specified in OGWS-1.txt Section 5.1.
According to the specification:
- Elements are indexed structures containing fields
- Each element must have:
  - Index: Zero-based position in array (must be sequential)
  - Fields: Container for element fields
"""

from typing import Any, Dict, List

from ...constants.message_format import REQUIRED_ELEMENT_PROPERTIES
from ..common.base_validator import BaseValidator
from ..common.exceptions import ValidationError
from ..common.types import ValidationContext, ValidationResult


class OGxElementValidator(BaseValidator):
    """Validates array elements according to OGWS-1.txt Section 5.1."""

    def validate_array(
        self, elements: List[Dict[str, Any]], context: ValidationContext
    ) -> ValidationResult:
        """Validate an array of elements according to OGWS-1.txt Section 5.1.

        Args:
            elements: List of element dictionaries to validate
            context: Validation context including network type and direction

        Returns:
            ValidationResult indicating if all elements are valid and any errors
        """
        self.context = context
        self._errors = []

        try:
            if not isinstance(elements, list):
                raise ValidationError("Elements must be an array")

            # Validate each element's structure first
            for element in elements:
                element_result = self.validate(element, context)
                if not element_result.is_valid:
                    for error in element_result.errors:
                        self._add_error(f"Element validation error: {error}")
                    return self._get_validation_result()

            # Then check for sequential indices
            indices = [e.get("Index") for e in elements]
            expected_indices = list(range(len(indices)))
            if indices != expected_indices:
                raise ValidationError("Array elements must have sequential indices starting from 0")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()

    def validate(self, element: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate an individual element's structure and content.

        Args:
            element: The element dictionary to validate containing Index and Fields
            context: Validation context including network type and direction

        Returns:
            ValidationResult indicating if the element is valid and any errors
        """
        self.context = context
        self._errors = []

        try:
            # Validate required properties per OGWS-1.txt Section 5.1
            self._validate_required_fields(element, REQUIRED_ELEMENT_PROPERTIES, "element")

            # Validate Index is non-negative integer (zero-based per spec)
            index = element.get("Index")
            if not isinstance(index, int):
                raise ValidationError("Element Index must be an integer")
            if index < 0:
                raise ValidationError("Element Index must be non-negative (zero-based)")

            # Validate Fields is an array
            fields = element.get("Fields")
            if not isinstance(fields, list):
                raise ValidationError("Element Fields must be an array")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
